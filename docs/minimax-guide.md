# 🌌 Minimax 大模型配置指南

本文档介绍如何在三省六部系统中配置和使用 Minimax 大模型。

## ✅ 已完成的配置

Minimax 模型已成功添加到系统中，包括：

- ✅ Minimax 提供商配置（OpenAI 兼容端点）
- ✅ 2 个 Minimax 模型已注册
- ✅ 模型别名配置（MiniMax M2.1、MiniMax M2.5）
- ✅ Agent 配置已同步

## 📋 已添加的模型

| 模型 ID | 模型名称 | 上下文窗口 | 最大输出 | 推理能力 |
|---------|---------|-----------|---------|---------|
| `minimax/m2.1-raw` | M2.1-raw | 32,768 tokens | 8,192 tokens | ✅ 支持 |
| `minimax/m2.5` | M2.5 | 65,536 tokens | 8,192 tokens | ✅ 支持 |

## 🔑 配置 Minimax API Key

### 方法一：通过配置文件（推荐）

1. 打开 OpenClaw 配置文件：
   ```bash
   open ~/.openclaw/openclaw.json
   ```

2. 找到 `models.providers.minimax` 配置段：

   ```json
   {
     "models": {
       "providers": {
         "minimax": {
           "baseUrl": "https://api.minimax.chat/v1",
           "apiKey": "YOUR_MINIMAX_API_KEY",
           "api": "openai-completions",
           "models": [...]
         }
       }
     }
   }
   ```

3. 将 `YOUR_MINIMAX_API_KEY` 替换为你的实际 Minimax API Key：

   ```json
   {
     "apiKey": "your-actual-minimax-api-key-here"
   }
   ```

4. 保存文件并重启 Gateway：

   ```bash
   openclaw gateway restart
   ```

### 方法二：通过看板界面

1. 启动看板服务器（如果未运行）：
   ```bash
   cd /path/to/Tang-Political-System
   python3 dashboard/server.py
   ```

2. 打开浏览器访问：http://127.0.0.1:7891

3. 进入 **⚙️ 模型配置** 面板

4. 选择需要切换模型的 Agent

5. 在模型下拉框中选择：
   - `MiniMax M2.1` (对应 `minimax/m2.1-raw`)
   - `MiniMax M2.5` (对应 `minimax/m2.5`)

6. 点击 **应用更改**

## 🎯 使用场景

### 推荐使用场景

| 模型 | 适用场景 | 优势 |
|------|---------|------|
| **M2.1-raw** | 通用任务、代码生成、文本处理 | 速度快、成本低、推理能力强 |
| **M2.5** | 复杂任务、长文本处理、多步骤推理 | 上下文窗口大、推理更准确 |

### 示例任务

**使用 M2.1-raw：**
- 简单的代码编写
- 文档摘要
- 快速的问答任务
- 中等长度的文本生成

**使用 M2.5：**
- 复杂的系统设计
- 长篇文档编写
- 多步骤的分析任务
- 需要大量上下文的任务

## 💡 提示

1. **API Key 安全**：不要将 API Key 提交到 Git 仓库
   - 配置文件已在 `.gitignore` 中
   - 建议使用环境变量（如果 OpenClaw 支持）

2. **成本控制**：
   - Minimax 提供免费额度
   - 建议设置使用限额
   - 定期检查使用情况

3. **性能优化**：
   - M2.1-raw 适合快速迭代
   - M2.5 适合高质量输出
   - 根据任务复杂度选择合适的模型

4. **故障排查**：
   - 如果模型不可用，检查 API Key 是否正确
   - 确认网络可以访问 `https://api.minimax.chat`
   - 查看 Gateway 日志：`openclaw gateway logs`

## 📚 相关资源

- [Minimax 官网](https://www.minimax.ai/)
- [Minimax API 文档](https://docs.minimax.ai/)
- [OpenClaw 配置文档](https://docs.openclaw.ai/)
- [三省六部项目主页](https://github.com/cft0808/edict)

## 🔧 验证配置

配置完成后，可以通过以下方式验证：

1. **查看 Agent 配置**：
   ```bash
   cat data/agent_config.json | grep -A 2 minimax
   ```

2. **查看可用模型**：
   - 打开看板
   - 进入 **⚙️ 模型配置**
   - 检查模型下拉框中是否包含 Minimax 模型

3. **测试模型**：
   - 为某个 Agent 切换到 Minimax 模型
   - 发送一个简单任务
   - 检查任务是否正常执行

## 📝 更新历史

- **2026-03-31**：添加 Minimax 模型支持
  - 添加 `minimax/m2.1-raw` 和 `minimax/m2.5`
  - 配置 OpenAI 兼容端点
  - 更新 Agent 配置同步脚本
