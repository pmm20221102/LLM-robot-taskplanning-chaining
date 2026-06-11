# LLM Robot Task Planner - Usage Guide / 使用说明

## Prerequisites / 前置条件

### 1. Install Python Dependencies / 安装 Python 依赖

Requires Python 3.12+.

需要 Python 3.12+。

```bash
pip install ollama pydantic pyyaml
```

### 2. WSL2 + Windows Ollama Setup / WSL2 + Windows Ollama 搭建

This project runs in **WSL2** (Ubuntu 24.04) with Ollama running natively on **Windows** to directly use the Windows GPU.

本项目在 **WSL2**（Ubuntu 24.04）中运行，Ollama 在 **Windows 原生环境** 中运行，这样可以直接使用 Windows GPU。

#### Windows Side / Windows 端

1. Download and install Ollama from https://ollama.com
   从 https://ollama.com 下载安装 Ollama
2. Pull models:
   拉取模型：
   ```bash
   ollama pull mistral
   ollama pull gemma4:e4b
   ```
3. Set **Windows system environment variables** (not WSL env vars):
   设置 **Windows 系统环境变量**（不是 WSL 内的环境变量）：

   | Variable 变量名 | Value 值 | Description 说明 |
   |---|---|---|
   | `OLLAMA_HOST` | `0.0.0.0:11434` | Makes Ollama listen on all interfaces, allowing WSL2 to connect / 让 Ollama 监听所有网卡，允许 WSL2 连入 |
   | `OLLAMA_KEEP_ALIVE` | `0` | Disables 5-minute idle timeout for models / 禁用空闲模型的 5 分钟超时 |

#### WSL2 Side / WSL2 端

```bash
# Create and activate conda environment
# 创建并激活 conda 环境
conda create -n llm-task-planner python=3.12 -y
conda activate llm-task-planner

# Install dependencies
# 安装依赖
pip install ollama pydantic pyyaml
```

### 3. Ollama Connection Config / Ollama 连接配置

Edit `ollama_host` in `config.yaml`:

编辑 `config.yaml` 中的 `ollama_host`：

```yaml
# Empty = auto-detect Windows host IP from WSL2 default gateway
# 空字符串 = 自动检测 Windows 宿主机 IP（从 WSL2 默认网关读取）
ollama_host: ''

# Or manually specify Windows host IP
# 或手动指定 Windows 主机 IP
ollama_host: 'http://172.x.x.x:11434'
```

Auto-detection reads the WSL2 gateway address (the Windows host) via `ip route show default`. Manual config is usually unnecessary.

自动检测通过 `ip route show default` 获取 WSL2 网关地址（即 Windows 主机），通常无需手动配置。

### 4. Pull Models (Alternative) / 拉取模型（替代方式）

If running Ollama directly on Linux (non-WSL2 scenario):

如果在 Linux 端直接运行 Ollama（非 WSL2 场景）：

```bash
# Install Ollama
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start service
# 启动服务
ollama serve &

# Pull models
# 拉取模型
ollama pull mistral
ollama pull gemma4:e4b
```

## File Structure / 文件结构

```
├── schema.py          # Pydantic data model definitions (with docstrings)
│                      # Pydantic 数据模型定义（含文档字符串）
├── prompt.py          # System prompt and user prompt construction (with type annotations)
│                      # System prompt 和 user prompt 构造（含类型注解）
├── config.yaml        # Model list, inference params, and Ollama connection config
│                      # 模型列表、推理参数和 Ollama 连接配置
├── main.py            # Main entry point (modular function structure)
│                      # 主程序入口（重构为模块化函数结构）
├── scene_graph.json   # Hospital scene graph input (entities + relations)
│                      # 医院场景图输入（实体 + 关系）
├── task_plan_output.json  # Last run output
│                      # 上次运行输出
└── README_USAGE.md    # This file
                       # 本文件
```

## Running / 运行

```bash
conda activate llm-task-planner
python main.py
```

Make sure Ollama is running on the Windows side. If `ollama_host` is empty in `config.yaml`, the program auto-detects the WSL2 gateway address to connect to Ollama on Windows. No build system, no tests, no linting configured.

确保 Windows 端 Ollama 已启动。如果 `config.yaml` 中 `ollama_host` 为空，程序会自动检测 WSL2 网关地址连接 Windows 上的 Ollama。无构建系统、无测试、无代码检查配置。

## Configuration / 配置说明

All configuration is in `config.yaml`: model selection, inference parameters, and Ollama connection.

所有配置在 `config.yaml` 中：模型选择、推理参数和 Ollama 连接。

### Switching Models / 切换模型

Edit `config.yaml` and change which model has `default: true`:

编辑 `config.yaml`，修改 `default: true` 的模型：

```yaml
models:
  mistral:
    name: "mistral"
    description: "Mistral 7B - Strong general reasoning"
    # Mistral 7B - 通用推理能力强
    default: true            # ← change here / ← 改这里

  gemma4e4b:
    name: "gemma4:e4b"
    description: "Gemma 4 4B - Lightweight and fast, suitable for simple tasks"
    # Gemma 4 4B - 轻量快速，适合简单任务
    default: false           # ← or change here / ← 或改这里
```

You can also specify the model via parameter at call time:

也可以在调用时通过参数指定模型：

```python
result = call_llm_task_planner(user_command, scene_graph, model_name="gemma4:e4b")
```

### Adding New Models / 添加新模型

1. Pull the model first: `ollama pull <model_name>`
   先拉取模型：`ollama pull <模型名>`
2. Add config under `models` in `config.yaml`
   在 `config.yaml` 的 `models` 下添加配置

### Adjusting Inference Parameters / 调整推理参数

Edit `options` in `config.yaml`:

编辑 `config.yaml` 中的 `options`：

```yaml
options:
  temperature: 0.1       # Lower → more deterministic, higher → more diverse
                         # 降低 → 更确定性，提高 → 更多样
  num_ctx: 4096          # Context window, increase for large scene graphs
                         # 上下文窗口，scene graph 大时调高
  num_predict: 512       # Max generated tokens, ≥ 816 recommended for multi-step tasks
                         # 最大生成 token，多步骤任务建议 ≥ 816
```

**Common Adjustment Scenarios / 常见调整场景：**

| Scenario 场景 | Recommended Params 建议参数 |
|---|---|
| Large scene graph (50+ entities) / Scene graph 很大（50+ 实体） | `num_ctx: 8192` or `16384` |
| Output is truncated / 输出被截断 | `num_predict: 1024` |
| Output is unstable / 输出不够稳定 | `temperature: 0.2`, remove `seed` |
| Debugging / 调试阶段 | Keep `seed: 42` for reproducibility / 保留 `seed: 42` 保证可复现 |

## Custom Input / 自定义输入

Modify `user_command` and `scene_graph` in the `if __name__ == "__main__":` block of `main.py`:

在 `main.py` 的 `if __name__ == "__main__":` 中修改 `user_command` 和 `scene_graph`：

```python
# The natural language instruction for the robot
# 机器人的自然语言指令
user_command = "Navigate to the nurse station and wait for instructions."

# Scene graph with entities and relations relevant to the instruction
# 与指令相关的场景图实体和关系
scene_graph = {
    "entities": [
        {"id": "nurse_station_1", "type": "staff_station"},
    ],
    "relations": []
}
```

## Output Example / 输出示例

The planner produces a validated `TaskPlan` JSON with status and task chain:

规划器输出一个包含状态和任务链的校验后 `TaskPlan` JSON：

```json
{
  "status": "valid",
  "task_chain": [
    {
      "step": 1,
      "action": "locate_entity",
      "target_type": "person",
      "target_id": "patient_01",
      "description": "Locate the patient in room_101",
      "executor": "scene_graph",
      "constraints": {}
    },
    {
      "step": 2,
      "action": "escort_to",
      "target_type": "room",
      "target_id": "room_302",
      "description": "Escort patient to Room 302",
      "executor": "nav2",
      "constraints": {}
    }
  ],
  "notes": []
}
```

## Future Integration / 后续集成

Wrap `call_llm_task_planner()` as a ROS2 node:

将 `call_llm_task_planner()` 封装为 ROS2 node：

- Input / 输入: JSON from Khronos scene graph / 来自 Khronos scene graph 的 JSON
- Output / 输出: `task_plan_json` with validated task chain / 包含校验后任务链的 `task_plan_json`
- Downstream / 下游: task executor converts it to Nav2 actions / task executor 将其转换为 Nav2 action
