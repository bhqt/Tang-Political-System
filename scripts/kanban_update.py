#!/usr/bin/env python3
"""
看板任务更新工具 - 供各省部 Agent 调用 (Windows 兼容版本)

用法:
  # 新建任务（收旨时）
  python kanban_update.py create ZYQ-20260223-012 "任务标题" Zhongshu 中书省 中书令

  # 更新状态
  python kanban_update.py state ZYQ-20260223-012 Menxia "规划方案已提交门下省"

  # 添加流转记录
  python kanban_update.py flow ZYQ-20260223-012 "中书省" "门下省" "规划方案提交审核"

  # 完成任务
  python kanban_update.py done ZYQ-20260223-012 "/path/to/output" "任务完成摘要"

  # 添加/更新子任务 todo
  python kanban_update.py todo ZYQ-20260223-012 1 "实现API接口" in-progress
  python kanban_update.py todo ZYQ-20260223-012 1 "" completed

  # 实时进展汇报（Agent 主动调用，频率不限）
  python kanban_update.py progress ZYQ-20260223-012 "正在分析需求，拟定3个子方案" "1.调研技术选型|2.撰写设计文档|3.实现原型"
"""
import json
import pathlib
import datetime
import sys
import subprocess
import logging
import os
import re

# 使用相对于脚本的路径
EDICT_HOME = pathlib.Path(__file__).resolve().parent.parent
TASKS_FILE = EDICT_HOME / 'data' / 'tasks_source.json'
REFRESH_SCRIPT = EDICT_HOME / 'scripts' / 'refresh_live_data.py'

log = logging.getLogger('kanban')
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s', datefmt='%H:%M:%S')

# 文件锁 —— 防止多 Agent 同时读写 tasks_source.json
from file_lock import atomic_json_read, atomic_json_update, atomic_json_write

STATE_ORG_MAP = {
    'Emperor': '皇上', 'Zhongshu': '中书省', 'Menxia': '门下省', 'Assigned': '尚书省',
    'Doing': '执行中', 'Review': '尚书省', 'Done': '完成', 'Blocked': '阻塞',
}

_STATE_AGENT_MAP = {
    'Emperor': 'main',
    'Zhongshu': 'zhongshu',
    'Menxia': 'menxia',
    'Assigned': 'shangshu',
    'Review': 'shangshu',
    'Pending': 'zhongshu',
}

_ORG_AGENT_MAP = {
    '礼部': 'libu', '户部': 'hubu', '兵部': 'bingbu',
    '刑部': 'xingbu', '工部': 'gongbu', '吏部': 'libu_hr',
    '中书省': 'zhongshu', '门下省': 'menxia', '尚书省': 'shangshu',
}

_AGENT_LABELS = {
    'main': '皇上', 'emperor': '皇上',
    'zhongshu': '中书省', 'menxia': '门下省', 'shangshu': '尚书省',
    'libu': '礼部', 'hubu': '户部', 'bingbu': '兵部', 'xingbu': '刑部',
    'gongbu': '工部', 'libu_hr': '吏部', 'zaochao': '钦天监',
}

MAX_PROGRESS_LOG = 100  # 单任务最大进展日志条数

def load():
    return atomic_json_read(TASKS_FILE, [])

def save(tasks):
    atomic_json_write(TASKS_FILE, tasks)
    # 异步触发刷新，不阻塞调用方
    try:
        subprocess.Popen(['python', str(REFRESH_SCRIPT)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')

def find_task(tasks, task_id):
    return next((t for t in tasks if t.get('id') == task_id), None)

def _infer_agent_id_from_runtime():
    """从运行时环境推断当前 Agent ID"""
    # 尝试从环境变量获取
    agent_id = os.environ.get('EDICT_AGENT_ID', '')
    if agent_id:
        return agent_id
    # 尝试从当前工作目录推断
    cwd = os.getcwd()
    for aid, label in _AGENT_LABELS.items():
        if aid in cwd.lower():
            return aid
    return 'unknown'

# 旨意标题最低要求
_MIN_TITLE_LEN = 6
_JUNK_TITLES = {
    '?', '？', '好', '好的', '是', '否', '不', '不是', '对', '了解', '收到',
    '嗯', '哦', '知道了', '开启了么', '可以', '不行', '行', 'ok', 'yes', 'no',
    '你去开启', '测试', '试试', '看看',
}

def _sanitize_text(raw, max_len=80):
    """清洗文本：剥离文件路径、URL、Conversation 元数据、传旨前缀、截断过长内容。"""
    t = (raw or '').strip()
    # 1) 剥离 Conversation info / Conversation 后面的所有内容
    t = re.split(r'\n*Conversation\b', t, maxsplit=1)[0].strip()
    # 2) 剥离 ```json 代码块
    t = re.split(r'\n*```', t, maxsplit=1)[0].strip()
    # 3) 剥离文件路径 (Windows/Linux)
    t = re.sub(r'[A-Za-z]:[\\/][^\n]*', '', t)
    t = re.sub(r'/[\w\-./]+/[\w\-./]+', '', t)
    # 4) 剥离 URL
    t = re.sub(r'https?://\S+', '', t)
    # 5) 剥离传旨前缀
    t = re.sub(r'^(传旨|圣旨|下旨|口谕)[：:\s]*', '', t, flags=re.IGNORECASE)
    # 6) 清理多余空格
    t = re.sub(r'\s+', ' ', t).strip()
    # 7) 截断
    if len(t) > max_len:
        t = t[:max_len-3] + '...'
    return t

def _sanitize_remark(raw):
    """清洗流转备注文本"""
    return _sanitize_text(raw, 120)

def _validate_title(title):
    """验证标题是否有效"""
    if not title or len(title.strip()) < _MIN_TITLE_LEN:
        return False, f"标题太短（至少{_MIN_TITLE_LEN}字符）"
    if title.strip() in _JUNK_TITLES:
        return False, "标题无效（无意义内容）"
    # 检查是否包含路径或URL
    if re.search(r'[A-Za-z]:[\\/]|https?://', title):
        return False, "标题包含路径或URL"
    return True, ""

def cmd_create(task_id, title, state, org, official, remark=''):
    """新建任务"""
    clean_title = _sanitize_text(title)
    clean_remark = _sanitize_remark(remark)
    
    valid, msg = _validate_title(clean_title)
    if not valid:
        log.warning(f'标题验证失败: {msg}，使用默认标题')
        clean_title = f"未命名任务_{task_id}"
    
    def modifier(tasks):
        if find_task(tasks, task_id):
            log.warning(f'任务 {task_id} 已存在，跳过创建')
            return tasks
        
        new_task = {
            'id': task_id,
            'title': clean_title,
            'state': state,
            'org': org,
            'official': official,
            'now': clean_remark[:60] if clean_remark else '任务已创建',
            'eta': '-',
            'block': '无',
            'output': '',
            'ac': '',
            'flow_log': [{'at': now_iso(), 'from': '皇上', 'to': org, 'remark': clean_remark or '下旨'}],
            'todos': [],
            'progress_log': [],
            'updatedAt': now_iso()
        }
        tasks.append(new_task)
        return tasks
        return tasks
    
    atomic_json_update(TASKS_FILE, modifier, [])
    log.info(f'[看板] 创建任务 {task_id}: {clean_title[:40]}...')
    print(f'[看板] 任务 {task_id} 已创建', flush=True)

def cmd_state(task_id, state, remark=''):
    """更新任务状态"""
    clean_remark = _sanitize_remark(remark)
    def modifier(tasks):
        task = find_task(tasks, task_id)
        if not task:
            log.warning(f'任务 {task_id} 不存在')
            return tasks
        old_state = task.get('state', '')
        task['state'] = state
        task['now'] = clean_remark[:60] if clean_remark else f'状态更新：{state}'
        task['updatedAt'] = now_iso()
        if clean_remark:
            task.setdefault('flow_log', []).append({
                "at": now_iso(), "from": task.get('org', ''), "to": STATE_ORG_MAP.get(state, state),
                "remark": clean_remark
            })
        log.info(f'[看板] {task_id} {old_state} -> {state}')
        return tasks
    atomic_json_update(TASKS_FILE, modifier, [])
    print(f'[看板] {task_id} 状态更新为 {state}', flush=True)

def cmd_flow(task_id, from_dept, to_dept, remark):
    """添加流转记录"""
    clean_remark = _sanitize_remark(remark)
    def modifier(tasks):
        task = find_task(tasks, task_id)
        if not task:
            log.warning(f'任务 {task_id} 不存在')
            return tasks
        task.setdefault('flow_log', []).append({
            "at": now_iso(), "from": from_dept, "to": to_dept, "remark": clean_remark
        })
        task['updatedAt'] = now_iso()
        log.info(f'[看板] {task_id} 流转: {from_dept} -> {to_dept}')
        return tasks
    atomic_json_update(TASKS_FILE, modifier, [])
    print(f'[看板] {task_id} 流转记录已添加', flush=True)

def cmd_done(task_id, output_path='', ac=''):
    """完成任务"""
    def modifier(tasks):
        task = find_task(tasks, task_id)
        if not task:
            log.warning(f'任务 {task_id} 不存在')
            return tasks
        task['state'] = 'Done'
        task['now'] = '✅ 已完成'
        task['output'] = output_path
        task['ac'] = ac
        task['updatedAt'] = now_iso()
        task.setdefault('flow_log', []).append({
            "at": now_iso(), "from": task.get('org', ''), "to": "皇上",
            "remark": f"任务完成，回奏：{ac[:60] if ac else '已完成'}"
        })
        log.info(f'[看板] {task_id} 已完成')
        return tasks
    atomic_json_update(TASKS_FILE, modifier, [])
    print(f'[看板] {task_id} 已标记为完成', flush=True)

def cmd_todo(task_id, todo_id, title='', status=''):
    """添加/更新子任务"""
    def modifier(tasks):
        task = find_task(tasks, task_id)
        if not task:
            log.warning(f'任务 {task_id} 不存在')
            return tasks
        todos = task.setdefault('todos', [])
        existing = next((t for t in todos if str(t.get('id')) == str(todo_id)), None)
        if existing:
            if title:
                existing['title'] = title
            if status:
                existing['status'] = status
        else:
            todos.append({"id": str(todo_id), "title": title or f"子任务{todo_id}", "status": status or "not-started"})
        task['updatedAt'] = now_iso()
        return tasks
    atomic_json_update(TASKS_FILE, modifier, [])
    print(f'[看板] {task_id} todo 已更新', flush=True)

def cmd_progress(task_id, text='', todos_text='', agent_id=''):
    """实时进展汇报（Agent 主动调用，频率不限）"""
    # 推断 Agent ID
    if not agent_id:
        agent_id = _infer_agent_id_from_runtime()
    agent_label = _AGENT_LABELS.get(agent_id, agent_id)
    
    # 解析 todos_text（格式: "标题1|标题2|标题3" 或 "1:标题1|2:标题2"）
    todos = []
    if todos_text:
        items = todos_text.split('|')
        for i, item in enumerate(items):
            item = item.strip()
            if not item:
                continue
            # 支持 "1:标题" 格式
            if ':' in item:
                parts = item.split(':', 1)
                tid = parts[0].strip()
                ttitle = parts[1].strip()
            else:
                tid = str(i + 1)
                ttitle = item
            todos.append({"id": tid, "title": ttitle, "status": "in-progress"})
    
    def modifier(tasks):
        task = find_task(tasks, task_id)
        if not task:
            log.warning(f'任务 {task_id} 不存在')
            return tasks
        
        # 获取当前状态
        state = task.get('state', '')
        org = task.get('org', '')
        
        # 追加进展日志
        progress_entry = {
            "at": now_iso(),
            "agent": agent_id,
            "agentLabel": agent_label,
            "state": state,
            "org": org,
            "text": _sanitize_text(text, 200) if text else '',
            "todos": todos if todos else None,
        }
        
        # 清理 None 值
        progress_entry = {k: v for k, v in progress_entry.items() if v is not None}
        
        progress_log = task.setdefault('progress_log', [])
        progress_log.append(progress_entry)
        
        # 限制日志条数
        if len(progress_log) > MAX_PROGRESS_LOG:
            progress_log[:] = progress_log[-MAX_PROGRESS_LOG:]
        
        # 同时更新当前 now 字段（供快速查看）
        if text:
            task['now'] = f"[{agent_label}] {_sanitize_text(text, 60)}"
        
        task['updatedAt'] = now_iso()
        return tasks
    
    atomic_json_update(TASKS_FILE, modifier, [])
    log.info(f'[看板] {task_id} 进展汇报: {agent_label} - {text[:40] if text else "(无文本)"}...')
    print(f'[看板] {task_id} 进展已记录', flush=True)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'create':
        if len(sys.argv) < 7:
            print('用法: kanban_update.py create <task_id> <title> <state> <org> <official> [remark]')
            sys.exit(1)
        cmd_create(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7] if len(sys.argv) > 7 else '')
    elif cmd == 'state':
        if len(sys.argv) < 4:
            print('用法: kanban_update.py state <task_id> <state> [remark]')
            sys.exit(1)
        cmd_state(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else '')
    elif cmd == 'flow':
        if len(sys.argv) < 6:
            print('用法: kanban_update.py flow <task_id> <from> <to> <remark]')
            sys.exit(1)
        cmd_flow(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif cmd == 'done':
        if len(sys.argv) < 3:
            print('用法: kanban_update.py done <task_id> [output_path] [ac]')
            sys.exit(1)
        cmd_done(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '', sys.argv[4] if len(sys.argv) > 4 else '')
    elif cmd == 'todo':
        if len(sys.argv) < 4:
            print('用法: kanban_update.py todo <task_id> <todo_id> [title] [status]')
            sys.exit(1)
        cmd_todo(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else '', sys.argv[5] if len(sys.argv) > 5 else '')
    elif cmd == 'progress':
        if len(sys.argv) < 3:
            print('用法: kanban_update.py progress <task_id> [text] [todos_text]')
            sys.exit(1)
        cmd_progress(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '', sys.argv[4] if len(sys.argv) > 4 else '')
    else:
        print(f'未知命令: {cmd}')
        print(__doc__)
        sys.exit(1)