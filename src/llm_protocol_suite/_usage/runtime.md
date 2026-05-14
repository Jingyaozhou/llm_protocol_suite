# Runtime Envelope

Use `RuntimeRequest` and `RuntimeResponse` when application-level metadata is
needed around a model call.

Rules:
- Model-facing data stays inside `ModelRequest` and `ModelResponse`.
- Runtime ids, trace data, provider options, usage, timing, errors, and raw data
  stay in runtime envelope objects.
- `ToolExecutionPolicy` describes execution policy only; it does not execute tools.

Example:

```python
from llm_protocol_suite import RuntimeRequest, ToolExecutionPolicy

runtime_request = RuntimeRequest(
    id="req_1",
    model_request=model_request,
    tool_execution=ToolExecutionPolicy(parallel=True, timeout_ms=30000),
    metadata={"session_id": "session_1"},
)
```
