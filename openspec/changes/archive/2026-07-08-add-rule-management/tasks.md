## 1. 数据库

- [x] 1.1 追加 `behavior_rule` 表 DDL（含 confidence_threshold + cooldown_seconds）

## 2. Entity、Mapper

- [x] 2.1 创建 `BehaviorRule` Entity
- [x] 2.2 创建 `BehaviorRuleMapper`（update 语句含 confidence_threshold + cooldown_seconds）

## 3. DTO、VO

- [x] 3.1 创建 `RuleCreateRequest`（含 confidence_threshold + cooldown_seconds @Schema）
- [x] 3.2 创建 `RuleUpdateRequest`（含 confidence_threshold + cooldown_seconds @Schema）
- [x] 3.3 创建 `RuleVO`（含 confidence_threshold + cooldown_seconds）

## 4. Service + Controller

- [x] 4.1 创建 `RuleService`（CRUD + reloadConfig）
- [x] 4.2 创建 `RuleController`（5 个端点）

## 5. 编译与验证

- [x] 5.1 运行 `mvn -DskipTests compile`
- [x] 5.2 确认 `RuleUpdateRequest` 包含 `confidence_threshold` 和 `cooldown_seconds`
- [x] 5.3 确认 Swagger `@Schema(example=...)` 包含这两个字段
