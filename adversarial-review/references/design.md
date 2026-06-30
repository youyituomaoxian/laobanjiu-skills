# Design — 设计原理与对比分析

> Human-readable design documentation. Load this when the user asks "why is it designed this way"
> or when writing documentation/presentation about the skill.

---

## 第一性原理

**代码审查的根本问题：单个智能体有盲点。** 注意力有限、偏见固定、容易自我验证。

**对抗性审查为什么有效：当审查者的激励函数是"找缺陷"而不是"通过审查"，注意力方向反转，盲点被主动暴露。**

基于这个原理，本 Skill 设计了两个角色对立的子 Agent：

```
Red Team (攻击者)          Blue Team (辩护者)
激励: 找到真实缺陷           激励: 用证据成功辩护
视每行代码为"有罪"           视每行代码为"无辜"
从恶意输入/竞态/边界切入      从代码逻辑/覆盖/设计切入
```

同样的底层模型 + 完全相反的激励函数 = 注意力覆盖互补 → 盲点被暴露。

Role-prompting 已被研究证实能显著改变 LLM 的输出分布。同一模型在两个极端角色下会产生差异显著的审查结果。

---

## 为什么主 Agent 做裁判而不是第三个子 Agent

独立的裁判 Agent 需要和主 Agent 完全相同的工具权限和上下文，形成了一个冗余的中间层，且没有产生信息增益。主 Agent 自己就拥有：

- 完整的文件读写能力
- Linter / type-checker / 测试执行
- 跨文件 grep 和依赖追踪
- 直接修复代码的能力

主 Agent 作为信息汇聚点和决策者 — 读两份报告、独立验证、做最终裁决。这是最省 Token、信息损失最小、决策可追溯的设计。

---

## 为什么 Phase 1 和 Phase 2 串行而非并行

这是整个设计的核心决策。表面上并行可以省时间，但——

如果 Red 和 Blue 并行启动：
- Blue 不知道 Red 会攻击什么
- Blue 只能做"预防性声明"，不能做"针对性辩护"
- 这不叫对抗，叫两个 Agent 各说各的

串行的好处：
- Red 先出完整攻击报告
- Blue 的 prompt 里嵌入 Red 的每一条指控
- Blue 逐条回应 — 承认、反驳、或要求更多上下文
- 这才是真正的"对抗"

---

## 与 Codex UltraCode / Dynamic Workflow 的对比

### UltraCode 是什么（CLI Dynamic Workflow）

CodeBuddy Code v2.105.0 引入的原生工作流编排层：
- 自动化的子 Agent 链式调度（plan → implement → adversarial review → verify）
- 内置对抗性审查角色
- 阶段间共享上下文
- 可编程收敛条件
- `/workflows` 面板管理暂停/恢复/重启

### 对比

| 维度 | UltraCode (CLI Workflow) | 本 Skill (GUI) |
|------|--------------------------|-----------------|
| 编排方式 | 引擎自动调度 | 主 Agent 手动推进阶段 |
| Agent 通信 | 直接传递，共享上下文 | 文件中转（输出 → 下一 Agent prompt） |
| 收敛条件 | 可编程，自动停止 | 固定 2 轮（Red→Blue→裁决） |
| 对抗深度 | 内置对抗审查角色 | Role-prompting 产生对立激励 |
| 模型多样性 | 可能支持不同模型分配 | 同一模型（GUI 限制） |
| 修复执行 | Coder Agent 自动 | 主 Agent 直接 Edit |
| 使用门槛 | 需要 CLI + 配置文件 | 安装 Skill，输入触发词 |
| 分发方式 | Workflow 脚本 (.yaml) | 一个目录，GitHub 即分发 |
| 使用门槛 | 高（需学 workflow 语法） | 低（自然语言触发） |

### 优势

1. **零配置。** 安装后输入"对抗审查 file.js"即用，无需写 workflow YAML。
2. **裁决透明。** 每条判决都有可追溯链路：Red 报告 → Blue 辩护 → 主 Agent 带证据的裁决。没有黑箱。
3. **Token 更省。** 只有 2 个子 Agent + 1 个 QA 验证，vs UltraCode 的 4+ 角色。每个 Agent 任务边界清晰。
4. **GitHub 可分发的 Skill。** 一个目录，任何人 clone 到 `~/.workbuddy/skills/` 即可。不需要插件注册、不需要市场审核。
5. **Human-in-the-loop 设计。** 不确定的争议项标记为人工审查，而不是低置信度自动拍板。

### 劣势

1. **不能真正自动化。** 无法设为每次 commit 自动触发。需要人输入触发词。
2. **只能串行。** Red 必须在 Blue 之前完成。UltraCode 可以把对抗审查和别的阶段并行。
3. **无收敛循环。** 固定 2 轮。UltraCode 可以循环直到找不到新缺陷。
4. **无法混用模型。** 所有子 Agent 共享同一模型，存在深层盲点共享的风险。
5. **无工作流持久化。** 每次审查是一次性会话。UltraCode 的 `/workflows` 面板保存运行历史。

### 用哪个

| 场景 | 推荐 |
|------|------|
| 合 PR 前的快速审查 | 本 Skill (GUI) |
| 安全关键模块深度审计 | 本 Skill (GUI) + 人工审查 UNDECIDABLE 项 |
| CI/CD 流水线集成 | UltraCode (CLI Workflow) |
| 每次 commit 自动对抗审查 | UltraCode (CLI Workflow) |
| 跨模型的对抗审查 | UltraCode (CLI Workflow)，如果支持多模型 |
| 团队共享审查标准 | 本 Skill (GitHub 分发) |
| 单文件一次性深挖 | 本 Skill (GUI) |

---

## 局限性

| 局限 | 说明 | 是否可解决 |
|------|------|-----------|
| 单一模型盲点 | 子 Agent 共享同一底层模型，深层盲点（浮点精度、框架特定 CVE）可能集体遗漏 | ❌ GUI 限制，可通过 role-prompting 部分补偿 |
| 无运行时验证 | Red Team 只能做静态分析，不能跑 fuzzer、注入 payload、调堆栈 | ❌ LLM 静态审查的根本局限 |
| 裁决上限 | 主 Agent 的判断力受限于自己的代码理解能力 | ⚠️ 极模糊争议标记人工审查 |
| 串行开销 | Phase 1+2 串行执行，总时间 = 两次子 Agent 调用 | ⚠️ 设计选择，比单次审查慢但深得多 |
| 非 CI/CD 集成 | 不能自动触发 | ✅ 设计选择，目标场景是交互式深度审查 |
