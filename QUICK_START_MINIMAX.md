# 🌌 Minimax 模型快速参考

## ✅ 已添加的模型

| 模型 ID | 模型名称 | 上下文 | 输出 | 推理 |
|---------|---------|--------|------|------|
| `minimax/m2.1-raw` | MiniMax M2.1 | 32K | 8K | ✅ |
| `minimax/m2.5` | MiniMax M2.5 | 64K | 8K | ✅ |

## 🔑 配置 API Key

```bash
open ~/.openclaw/openclaw.json
```

找到并修改：
```json
"models": {
  "providers": {
    "minimax": {
      "apiKey": "你的实际API-Key"
    }
  }
}
```

## 🚀 重启 Gateway

```bash
openclaw gateway restart
```

## 📊 在看板中使用

1. 访问：http://127.0.0.1:7891
2. 进入 **⚙️ 模型配置**
3. 选择 Agent → 选择模型 → 应用更改

## 🔍 验证配置

```bash
python3 scripts/check_minimax_config.py
```

## 📚 详细文档

[查看完整配置指南](docs/minimax-guide.md)
