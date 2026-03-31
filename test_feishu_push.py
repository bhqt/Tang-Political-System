#!/usr/bin/env python3
"""测试飞书推送功能"""
import json
import pathlib
from urllib.request import Request, urlopen

DATA = pathlib.Path('data')

# 读取配置
config_file = DATA / 'morning_brief_config.json'
config = json.loads(config_file.read_text())
webhook = config.get('feishu_webhook', '').strip()

if not webhook or webhook == 'https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx':
    print('❌ 飞书 Webhook URL 未配置或使用了示例 URL')
    print('请先在 http://127.0.0.1:7891 的天下要闻页面配置真实的飞书 Webhook URL')
    print('或编辑 data/morning_brief_config.json 文件')
else:
    print('飞书 Webhook URL 已配置:', webhook)
    
    # 读取今日要闻
    brief_file = DATA / 'morning_brief.json'
    brief = json.loads(brief_file.read_text())
    date_str = brief.get('date', '')
    total = sum(len(v) for v in brief.get('categories', {}).values())
    
    if total > 0:
        print(f'✅ 今日要闻已采集: {total} 条')
        print(f'日期: {date_str}')
        
        # 测试飞书推送
        print('\n正在测试飞书推送...')
        date_fmt = date_str[:4] + '年' + date_str[4:6] + '月' + date_str[6:] + '日' if len(date_str) == 8 else date_str
        cat_lines = []
        for cat, items in brief.get('categories', {}).items():
            if items:
                cat_lines.append(f'  {cat}: {len(items)} 条')
        summary = '\n'.join(cat_lines)
        
        payload = json.dumps({
            'msg_type': 'interactive',
            'card': {
                'header': {'title': {'tag': 'plain_text', 'content': f'📰 天下要闻 · {date_fmt}'}, 'template': 'blue'},
                'elements': [
                    {'tag': 'div', 'text': {'tag': 'lark_md', 'content': f'共 **{total}** 条要闻已更新\n{summary}'}},
                    {'tag': 'action', 'actions': [{'tag': 'button', 'text': {'tag': 'plain_text', 'content': '🔗 查看完整简报'}, 'url': 'http://127.0.0.1:7891', 'type': 'primary'}]},
                    {'tag': 'note', 'elements': [{'tag': 'plain_text', 'content': f"采集于 {brief.get('generated_at', '')}"}]}
                ]
            }
        }).encode()
        
        try:
            req = Request(webhook, data=payload, headers={'Content-Type': 'application/json'})
            resp = urlopen(req, timeout=10)
            print(f'✅ 飞书推送成功! 状态码: {resp.status}')
        except Exception as e:
            print(f'❌ 飞书推送失败: {e}')
    else:
        print('⚠️ 今日暂无要闻数据，请先点击「立即采集」按钮')
