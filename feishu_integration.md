# 飞书机器人集成指南

## 一、创建飞书应用

1. **登录飞书开放平台**：https://open.feishu.cn
2. **创建企业自建应用**：
   - 应用名称：三省六部
   - 应用描述：基于三省六部架构的 AI 多 Agent 协作系统
   - 选择「机器人」类型

3. **获取应用凭证**：
   - App ID
   - App Secret

4. **配置权限**：
   - 消息与群组：`im:message` 相关权限
   - 机器人：`bot:message` 相关权限

## 二、配置飞书机器人

1. **设置机器人信息**：
   - 机器人名称：三省六部
   - 机器人头像：可上传相关图片

2. **配置消息接收**：
   - 消息接收地址：http://your-server-ip:7891/api/feishu/webhook
   - 验证令牌：可自行设置

3. **发布应用**：
   - 点击「发布」按钮
   - 选择可见范围

## 三、配置 OpenClaw

1. **创建飞书集成技能**：
   - 在 `workspace-zhongshu/skills` 目录创建 `feishu_integration` 文件夹
   - 创建 `SKILL.md` 文件，内容如下：

```markdown
---
name: feishu_integration
description: 飞书机器人集成技能
---

# 飞书集成技能

用于与飞书机器人通信，接收和发送消息。

## 输入

- 消息内容
- 消息类型
- 发送目标

## 处理流程

1. 接收来自飞书机器人的消息
2. 解析消息内容
3. 转发消息到 OpenClaw
4. 处理 OpenClaw 的响应
5. 将响应发送回飞书

## 输出规范

- 飞书消息格式
- 响应状态

## 注意事项

- 需要在飞书开放平台创建企业自建应用
- 需要配置 App ID 和 Secret
- 需要配置相应的权限
```

2. **配置飞书 Webhook**：
   - 编辑 `data/morning_brief_config.json` 文件
   - 填入飞书 Webhook URL

## 四、启动服务

1. **启动 Dashboard 服务器**：
   ```bash
   python3 dashboard/server.py
   ```

2. **启动数据刷新循环**：
   ```bash
   bash scripts/run_loop.sh
   ```

## 五、测试集成

1. **在飞书中向机器人发送消息**：
   - 例如："朕要做一个竞品分析"

2. **查看看板**：
   - 访问 http://127.0.0.1:7891
   - 查看任务是否创建

3. **查看飞书推送**：
   - 系统会定期推送天下要闻到飞书

## 六、故障排查

1. **检查服务状态**：
   ```bash
   ps aux | grep server.py
   ps aux | grep run_loop.sh
   ```

2. **查看日志**：
   ```bash
   tail -f logs/dashboard_server.log
   tail -f logs/run_loop.log
   ```

3. **检查飞书 Webhook 配置**：
   - 确保 Webhook URL 正确
   - 确保验证令牌匹配

4. **检查 OpenClaw 状态**：
   ```bash
   openclaw gateway status
   ```
