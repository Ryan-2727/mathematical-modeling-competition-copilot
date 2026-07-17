# Mathematical Modeling Competition Copilot

**Mathematical Modeling Competition Copilot** 是一个自包含的 Codex skill，用于数学建模竞赛的端到端工作流：审题、建模、文献细节查证、可复现实验、图表表格、论文撰写和最终核验。

适用场景包括 MCM/ICM、CUMCM、华为杯、校赛以及其他类似数学建模竞赛。

[English README](README.md)

## 仅限显式调用

普通的数学建模、竞赛或论文问题不会触发本 skill。只有显式写出
`$mathematical-modeling-competition-copilot`，或直接引用其 `SKILL.md`
链接时才使用。

```text
使用 $mathematical-modeling-competition-copilot 完成这道竞赛题。
```


新电脑只需要安装这个仓库，就能获得完整的数学建模竞赛工作流。原先分散在多个小 skill 里的流程知识已经内嵌到 `references/embedded/`：

- 竞赛启动与 `plan.md` / `todo.md`
- 获奖导向证据门、72 小时里程碑看板和止损规则
- 有边界的建模路线 brainstorming
- 按问题结构选路，以及可审计的“基线—候选模型”取舍日志
- 数学建模六阶段流程
- LLM-MM-Agent 四阶段方法论与 HMML/MLE-Solver 风格建模
- 文献检索和论文解释流程
- 论文/文献复现细节查证规则
- 代码、Notebook、结果表和数据图流程
- 数据来源范围、量纲单位核验，以及预先登记的失败导向压力测试
- 流程图和结构图规则
- 中文 2025 格式和英语比赛基础版论文撰写分支
- 从优秀论文语料库学习结构、图表语法、验证叙事和 LaTeX 写作规范
- 多年份优秀论文库的跨题型写作规律
- LaTeX 和学术表格规则
- 最终核验规则
- 工具缺失时的 fallback 规则
- 比赛模式、当年规则快照、AI 使用留痕与提交冻结
- 数据审计、追踪表、环境记录、匿名扫描和哈希核验
- CUMCM 2026 规则配置、AI 使用详情 PDF、证据账本、可复现运行清单与论证覆盖检查
- 论文完成后的可选冲奖评审：三类模拟评委、四维证据评分卡与获奖准备度结构验收，仅在用户确认后执行
- 隐藏优秀论文的独立基线回归：学习可迁移优点，但不依赖配对答案

## 国赛模型路由增强

当比赛类型为中国大学生数学建模竞赛（CUMCM / 国赛）时，skill 会先读取 `references/embedded/cumcm-model-selection.md`，再为每个小问建立“题目特征 → 模型 → 软件实现 → 验证 → 结果 → 论文位置”的追踪链。

- 按任务特征选择优化与调度、网络与路径、综合评价、预测与拟合、统计与分类、随机系统或机理动态模型。
- 覆盖本地模型库的 30 章内容及判别分析，包括规划、AHP、灰色系统、时间序列、回归、排队、马尔可夫链、微分方程等。
- Python、MATLAB、LINGO 为同等路径：按模型匹配度、可复现性和团队可用环境选择，不要求三者同时使用。
- 每个模型均包含适用条件、常见误用、实现边界和最低验证要求；默认先完成可解释的基线模型，再按证据增加一个增强或对照模型。

国赛示例：

```text
使用 $mathematical-modeling-competition-copilot 参加中国大学生数学建模竞赛。
比赛剩余 3 天，可用 Python、MATLAB、LINGO。请先完成题意拆解、模型候选比较和验证方案。
```

## 不能完全内嵌的能力

下面这些不是纯文字工作流，而是依赖 Codex 插件或本机运行时。新电脑如果需要这些能力，请在 Codex 中安装或启用对应插件：

| 能力 | 需要安装/启用 | 没有时的 fallback |
| --- | --- | --- |
| Jupyter Notebook 创建、编辑、执行 | Data Analytics 插件中的 `jupyter-notebooks` | 使用 Python 脚本和 Markdown 报告，并记录 Notebook 未执行 |
| DOCX 创建、编辑、渲染检查 | Documents 插件 | 用 Markdown/LaTeX 起草论文，并记录 DOCX 未视觉验证 |
| PDF 渲染、抽取、页面检查 | PDF 插件 | 生成源文件或请求本地 PDF 检查，并记录未验证项 |
| XLSX、公式、图表、工作簿渲染 | Spreadsheets 插件 | 使用 CSV/Markdown 表格，并记录公式或布局未验证 |

这些插件不能在本仓库安装时自动带上

## 这个 Skill 能做什么

这个 skill 是数学建模项目的总控入口。它不承诺“保证拿奖”，而是通过规范流程提高产出质量和获奖概率：

1. 固定比赛模式并快照当年官方规则、AI 政策、截止时间和提交流程。
2. 拆解赛题子问题，形成可执行建模路线和追踪表。
3. 完成数据审计与量纲核验，对比可信基线和候选模型，并记录所选模型为何匹配问题机理。
4. 在合规范围内查证文献与复现细节；正式比赛禁止当前题目的公开讨论和互动求助。
5. 用可复现代码、Notebook 或电子表格完成实验，记录环境、数据哈希、求解器、不确定性与失败导向压力测试证据。
6. 生成有明确论证作用的数据图、流程图、模型图和论文表格。
7. 组装论文并披露 AI 使用。
8. 从优秀论文语料库学习通用规则后，再独立解题并进行事后复盘。
9. 论文完整完成后，询问是否进行假设合理性、模型创新性、结果正确性和表达清晰度的独立冲奖评审。
10. 执行匿名检查、哈希冻结、提交包验证和回执确认。

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

### 0. 比赛模式与合规

固定训练、正式比赛或赛后复盘模式；记录当年官方规则、AI 政策、允许的资料、截止时间和提交流程。正式比赛禁止浏览当前题目的讨论、答案和互动求助来源。

参考：`references/embedded/contest-modes-and-compliance.md`

### 1. 竞赛启动与策略

确认竞赛类型、论文语言、提交格式、时间预算、队伍分工、可用数据和最终交付物。创建或更新 `plan.md`、`todo.md` 和 `reports/milestones.csv`。

参考：

- `references/embedded/contest-setup.md`
- `references/embedded/award-oriented-workflow.md`
- `references/embedded/contest-operations-72h.md`

### 2. 赛题分析与建模设计

拆解子问题，定义假设、变量、参数、约束、目标函数、候选模型和验证计划。按问题结构选路，并在 `reports/model_decision_log.csv` 中记录基线、候选、失败测试、验证成本和取舍证据。

参考：

- `references/embedded/llm-mm-agent-methodology.md`
- `references/embedded/mathmodel-six-phase.md`
- `references/embedded/problem-structure-playbooks.md`

### 3. 文献与复现细节

只在关键细节影响建模或复现时查证文献，例如数据划分、预处理、评价协议、方法细节、运行假设或来源冲突。

参考：

- `references/embedded/literature-fetch-and-explain.md`
- `references/embedded/paper-context-resolver.md`

### 4. 计算与实验

区分原始数据、处理后数据、代码、Notebook、结果表和图表；完成数据审计、单位与来源范围核验、子问题追踪、环境记录和失败导向压力测试。所有数值结论必须来自已执行代码、电子表格公式或可信来源。

参考：

- `references/embedded/data-traceability-and-reproducibility.md`
- `references/embedded/data-units-and-source-quality.md`
- `references/embedded/stress-testing-and-uncertainty.md`
- `references/embedded/computation-and-visualization.md`

### 5. 表格分析与情景表

处理评分矩阵、敏感性分析、情景对比、仪表盘和 Excel/CSV 表格。公式、单位、假设和数据来源必须可追踪。

### 6. 图表、流程图与结构图

数据图和非数据图分开处理。数据图用于支持结论；流程图、算法结构图、因果图和框架图用于解释方法。

参考：`references/embedded/diagrams.md`

### 7. 论文撰写

把模型、结果、图表、假设、文献和验证结论组装成竞赛论文。论文必须让公式、结果、图表和结论互相一致。

参考：

- `references/embedded/paper-writing.md`
- `references/embedded/paper-writing-zh-cn-format2025.md`
- `references/embedded/paper-learning-from-exemplars.md`
- `references/embedded/2025-corpus-observations.md`
- `references/embedded/latex-paper-pipeline.md`
- `references/embedded/paper-writing-en-contest-base.md`
- `references/embedded/paper-writing-mcm-icm-current.md`

### 8. 表格润色

处理 LaTeX 表格、统计表、摘要表和普通竞赛表格。重点检查标题、单位、来源、精度、列对齐和数值来源。

参考：`references/embedded/latex-tables.md`

### 9. 最终核验

提交前必须检查题目要求、假设、公式、代码执行状态、数据来源、图表一致性、引用、论文格式和最终文件。

参考：

- `references/embedded/final-verification.md`
- `references/embedded/tool-fallbacks.md`
- `references/embedded/submission-and-anonymity.md`

### 10. 可选冲奖评审

仅在建模、完整论文和第 9 阶段核验全部完成后，询问用户是否需要。用户确认后，由模型、证据和论文三类评委独立审阅，完成四维评分卡，并运行获奖准备度结构验收；通过不等于数学正确，也不代表保证获奖。

参考：

- `references/embedded/post-paper-award-review.md`
- `references/embedded/reviewer-scorecard-and-presentation.md`

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
|   |-- model_decision_log.csv
|   |-- stress_tests.csv
|   |-- units.csv
|   |-- reviewer_scorecard.csv
|   |-- milestones.csv
|   `-- verification_report.md
`-- paper/
```

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

Windows 上更新已有本地安装时，先预览再执行：

```powershell
.\scripts\sync_local_skill.ps1 -WhatIf
.\scripts\sync_local_skill.ps1
```

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
    |-- workflow-map.md
    `-- embedded/
        |-- contest-setup.md
        |-- cumcm-model-selection.md
        |-- mathmodel-six-phase.md
        |-- llm-mm-agent-methodology.md
        |-- literature-fetch-and-explain.md
        |-- paper-context-resolver.md
        |-- computation-and-visualization.md
        |-- diagrams.md
        |-- paper-writing.md
        |-- paper-writing-zh-cn-format2025.md
        |-- paper-writing-en-contest-base.md
        |-- latex-tables.md
        |-- final-verification.md
        `-- tool-fallbacks.md
```

## 设计说明

这个 skill 采用“单 skill + 内嵌参考模块”的结构，而不是在仓库里放多个嵌套小 skill。这样新电脑只安装一个仓库，也能稳定触发主 skill，并由主 skill 按阶段读取内嵌规则。

对于 DOCX、PDF、XLSX 和 Notebook 这类需要运行时工具的任务，本仓库提供流程和 fallback，但用户仍应在 Codex 中安装对应插件来获得完整文件处理能力。
