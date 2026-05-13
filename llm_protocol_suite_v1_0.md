# LLM Protocol Suite v1.0

一套面向多模型、多模态、Tool Calling 和自研 Runtime 的协议套件。核心思想是“小核心 + 外围扩展”：Model Message Protocol 保持稳定简洁，Runtime Envelope 负责系统语义，Tool Execution Policy 作为 Runtime 子模块，Adapter Mapping Guide 只定义映射规则而不污染核心协议。

## 1. 协议套件总览

两个正式协议、一个 Runtime 子模块和一个实现文档。

```
LLM Protocol Suite
├── 1. LLM Model Message Protocol       # 核心协议
├── 2. LLM Runtime Envelope Protocol    # 外围协议
│   └── Tool Execution Policy           # Runtime 子模块
└── 3. Adapter Mapping Guide            # 实现文档，不是协议
```

### Model Message Protocol

只描述模型输入和模型输出的语义，例如 messages、content、tool_calls、response_format。

### Runtime Envelope Protocol

包装一次模型调用，负责 request id、trace、usage、error、raw、provider_options 等系统语义。

### Tool Execution Policy

作为 Runtime 的子模块，描述工具执行策略，例如 timeout、retry、parallel、approval。

### Adapter Mapping Guide

说明内部协议如何映射到 OpenAI、DeepSeek、Anthropic、Gemini、LangChain 等外部格式。

> **提示：** 关键结论：正式协议只有两个，Model Message Protocol 和 Runtime Envelope Protocol。Tool Execution Policy 是 Runtime 的子模块，Adapter Mapping Guide 是实现指南。

## 2. 设计原则

### 2.1 小核心 + 外围扩展

Model 层必须尽量小、稳定、结构化。Runtime 层可以丰富，用于追踪、审计、错误、usage、provider 原始响应和执行策略。

### 2.2 Provider Transport 不等于 Runtime Semantics

Provider 的传输格式不应直接成为内部语义。例如 OpenAI Chat Completions 的 tool arguments 是 JSON string，但内部协议中 arguments 必须保持 dict。

```
# 内部语义
ToolCall.arguments: dict

# OpenAI Chat Completions adapter
function.arguments: json.dumps(arguments)

# Anthropic adapter
input: arguments
```

### 2.3 不把 Event Sourcing 作为协议原则

本协议以 request / response 为核心。Streaming 可以作为 adapter 或 runtime extension 支持，但不作为核心协议设计原则。

### 2.4 不做 Workflow / DAG / Agent Orchestration 协议

本协议不是工作流引擎协议，不描述多 Agent DAG、任务编排、事件总线或长期任务调度。

## 3. LLM Model Message Protocol

Model Message Protocol 只描述模型侧语义：模型看到什么，以及模型输出什么。

### 3.1 ModelRequest

```python
ModelRequest = {
    "model": "deepseek-chat",
    "messages": list,              # list[ModelMessage]
    "tools": list,                 # list[ToolDefinition]
    "tool_choice": "auto",         # none | auto | required | dict
    "response_format": {"type": "text"},
    "options": {
        "temperature": 0.7,
        "top_p": 1.0,
        "max_tokens": 2048,
        "stream": False,
        "stop": None,
        "seed": None
    }
}
```

### 3.2 ModelMessage

```python
ModelMessage = {
    "role": "system" | "user" | "assistant" | "tool",
    "content": list,               # list[ContentPart]
    "name": None,

    # assistant only
    "tool_calls": None,            # list[ToolCall] | None

    # tool only
    "tool_call_id": None
}
```

| role | 允许字段 | 说明 |
| --- | --- | --- |
| `system` | `content`, `name` | 系统指令。 |
| `user` | `content`, `name` | 用户输入。 |
| `assistant` | `content`, `tool_calls`, `name` | 模型回复或模型发起工具调用。 |
| `tool` | `content`, `tool_call_id`, `name` | 工具执行结果。 |

> **注意：** **注意：**`tool_call_id` 只出现在 `role="tool"` 的消息中。assistant 发起调用时使用 `tool_calls[].id`，tool 返回结果时使用 `tool_call_id` 引用该 id。

### 3.3 ContentPart

所有消息内容统一使用 `content: list[ContentPart]`，即使只有纯文本也必须使用 list。

`text``image``audio``file``json``tool_result``reasoning`

```python
# Text
{"type": "text", "text": "你好，请帮我分析这份文件。"}

# Image
{
    "type": "image",
    "source": {"type": "url", "url": "https://example.com/image.png"},
    "metadata": {"detail": "auto"}
}

# File
{
    "type": "file",
    "source": {"type": "file_id", "file_id": "file_001"},
    "metadata": {"filename": "report.pdf", "mime_type": "application/pdf"}
}

# JSON
{"type": "json", "data": {"order_id": "o_123", "amount": 99.9}}

# Tool Result
{"type": "tool_result", "ok": True, "data": {"city": "北京", "temperature": 25}}

# Reasoning
{"type": "reasoning", "text": "模型内部推理内容"}
```

> **提示：** `reasoning` 是模型语义的一部分，但是否暴露给最终用户由 Runtime 或 Adapter 决定。

### 3.4 Source

```python
{"type": "url", "url": str}
{"type": "base64", "mime_type": str, "data": str}
{"type": "file_id", "file_id": str}
{"type": "path", "path": str}
```

- `base64` 必须带 `mime_type`。
- 大文件不建议内联，推荐使用 `file_id` 或 `url`。
- `file_id` 的有效期和访问范围由 Runtime 或 Adapter 定义。
- `path` 只用于内部 Runtime，不建议直接透传给 provider。

### 3.5 ToolDefinition

```python
ToolDefinition = {
    "name": "get_weather",
    "description": "获取指定城市的实时天气。",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        },
        "required": ["city"]
    }
}
```

### 3.6 ToolCall

```python
ToolCall = {
    "id": "call_001",
    "type": "function",
    "name": "get_weather",
    "arguments": {"city": "北京"}
}
```

- 表示一次逻辑 tool invocation。
- 可以来自 provider/model。
- Runtime 可以补齐或重写。
- Runtime 必须保证在一次 request/response lifecycle 内唯一。
- retry 不应改变该 id。
- tool message 使用 `tool_call_id` 引用该 id。

> **结论：** 内部协议中 `ToolCall.arguments` 永远使用 `dict`。映射到 OpenAI Chat Completions 时，再由 adapter 转为 JSON string。

### 3.7 ResponseFormat

```python
{"type": "text"}

{"type": "json_object"}

{
    "type": "json_schema",
    "json_schema": {
        "name": "weather_answer",
        "schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "temperature": {"type": "number"}
            },
            "required": ["city", "temperature"],
            "additionalProperties": False
        },
        "strict": True
    },
    "on_validation_error": "retry"  # retry | repair | error | ignore
}
```

### 3.8 ModelResponse

```python
ModelResponse = {
    "model": "deepseek-chat",
    "message": ModelMessage
}
```

ModelResponse 只保留模型输出的结构化语义，不包含 usage、trace、raw、provider_options、latency 等系统字段。

## 4. LLM Runtime Envelope Protocol

Runtime Envelope 包装一次模型调用，负责系统层语义。

### 4.1 RuntimeRequest

```python
RuntimeRequest = {
    "id": "req_001",
    "protocol_version": "llm-runtime-v1.0",
    "model_request": ModelRequest,
    "tool_execution": ToolExecutionPolicy,
    "trace": {
        "trace_id": "trace_001",
        "span_id": "span_001",
        "parent_span_id": None
    },
    "metadata": {
        "session_id": "session_001",
        "user_id": "user_001"
    },
    "provider_options": {
        "openai": {},
        "anthropic": {},
        "deepseek": {}
    }
}
```

### 4.2 RuntimeResponse

```python
RuntimeResponse = {
    "id": "resp_001",
    "request_id": "req_001",
    "protocol_version": "llm-runtime-v1.0",
    "model_response": ModelResponse,
    "finish_reason": "stop",
    "stop_reason": "stop_sequence",
    "usage": {
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150,
        "reasoning_tokens": 0,
        "cached_tokens": 0,
        "details": {}
    },
    "timing": {
        "started_at": "2026-05-13T12:00:00Z",
        "ended_at": "2026-05-13T12:00:02Z",
        "latency_ms": 2000
    },
    "error": None,
    "metadata": {},
    "provider_response_metadata": {},
    "raw": None
}
```

### 4.3 FinishReason

```
stop
length
tool_calls
content_filter
error
cancelled
timeout
provider_error
```

### 4.4 StopReason

```
eos_token
stop_sequence
user_interrupt
max_tokens
tool_use
safety_filter
provider_stop
```

> **提示：** `finish_reason` 表示最终终止类型，`stop_reason` 表示更具体的停止原因。

### 4.5 Runtime Error

```python
RuntimeErrorObject = {
    "code": "PROVIDER_TIMEOUT",
    "message": "Provider request timeout.",
    "type": "timeout",
    "retryable": True,
    "details": {}
}
```

### 4.6 Usage

```python
Usage = {
    "input_tokens": 100,
    "output_tokens": 50,
    "total_tokens": 150,
    "reasoning_tokens": 20,
    "cached_tokens": 10,
    "image_tokens": 0,
    "audio_tokens": 0,
    "tool_tokens": 0,
    "details": {}
}
```

### 4.7 Runtime 字段说明

| 字段 | 归属 | 说明 |
| --- | --- | --- |
| `metadata` | Runtime | 业务侧元信息，例如 session_id、user_id、业务 trace。 |
| `provider_options` | Runtime / Adapter | provider 私有参数，只允许 adapter 使用，业务层不应依赖。 |
| `provider_response_metadata` | Runtime | provider 返回的非核心元信息。 |
| `raw` | Runtime | provider 原始响应，可选，生产环境可关闭保存。 |

### 4.8 Null、时间与日志

- 字段缺失表示使用默认行为。
- `field = None` 表示显式为空。
- 所有时间字段统一使用 RFC3339 / ISO8601 UTC，例如 `2026-05-13T12:30:00Z`。
- 生产日志默认不建议记录 base64 原文、文件内容、API key、用户敏感信息和完整 raw provider payload。

## 5. Tool Execution Policy

Tool Execution Policy 是 Runtime Envelope 的子模块，不是独立顶层协议。

### 5.1 Policy Schema

```python
ToolExecutionPolicy = {
    "enabled": True,
    "parallel": True,
    "timeout_ms": 30000,
    "max_retries": 1,
    "retry_policy": {
        "backoff": "exponential",
        "initial_delay_ms": 200,
        "max_delay_ms": 2000
    },
    "approval_required_tools": [
        "send_email",
        "delete_file",
        "execute_shell"
    ],
    "default_approval_required": False
}
```

### 5.2 Tool Execution Record

```python
ToolExecutionRecord = {
    "tool_call_id": "call_001",
    "name": "get_weather",
    "status": "success",  # pending | running | success | error | cancelled | timeout | retrying
    "attempt": 1,
    "max_retries": 1,
    "started_at": "2026-05-13T12:00:00Z",
    "ended_at": "2026-05-13T12:00:01Z",
    "latency_ms": 1000,
    "error": None,
    "approval": {"required": False, "status": "not_required"}
}
```

### 5.3 Tool Error

```python
{
    "type": "tool_result",
    "ok": False,
    "error": {
        "code": "NETWORK_ERROR",
        "message": "请求超时",
        "retryable": True
    }
}
```

### 5.4 并发与审批

- assistant 可以一次返回多个 tool calls。
- Runtime 可以并发执行。
- 允许部分成功、部分失败。
- tool result 不要求按原顺序返回。
- 绑定关系只依赖 `assistant.tool_calls[].id` 与 `tool.tool_call_id`。
- 高风险工具必须支持用户审批，例如发邮件、删除文件、付款、执行 shell、修改生产数据。

## 6. Adapter Mapping Guide

Adapter Mapping Guide 不是核心协议，只描述内部协议与外部 provider 之间的映射。

### 6.1 OpenAI Chat Completions

| 内部字段 | OpenAI Chat Completions | 说明 |
| --- | --- | --- |
| `ModelMessage.role` | `messages[].role` | 直接映射。 |
| `ContentPart.text` | `content[].text` 或 string content | 由 adapter 选择兼容格式。 |
| `ToolDefinition` | `tools[].function` | parameters 直接映射为 JSON Schema。 |
| `ToolCall.arguments: dict` | `function.arguments: string` | adapter 执行 `json.dumps(arguments)`。 |
| `tool.tool_call_id` | `tool_call_id` | 直接映射。 |

### 6.2 Anthropic

| 内部字段 | Anthropic | 说明 |
| --- | --- | --- |
| `ToolCall.arguments` | `input` | Anthropic tool input 通常是 object，可直接映射。 |
| `tool_result` | `tool_result block` | 由 adapter 转换 content block。 |
| `reasoning` | `thinking / reasoning block` | 是否启用取决于 provider capability。 |

### 6.3 OpenAI-compatible Provider

DeepSeek、部分国产模型、部分本地模型可能声称 OpenAI-compatible，但实际行为可能存在差异：

- tool_call id 可能缺失或重复。
- arguments 可能不是合法 JSON string。
- finish_reason 枚举可能不同。
- usage 字段可能缺失。

> **注意：** Adapter 必须 normalize provider response，再进入内部协议。业务层不应直接消费 provider 原始结构。

### 6.4 Capability

```python
ModelCapability = {
    "text": True,
    "image": True,
    "audio": False,
    "file": True,
    "tools": True,
    "json_schema": True,
    "stream": True,
    "reasoning": False
}
```

## 7. 字段边界总结

| 字段 | 归属 | 是否进入 Model Protocol |
| --- | --- | --- |
| `role` | Model | 是 |
| `content` | Model | 是 |
| `tool_calls` | Model | 是 |
| `tool_call_id` | Model | 是，仅 tool message |
| `tools` | Model | 是 |
| `response_format` | Model | 是 |
| `temperature/top_p/max_tokens` | Model | 是 |
| `id/request_id/trace_id` | Runtime | 否 |
| `usage` | Runtime | 否 |
| `finish_reason/stop_reason` | Runtime Response | 否 |
| `error` | Runtime | 否 |
| `raw` | Runtime | 否 |
| `provider_options` | Runtime / Adapter | 否 |
| `approval/retry/timeout` | Tool Execution Policy | 否 |

## 8. 完整示例

### 8.1 RuntimeRequest

```python
request = {
    "id": "req_001",
    "protocol_version": "llm-runtime-v1.0",
    "model_request": {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": [{"type": "text", "text": "你是一个严谨、简洁的 AI 助手。"}]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": "北京天气怎么样？"}]
            }
        ],
        "tools": [
            {
                "name": "get_weather",
                "description": "获取指定城市的实时天气。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称"}
                    },
                    "required": ["city"]
                }
            }
        ],
        "tool_choice": "auto",
        "response_format": {"type": "text"},
        "options": {"temperature": 0.2, "top_p": 1.0, "max_tokens": 1024, "stream": False}
    },
    "tool_execution": {
        "enabled": True,
        "parallel": True,
        "timeout_ms": 30000,
        "max_retries": 1,
        "approval_required_tools": [],
        "default_approval_required": False
    },
    "trace": {"trace_id": "trace_001", "span_id": "span_001", "parent_span_id": None},
    "metadata": {"session_id": "session_001"},
    "provider_options": {}
}
```

### 8.2 Assistant Tool Call

```python
assistant_message = {
    "role": "assistant",
    "content": [],
    "tool_calls": [
        {
            "id": "call_001",
            "type": "function",
            "name": "get_weather",
            "arguments": {"city": "北京"}
        }
    ]
}
```

### 8.3 Tool Result Message

```python
tool_message = {
    "role": "tool",
    "tool_call_id": "call_001",
    "name": "get_weather",
    "content": [
        {
            "type": "tool_result",
            "ok": True,
            "data": {"city": "北京", "temperature": 25, "condition": "晴"}
        }
    ]
}
```

### 8.4 RuntimeResponse

```python
response = {
    "id": "resp_001",
    "request_id": "req_001",
    "protocol_version": "llm-runtime-v1.0",
    "model_response": {
        "model": "deepseek-chat",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": "北京当前天气晴，气温约 25℃。"}],
            "tool_calls": None,
            "tool_call_id": None,
            "name": None
        }
    },
    "finish_reason": "stop",
    "stop_reason": "eos_token",
    "usage": {
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150,
        "reasoning_tokens": 0,
        "cached_tokens": 0,
        "details": {}
    },
    "timing": {
        "started_at": "2026-05-13T12:00:00Z",
        "ended_at": "2026-05-13T12:00:02Z",
        "latency_ms": 2000
    },
    "error": None,
    "metadata": {},
    "provider_response_metadata": {},
    "raw": None
}
```

## 9. 版本与迁移

### 9.1 版本号

Runtime 协议版本与 Model 协议版本可以分开演进。

```
model_protocol_version: llm-model-v1.0
runtime_protocol_version: llm-runtime-v1.0
```

### 9.2 Breaking Change

- 删除字段
- 字段改名
- 字段类型变化
- 枚举值删除
- 字段语义变化

### 9.3 Non-breaking Change

- 新增可选字段
- 新增 provider_options 子字段
- usage.details 增加新 key
- 新增可忽略的 metadata 字段

### 9.4 v1 迁移建议

| 旧字段 | 新位置 |
| --- | --- |
| `messages` | `runtime_request.model_request.messages` |
| `tools` | `runtime_request.model_request.tools` |
| `response_format` | `runtime_request.model_request.response_format` |
| `metadata` | `runtime_request.metadata` |
| `provider_options` | `runtime_request.provider_options` |
| `usage` | `runtime_response.usage` |
| `raw` | `runtime_response.raw` |

## 10. 测试矩阵

| 场景 | 必须覆盖 |
| --- | --- |
| 纯文本对话 | system/user/assistant text content |
| 图片输入 | image url / image base64 / mime_type |
| 文件输入 | file_id / url / filename / mime_type |
| 单 tool call | assistant.tool_calls[].id 与 tool.tool_call_id 绑定 |
| 多 tool call | 并发、乱序返回、部分失败 |
| tool error | ok=false / error.code / retryable |
| JSON Schema 输出 | strict / validation failure / retry policy |
| length stop | finish_reason=length / stop_reason=max_tokens |
| safety/content filter | finish_reason=content_filter |
| provider error | RuntimeResponse.error / retryable |
| OpenAI adapter | arguments dict ↔ JSON string |
| OpenAI-compatible 异常 | 缺失 tool id、重复 tool id、非法 JSON arguments |

## 11. 最终结论

> **结论：** 推荐采用：两个正式协议，一个 Runtime 子模块，一个实现指南。

```
LLM Protocol Suite
├── LLM Model Message Protocol
│   └── 小核心，描述模型输入输出
├── LLM Runtime Envelope Protocol
│   └── 外围包装，描述系统运行语义
│       └── Tool Execution Policy
│           └── 工具执行策略，不独立成顶层协议
└── Adapter Mapping Guide
    └── 映射指南，不污染核心协议
```

这套结构的核心优势：

- Model Protocol 稳定，不被系统字段污染。
- Runtime Envelope 可演进，适合 trace、usage、error、raw、provider 差异。
- Tool Execution 不过度抽象，避免滑向 workflow engine。
- Adapter Guide 独立，防止 OpenAI / Anthropic / DeepSeek 等 provider 细节污染核心协议。
