# ClawBot 微信交互经验总结

本文档记录了在 OpenClaw 中使用 ClawBot 插件与微信进行交互的完整经验，包括技术原理、安装配置、使用方法以及关键注意事项。

## 一、技术架构概述

### 1.1 系统架构

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   三省六部系统   │────▶│   OpenClaw       │────▶│  微信服务器      │
│  (Tang-Political│     │  (ClawBot插件)   │     │  (微信API)      │
│   -System)      │◀────│                  │◀────│                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
   天下要闻推送            MCP协议通信              用户微信客户端
```

### 1.2 核心组件

| 组件 | 说明 |
|------|------|
| **OpenClaw** | AI多Agent协作系统，支持多渠道消息集成 |
| **ClawBot插件** | `@tencent-weixin/openclaw-weixin`，实现微信机器人功能 |
| **MCP协议** | Model Context Protocol，OpenClaw与外部服务通信的标准协议 |
| **微信API** | 微信提供的 Bot API，用于消息收发 |

### 1.3 关键概念

- **Account ID**: 微信插件账号标识，格式为 `xxx-im-bot`
- **User ID**: 用户微信标识，格式为 `xxx@im.wechat`
- **Context Token**: 会话上下文令牌，用于维持与用户的对话状态
- **Gateway**: OpenClaw网关服务，处理外部连接和请求路由

## 二、安装配置步骤

### 2.1 前置条件

- macOS 系统（本文基于 Mac Air M1）
- Node.js 环境（>= 22.x）
- OpenClaw 已安装（版本 >= 2026.3.22）

### 2.2 安装微信插件

```bash
# 方式1：快速安装（推荐）
npx -y @tencent-weixin/openclaw-weixin-cli install

# 方式2：手动安装
openclaw plugins install "@tencent-weixin/openclaw-weixin"
openclaw config set plugins.entries.openclaw-weixin.enabled true
```

### 2.3 配置 MCP 服务器

```bash
# 设置 MCP 服务器配置
openclaw mcp set wechat '{"command":"npx","args":["-y","@tencent-weixin/openclaw-weixin"]}'
```

配置完成后，`~/.openclaw/openclaw.json` 中会增加：

```json
{
  "mcpServers": {
    "wechat": {
      "command": "npx",
      "args": ["-y", "@tencent-weixin/openclaw-weixin"]
    }
  }
}
```

### 2.4 启动网关服务

```bash
# 安装网关服务
openclaw gateway install

# 启动网关服务
openclaw gateway

# 或使用后台模式
openclaw gateway --port 18789 &
```

### 2.5 微信扫码登录

```bash
# 执行登录命令，会显示二维码
openclaw channels login --channel openclaw-weixin
```

操作步骤：
1. 终端显示二维码
2. 使用微信扫描二维码
3. 在手机上确认授权
4. 登录成功后，凭证自动保存

登录成功后，配置文件保存在：
- `~/.openclaw/openclaw-weixin/accounts/xxx-im-bot.json`
- `~/.openclaw/openclaw-weixin/accounts.json`

### 2.6 验证安装

```bash
# 查看已配置的渠道
openclaw channels list

# 预期输出：
# Chat channels:
# - openclaw-weixin xxx-im-bot: configured, enabled
```

## 三、三省六部系统集成

### 3.1 系统架构

在三省六部系统中，微信推送功能集成在 **dashboard/server.py** 中，与天下要闻模块联动。

### 3.2 核心代码实现

#### 3.2.1 微信推送函数

```python
def push_to_weixin():
    """Push morning brief to Weixin AI."""
    import subprocess
    
    # 读取天下要闻数据
    cfg = read_json(DATA / 'morning_brief_config.json', {})
    brief = read_json(DATA / 'morning_brief.json', {})
    
    # 构建消息内容
    date_str = brief.get('date', '')
    total = sum(len(v) for v in (brief.get('categories') or {}).values())
    
    message = f'''📰 天下要闻 · {date_fmt}
共 **{total}** 条要闻已更新
{summary}

🔗 查看完整简报: http://127.0.0.1:7891

采集于 {brief.get('generated_at', '')}'''
    
    # 调用 OpenClaw 发送消息
    result = subprocess.run(
        ['openclaw', 'message', 'send',
         '--channel', 'openclaw-weixin',
         '--target', 'o9cq802KkVl3OKboQH--12ttmTag@im.wechat',  # 用户微信ID
         '--message', message],
        capture_output=True,
        text=True,
        timeout=30
    )
```

#### 3.2.2 独立推送脚本

创建 `push_to_weixin.py`：

```python
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
    brief = read_json(DATA / 'morning_brief.json', {})
    
    # 构建并发送消息...
    # 详见上文代码

if __name__ == '__main__':
    success = push_to_weixin()
    sys.exit(0 if success else 1)
```

### 3.3 触发方式

1. **自动触发**：在 dashboard 点击「立即采集」按钮
2. **手动触发**：运行 `python3 push_to_weixin.py`
3. **定时触发**：可配置 cron 任务定期执行

## 四、关键技术细节

### 4.1 用户 ID 获取机制

**关键发现**：微信插件需要用户主动发送消息给机器人，才能获取用户的微信 ID。

流程：
```
用户发送消息 → 微信服务器 → OpenClaw Gateway → 保存 Context Token
                                                    ↓
                                          生成用户ID映射关系
                                                    ↓
                                          存储在 context-tokens.json
```

**Context Token 文件位置**：
```
~/.openclaw/openclaw-weixin/accounts/{account-id}.context-tokens.json
```

**文件内容示例**：
```json
{
  "o9cq802KkVl3OKboQH--12ttmTag@im.wechat": "AARzJWAFAAABAAAAAAB7zfq6nMhJc6NPQXvLaSAAAAB+9905Q6UiugPBawU3n3cyzQX+LkN8ofRzsCZYN0mt7odn7mvdyi28Jk+caeOeyC6CPIbJtiaVVcTWagqf5pdO/8qlcXgL"
}
```

### 4.2 ID 类型说明

| ID 类型 | 格式 | 示例 | 用途 |
|---------|------|------|------|
| Account ID | `xxx-im-bot` | `f751c0f2cad5-im-bot` | 标识微信插件账号 |
| User ID | `xxx@im.wechat` | `o9cq802KkVl3OKboQH--12ttmTag@im.wechat` | 标识微信用户 |
| Bot User ID | `xxx@im.bot` | `f751c0f2cad5@im.bot` | 标识机器人自身 |

**重要区别**：
- `--target` 参数需要填写 **User ID**（用户微信ID）
- 不是 Account ID，也不是 Bot User ID

### 4.3 消息发送命令

```bash
# 完整命令格式
openclaw message send \
  --channel openclaw-weixin \
  --target {user_id}@im.wechat \
  --message "消息内容"

# 实际示例
openclaw message send \
  --channel openclaw-weixin \
  --target o9cq802KkVl3OKboQH--12ttmTag@im.wechat \
  --message "📰 天下要闻 · 2026年03月31日"
```

### 4.4 常见问题排查

#### 问题1：Unknown target 错误
**原因**：使用了错误的 target ID（如 Account ID 或 Bot User ID）
**解决**：使用正确的 User ID（`xxx@im.wechat` 格式）

#### 问题2：requires target 错误
**原因**：未指定 `--target` 参数
**解决**：必须指定 `--target` 参数

#### 问题3：cannot determine which account to use
**原因**：没有可用的 context token
**解决**：用户需要先发送消息给机器人，建立会话

#### 问题4：微信插件未加载
**原因**：网关服务未启动或插件未启用
**解决**：
```bash
openclaw gateway restart
openclaw config set plugins.entries.openclaw-weixin.enabled true
```

## 五、配置文件详解

### 5.1 微信账号配置

**文件**：`~/.openclaw/openclaw-weixin/accounts/{account-id}.json`

```json
{
  "token": "f751c0f2cad5@im.bot:060000d778afd6337678dbe88c8b501b85f15d",
  "savedAt": "2026-03-31T07:10:06.974Z",
  "baseUrl": "https://ilinkai.weixin.qq.com",
  "userId": "o9cq802KkVl3OKboQH--12ttmTag@im.wechat"
}
```

字段说明：
- `token`: 登录凭证
- `baseUrl`: 微信 API 基础地址
- `userId`: 机器人自身的微信 ID（不是用户的）

### 5.2 OpenClaw 主配置

**文件**：`~/.openclaw/openclaw.json`

```json
{
  "channels": {
    "openclaw-weixin": {
      "accounts": {}
    }
  },
  "plugins": {
    "entries": {
      "openclaw-weixin": {
        "enabled": true,
        "config": {}
      }
    }
  },
  "mcpServers": {
    "wechat": {
      "command": "npx",
      "args": ["-y", "@tencent-weixin/openclaw-weixin"]
    }
  }
}
```

### 5.3 账号索引

**文件**：`~/.openclaw/openclaw-weixin/accounts.json`

```json
[
  "f751c0f2cad5-im-bot"
]
```

## 六、最佳实践

### 6.1 安全建议

1. **保护 Token**：`token` 字段包含敏感信息，不要提交到代码仓库
2. **权限控制**：确保 `~/.openclaw` 目录权限为 `700`
3. **定期备份**：定期备份账号配置，防止丢失

### 6.2 使用建议

1. **首次使用**：用户必须先发送消息给机器人，才能接收推送
2. **消息格式**：支持纯文本，不支持 Markdown 格式（微信会自动转换）
3. **消息长度**：建议控制在 2000 字以内，避免被截断
4. **频率控制**：避免频繁推送，防止被微信限制

### 6.3 调试技巧

```bash
# 查看网关日志
openclaw gateway logs

# 查看渠道状态
openclaw channels list

# 测试消息发送（dry-run）
openclaw message send --channel openclaw-weixin --target {user_id} --message "测试" --dry-run

# 查看插件配置
openclaw config get plugins.entries.openclaw-weixin
```

## 七、与其他渠道的对比

| 特性 | 微信 | 飞书 |
|------|------|------|
| 配置复杂度 | 中等（需扫码） | 简单（Webhook） |
| 消息格式 | 纯文本 | 富文本卡片 |
| 交互方式 | 双向 | 单向/双向 |
| 用户 ID 获取 | 需先交互 | 直接配置 |
| 使用场景 | 个人通知 | 群组通知 |

## 八、总结

通过 ClawBot 插件，OpenClaw 可以方便地与微信进行集成，实现：

1. **双向通信**：既可以接收用户消息，也可以主动推送消息
2. **多账号支持**：支持多个微信账号同时在线
3. **上下文保持**：通过 context token 维持对话状态
4. **无缝集成**：与三省六部系统深度集成，实现天下要闻自动推送

**关键成功因素**：
- 正确理解 Account ID、User ID、Bot User ID 的区别
- 确保用户先发送消息给机器人，建立会话上下文
- 使用正确的 `--target` 参数（User ID）发送消息

---

*文档版本：2026.3.31*  
*适用版本：OpenClaw >= 2026.3.22, ClawBot >= 2.0.x*
