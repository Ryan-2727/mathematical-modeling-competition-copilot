# Mathematical Modeling Competition Copilot

**Mathematical Modeling Competition Copilot** 是一个面向数学建模竞赛的 Codex skill，用于把赛题分析、建模设计、文献细节、可复现实验、图表表格、论文撰写和最终核验串成一个完整工作流。

适用场景包括 MCM/ICM、CUMCM、华为杯、校赛以及其他类似数学建模竞赛。

[English README](README.en.md)

## 这个 Skill 能做什么

这个 skill 是数学建模项目的总控入口。它不承诺“保证拿奖”，而是通过更规范的流程提高产出质量和获奖概率：

1. 明确竞赛要求、提交格式、论文语言和时间预算。
2. 拆解赛题子问题，形成可执行建模路线。
3. 设计可解释、可验证、可写进论文的数学模型。
4. 在需要时查证论文/文献中的关键复现细节。
5. 用代码、Notebook 或电子表格完成可复现实验。
6. 生成数据图、流程图、模型图和论文表格。
7. 组装 DOCX、PDF、LaTeX 或 Typst 论文。
8. 在最终提交前核验题目要求、公式、结果、图表、引用和格式。

## 什么时候使用

当你需要 Codex 帮你完成以下工作时，可以使用本 skill：

- 数学建模竞赛完整解题。
- 根据赛题生成建模计划和论文结构。
- 构建包含数据、代码、结果、图表和报告的可复现项目。
- 撰写、润色或检查数学建模论文。
- 在提交前检查结果和论文是否一致、完整、可验证。

示例：

```text
使用 $mathematical-modeling-competition-copilot 帮我完成这个数学建模题，从建模到论文终检。
```

英文示例：

```text
Use $mathematical-modeling-competition-copilot to solve this mathematical modeling contest problem and prepare a verified paper.
```

## 工作流

### 1. 竞赛启动与策略

首先确认竞赛类型、论文语言、提交格式、时间预算、队伍分工、可用数据和最终交付物。如果任务目标不清楚，会先进行需求澄清，再开始建模。

最低产出：

- `plan.md`
- `todo.md`
- 竞赛约束和成功标准

### 2. 赛题分析与建模设计

工作流使用受 LLM-MM-Agent 启发的四阶段框架：

- Problem Analysis：赛题分析
- Mathematical Modeling：数学建模
- Computational Solving：计算求解
- Solution Reporting：结果报告

建模选择采用 HMML 风格的层级方法选择：先判断建模领域，再细分子领域，比较候选方法，最后选择最简单且足够有说服力的模型。

最低产出：

- 子问题拆解
- 核心假设
- 变量和参数定义
- 约束条件和目标函数
- 候选方法与选择理由
- 验证计划

### 3. 文献与复现细节

当 README、论文或已有资料留下关键空白时，可以使用 `paper-context-resolver` 处理窄范围复现问题，例如：

- 数据集划分
- 数据预处理
- 评价协议
- 方法细节
- checkpoint 或运行假设
- 论文与仓库说明之间的冲突

它不用于泛泛总结论文。一般文献综述只提取能改进竞赛方案的模型、数据、评价方法或对照基线。

最低产出：

- 文献来源记录
- 直接证据和推断的区分
- 来源冲突说明

### 4. 计算与实验

工作流要求区分原始数据、处理后数据、代码、Notebook、结果表和图表。所有数值结论必须来自已执行代码、电子表格公式或可信来源。

最低产出：

- `code/`
- `notebooks/`
- `results/`
- `reports/experiment_log.md`
- 代码或 Notebook 的执行状态

### 5. 表格分析与情景表

当任务涉及评分矩阵、敏感性分析、情景对比、仪表盘或 Excel 交付物时，使用电子表格工作流。

要求：

- 公式可见、可追踪。
- 不硬编码派生结果。
- 标明单位、假设和数据来源。
- 保留源数据路径或说明。

### 6. 图表、流程图与结构图

数据图和非数据图分开处理：

- 数据驱动图表属于计算与可视化阶段。
- 方法流程图、算法结构图、因果结构图、框架图属于图示阶段。
- 不重复绘制没有信息增量的装饰图。

最低产出：

- `figures/`
- 图表生成脚本或源数据引用
- 必要时保留流程图源文件

### 7. 论文撰写

论文阶段把模型、结果、图表、假设、文献和验证结论组装成竞赛论文。

最终论文应包含：

- 清晰的摘要：问题、模型、结果、验证。
- 明确的假设和符号说明。
- 与子问题对应的模型章节。
- 可追溯的结果来源。
- 易读的图表和表格。
- 关键假设的敏感性或鲁棒性分析。
- 诚实但不过度削弱结论的局限性。
- 支撑方法、数据或对照基线的参考文献。

### 8. 表格润色

LaTeX 论文可以使用 `latex-tables` 优化回归表、统计摘要表和学术表格。普通竞赛表格也要满足：

- 标题简洁。
- 单位清楚。
- 来源说明完整。
- 数值列对齐。
- 精度合理。
- 表格数值与结果文件一致。

### 9. 最终核验

工作流最后必须进行终检，不能在没有证据的情况下声称完成。

核验内容包括：

- 每个子问题都有回答。
- 每个表格和图都被正文引用并有标题。
- 单位、符号、变量名称一致。
- 代码或 Notebook 执行状态已记录。
- 文献结论有来源链接或引用。
- DOCX、PDF、LaTeX 或 Typst 输出在适用时完成视觉检查。
- 最终回复说明哪些内容已验证，哪些仍未验证。

## 默认项目结构

```text
.
|-- plan.md
|-- todo.md
|-- data/
|   |-- raw/
|   `-- processed/
|-- notebooks/
|-- code/
|-- results/
|-- figures/
|-- reports/
|   |-- problem_analysis.md
|   |-- model_design.md
|   |-- experiment_log.md
|   `-- verification_report.md
`-- paper/
```

## 集成的 Skills

本 skill 会在可用时协调以下个人或插件 skills：

- `brainstorming`
- `1start-mathmodel`
- `2analysis-modeling`
- `3coding-visual`
- `4drawio`
- `5writing`
- `6verity`
- `llm-mm-agent`
- `paper-context-resolver`
- `latex-tables`
- `verification-before-completion`
- `jupyter-notebooks`
- `documents`
- `pdf`
- `spreadsheets`

如果某个辅助 skill 不可用，工作流会继续执行同一阶段，并在 `reports/verification_report.md` 中记录缺失项。

## 安装

把仓库克隆到 Codex skills 目录：

### Windows PowerShell

```powershell
git clone https://github.com/Ryan-2727/mathematical-modeling-competition-copilot.git "$env:USERPROFILE\.codex\skills\mathematical-modeling-competition-copilot"
```

### macOS/Linux

```bash
git clone https://github.com/Ryan-2727/mathematical-modeling-competition-copilot.git "$HOME/.codex/skills/mathematical-modeling-competition-copilot"
```

安装后重启 Codex，让 skill 被重新发现。

## 仓库结构

```text
.
|-- SKILL.md
|-- README.md
|-- README.en.md
|-- DESCRIPTION.md
|-- agents/
|   `-- openai.yaml
`-- references/
    `-- workflow-map.md
```

## 设计说明

这个 skill 故意保持轻量。它不捆绑完整求解器、前端应用或论文模板系统，而是给 Codex 一个可靠的数学建模竞赛总控流程。具体工具只在当前任务需要时调用。

`LLM-MM-Agent` 在这里被视为方法论来源，而不是必须运行的本地依赖。这样可以保留四阶段建模思路，同时让工作流更适合 Codex 内部使用。
