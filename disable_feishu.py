#!/usr/bin/env python3
import json

config_file = '/Users/macxu/.openclaw/openclaw.json'

with open(config_file, 'r') as f:
    config = json.load(f)

config['channels']['feishu']['enabled'] = False
config['plugins']['entries']['feishu']['enabled'] = False

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print('✅ 飞书渠道已禁用')
print('✅ 飞书插件已禁用')
