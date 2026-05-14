# Tool Calls

Use `ToolCall` to represent a model-requested function invocation.

Rules:
- `ToolCall.arguments` is always a dict.
- Do not store provider JSON strings in `arguments`.
- OpenAI adapters serialize `arguments` to JSON strings when needed.
- Put `tool_calls` only on assistant messages.
- Return tool output with a tool-role `ModelMessage` using matching `tool_call_id`.

Example:

```python
from llm_protocol_suite import ModelMessage, ToolCall, ToolResultPart

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

tool_message = ModelMessage(
    role="tool",
    tool_call_id="call_1",
    content=[
        ToolResultPart(ok=True, data={"temperature": 25}),
    ],
)
```
