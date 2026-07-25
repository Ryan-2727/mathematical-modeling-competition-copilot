# Mathematical Modeling Competition Copilot

**Mathematical Modeling Competition Copilot** 是一个自包含的 Codex skill，用于数学建模竞赛的端到端工作流：审题、建模、文献细节查证、可复现实验、图表表格、论文撰写和最终核验。

适用场景包括 MCM/ICM、CUMCM、华为杯、校赛以及其他类似数学建模竞赛。

[![Switch to English](https://img.shields.io/badge/README-English-0969da)](README.md)

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
- 真实文献证据账本：至少 10 篇真实、相关且在正文实际引用的学术
  文献，核对权威元数据、Google Scholar 精确题名检索和支持性原文
- 论文/文献复现细节查证规则
- 代码、Notebook、结果表和数据图流程
- 数据来源范围、量纲单位核验，以及预先登记的失败导向压力测试
- 流程图和结构图规则
- 中文 2025 格式和英语比赛基础版论文撰写分支
- 从优秀论文语料库学习结构、图表语法、验证叙事和 LaTeX 写作规范
- 多年份优秀论文库的跨题型写作规律
- LaTeX 和学术表格规则
- 可在 Overleaf 与 VS Code 中编译和预览的可移植 XeLaTeX/latexmk 论文脚手架
- 最终核验规则
- 工具缺失时的 fallback 规则
- 比赛模式、当年规则快照、AI 使用留痕与提交冻结
- 绑定官方来源 URL、快照哈希、有效期和结构化字段的规则锁，以及累计阶段门
- 数据审计、追踪表、环境记录、匿名扫描和哈希核验
- CUMCM 2026 规则配置、AI 使用详情 PDF、证据账本、可复现运行清单与论证覆盖检查
- CUMCM 与 MCM/ICM 可执行规则配置，以及初始化时自动选择的独立可移植
  LaTeX 模板
- 由计算结果哈希驱动的关键数值唯一真源、LaTeX 宏生成器和 11 类模型族验证适配器
- 面向答案的摘要、权威书目快照、支持性原文、LaTeX 日志、图表题注/标签和图表清单检查
- 不默认调用 shell 的干净副本重复复现
- PDF 渲染与元数据质检、图像/OCR 匿名检查和真实 TeX CI
- 论文完成后的可选冲奖评审：三类模拟评委、四维证据评分卡与获奖准备度结构验收，仅在用户确认后执行
- 盲化独立评委聚合与隐藏基准回归：学习可迁移优点，但不依赖配对答案，
  也不会自动改写基线
- 双交付硬门槛：编译后的 PDF 与完整 LaTeX 源码，以及包含代码、
  数据证据、环境、命令和结果哈希的支撑材料包
- 分离 `delivery/` 与 `official-submission/`，避免把用户侧源码或支撑包
  误传到禁止附加文件的比赛

## 完成硬标准

一篇论文只有同时满足以下两项才算完成：

1. `paper/main.pdf` 由随附的 LaTeX 源码编译得到；源码包含
   `paper/main.tex`、`paper/references.bib`、所有分节文件，以及重建 PDF
   所需的图、表、类、样式和本地资源。
2. `support.zip` 包含可运行代码、允许分发的数据或可复现的数据获取
   证据、环境/依赖信息、精确运行命令、代表性结果、许可信息和 SHA-256。

LaTeX 正文必须实际引用至少 10 篇互不重复、真实且相关的学术文献。
每篇文献都要写入 `reports/bibliography.csv`，核对出版社、DOI/Crossref、
OpenAlex、期刊或会议等权威元数据，保存 Google Scholar 精确题名检索，
确认精确题名结果并记录核验日期，再阅读支持论文论断的原文位置。
`verification_source` 必须填写与元数据快照一致的 Crossref、DOI 或 OpenAlex
具体 HTTPS 记录 URL；Scholar 查询统一使用
`https://scholar.google.com/scholar?q=...`。严禁虚构书目信息、原文内容和定位信息。
还必须使用 `scripts/verify_bibliography_metadata.py` 核对保存的权威元数据
快照、撤稿检查记录和支持性原文哈希。
完成前必须运行 `scripts/verify_paper_delivery.py`；脚本通过只代表结构核验
通过，不能替代人工阅读原文和检查 PDF 版面。
在此之前必须运行 `scripts/verify_latex_compatibility.py`，通过
Overleaf 风格和 VS Code 风格的真实编译，并生成与当前源码指纹一致的
`reports/latex_compatibility.json`。

## 可执行证据门禁

初始化会自动选择竞赛模板和提交配置：

```bash
python scripts/init_contest.py --project-dir <project> --contest CUMCM --year 2026 --mode training
python scripts/init_contest.py --project-dir <project> --contest MCM/ICM --year 2027 --mode training
```

论文与 Skill 发布流程使用以下确定性检查：

- `lock_contest_rules.py` 将保存的官方规则快照与 URL、哈希、结构化字段
  和有效期绑定；`contestctl.py check` 累计协调各阶段门，但不替代专项检查器。
- `results/verified_values.csv` 是关键计算数值的唯一真源；
  `generate_verified_values.py` 生成 `paper/generated/results.tex`，
  `verify_verified_values.py` 检查哈希、类型、单位、LaTeX 可达性和过期状态。
- `verify_model_validation.py` 检查回归/预测、分类、优化、随机仿真、
  网络/排序、机理/动力学、因果/计量、无监督、排队/可靠性、空间/时空及
  多目标/动态优化模型声明的验证证据，但不宣称证明数学正确性。
- `verify_abstract_quality.py`、`verify_bibliography_metadata.py` 和
  `verify_manuscript_quality.py` 检查摘要逐问答案、保存的来源证据、引用、
  题注、标签、图表清单和 LaTeX 日志。
- `verify_delivery_profiles.py` 将完整用户交付与比赛官方允许提交的文件分开核验。
- `run_reproduction.py` 在干净副本中执行 argv 命令，保存每次运行日志，
  并按哈希或声明的数值容差比较重复运行；shell 执行必须显式启用。
- `verify_pdf_visual.py`、`anonymity_scan.py` 和 `verify_submission.py`
  区分 `PASS`、`LIMITED` 与 `FAIL`；强制视觉规则不会因为渲染器或 OCR
  缺失而被误判为通过。
- `run_benchmark_regression.py` 评估盲化工件/评分清单。超出容差的回归会
  阻止 Skill 发布，脚本不会自动改写基线。

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
7. 用 LaTeX 组装并编译论文，实际引用至少 10 篇已核验学术文献，并按规则披露 AI 使用。
8. 生成并核验独立支撑材料包，包含代码、数据证据、环境、命令、结果、许可和哈希。
9. 从优秀论文语料库学习通用规则后，再独立解题并进行事后复盘。
10. 完整论文和基础核验完成后，询问是否进行假设合理性、模型创新性、结果正确性和表达清晰度的独立冲奖评审。
11. 执行匿名检查、哈希冻结、提交包验证和回执确认。

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
- `references/embedded/verified-literature-and-two-part-delivery.md`

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

把模型、结果、图表、假设、文献和验证结论组装成竞赛论文。论文必须让公式、结果、图表和结论互相一致，并交付编译后的 `paper/main.pdf` 与完整 LaTeX 源码。源码使用可移植 XeLaTeX/latexmk 工程，必须能在 Overleaf 和 VS Code 中正常编译与预览。

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

提交前必须检查题目要求、假设、公式、代码执行状态、数据来源、图表一致性、引用、论文格式和最终文件。先运行 `scripts/verify_latex_compatibility.py`，确认项目根目录输出和 `build/` 输出两种编译均成功；再构建 `support.zip` 并运行 `scripts/verify_paper_delivery.py`，核验真实文献证据与论文/支撑材料双交付。

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
|-- rules.lock.json
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
|   |-- bibliography.csv
|   |-- bibliography_metadata/
|   |-- source_passages/
|   |-- figure_manifest.csv
|   |-- paper_depth_plan.csv
|   |-- reviewer_scorecard.csv
|   |-- milestones.csv
|   |-- latex_compatibility.json
|   |-- portable_latex_verification.json
|   |-- paper_delivery.json
|   `-- verification_report.md
|-- environment/
|-- support/
|   |-- README.md
|   |-- reproduction_commands.txt
|   |-- materials_manifest.csv
|   `-- data_inventory.csv
|-- support.zip
|-- delivery/
|   `-- manifest.csv
|-- official-submission/
|   `-- manifest.csv
`-- paper/
    |-- main.tex
    |-- README.md
    |-- references.bib
    |-- .latexmkrc
    |-- .vscode/
    |   |-- settings.json
    |   `-- extensions.json
    |-- sections/
    |-- figures/
    |-- build/
    `-- main.pdf
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

Windows 上运行 Python 验证时显式启用 UTF-8：

```powershell
python -X utf8 scripts\validate_skill_contract.py
python -X utf8 -m unittest discover -s tests -v
```

## 仓库结构

```text
.
|-- SKILL.md
|-- README.md
|-- README.en.md
|-- DESCRIPTION.md
|-- scripts/
|   |-- contestctl.py
|   |-- lock_contest_rules.py
|   |-- scaffold_latex_paper.py
|   |-- verify_abstract_quality.py
|   |-- verify_bibliography_metadata.py
|   |-- verify_delivery_profiles.py
|   `-- verify_latex_compatibility.py
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
        |-- verified-literature-and-two-part-delivery.md
        |-- operational-quality-gates.md
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
