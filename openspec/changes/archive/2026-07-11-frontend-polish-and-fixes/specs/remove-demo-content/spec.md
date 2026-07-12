## REMOVED Requirements

### Requirement: Remove static demo/ppt content modules

The following purely decorative, non-functional content modules SHALL be removed from the frontend. These modules contain only static text or placeholder visuals with no real data or interaction.

#### Modules to remove from 实时监控 (monitor) page

- "前端呈现模块" panel (`activeModules`): 4 static text cards describing system capabilities. No real data.
- The "注册人脸" button inside this panel is redundant (already available in the left sidebar "人脸库" page).

#### Modules to remove from 告警管理 (alerts) page

- "处置建议" panel (`handlingGuides`): 3 static text items ("先看等级", "再看证据", "最后闭环"). No actionable functionality.
- "证据链概览" panel: 3 static text cards ("截图", "片段", "记录"). No real data.
- "处理节奏" panel: 3 static flow steps ("接收", "确认", "闭环"). No real data.

#### Modules to remove from 区域规则 (rules) page

- "推荐模板" panel (`ruleTemplates`): 3 static text items. No template creation functionality.
- "规则联动" panel: 3 static flow steps. No real data.
- "实时禁用区坐标" panel: JSON export display. Developer-only, not useful for end users.
- "区域示意" panel: CSS-drawn classroom diagram. Not based on real zone data.

#### Modules to remove from 人脸库 (people) page

- "陌生人核验" panel: Placeholder face icon + static text. No real stranger detection data.
- "身份策略" panel: 2 static text cards ("学生档案", "访客名单"). No real data.
- "注册进度" panel (`registrationSteps`): 3 computed text items. Redundant with the main table.

#### Modules to remove from 系统状态 (system) page

- "依赖调用链路" panel (`dependencySteps`): 4 static flow steps. No real data.
- "运行提示" panel (`operationLogs`): 3 static text items. No real data.

#### Scenario: Monitor page no longer shows activeModules panel

- **WHEN** the monitor page is rendered
- **THEN** the "前端呈现模块" panel SHALL NOT appear
- **AND** the overview grid SHALL only contain the "告警追踪记录" panel

#### Scenario: Alerts page no longer shows static guide panels

- **WHEN** the alerts page is rendered
- **THEN** the "处置建议", "证据链概览", and "处理节奏" panels SHALL NOT appear
- **AND** the "告警评分配置" panel SHALL remain

#### Scenario: Rules page no longer shows static template and flow panels

- **WHEN** the rules page is rendered
- **THEN** the "推荐模板", "规则联动", "实时禁用区坐标", and "区域示意" panels SHALL NOT appear
- **AND** the "区域规则配置" and "当前已设定区域" panels SHALL remain

#### Scenario: People page no longer shows static info panels

- **WHEN** the people page is rendered
- **THEN** the "陌生人核验", "身份策略", and "注册进度" panels SHALL NOT appear
- **AND** the main "人员与人脸库" table panel SHALL remain

#### Scenario: System page no longer shows static dependency panels

- **WHEN** the system page is rendered
- **THEN** the "依赖调用链路" and "运行提示" panels SHALL NOT appear
- **AND** the "视频源与服务状态" and "运行概览" panels SHALL remain

### Requirement: Remove unused data definitions

The following data definitions that only serve the removed modules SHALL be deleted from the script section:

- `activeModules` array
- `handlingGuides` array
- `ruleTemplates` array
- `dependencySteps` array
- `operationLogs` array
- `registrationSteps` computed property

#### Scenario: No orphan data definitions

- **WHEN** the script section is reviewed after changes
- **THEN** none of the above data definitions SHALL exist
- **AND** no template section SHALL reference them
