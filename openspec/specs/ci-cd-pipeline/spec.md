## Requirement: CI/CD 持续集成与部署
系统必须通过 Jenkins 实现代码 push 后自动检查和部署。

### Scenario: 代码检查（CI）
- GIVEN 组员 push 代码到任意分支
- WHEN Jenkins 检测到代码变更
- THEN 自动拉取最新代码
- AND 运行 flake8 检查 Python 代码语法
- AND 运行 npm build 检查前端构建
- AND 构建结果在 Jenkins 页面显示 ✅ 或 ❌

### Scenario: 自动部署（CD）
- GIVEN 代码合并到 dev 分支
- WHEN Jenkins 执行部署流水线
- THEN 构建前端 → 复制到 /var/www/html/
- AND 复制后端代码到 /app/
- AND 保护 runtime-config.js 不被覆盖

### Scenario: 开发者模式
- GIVEN CD 部署的前端页面
- WHEN 用户访问 http://39.106.209.208
- THEN 登录页显示「开发者模式临时进入」按钮
- AND 无需后端即可浏览系统界面
