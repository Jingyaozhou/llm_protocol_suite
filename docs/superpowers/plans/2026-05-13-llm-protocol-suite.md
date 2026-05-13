# LLM Protocol Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pip-installable `llm-protocol-suite` Python package that defines, validates, serializes, and maps the v0.1 LLM protocol data structures.

**Architecture:** Use a `src/` Python package with Pydantic v2 models split by protocol boundary: model-facing data in `model.py`, runtime envelopes in `runtime.py`, tool execution policy records in `tools.py`, and provider dict mapping in `adapters/openai.py`. Keep provider SDKs out of v0.1; adapters accept and return plain dictionaries.

**Tech Stack:** Python 3.10+, Pydantic v2, pytest, hatchling build backend.

---

## File Structure

- Create `pyproject.toml`: package metadata, build backend, runtime dependency on Pydantic v2, pytest dev dependency.
- Create `README.md`: minimal install and usage examples.
- Create `src/llm_protocol_suite/__init__.py`: public exports.
- Create `src/llm_protocol_suite/enums.py`: string enums for roles, content types, finish reasons, stop reasons, tool states, approval states.
- Create `src/llm_protocol_suite/exceptions.py`: package-specific adapter normalization errors.
- Create `src/llm_protocol_suite/model.py`: model protocol Pydantic models and validators.
- Create `src/llm_protocol_suite/runtime.py`: runtime envelope Pydantic models.
- Create `src/llm_protocol_suite/tools.py`: tool execution policy and record Pydantic models.
- Create `src/llm_protocol_suite/schema.py`: grouped JSON Schema export helpers.
- Create `src/llm_protocol_suite/adapters/__init__.py`: adapter namespace.
- Create `src/llm_protocol_suite/adapters/openai.py`: OpenAI Chat Completions dict-level mapping.
- Create `tests/test_model.py`: model layer validation tests.
- Create `tests/test_runtime.py`: runtime envelope tests.
- Create `tests/test_tools.py`: tool policy and record tests.
- Create `tests/test_openai_adapter.py`: OpenAI mapping and normalization tests.
- Create `tests/test_schema.py`: grouped schema export tests.

---

### Task 1: Package Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/llm_protocol_suite/__init__.py`
- Create: `src/llm_protocol_suite/enums.py`
- Create: `src/llm_protocol_suite/exceptions.py`
- Create: `tests/test_imports.py`

- [ ] **Step 1: Write the failing import test**

Create `tests/test_imports.py`:

```python
def test_public_imports():
    import llm_protocol_suite

    assert llm_protocol_suite.__version__ == "0.1.0"
```

- [ ] **Step 2: Run the import test to verify it fails**

Run:

```bash
pytest tests/test_imports.py -v
```

Expected: FAIL because `llm_protocol_suite` does not exist.

- [ ] **Step 3: Create package metadata**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "llm-protocol-suite"
version = "0.1.0"
description = "Pydantic data models and adapters for the LLM Protocol Suite."
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "pydantic>=2.7,<3",
]

[project.optional-dependencies]
dev = [
  "pytest>=8,<9",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 4: Create base package files**

Create `src/llm_protocol_suite/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/llm_protocol_suite/enums.py`:

```python
from enum import Enum


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    FILE = "file"
    JSON = "json"
    TOOL_RESULT = "tool_result"
    REASONING = "reasoning"


class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"


class StopReason(str, Enum):
    EOS_TOKEN = "eos_token"
    STOP_SEQUENCE = "stop_sequence"
    USER_INTERRUPT = "user_interrupt"
    MAX_TOKENS = "max_tokens"
    TOOL_USE = "tool_use"
    SAFETY_FILTER = "safety_filter"
    PROVIDER_STOP = "provider_stop"
```

Create `src/llm_protocol_suite/exceptions.py`:

```python
class LLMProtocolSuiteError(Exception):
    """Base exception for llm-protocol-suite."""


class AdapterNormalizationError(LLMProtocolSuiteError):
    """Raised when provider data cannot be normalized into the internal protocol."""
```

- [ ] **Step 5: Run import test**

Run:

```bash
pytest tests/test_imports.py -v
```

Expected: PASS.

---

### Task 2: Model Protocol

**Files:**
- Create: `src/llm_protocol_suite/model.py`
- Modify: `src/llm_protocol_suite/__init__.py`
- Create: `tests/test_model.py`

- [ ] **Step 1: Write failing model tests**

Create `tests/test_model.py`:

```python
import pytest
from pydantic import ValidationError

from llm_protocol_suite import (
    Base64Source,
    ModelMessage,
    ModelRequest,
    TextPart,
    ToolCall,
    ToolDefinition,
)


def test_text_message_requires_content_list():
    message = ModelMessage(role="user", content=[TextPart(text="hello")])

    assert message.model_dump()["content"][0]["type"] == "text"


def test_tool_call_arguments_must_be_dict():
    with pytest.raises(ValidationError):
        ToolCall(id="call_1", name="get_weather", arguments='{"city": "Beijing"}')


def test_tool_call_id_only_allowed_on_tool_messages():
    with pytest.raises(ValidationError):
        ModelMessage(role="assistant", content=[], tool_call_id="call_1")


def test_tool_calls_only_allowed_on_assistant_messages():
    with pytest.raises(ValidationError):
        ModelMessage(
            role="user",
            content=[],
            tool_calls=[ToolCall(id="call_1", name="get_weather", arguments={})],
        )


def test_base64_source_requires_mime_type():
    with pytest.raises(ValidationError):
        Base64Source(data="abc")


def test_model_request_round_trip():
    request = ModelRequest(
        model="deepseek-chat",
        messages=[ModelMessage(role="user", content=[TextPart(text="hi")])],
        tools=[
            ToolDefinition(
                name="get_weather",
                description="Get weather.",
                parameters={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            )
        ],
        tool_choice="auto",
    )

    restored = ModelRequest.model_validate(request.model_dump())

    assert restored.model == "deepseek-chat"
    assert restored.messages[0].content[0].text == "hi"
```

- [ ] **Step 2: Run model tests to verify they fail**

Run:

```bash
pytest tests/test_model.py -v
```

Expected: FAIL because model classes are not implemented.

- [ ] **Step 3: Implement model protocol**

Create `src/llm_protocol_suite/model.py`:

```python
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import Role


JsonDict = dict[str, Any]


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class UrlSource(ProtocolModel):
    type: Literal["url"] = "url"
    url: str


class Base64Source(ProtocolModel):
    type: Literal["base64"] = "base64"
    mime_type: str
    data: str


class FileIdSource(ProtocolModel):
    type: Literal["file_id"] = "file_id"
    file_id: str


class PathSource(ProtocolModel):
    type: Literal["path"] = "path"
    path: str


Source = UrlSource | Base64Source | FileIdSource | PathSource


class TextPart(ProtocolModel):
    type: Literal["text"] = "text"
    text: str


class ImagePart(ProtocolModel):
    type: Literal["image"] = "image"
    source: Source
    metadata: JsonDict = Field(default_factory=dict)


class AudioPart(ProtocolModel):
    type: Literal["audio"] = "audio"
    source: Source
    metadata: JsonDict = Field(default_factory=dict)


class FilePart(ProtocolModel):
    type: Literal["file"] = "file"
    source: Source
    metadata: JsonDict = Field(default_factory=dict)


class JsonPart(ProtocolModel):
    type: Literal["json"] = "json"
    data: Any


class ToolResultError(ProtocolModel):
    code: str
    message: str
    retryable: bool = False
    details: JsonDict = Field(default_factory=dict)


class ToolResultPart(ProtocolModel):
    type: Literal["tool_result"] = "tool_result"
    ok: bool
    data: Any | None = None
    error: ToolResultError | None = None

    @model_validator(mode="after")
    def validate_result_shape(self) -> "ToolResultPart":
        if self.ok and self.error is not None:
            raise ValueError("successful tool_result cannot include error")
        if not self.ok and self.error is None:
            raise ValueError("failed tool_result must include error")
        return self


class ReasoningPart(ProtocolModel):
    type: Literal["reasoning"] = "reasoning"
    text: str


ContentPart = (
    TextPart
    | ImagePart
    | AudioPart
    | FilePart
    | JsonPart
    | ToolResultPart
    | ReasoningPart
)


class ToolDefinition(ProtocolModel):
    name: str
    description: str
    parameters: JsonDict


class ToolCall(ProtocolModel):
    id: str
    type: Literal["function"] = "function"
    name: str
    arguments: JsonDict = Field(default_factory=dict)


class TextResponseFormat(ProtocolModel):
    type: Literal["text"] = "text"


class JsonObjectResponseFormat(ProtocolModel):
    type: Literal["json_object"] = "json_object"


class JsonSchemaDefinition(ProtocolModel):
    name: str
    schema: JsonDict
    strict: bool = False


class JsonSchemaResponseFormat(ProtocolModel):
    type: Literal["json_schema"] = "json_schema"
    json_schema: JsonSchemaDefinition
    on_validation_error: Literal["retry", "repair", "error", "ignore"] = "error"


ResponseFormat = TextResponseFormat | JsonObjectResponseFormat | JsonSchemaResponseFormat


class ModelOptions(ProtocolModel):
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    seed: int | None = None


class ModelMessage(ProtocolModel):
    role: Role
    content: list[ContentPart] = Field(default_factory=list)
    name: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None

    @model_validator(mode="after")
    def validate_role_fields(self) -> "ModelMessage":
        role = str(self.role)
        if self.tool_call_id is not None and role != Role.TOOL:
            raise ValueError("tool_call_id is only valid for tool messages")
        if self.tool_calls is not None and role != Role.ASSISTANT:
            raise ValueError("tool_calls is only valid for assistant messages")
        if role == Role.TOOL and self.tool_call_id is None:
            raise ValueError("tool messages require tool_call_id")
        return self


class ModelRequest(ProtocolModel):
    model: str
    messages: list[ModelMessage]
    tools: list[ToolDefinition] = Field(default_factory=list)
    tool_choice: Literal["none", "auto", "required"] | JsonDict | None = "auto"
    response_format: ResponseFormat = Field(default_factory=TextResponseFormat)
    options: ModelOptions = Field(default_factory=ModelOptions)


class ModelResponse(ProtocolModel):
    model: str
    message: ModelMessage
```

- [ ] **Step 4: Export model protocol**

Modify `src/llm_protocol_suite/__init__.py`:

```python
from .model import (
    AudioPart,
    Base64Source,
    FileIdSource,
    FilePart,
    ImagePart,
    JsonObjectResponseFormat,
    JsonPart,
    JsonSchemaDefinition,
    JsonSchemaResponseFormat,
    ModelMessage,
    ModelOptions,
    ModelRequest,
    ModelResponse,
    PathSource,
    ReasoningPart,
    TextPart,
    TextResponseFormat,
    ToolCall,
    ToolDefinition,
    ToolResultError,
    ToolResultPart,
    UrlSource,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "AudioPart",
    "Base64Source",
    "FileIdSource",
    "FilePart",
    "ImagePart",
    "JsonObjectResponseFormat",
    "JsonPart",
    "JsonSchemaDefinition",
    "JsonSchemaResponseFormat",
    "ModelMessage",
    "ModelOptions",
    "ModelRequest",
    "ModelResponse",
    "PathSource",
    "ReasoningPart",
    "TextPart",
    "TextResponseFormat",
    "ToolCall",
    "ToolDefinition",
    "ToolResultError",
    "ToolResultPart",
    "UrlSource",
]
```

- [ ] **Step 5: Run model tests**

Run:

```bash
pytest tests/test_model.py tests/test_imports.py -v
```

Expected: PASS.

---

### Task 3: Runtime And Tool Policy Models

**Files:**
- Create: `src/llm_protocol_suite/runtime.py`
- Create: `src/llm_protocol_suite/tools.py`
- Modify: `src/llm_protocol_suite/__init__.py`
- Create: `tests/test_runtime.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write failing runtime and tool tests**

Create `tests/test_tools.py`:

```python
from llm_protocol_suite import RetryPolicy, ToolApproval, ToolExecutionPolicy, ToolExecutionRecord


def test_tool_execution_policy_defaults():
    policy = ToolExecutionPolicy()

    assert policy.enabled is True
    assert policy.parallel is True
    assert policy.timeout_ms == 30000
    assert policy.max_retries == 1


def test_tool_execution_record_round_trip():
    record = ToolExecutionRecord(
        tool_call_id="call_1",
        name="get_weather",
        status="success",
        attempt=1,
        max_retries=1,
        approval=ToolApproval(required=False, status="not_required"),
    )

    restored = ToolExecutionRecord.model_validate(record.model_dump())

    assert restored.tool_call_id == "call_1"
```

Create `tests/test_runtime.py`:

```python
from llm_protocol_suite import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RuntimeErrorObject,
    RuntimeRequest,
    RuntimeResponse,
    TextPart,
    ToolExecutionPolicy,
    Usage,
)


def test_runtime_request_wraps_model_request():
    request = RuntimeRequest(
        id="req_1",
        model_request=ModelRequest(
            model="deepseek-chat",
            messages=[ModelMessage(role="user", content=[TextPart(text="hi")])],
        ),
        tool_execution=ToolExecutionPolicy(enabled=False),
    )

    assert request.protocol_version == "llm-runtime-v1.0"
    assert request.model_request.messages[0].content[0].text == "hi"


def test_runtime_response_allows_provider_error():
    response = RuntimeResponse(
        id="resp_1",
        request_id="req_1",
        model_response=ModelResponse(
            model="deepseek-chat",
            message=ModelMessage(role="assistant", content=[]),
        ),
        finish_reason="provider_error",
        stop_reason="provider_stop",
        usage=Usage(input_tokens=0, output_tokens=0, total_tokens=0),
        error=RuntimeErrorObject(
            code="PROVIDER_TIMEOUT",
            message="Provider request timeout.",
            type="timeout",
            retryable=True,
        ),
    )

    assert response.error.retryable is True
```

- [ ] **Step 2: Run runtime and tool tests to verify they fail**

Run:

```bash
pytest tests/test_runtime.py tests/test_tools.py -v
```

Expected: FAIL because runtime and tool classes are not implemented.

- [ ] **Step 3: Implement tool models**

Create `src/llm_protocol_suite/tools.py`:

```python
from typing import Any, Literal

from pydantic import Field

from .model import ProtocolModel


JsonDict = dict[str, Any]


class RetryPolicy(ProtocolModel):
    backoff: Literal["none", "fixed", "exponential"] = "exponential"
    initial_delay_ms: int = 200
    max_delay_ms: int = 2000


class ToolExecutionPolicy(ProtocolModel):
    enabled: bool = True
    parallel: bool = True
    timeout_ms: int = 30000
    max_retries: int = 1
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    approval_required_tools: list[str] = Field(default_factory=list)
    default_approval_required: bool = False


class ToolApproval(ProtocolModel):
    required: bool
    status: Literal["not_required", "pending", "approved", "rejected", "expired"]


class ToolExecutionRecord(ProtocolModel):
    tool_call_id: str
    name: str
    status: Literal["pending", "running", "success", "error", "cancelled", "timeout", "retrying"]
    attempt: int
    max_retries: int
    started_at: str | None = None
    ended_at: str | None = None
    latency_ms: int | None = None
    error: JsonDict | None = None
    approval: ToolApproval | None = None
```

- [ ] **Step 4: Implement runtime models**

Create `src/llm_protocol_suite/runtime.py`:

```python
from typing import Any

from pydantic import Field

from .enums import FinishReason, StopReason
from .model import ModelRequest, ModelResponse, ProtocolModel
from .tools import ToolExecutionPolicy


JsonDict = dict[str, Any]


class Trace(ProtocolModel):
    trace_id: str
    span_id: str
    parent_span_id: str | None = None


class Usage(ProtocolModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    image_tokens: int = 0
    audio_tokens: int = 0
    tool_tokens: int = 0
    details: JsonDict = Field(default_factory=dict)


class Timing(ProtocolModel):
    started_at: str | None = None
    ended_at: str | None = None
    latency_ms: int | None = None


class RuntimeErrorObject(ProtocolModel):
    code: str
    message: str
    type: str
    retryable: bool = False
    details: JsonDict = Field(default_factory=dict)


class RuntimeRequest(ProtocolModel):
    id: str
    protocol_version: str = "llm-runtime-v1.0"
    model_request: ModelRequest
    tool_execution: ToolExecutionPolicy = Field(default_factory=ToolExecutionPolicy)
    trace: Trace | None = None
    metadata: JsonDict = Field(default_factory=dict)
    provider_options: JsonDict = Field(default_factory=dict)


class RuntimeResponse(ProtocolModel):
    id: str
    request_id: str
    protocol_version: str = "llm-runtime-v1.0"
    model_response: ModelResponse
    finish_reason: FinishReason | str
    stop_reason: StopReason | str | None = None
    usage: Usage | None = None
    timing: Timing | None = None
    error: RuntimeErrorObject | None = None
    metadata: JsonDict = Field(default_factory=dict)
    provider_response_metadata: JsonDict = Field(default_factory=dict)
    raw: Any | None = None
```

- [ ] **Step 5: Export runtime and tool models**

Append imports and names in `src/llm_protocol_suite/__init__.py`:

```python
from .runtime import RuntimeErrorObject, RuntimeRequest, RuntimeResponse, Timing, Trace, Usage
from .tools import RetryPolicy, ToolApproval, ToolExecutionPolicy, ToolExecutionRecord
```

Add these strings to `__all__`:

```python
"RetryPolicy",
"RuntimeErrorObject",
"RuntimeRequest",
"RuntimeResponse",
"Timing",
"ToolApproval",
"ToolExecutionPolicy",
"ToolExecutionRecord",
"Trace",
"Usage",
```

- [ ] **Step 6: Run runtime and tool tests**

Run:

```bash
pytest tests/test_runtime.py tests/test_tools.py tests/test_model.py -v
```

Expected: PASS.

---

### Task 4: OpenAI Chat Completions Adapter

**Files:**
- Create: `src/llm_protocol_suite/adapters/__init__.py`
- Create: `src/llm_protocol_suite/adapters/openai.py`
- Create: `tests/test_openai_adapter.py`

- [ ] **Step 1: Write failing OpenAI adapter tests**

Create `tests/test_openai_adapter.py`:

```python
import json

import pytest

from llm_protocol_suite import ModelMessage, ModelRequest, TextPart, ToolCall, ToolDefinition
from llm_protocol_suite.adapters.openai import from_openai_chat_response, to_openai_chat_request
from llm_protocol_suite.exceptions import AdapterNormalizationError


def test_to_openai_chat_request_serializes_tool_arguments():
    request = ModelRequest(
        model="gpt-4.1-mini",
        messages=[
            ModelMessage(role="user", content=[TextPart(text="weather?")]),
            ModelMessage(
                role="assistant",
                content=[],
                tool_calls=[ToolCall(id="call_1", name="get_weather", arguments={"city": "Beijing"})],
            ),
        ],
        tools=[
            ToolDefinition(
                name="get_weather",
                description="Get weather.",
                parameters={"type": "object", "properties": {"city": {"type": "string"}}},
            )
        ],
    )

    payload = to_openai_chat_request(request)

    assert payload["model"] == "gpt-4.1-mini"
    assert payload["messages"][0]["content"][0]["text"] == "weather?"
    arguments = payload["messages"][1]["tool_calls"][0]["function"]["arguments"]
    assert json.loads(arguments) == {"city": "Beijing"}


def test_from_openai_chat_response_normalizes_tool_arguments():
    response = {
        "model": "gpt-4.1-mini",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city": "Beijing"}',
                            },
                        }
                    ],
                }
            }
        ],
    }

    normalized = from_openai_chat_response(response)

    assert normalized.message.tool_calls[0].arguments == {"city": "Beijing"}


def test_from_openai_chat_response_rejects_duplicate_tool_ids():
    response = {
        "model": "gpt-4.1-mini",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_1", "function": {"name": "a", "arguments": "{}"}},
                        {"id": "call_1", "function": {"name": "b", "arguments": "{}"}},
                    ],
                }
            }
        ],
    }

    with pytest.raises(AdapterNormalizationError):
        from_openai_chat_response(response)


def test_from_openai_chat_response_rejects_invalid_arguments_json():
    response = {
        "model": "gpt-4.1-mini",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_1", "function": {"name": "a", "arguments": "not-json"}}
                    ],
                }
            }
        ],
    }

    with pytest.raises(AdapterNormalizationError):
        from_openai_chat_response(response)
```

- [ ] **Step 2: Run adapter tests to verify they fail**

Run:

```bash
pytest tests/test_openai_adapter.py -v
```

Expected: FAIL because adapter functions are not implemented.

- [ ] **Step 3: Implement adapter namespace**

Create `src/llm_protocol_suite/adapters/__init__.py`:

```python
"""Provider adapter namespace."""
```

- [ ] **Step 4: Implement OpenAI adapter**

Create `src/llm_protocol_suite/adapters/openai.py`:

```python
import json
from typing import Any

from llm_protocol_suite.exceptions import AdapterNormalizationError
from llm_protocol_suite.model import (
    FilePart,
    ImagePart,
    JsonPart,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ReasoningPart,
    TextPart,
    ToolCall,
    ToolDefinition,
    ToolResultPart,
)
from llm_protocol_suite.runtime import RuntimeRequest


def to_openai_chat_request(request: ModelRequest | RuntimeRequest) -> dict[str, Any]:
    model_request = request.model_request if isinstance(request, RuntimeRequest) else request
    payload: dict[str, Any] = {
        "model": model_request.model,
        "messages": [_message_to_openai(message) for message in model_request.messages],
    }
    if model_request.tools:
        payload["tools"] = [_tool_to_openai(tool) for tool in model_request.tools]
    if model_request.tool_choice is not None:
        payload["tool_choice"] = model_request.tool_choice
    payload.update(model_request.options.model_dump(exclude_none=True))
    return payload


def from_openai_chat_response(response: dict[str, Any]) -> ModelResponse:
    try:
        choice = response["choices"][0]
        message_data = choice["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AdapterNormalizationError("OpenAI response is missing choices[0].message") from exc

    tool_calls = _normalize_tool_calls(message_data.get("tool_calls") or [])
    content = _normalize_content(message_data.get("content"))
    message = ModelMessage(
        role=message_data.get("role", "assistant"),
        content=content,
        tool_calls=tool_calls or None,
        name=message_data.get("name"),
    )
    return ModelResponse(model=response.get("model", ""), message=message)


def _message_to_openai(message: ModelMessage) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "role": str(message.role),
        "content": [_content_part_to_openai(part) for part in message.content],
    }
    if message.name is not None:
        payload["name"] = message.name
    if message.tool_calls is not None:
        payload["tool_calls"] = [_tool_call_to_openai(call) for call in message.tool_calls]
    if message.tool_call_id is not None:
        payload["tool_call_id"] = message.tool_call_id
    return payload


def _content_part_to_openai(part: Any) -> dict[str, Any]:
    if isinstance(part, TextPart):
        return {"type": "text", "text": part.text}
    if isinstance(part, ImagePart):
        return {"type": "image_url", "image_url": _source_to_openai_image(part.source)}
    if isinstance(part, FilePart):
        return {"type": "file", "file": part.source.model_dump()}
    if isinstance(part, JsonPart):
        return {"type": "text", "text": json.dumps(part.data, ensure_ascii=False)}
    if isinstance(part, ToolResultPart):
        return {"type": "text", "text": json.dumps(part.model_dump(), ensure_ascii=False)}
    if isinstance(part, ReasoningPart):
        return {"type": "text", "text": part.text}
    return part.model_dump()


def _source_to_openai_image(source: Any) -> dict[str, str]:
    if source.type == "url":
        return {"url": source.url}
    if source.type == "base64":
        return {"url": f"data:{source.mime_type};base64,{source.data}"}
    raise AdapterNormalizationError("OpenAI image content requires url or base64 source")


def _tool_to_openai(tool: ToolDefinition) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def _tool_call_to_openai(call: ToolCall) -> dict[str, Any]:
    return {
        "id": call.id,
        "type": call.type,
        "function": {
            "name": call.name,
            "arguments": json.dumps(call.arguments, ensure_ascii=False),
        },
    }


def _normalize_content(content: Any) -> list[TextPart]:
    if content is None:
        return []
    if isinstance(content, str):
        return [TextPart(text=content)]
    if isinstance(content, list):
        parts: list[TextPart] = []
        for item in content:
            if item.get("type") == "text":
                parts.append(TextPart(text=item.get("text", "")))
        return parts
    raise AdapterNormalizationError("Unsupported OpenAI message content")


def _normalize_tool_calls(tool_calls: list[dict[str, Any]]) -> list[ToolCall]:
    normalized: list[ToolCall] = []
    seen_ids: set[str] = set()
    for index, raw_call in enumerate(tool_calls):
        call_id = raw_call.get("id") or f"llmps_call_{index}"
        if call_id in seen_ids:
            raise AdapterNormalizationError(f"Duplicate tool call id: {call_id}")
        seen_ids.add(call_id)

        function = raw_call.get("function") or {}
        arguments_text = function.get("arguments") or "{}"
        try:
            arguments = json.loads(arguments_text)
        except json.JSONDecodeError as exc:
            raise AdapterNormalizationError(f"Invalid JSON arguments for tool call {call_id}") from exc
        if not isinstance(arguments, dict):
            raise AdapterNormalizationError(f"Tool call {call_id} arguments must decode to an object")

        normalized.append(
            ToolCall(
                id=call_id,
                type=raw_call.get("type", "function"),
                name=function.get("name", ""),
                arguments=arguments,
            )
        )
    return normalized
```

- [ ] **Step 5: Run adapter tests**

Run:

```bash
pytest tests/test_openai_adapter.py tests/test_model.py -v
```

Expected: PASS.

---

### Task 5: Schema Helpers And README

**Files:**
- Create: `src/llm_protocol_suite/schema.py`
- Create: `tests/test_schema.py`
- Create: `README.md`

- [ ] **Step 1: Write failing schema test**

Create `tests/test_schema.py`:

```python
from llm_protocol_suite.schema import export_json_schemas


def test_export_json_schemas_contains_core_models():
    schemas = export_json_schemas()

    assert "ModelRequest" in schemas
    assert "RuntimeRequest" in schemas
    assert "ToolExecutionPolicy" in schemas
    assert schemas["ModelRequest"]["type"] == "object"
```

- [ ] **Step 2: Run schema test to verify it fails**

Run:

```bash
pytest tests/test_schema.py -v
```

Expected: FAIL because `schema.py` is not implemented.

- [ ] **Step 3: Implement schema helper**

Create `src/llm_protocol_suite/schema.py`:

```python
from typing import Any

from .model import ModelMessage, ModelRequest, ModelResponse, ToolCall, ToolDefinition
from .runtime import RuntimeRequest, RuntimeResponse
from .tools import ToolExecutionPolicy, ToolExecutionRecord


def export_json_schemas() -> dict[str, dict[str, Any]]:
    models = [
        ModelMessage,
        ModelRequest,
        ModelResponse,
        ToolCall,
        ToolDefinition,
        RuntimeRequest,
        RuntimeResponse,
        ToolExecutionPolicy,
        ToolExecutionRecord,
    ]
    return {model.__name__: model.model_json_schema() for model in models}
```

- [ ] **Step 4: Add README**

Create `README.md`:

````markdown
# LLM Protocol Suite

Pydantic v2 data models and dict-level adapters for the LLM Protocol Suite.

## Install

```bash
pip install -e ".[dev]"
```

## Example

```python
from llm_protocol_suite import ModelMessage, ModelRequest, TextPart

request = ModelRequest(
    model="deepseek-chat",
    messages=[
        ModelMessage(role="user", content=[TextPart(text="Hello")]),
    ],
)

print(request.model_dump())
```

## OpenAI Mapping

```python
from llm_protocol_suite import ModelMessage, ModelRequest, TextPart
from llm_protocol_suite.adapters.openai import to_openai_chat_request

request = ModelRequest(
    model="gpt-4.1-mini",
    messages=[ModelMessage(role="user", content=[TextPart(text="Hello")])],
)

payload = to_openai_chat_request(request)
```

## Non-goals

v0.1 does not call provider APIs, execute tools, run retries, manage approvals, or orchestrate agents.
````

- [ ] **Step 5: Run schema test**

Run:

```bash
pytest tests/test_schema.py -v
```

Expected: PASS.

---

### Task 6: Full Verification And Cleanup

**Files:**
- Modify only files already created in earlier tasks if tests expose mismatches.

- [ ] **Step 1: Run the full test suite**

Run:

```bash
pytest -v
```

Expected: all tests PASS.

- [ ] **Step 2: Verify editable install**

Run:

```bash
python -m pip install -e ".[dev]"
python -c "from llm_protocol_suite import ModelRequest; print(ModelRequest.__name__)"
```

Expected output includes:

```text
ModelRequest
```

- [ ] **Step 3: Build package metadata check**

Run:

```bash
python -m pip show llm-protocol-suite
```

Expected output includes:

```text
Name: llm-protocol-suite
Version: 0.1.0
```

- [ ] **Step 4: Final review**

Run:

```bash
python -m compileall src
```

Expected: command exits successfully.
