# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码仓库中工作时提供指引。

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介 / What This Project Does

医院机器人导航的本地 LLM 任务规划器。将自然语言指令 + 场景图 JSON 转换为结构化 `TaskPlan` JSON，使用 Ollama（mistral / gemma4:e4b）配合 Pydantic 模式校验。

Local LLM task planner for hospital robot navigation. Converts natural-language instructions + scene graph JSON into structured `TaskPlan` JSON using Ollama (mistral / gemma4:e4b) with Pydantic schema enforcement.

## 环境配置（WSL2 + Windows）/ Environment Setup (WSL2 + Windows)

项目运行在 **WSL2**（Ubuntu 24.04）中，Ollama 在 **Windows** 原生运行。这样避免在 Linux 虚拟机中运行 LLM，Ollama 可直接使用 Windows GPU。

The project runs inside **WSL2** (Ubuntu 24.04) with Ollama running natively on **Windows**. This avoids running the LLM inside a Linux VM and lets Ollama use the Windows GPU directly.

### WSL2 侧（Linux）/ WSL2 side (Linux)

使用专用 conda 环境 `llm-task-planner` 以避免污染系统 Python。

Uses a dedicated conda environment `llm-task-planner` to avoid polluting the system Python.

```bash
# 激活 conda 环境 / Activate conda environment
conda activate llm-task-planner
```

**`llm-task-planner` conda 环境中已安装的包：**
- Python 3.12、`ollama`（v0.6.2）、`pydantic`（v2.13.4）、`pyyaml`

**Already installed in the `llm-task-planner` conda env:**
- Python 3.12, `ollama` (v0.6.2), `pydantic` (v2.13.4), `pyyaml`

从零重新安装：
```bash
# 从零安装 / Install from scratch
conda create -n llm-task-planner python=3.12 -y
conda activate llm-task-planner
pip install ollama pydantic pyyaml
```

### Windows 侧（Ollama 宿主）/ Windows side (Ollama host)

1. 从 https://ollama.com 安装 Ollama
2. 拉取模型：`ollama pull mistral` 和 `ollama pull gemma4:e4b`
3. 设置以下 **Windows 系统环境变量**（不是 WSL 环境变量），使 Ollama 接受远程连接：

```
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_KEEP_ALIVE=0
```

`OLLAMA_HOST=0.0.0.0:11434` 让 Ollama 监听所有网络接口（WSL2 需要此设置才能访问）。`OLLAMA_KEEP_ALIVE=0` 禁用空闲模型默认的 5 分钟保活超时。

`OLLAMA_HOST=0.0.0.0:11434` tells Ollama to listen on all interfaces (required for WSL2 to reach it). `OLLAMA_KEEP_ALIVE=0` disables the default 5-minute keep-alive timeout for idle models.

### Ollama 主机自动检测 / Ollama host auto-detection

在 `config.yaml` 中，`ollama_host` 字段控制连接：

In `config.yaml`, the `ollama_host` field controls connection:

```yaml
ollama_host: ''  # 空值 = 从 WSL2 默认网关自动检测 Windows 主机 IP
                 # empty = auto-detect Windows host IP from WSL2 default gateway
```

留空时，`get_ollama_host()` 执行 `ip route show default` 提取 WSL2 网关 IP（即 Windows 宿主机）。也可以显式设置：

When empty, `get_ollama_host()` runs `ip route show default` to extract the WSL2 gateway IP (the Windows host). You can also set it explicitly:

```yaml
ollama_host: 'http://172.x.x.x:11434'
```

## 运行 / Running

```bash
# 先激活 conda 环境 / Activate conda env first
conda activate llm-task-planner

# 运行规划器（Ollama 需在 Windows 上运行并设置上述环境变量）
# Run the planner (Ollama must be running on Windows with the env vars above)
python3 main.py
```

Ollama 运行在 Windows 上，不在 WSL2 中。运行 `main.py` 前确保 Ollama 已启动。无构建系统、无测试、无代码检查配置。依赖：`ollama`、`pydantic`、`pyyaml`。

Ollama runs on Windows, not in WSL2. Ensure it is running before `main.py`. No build system, no tests, no linting configured. Dependencies: `ollama`, `pydantic`, `pyyaml`.

## 架构 / Architecture

`main.py` 中 `call_llm_task_planner()` 的流水线：

The pipeline in `main.py` `call_llm_task_planner()`:

1. **子图提取**（`extract_relevant_subgraph`）—— 从完整场景图中筛选用户指令提到的实体，构建 `llm_grounding_index` 将别名映射到规范 ID。
   **Subgraph extraction** (`extract_relevant_subgraph`) — filters the full scene graph down to entities mentioned in the user instruction, builds a `llm_grounding_index` mapping aliases to canonical IDs.

2. **LLM 调用**（`run_llm_once`）—— 将系统提示词 + 相关子图发送到 Ollama，以 `TaskPlan` JSON schema 作为格式约束。Ollama 主机通过 `get_ollama_host()` 解析（自动检测或配置覆盖）。
   **LLM call** (`run_llm_once`) — sends system prompt + relevant subgraph to Ollama with `TaskPlan` JSON schema as the format constraint. Ollama host is resolved via `get_ollama_host()` (auto-detect or config override).

3. **JSON 清理**（`extract_json_object`）—— 去除 markdown 围栏，提取第一个有效 JSON 对象。
   **JSON cleanup** (`extract_json_object`) — strips markdown fences, extracts first valid JSON object.

4. **模式校验** —— `TaskPlan.model_validate_json()`。
   **Schema validation** — `TaskPlan.model_validate_json()`.

5. **规范化**（`canonicalize_task_plan`）—— 通过 grounding index 将别名 target_id 映射回精确的场景图 ID。
   **Canonicalization** (`canonicalize_task_plan`) — maps any alias target_ids back to exact scene graph IDs via the grounding index.

6. **语义校验**（`validate_task_plan_semantics`）—— 检查步骤顺序、执行器正确性、实体锚定、护送/转移/避障需求。分解为独立的检查函数（`_validate_chain_structure`、`_validate_transfer_requirements` 等）。
   **Semantic validation** (`validate_task_plan_semantics`) — checks step sequencing, executor correctness, grounding, screening/transfer/avoid requirements. Decomposed into individual check functions (`_validate_chain_structure`, `_validate_transfer_requirements`, etc.).

7. **修复循环** —— 最多 2 次尝试；校验失败时，`build_repair_prompt` 将错误发送回 LLM。
   **Repair loop** — up to 2 attempts; if validation fails, `build_repair_prompt` sends errors back to the LLM.

8. **基于规则的回退**（`build_rule_based_transfer_plan`）—— 当 LLM 失败时，为"将患者从 A 转移到 B"模式提供确定性计划。
   **Rule-based fallback** (`build_rule_based_transfer_plan`) — deterministic plan for "bring patient from A to B" patterns when LLM fails.

### main.py 函数结构 / main.py function structure

`main.py` 按功能分区组织，包含提取的常量：

`main.py` is organized into clearly separated sections with extracted constants:

- **常量** —— `NAVIGATION_ACTIONS`、`WORKFLOW_ACTIONS`、`EXECUTOR_RULES`、评分常量（`SCORE_EXACT_ALIAS`、`SCORE_MIN_THRESHOLD` 等）
  **Constants** — `NAVIGATION_ACTIONS`, `WORKFLOW_ACTIONS`, `EXECUTOR_RULES`, scoring constants (`SCORE_EXACT_ALIAS`, `SCORE_MIN_THRESHOLD`, etc.)
- **文本辅助函数** —— `normalize_text()`、`compact_text()`、`alias_forms()`
  **Text helpers** — `normalize_text()`, `compact_text()`, `alias_forms()`
- **实体索引辅助函数** —— `build_entity_index()`、`detect_intent()`、`find_restricted_entities()`、`target_type_matches_entity()`
  **Entity index helpers** — `build_entity_index()`, `detect_intent()`, `find_restricted_entities()`, `target_type_matches_entity()`
- **JSON 提取** —— `extract_json_object()`
  **JSON extraction** — `extract_json_object()`
- **实体别名收集** —— `collect_entity_aliases()`
  **Entity alias collection** — `collect_entity_aliases()`
- **实体评分** —— `score_entity_for_instruction()`（由 `_score_alias_matches`、`_score_room_number_match`、`_score_entity_type_bonus` 组成）
  **Entity scoring** — `score_entity_for_instruction()` (composed of `_score_alias_matches`, `_score_room_number_match`, `_score_entity_type_bonus`)
- **子图扩展** —— `expand_relevant_entity_ids()`（由 `_expand_by_location`、`_expand_persons_in_rooms`、`_expand_by_relations` 组成）
  **Subgraph expansion** — `expand_relevant_entity_ids()` (composed of `_expand_by_location`, `_expand_persons_in_rooms`, `_expand_by_relations`)
- **锚定索引** —— `canonicalize_identifier()`、`build_llm_grounding_index()`、`find_grounded_mentions()`
  **Grounding index** — `canonicalize_identifier()`, `build_llm_grounding_index()`, `find_grounded_mentions()`
- **任务计划规范化** —— `canonicalize_task_plan()`
  **Task-plan canonicalization** — `canonicalize_task_plan()`
- **语义校验** —— `validate_task_plan_semantics()` 调度器 + 各 `_validate_*` 函数
  **Semantic validation** — `validate_task_plan_semantics()` orchestrator + individual `_validate_*` functions
- **基于规则的回退** —— `build_rule_based_transfer_plan()`
  **Rule-based fallback** — `build_rule_based_transfer_plan()`
- **子图提取** —— `extract_relevant_subgraph()`
  **Subgraph extraction** — `extract_relevant_subgraph()`
- **LLM 交互** —— `get_ollama_host()`、`run_llm_once()`
  **LLM interaction** — `get_ollama_host()`, `run_llm_once()`
- **配置** —— `load_config()`、`get_default_model()`
  **Config** — `load_config()`, `get_default_model()`

所有函数都有文档字符串。日志使用 `logging.getLogger(__name__)` 而非 `print()`。

All functions have docstrings. Logging uses `logging.getLogger(__name__)` instead of `print()`.

## 关键文件 / Key Files

- `config.yaml` — 模型选择（`models:` 中 `default: true`）、Ollama `options:`（temperature、num_ctx 等）、`ollama_host` 连接配置
  `config.yaml` — model selection (`models:` with `default: true`), Ollama `options:` (temperature, num_ctx, etc.), and `ollama_host` for connection
- `schema.py` — Pydantic 模型：`TaskPlan`、`TaskStep`、`Constraints` 及 Literal 类型别名（`AllowedAction`、`AllowedStatus` 等）
  `schema.py` — Pydantic models: `TaskPlan`, `TaskStep`, `Constraints`, and Literal type aliases (`AllowedAction`, `AllowedStatus`, etc.)
- `prompt.py` — `SYSTEM_PROMPT`、`build_user_prompt()`、`build_repair_prompt()`。系统提示词包含执行器规则、锚定规则、任务分解规则及完整的好/坏示例。
  `prompt.py` — `SYSTEM_PROMPT`, `build_user_prompt()`, `build_repair_prompt()`. The system prompt contains executor rules, grounding rules, task decomposition rules, and a full good/bad example.
- `scene_graph.json` — 多楼层医院场景图输入（实体 + 关系）
  `scene_graph.json` — multi-floor hospital scene graph input (entities + relations)
- `task_plan_output.json` — 上次运行输出
  `task_plan_output.json` — last run output

## 约定 / Conventions

- `target_id` 值必须匹配精确的场景图实体 ID 或 `llm_grounding_index` 值，绝不能使用别名如 `R105` 或 `A_PATIENT_01`。
  `target_id` values must match exact scene graph entity IDs or `llm_grounding_index` values — never aliases like `R105` or `A_PATIENT_01`.

- 每个操作的执行器是确定性的：`locate_entity` → `scene_graph`，导航操作 → `nav2`，工作流操作 → `external_workflow` 等（定义在 main.py 的 `EXECUTOR_RULES` 字典中）。
  Executor is deterministic per action: `locate_entity` → `scene_graph`, navigation actions → `nav2`, workflow actions → `external_workflow`, etc. (defined in `EXECUTOR_RULES` dict in main.py).

- `task_chain` 最多 6 个步骤。转移任务始终遵循：定位 → 导航到源位置 → 护送到目的地 →（可选）触发工作流。
  `task_chain` max 6 steps. Transfer tasks always follow: locate → navigate_to source → escort_to destination → (optional) trigger_workflow.

- 实体评分使用 `normalize_text`（小写化、非字母数字字符替换为空格）和 `compact_text`（移除所有非字母数字字符）进行别名匹配。
  Entity scoring uses `normalize_text` (lowercased, non-alphanumeric → space) and `compact_text` (all non-alphanumeric removed) for alias matching.

- 所有输出使用 `logging.getLogger(__name__)`，不使用 `print()` 调用。通过 `logging.basicConfig()` 在 `__main__` 中配置。
  All output uses `logging.getLogger(__name__)` — no `print()` calls. Configure via `logging.basicConfig()` in `__main__`.
