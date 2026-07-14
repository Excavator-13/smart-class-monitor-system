## Context
钉钉通知使用 Webhook 发送 text 消息（支持 atMobiles 蓝色 @），配合 Stream 模式接收群回复。截图通过钉钉 OpenAPI media/upload 上传获得 media_id，嵌入 markdown 消息展示。

## Decisions
- text 消息用于蓝色 @，markdown 仅用于展示截图
- 事件ID 在 trigger_alert 时生成，通过函数参数一路传递，不依赖全局查找
- 逐级上报不复用截图 markdown，减少冗余消息

## Risks
- 钉钉 Stream 连接可能因网络断开，需要自动重连
- 机器人仅在被 @ 时能收到消息，需要引导用户 @ 机器人
