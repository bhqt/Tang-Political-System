#!/usr/bin/env python3
"""在 OpenClaw 配置中添加 Minimax 模型"""
import json
import pathlib

OPENCLAW_CFG = pathlib.Path.home() / '.openclaw' / 'openclaw.json'

def main():
    # 读取现有配置
    with open(OPENCLAW_CFG, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    # 添加 Minimax 提供商配置
    models = cfg.setdefault('models', {})
    providers = models.setdefault('providers', {})
    
    # Minimax 配置 - 使用 OpenAI 兼容端点
    minimax_config = {
        "baseUrl": "https://api.minimax.chat/v1",
        "apiKey": "YOUR_MINIMAX_API_KEY",  # 用户需要填写
        "api": "openai-completions",
        "models": [
            {
                "id": "minimax/m2.1-raw",
                "name": "m2.1-raw",
                "reasoning": True,
                "input": ["text"],
                "contextWindow": 32768,
                "maxTokens": 8192
            },
            {
                "id": "minimax/m2.5",
                "name": "m2.5",
                "reasoning": True,
                "input": ["text"],
                "contextWindow": 65536,
                "maxTokens": 8192
            }
        ]
    }
    
    providers['minimax'] = minimax_config
    
    # 在默认模型中添加 Minimax 模型别名
    agents = cfg.setdefault('agents', {})
    defaults = agents.setdefault('defaults', {})
    models_config = defaults.setdefault('models', {})
    
    # 添加 Minimax 模型别名
    models_config['minimax/m2.1-raw'] = {
        "alias": "MiniMax M2.1"
    }
    models_config['minimax/m2.5'] = {
        "alias": "MiniMax M2.5"
    }
    
    # 保存配置
    with open(OPENCLAW_CFG, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    
    print("✅ Minimax 模型已添加到 OpenClaw 配置")
    print("⚠️  请记得在配置文件中填写你的 Minimax API Key")
    print(f"📁 配置文件路径: {OPENCLAW_CFG}")
    print("🔧 具体位置: models.providers.minimax.apiKey")

if __name__ == '__main__':
    main()
