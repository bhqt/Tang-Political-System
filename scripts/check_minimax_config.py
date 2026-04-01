#!/usr/bin/env python3
"""验证 Minimax 模型配置"""
import json
import pathlib

OPENCLAW_CFG = pathlib.Path.home() / '.openclaw' / 'openclaw.json'

def main():
    print("🔍 正在检查 Minimax 配置...\n")
    
    if not OPENCLAW_CFG.exists():
        print("❌ 错误：OpenClaw 配置文件不存在")
        print(f"   请先运行 'openclaw init' 初始化\n")
        return False
    
    try:
        with open(OPENCLAW_CFG, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"❌ 错误：无法读取配置文件 - {e}\n")
        return False
    
    models = cfg.get('models', {})
    providers = models.get('providers', {})
    
    if 'minimax' not in providers:
        print("❌ Minimax 提供商未配置")
        print("   请运行 scripts/add_minimax_model.py 添加配置\n")
        return False
    
    minimax = providers['minimax']
    
    # 检查基础配置
    base_url = minimax.get('baseUrl', '')
    api_key = minimax.get('apiKey', '')
    api = minimax.get('api', '')
    
    print("✅ Minimax 提供商已配置")
    print(f"   Base URL: {base_url}")
    print(f"   API Type: {api}")
    
    # 检查 API Key
    if api_key == 'YOUR_MINIMAX_API_KEY' or not api_key:
        print("⚠️  警告：API Key 未设置或为默认值")
        print("   请编辑 ~/.openclaw/openclaw.json 填写实际的 API Key\n")
        print("   配置位置：models.providers.minimax.apiKey\n")
    else:
        print(f"✅ API Key 已配置（{len(api_key)} 字符）\n")
    
    # 检查模型
    models_list = minimax.get('models', [])
    if not models_list:
        print("❌ 错误：Minimax 模型列表为空\n")
        return False
    
    print(f"✅ 已注册 {len(models_list)} 个 Minimax 模型：")
    for model in models_list:
        model_id = model.get('id', 'unknown')
        model_name = model.get('name', 'unknown')
        context = model.get('contextWindow', 0)
        max_tokens = model.get('maxTokens', 0)
        reasoning = "✅" if model.get('reasoning', False) else "❌"
        
        print(f"   • {model_id} ({model_name})")
        print(f"     - 上下文: {context} tokens")
        print(f"     - 最大输出: {max_tokens} tokens")
        print(f"     - 推理能力: {reasoning}")
    
    print("\n📝 下一步：")
    print("   1. 如果 API Key 未设置，请编辑 ~/.openclaw/openclaw.json")
    print("   2. 运行 'openclaw gateway restart' 重启 Gateway")
    print("   3. 打开看板 http://127.0.0.1:7891 查看模型配置\n")
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
