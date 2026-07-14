## ADDED Requirements

### Requirement: RTMP 地址按调用者权限返回

SpringBoot SHALL 仅向管理员和通过内部令牌鉴权的服务返回视频源 RTMP 地址。

#### Scenario: 管理员查询视频源

- **GIVEN** 当前登录角色为 `admin`
- **WHEN** 调用视频源列表、详情、已启用列表或播放地址接口
- **THEN** 响应 SHALL 包含该视频源的 `rtmp_url`

#### Scenario: 教师查询视频源

- **GIVEN** 当前登录角色为 `teacher`
- **WHEN** 调用视频源列表、详情、已启用列表或播放地址接口
- **THEN** 响应 SHALL 不暴露有效的 `rtmp_url`

#### Scenario: AI 内部服务加载视频源

- **GIVEN** 请求携带有效 `X-Internal-Token`
- **WHEN** 调用视频源列表接口
- **THEN** 响应 SHALL 包含完整 `rtmp_url`

### Requirement: 视频源状态反映真实发布者

系统 SHALL 区分视频源配置状态和真实推流在线状态。

#### Scenario: 标准 Nginx-RTMP 发布者在线

- **GIVEN** `/stat` XML 中同名 stream 的 client 含 `<publishing/>`
- **WHEN** 查询该视频源状态
- **THEN** 返回 `online=true` 且 `status=online`

#### Scenario: 视频源无发布者

- **GIVEN** `/stat` 可访问但同名 stream 不存在或不存在 publishing client
- **WHEN** 查询该视频源状态
- **THEN** 返回 `online=false` 且 `status=offline`

#### Scenario: 状态服务不可用

- **GIVEN** `/stat` 请求失败或 XML 无法解析
- **WHEN** 查询该视频源状态
- **THEN** 返回 `online=false` 且 `status=unknown`

#### Scenario: 系统状态页加载视频源

- **WHEN** 前端取得视频源列表
- **THEN** 前端 SHALL 查询各视频源实时状态并展示
- **AND** SHALL NOT 把 `enabled` 直接显示为 `online`

