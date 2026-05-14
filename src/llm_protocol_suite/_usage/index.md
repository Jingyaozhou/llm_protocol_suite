# LLM Protocol Suite Usage For LLM Agents

Use this package as a provider-neutral data layer for LLM agent applications.
It defines shared Python objects for model messages, multimodal content, tool
calls, runtime envelopes, usage, errors, and provider adapters.

This package does not call provider APIs, execute tools, run retries, manage
approvals, or orchestrate agents.

## Core Classes

Model layer:
- `ModelRequest`: complete model request.
- `ModelResponse`: normalized model response.
- `ModelMessage`: one conversation message.
- `TextPart`: plain text content.
- `ImagePart`: image content with `UrlSource` or `Base64Source`.
- `FilePart`: file content with `FileIdSource`, `UrlSource`, or `PathSource`.
- `JsonPart`: structured JSON content.
- `ToolDefinition`: JSON Schema definition for a callable tool.
- `ToolCall`: model-requested function invocation.
- `ToolResultPart`: structured tool execution result.

Runtime layer:
- `RuntimeRequest`: wraps `ModelRequest` with id, trace, metadata, provider options, and tool policy.
- `RuntimeResponse`: wraps `ModelResponse` with finish reason, usage, timing, errors, and raw metadata.
- `Usage`: token accounting.
- `RuntimeErrorObject`: structured runtime error.
- `ToolExecutionPolicy`: data-only timeout, retry, parallel, and approval policy.

Adapters:
- `to_openai_chat_request`: convert internal request objects to OpenAI Chat-style dicts.
- `from_openai_chat_response`: normalize OpenAI Chat-style dicts to `ModelResponse`.

## Hard Rules

- `ModelMessage.content is always a list`, even for one text item.
- `ToolCall.arguments is always a dict`, never a JSON string.
- OpenAI adapters handle JSON string conversion for tool arguments.
- `tool_calls` only belongs on assistant messages.
- `tool_call_id` only belongs on tool messages.
- Runtime metadata does not belong in `ModelRequest`.
- Provider SDK objects should be normalized before entering app business logic.

## Common Construction Patterns

### 1. Text Message

```python
from llm_protocol_suite import ModelMessage, TextPart

message = ModelMessage(
    role="user",
    content=[TextPart(text="Hello")],
)
```

### 2. Text Model Request

```python
from llm_protocol_suite import ModelMessage, ModelRequest, TextPart

request = ModelRequest(
    model="deepseek-chat",
    messages=[
        ModelMessage(role="user", content=[TextPart(text="Hello")]),
    ],
)
```

### 3. Image Message

```python
from llm_protocol_suite import ImagePart, ModelMessage, TextPart, UrlSource

message = ModelMessage(
    role="user",
    content=[
        TextPart(text="Describe this image."),
        ImagePart(source=UrlSource(url="https://example.com/image.png")),
    ],
)
```

### 4. Tool Definition

```python
from llm_protocol_suite import ToolDefinition

tool = ToolDefinition(
    name="get_weather",
    description="Get current weather for a city.",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
)
```

### 5. Assistant Tool Call

```python
from llm_protocol_suite import ModelMessage, ToolCall

assistant_message = ModelMessage(
    role="assistant",
    content=[],
    tool_calls=[
        ToolCall(
            id="call_1",
            name="get_weather",
            arguments={"city": "Beijing"},
        )
    ],
)
```

### 6. Tool Result Message

```python
from llm_protocol_suite import ModelMessage, ToolResultPart

tool_message = ModelMessage(
    role="tool",
    tool_call_id="call_1",
    content=[
        ToolResultPart(ok=True, data={"city": "Beijing", "temperature": 25}),
    ],
)
```

### 7. Runtime Request

```python
from llm_protocol_suite import RuntimeRequest, ToolExecutionPolicy

runtime_request = RuntimeRequest(
    id="req_1",
    model_request=request,
    tool_execution=ToolExecutionPolicy(timeout_ms=30000, max_retries=1),
    metadata={"session_id": "session_1"},
)
```

### 8. Runtime Response With Usage

```python
from llm_protocol_suite import ModelMessage, ModelResponse, RuntimeResponse, TextPart, Usage

response = RuntimeResponse(
    id="resp_1",
    request_id="req_1",
    model_response=ModelResponse(
        model="deepseek-chat",
        message=ModelMessage(role="assistant", content=[TextPart(text="Hi!")]),
    ),
    finish_reason="stop",
    usage=Usage(input_tokens=10, output_tokens=5, total_tokens=15),
)
```

### 9. OpenAI Request Mapping

```python
from llm_protocol_suite.adapters.openai import to_openai_chat_request

payload = to_openai_chat_request(request)
```

### 10. OpenAI Response Mapping

```python
from llm_protocol_suite.adapters.openai import from_openai_chat_response

model_response = from_openai_chat_response(openai_response_dict)
```

## Topic Help

Use focused help when a task needs more detail:

```python
from llm_protocol_suite import help_for, list_topics

print(list_topics())
print(help_for("tool_call"))
print(help_for("openai_adapter"))
```

CLI:

```bash
python -m llm_protocol_suite usage
python -m llm_protocol_suite usage tool_call
python -m llm_protocol_suite topics
```
