# OpenAI Adapter

Use `to_openai_chat_request` and `from_openai_chat_response` for dict-level
mapping. This package does not call the OpenAI API.

Rules:
- Internal `ToolCall.arguments` is a dict.
- OpenAI Chat tool arguments are JSON strings.
- The adapter handles this conversion in both directions.
- `from_openai_chat_response` returns `ModelResponse`, not `RuntimeResponse`.

Example:

```python
from llm_protocol_suite import ModelMessage, ModelRequest, TextPart
from llm_protocol_suite.adapters.openai import (
    from_openai_chat_response,
    to_openai_chat_request,
)

request = ModelRequest(
    model="gpt-4.1-mini",
    messages=[ModelMessage(role="user", content=[TextPart(text="Hello")])],
)

payload = to_openai_chat_request(request)
model_response = from_openai_chat_response(openai_response_dict)
```
