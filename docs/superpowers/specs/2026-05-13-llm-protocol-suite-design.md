# LLM Protocol Suite v0.1 Design

## Goal

Build a pip-installable Python package named `llm-protocol-suite`, imported as `llm_protocol_suite`, that implements the data protocol described in `llm_protocol_suite_v1_0.md`.

The v0.1 release is for internal agent projects first, while keeping the project structure suitable for future public PyPI release.

## Scope

v0.1 focuses on protocol data definitions, validation, serialization, JSON Schema export, and OpenAI Chat Completions dict-level mapping.

The package does not call model providers, execute tools, manage retries, request approvals, run agent workflows, or implement streaming events.

## Package Shape

```text
llm-protocol-suite/
  pyproject.toml
  README.md
  src/
    llm_protocol_suite/
      __init__.py
      enums.py
      exceptions.py
      model.py
      runtime.py
      tools.py
      schema.py
      adapters/
        __init__.py
        openai.py
  tests/
    test_model.py
    test_runtime.py
    test_tools.py
    test_openai_adapter.py
```

## Dependencies

The package will require Pydantic v2. Pydantic is a core dependency because the package's main value is runtime validation, structured serialization, and JSON Schema generation.

Provider SDKs are intentionally not dependencies in v0.1. Adapters operate on plain Python dictionaries.

## Public API

The package should expose the main protocol objects from `llm_protocol_suite.__init__`:

```python
from llm_protocol_suite import (
    ModelRequest,
    ModelResponse,
    ModelMessage,
    TextPart,
    ImagePart,
    FilePart,
    JsonPart,
    ToolResultPart,
    ReasoningPart,
    ToolDefinition,
    ToolCall,
    RuntimeRequest,
    RuntimeResponse,
    ToolExecutionPolicy,
)
```

OpenAI mapping should be available under:

```python
from llm_protocol_suite.adapters.openai import (
    to_openai_chat_request,
    from_openai_chat_response,
)
```

## Data Model

### Model Layer

`model.py` owns the stable model-facing protocol:

- `ModelRequest`
- `ModelResponse`
- `ModelMessage`
- content part models
- source models
- `ToolDefinition`
- `ToolCall`
- response format models
- model options

`ModelMessage.content` is always a list of content parts, including pure text. Tool call arguments remain Python dictionaries inside the internal protocol.

### Runtime Layer

`runtime.py` owns system-level envelope data:

- `RuntimeRequest`
- `RuntimeResponse`
- `Trace`
- `Usage`
- `Timing`
- `RuntimeErrorObject`
- provider options and metadata fields

Runtime data wraps model data but must not leak into `ModelRequest` or `ModelResponse`.

### Tool Layer

`tools.py` owns runtime tool execution metadata:

- `ToolExecutionPolicy`
- `RetryPolicy`
- `ToolExecutionRecord`
- `ToolApproval`
- tool error payloads used in `ToolResultPart`

These models describe tool execution policy and records only. They do not execute tools.

## Validation Rules

The package should enforce the most important protocol invariants:

- `ModelMessage.role` is one of `system`, `user`, `assistant`, or `tool`.
- `tool_call_id` is valid only when `role="tool"`.
- `tool_calls` is valid only when `role="assistant"`.
- `ToolCall.arguments` must be a dictionary.
- `content` must be a list, even for single text messages.
- `base64` sources must include `mime_type`.
- `path` sources are allowed internally but adapters must not pass them directly to providers.
- `ResponseFormat` must match one of `text`, `json_object`, or `json_schema`.
- `RuntimeResponse.finish_reason` and `stop_reason` use known enum values.

Validation should catch structural errors early and raise package-specific exceptions when an adapter cannot normalize provider data.

## OpenAI Adapter

The OpenAI adapter maps between internal protocol objects and OpenAI Chat Completions-style dictionaries.

`to_openai_chat_request(request: ModelRequest | RuntimeRequest) -> dict` should:

- accept either a `ModelRequest` or a `RuntimeRequest`
- map messages to OpenAI-compatible message dictionaries
- map `ToolDefinition` to OpenAI `tools[].function`
- serialize `ToolCall.arguments` with JSON encoding for OpenAI
- map `tool_call_id` directly for tool messages
- omit runtime-only fields

`from_openai_chat_response(response: dict) -> ModelResponse` should normalize provider response data into internal model structures. v0.1 returns `ModelResponse` only; wrapping provider usage, timing, raw payloads, and request ids into `RuntimeResponse` is reserved for a later runtime helper.

OpenAI-compatible provider irregularities should be handled explicitly:

- missing tool call ids are generated with a stable package prefix
- duplicate tool call ids should raise a normalization error
- invalid JSON tool arguments should raise a normalization error
- usage fields are ignored by this model-layer adapter in v0.1

## Serialization And Schema

Every model should support standard Pydantic v2 serialization:

- `model_dump()`
- `model_dump_json()`
- `model_validate()`
- `model_json_schema()`

`schema.py` should provide helper functions for exporting grouped JSON Schemas for downstream projects.

## Testing

The initial test suite should cover the highest-value cases from the protocol document:

- pure text messages
- image URL and base64 sources
- file references
- single tool call and matching tool result
- multiple tool calls with unordered tool results
- tool error payload
- JSON Schema response format
- length stop and max token stop reason
- provider error response
- OpenAI request mapping
- OpenAI response mapping
- OpenAI-compatible invalid arguments and duplicate ids

Tests should focus on protocol behavior and adapter normalization, not provider SDK behavior.

## Non-goals For v0.1

v0.1 will not include:

- real OpenAI, Anthropic, DeepSeek, or Gemini API calls
- streaming event protocol
- LangChain or AutoGen integrations
- tool execution runtime
- retry loops
- approval UI or approval workflow
- long-running task orchestration
- memory, DAG, or multi-agent workflow features

## Success Criteria

The v0.1 implementation is successful when:

- a downstream project can install the package locally with pip
- core protocol objects can be imported from `llm_protocol_suite`
- invalid protocol data fails validation with clear errors
- internal tool call arguments remain dictionaries
- OpenAI mapping serializes tool arguments to JSON strings
- OpenAI response mapping normalizes tool arguments back to dictionaries
- the test suite covers the main protocol matrix and passes locally
