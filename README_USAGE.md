# LLM Robot Task Planner - 使用说明

## 前置条件

### 1. 安装依赖

```bash
pip install ollama pydantic pyyaml
```

### 2. 安装并启动 Ollama

```bash
# 安装 Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 从 https://ollama.com 下载安装包

# 启动 Ollama 服务
ollama serve
```

### 3. 拉取模型

```bash
# 默认使用 mistral
ollama pull mistral

# 或选择其他模型
ollama pull gemma4:e4b
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
```

## 文件结构

```
├── schema.py          # Pydantic 数据模型定义
├── prompt.py          # System prompt 和 user prompt 构造
├── config.yaml        # 模型列表和推理参数配置
├── main.py            # 主程序入口
└── README_USAGE.md    # 本文件
```

## 运行

```bash
python main.py
```

## 配置说明

### 切换模型

编辑 `config.yaml`，修改 `default: true` 的模型：

```yaml
models:
  mistral:
    name: "mistral"
    description: "Mistral 7B - 通用推理能力强"
    default: true            # ← 改这里

  gemma4e4b:
    name: "gemma4:e4b"
    description: "Gemma 4 4B - 轻量快速，适合简单任务"
    default: false           # ← 或改这里
```

也可以在调用时通过参数指定模型：

```python
result = call_llm_task_planner(user_command, scene_graph, model_name="gemma4:e4b")
```

### 添加新模型

1. 先拉取模型：`ollama pull <模型名>`
2. 在 `config.yaml` 的 `models` 下添加配置

### 调整推理参数

编辑 `config.yaml` 中的 `options`：

```yaml
options:
  temperature: 0.1       # 降低 → 更确定性，提高 → 更多样
  num_ctx: 4096          # 上下文窗口，scene graph 大时调高
  num_predict: 512       # 最大生成 token，多步骤任务建议 ≥ 816
```

**常见调整场景：**

| 场景 | 建议参数 |
|------|----------|
| Scene graph 很大 (50+ 实体) | `num_ctx: 8192` 或 `16384` |
| 输出被截断 | `num_predict: 1024` |
| 输出不够稳定 | `temperature: 0.2`, 去掉 `seed` |
| 调试阶段 | 保留 `seed: 42` 保证可复现 |

## 自定义输入

在 `main.py` 的 `if __name__ == "__main__":` 中修改 `user_command` 和 `scene_graph`：

```python
user_command = "Navigate to the nurse station and wait for instructions."

scene_graph = {
    "entities": [
        {"id": "nurse_station_1", "type": "staff_station"},
    ],
    "relations": []
}
```

## 输出示例

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

## 后续集成

将 `call_llm_task_planner()` 封装为 ROS2 node：

- 输入：来自 Khronos scene graph 的 JSON
- 输出：`task_plan_json`
- 下游：task executor 将其转换为 Nav2 action
