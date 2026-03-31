#!/usr/bin/env python3
"""推送天下要闻到微信 AI"""
import json
import pathlib
import subprocess
import sys

DATA = pathlib.Path('data')

def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default if default is not None else {}


def push_to_weixin():
    """Push morning brief to Weixin AI."""
    cfg = read_json(DATA / 'morning_brief_config.json', {})
    if not cfg:
        print('❌ 天下要闻配置未找到')
        return False
    
    brief = read_json(DATA / 'morning_brief.json', {})
    date_str = brief.get('date', '')
    total = sum(len(v) for v in (brief.get('categories') or {}).values())
    
    if not total:
        print('⚠️ 今日暂无要闻数据，请先点击「立即采集」按钮')
        return False
    
    cat_lines = []
    for cat, items in (brief.get('categories') or {}).items():
        if items:
            cat_lines.append(f'  {cat}: {len(items)} 条')
    summary = '\n'.join(cat_lines)
    date_fmt = date_str[:4] + '年' + date_str[4:6] + '月' + date_str[6:] + '日' if len(date_str) == 8 else date_str
    
    message = f'''📰 天下要闻 · {date_fmt}
共 **{total}** 条要闻已更新
{summary}

🔗 查看完整简报: http://127.0.0.1:7891

采集于 {brief.get('generated_at', '')}'''
    
    print('正在推送微信 AI...')
    
    try:
        result = subprocess.run(
            ['openclaw', 'message', 'send',
             '--channel', 'openclaw-weixin',
             '--target', 'o9cq802KkVl3OKboQH--12ttmTag@im.wechat',
             '--message', message],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f'✅ 微信推送成功!')
            print(result.stdout)
            return True
        else:
            print(f'❌ 微信推送失败: {result.stderr}')
            return False
            
    except FileNotFoundError:
        print('❌ openclaw 命令未找到，请确保 OpenClaw 已安装并配置')
        return False
    except Exception as e:
        print(f'❌ 微信推送失败: {e}')
        return False


if __name__ == '__main__':
    success = push_to_weixin()
    sys.exit(0 if success else 1)
