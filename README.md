# LLM Protocol Suite

LLM Protocol Suite solves the data-definition drift that appears when different agent projects each invent their own message, tool-call, runtime, usage, and provider-response shapes.

It provides a small, explicit protocol layer for agent systems: Pydantic v2 models for model messages, multimodal content parts, tool calls, runtime envelopes, tool execution policy, usage, errors, and provider adapters. The goal is to let internal agent projects exchange structured LLM data without depending directly on any one provider SDK or framework's private format.

This package is not an agent framework. It does not call model APIs, execute tools, manage retries, request approvals, or orchestrate workflows. It defines and validates the shared data language those systems can build on.

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
