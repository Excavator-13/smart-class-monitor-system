# OpenSpec — 规范驱动开发

## 这是什么

OpenSpec 是一套规范驱动开发框架。核心理念：

```
你说需求 → AI 生成 spec → AI 按 spec 写代码
```

spec 是 "说明书"，AI 按说明书干活，不会跑偏。

## 功能

| 功能 | 说明 |
|---|---|
| `/opsx:explore` | 先和 AI 讨论需求，理清思路再动手 |
| `/opsx:propose` | AI 自动生成全套文档（proposal + spec + design + tasks） |
| `/opsx:apply` | AI 按 spec 自动写代码 |
| `/opsx:archive` | 功能完成后归档留底 |

## 目录结构

```
openspec/
├── README.md                ← 本文件
├── config.yaml              ← 项目配置（技术栈、规范要求）
├── 全流程范例.md             ← 完整示例，从 explore 到 archive
│
├── specs/                   ← 【正式版】开发完成后同步到这里，老师检查
│   └── add-api/
│       └── spec.md          ← 加法功能的正式 spec
│
└── changes/                 ← 【开发中】草稿区
    └── archive/             ← 【归档】已完成的功能留底
        └── 2026-07-07-add-api/
            ├── proposal.md  ← 为什么做
            ├── specs/        ← 详细规范
            ├── design.md    ← 怎么做
            └── tasks.md     ← 实现步骤
```

## 全流程（4 步）

### 1. `/opsx:explore` — 讨论需求

```
你: /opsx:explore
AI: What would you like to explore?
你: 我要做一个加法接口，怎么设计比较好？
AI: 用 Flask GET 接口，参数放 URL，返回 JSON……
你: 好，按这个来。
```

### 2. `/opsx:propose` — 生成文档

```
你: /opsx:propose add-api
AI: Created openspec/changes/add-api/
    ✓ proposal.md     — 动机与范围
    ✓ specs/           — 功能规范
    ✓ design.md       — 技术方案
    ✓ tasks.md        — 实现清单
    Ready!
```

### 3. `/opsx:apply` — 写代码

```
你: /opsx:apply
AI: Implementing tasks...
    ✓ Create backend_ai/adder.py
    ✓ Implement /api/add
    ✓ Add validation
    Done!
```

### 4. `/opsx:archive` — 归档

```
你: /opsx:archive add-api
AI: Archived. Specs 已同步到 openspec/specs/
    可以开始下一个功能了。
```

---

## 我是用 Claude Code 的

```bash
# 1. 讨论
/opsx:explore

# 2. 生成 spec
/opsx:propose "功能名：功能描述"

# 3. 写代码
/opsx:apply

# 4. 归档
/opsx:archive 功能名
```

## 我是用其他 AI 的（网页版 / Kimi / DeepSeek 等）

```
步骤1：打开 AI 网页，这样跟它说：

"帮我写 OpenSpec 规范文件。
项目：智慧教室监控系统，Python Flask + OpenCV + Vue 3。
功能：[你的功能]。要求：
- 必须做什么
- 不能做什么
- 用 GIVEN/WHEN/THEN 格式写场景"

步骤2：把 AI 返回的内容保存到：
openspec/changes/你的功能名/specs/xxx.md

步骤3：再跟 AI 说：
"按刚才的规范帮我写完整代码"

步骤4：把代码放到项目对应目录，功能跑通后：
把 spec 文件从 changes/ 复制到 openspec/specs/你的功能名/
```

---

## 范例参考

- **教学文档**：`全流程范例.md` — 完整演示 4 步流程
- **文件范例**：`changes/archive/2026-07-07-add-api/` — 每个文件长什么样
- **正式 spec**：`specs/add-api/spec.md` — 给老师看的最终版本

---

## 记住 3 句话

1. **specs/** = 给老师看的（正式版，和代码一致）
2. **changes/** = 给自己看的（草稿，开发中）
3. **先写 spec，再写代码，最后归档**
