# Git 工作流规范

一个简单可行的 Git 工作流规范。

**分支流向**：`feature` 分支 →（PR）→ `dev` →（PR）→ `main`

---

## 0. 分支保护规则（GitHub 设置）

为了保护 `main` 和 `dev` 两个核心分支，必须在 GitHub 仓库中设置分支保护规则。

### General（通用设置）

在仓库的 `Settings → General` 中，找到 `Pull Requests` 部分：

- 取消勾选 `Allow squash merging`
- 取消勾选 `Allow rebase merging`
- 保留勾选 `Allow merge commits`

这样在合并 PR 时，只允许使用 merge commit 方式，禁止 squash 和 rebase，保证提交历史完整可追溯。

### Branch Protection Rules（分支保护规则）

分别为 `main` 和 `dev` 创建分支保护规则，只需勾选：

- `Require pull request before merging`（必须通过 PR 才能合并）

组长在项目开始前设置好保护规则，之后所有人（包括组长）都不能直接 push 到 `main` 或 `dev`。

---

## 1. main 分支

这是稳定的生产分支，起到"稳定备份版本""稳定生产版本"的效果。

- 通常较少被更新。
- 只能通过从 `dev` 发起 PR 的方式更新。
- 只能在全员已知的情况下更新（例如发版前）。

---

## 2. dev 分支

团队共享的集成分支。

- 所有功能分支的基础和最终目标。
- 只能通过 PR 从 `feature` 分支合并进来。
- 禁止直接在本地 commit 到 `dev` 或 push 到 `origin/dev`。

本地不一定需要 `dev` 分支。因为所有对 `dev` 的更新都必须通过 PR，你不需要直接操作它。同步最新代码时可以用 `git fetch origin && git merge origin/dev`，推送也必须走 PR。

只有在你的本地需要完整运行项目时，才需要拉取本地 `dev` 分支。如果需要本地 `dev` 分支：

```bash
git fetch origin
git branch dev origin/dev
```

---

## 3. 克隆仓库到本地

项目开始时，将远程仓库克隆到本地：

```bash
# 必须使用 SSH 方式克隆，HTTP 方式每次操作都要验证身份，比较麻烦
git clone git@github.com:组织名/仓库名.git
cd 仓库名
```

> ⚠️ `git clone` 默认只会拉取 `main` 分支并切换到 `main`。远程的其他分支（如 `dev`）并不会自动在本地创建对应分支，但它们的信息已经存在于远程追踪中。

查看所有远程分支：

```bash
git branch -r
```

如果需要本地 `dev` 分支（非必须，见第 2 节说明）：

```bash
git fetch origin
git branch dev origin/dev
```

---

## 4. 两种 feature 工作流（全部基于远程分支 + PR）

所有开发都必须在 `feature` 分支上进行，最终通过 PR 合并到 `dev`。

### 4.1 短期 feature（当天或 1~2 天可完成）

适用场景：小功能、简单修复、文档调整。

合并后立即删除该 `feature` 分支（远程 + 本地），保持仓库整洁。

```bash
# 1. 从最新的 dev 创建短期 feature 分支（建议以名字/功能命名，如 tom/payment）
git fetch origin
git branch tom/xxx origin/dev
git switch tom/xxx

# 2. 开发、提交（可以多次 commit）
git add .
git commit -m "feat: 完成 xxx 功能"

# 3. 推送远程并创建 PR
git push -u origin tom/xxx
# 在 GitHub 上发起 PR 到 dev，请求 Code Review

# 4. PR 合并后，删除分支
git switch main                # 切换到一个安全分支
git branch -D tom/xxx          # 强制删除本地（合并是在 GitHub 上完成的，本地 git 不知道，-d 会报错）
git push origin --delete tom/xxx  # 删除远程
```

### 4.2 长期 feature（多日、跨设备、需要阶段性交付）

适用场景：大功能开发、需要多台设备同步、开发周期超过 2 天。

> ⚠️ 注意：长期 feature 在 PR 合并到 `dev` 时，使用 **merge commit**（不要 squash 或 rebase），以便保留完整的提交历史。同步最新代码时也统一使用 `git merge origin/dev`，不要使用 rebase，保持历史简单可追溯。

```bash
# 1. 创建长期 feature 分支（建议以名字/功能命名，如 tom/payment）
git fetch origin
git branch tom/long-feature origin/dev
git switch tom/long-feature

# 2. 推送到远程（第一天或第一次）
git push -u origin tom/long-feature
```

**日常开发（多日循环）：**

```bash
# 每天开始（如果本地已有分支）
git switch tom/long-feature
git pull                       # 从远程同步（多设备或隔夜工作）

# 合并最新的 dev 到长期分支（减少最终冲突）
git fetch origin
git merge origin/dev

# 开始工作，多次 commit
git add .
git commit -m "进度: xxx"

# 每天结束前推送远程备份
git push
```

**阶段性交付**（功能的一部分已经稳定，需要提前合入 `dev`）：

例如：完成了独立子功能、修复了紧急 bug、到了稳定节点。

1. 直接在 GitHub 上从 `tom/long-feature` 发起 PR 到 `dev`。
2. 注意：这次 PR 合入后，**不要删除 `tom/long-feature` 分支**（因为还要继续开发剩余部分）。
3. 继续开发剩余部分前，需要将本地分支同步回最新的 `dev`：

```bash
git switch tom/long-feature
git fetch origin
git merge origin/dev
# 然后继续工作、推送
```

**最终完成：**

当全部功能开发完毕，发起最后一个 PR 从 `tom/long-feature` 到 `dev`。合并后，此时才删除远程和本地分支：

```bash
git switch main                       # 切换到一个安全分支
git branch -D tom/long-feature        # 强制删除本地
git push origin --delete tom/long-feature  # 删除远程
```

---

## 5. 常见问题

### Q：我忘记创建 feature 分支，直接在 main 上写代码了怎么办？

**A：如果还没 commit**，直接创建新分支即可，未提交的改动会自动带过去：

```bash
git switch -c tom/xxx   # 从当前位置创建新分支并切换，改动跟着走
# 然后正常提交、推送、发 PR
```

**如果已经 commit 了：**

```bash
git branch tom/xxx              # 基于当前 commit 创建新分支
git reset --hard origin/main    # 把 main 回退到远程状态（丢弃本地那个 commit）
git switch tom/xxx              # 切换到新分支继续工作
git push -u origin tom/xxx
```

### Q：PR 被 Review 后要求改代码，怎么更新 PR？

**A：** 直接在本地同一个分支上继续 commit 并 push，PR 会自动更新：

```bash
git switch tom/xxx
# 修改代码 ...
git add .
git commit -m "fix: 根据 review 修改 xxx"
git push                     # PR 自动更新，不需要重新创建
```

### Q：GitHub 上 PR 显示有冲突，怎么解决？

**A：** 在本地 `feature` 分支上合并 `origin/dev`，解决冲突后推送：

```bash
git switch tom/xxx
git fetch origin
git merge origin/dev
# 手动解决冲突，然后提交
git add .
git commit -m "merge: 解决与 dev 的冲突"
git push                     # PR 上的冲突提示会自动消失
```

### Q：长期 feature 合并 dev 时冲突太多怎么办？

**A：** 在长期分支上定期（每天）执行 `git fetch origin && git merge origin/dev`，分散解决冲突，不要等到最后一天。
