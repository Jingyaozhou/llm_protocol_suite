"""Runtime envelope models that wrap model requests/responses with execution context.

Includes tracing, usage/token accounting, timing, and error reporting.
"""

from typing import Any

from pydantic import Field

from .enums import FinishReason, StopReason
from .model import ModelRequest, ModelResponse, ProtocolModel
from .tools import ToolExecutionPolicy


JsonDict = dict[str, Any]


class Trace(ProtocolModel):
    """Distributed tracing context for correlating requests across services.

    Example::

        trace = Trace(trace_id="abc123", span_id="span-1")
        assert trace.parent_span_id is None
    """

    trace_id: str
    span_id: str
    parent_span_id: str | None = None


class Usage(ProtocolModel):
    """Token usage accounting for a model call.

    Example::

        usage = Usage(input_tokens=100, output_tokens=50, total_tokens=150)
        assert usage.cached_tokens == 0
    """

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
    """Timing information for a model call.

    Example::

        timing = Timing(started_at="2025-01-01T00:00:00Z", latency_ms=1200)
        assert timing.latency_ms == 1200
    """

    started_at: str | None = None
    ended_at: str | None = None
    latency_ms: int | None = None


class RuntimeErrorObject(ProtocolModel):
    """Structured error returned by the runtime layer.

    Example::

        err = RuntimeErrorObject(code="RATE_LIMIT", message="Too many requests", type="provider_error")
        assert err.retryable is False
    """

    code: str
    message: str
    type: str
    retryable: bool = False
    details: JsonDict = Field(default_factory=dict)


class RuntimeRequest(ProtocolModel):
    """Runtime envelope wrapping a :class:`ModelRequest` with execution context.

    Includes tool execution policy, tracing, and provider-specific options.

    Example::

        from llm_protocol_suite import ModelRequest, ModelMessage, TextPart

        req = RuntimeRequest(
            id="req-001",
            model_request=ModelRequest(
                model="gpt-4.1-mini",
                messages=[ModelMessage(role="user", content=[TextPart(text="Hi")])],
            ),
            trace=Trace(trace_id="t-1", span_id="s-1"),
        )
        assert req.protocol_version == "llm-runtime-v1.0"
    """

    id: str
    protocol_version: str = "llm-runtime-v1.0"
    model_request: ModelRequest
    tool_execution: ToolExecutionPolicy = Field(default_factory=ToolExecutionPolicy)
    trace: Trace | None = None
    metadata: JsonDict = Field(default_factory=dict)
    provider_options: JsonDict = Field(default_factory=dict)


class RuntimeResponse(ProtocolModel):
    """Runtime envelope wrapping a :class:`ModelResponse` with execution metadata.

    Includes finish/stop reasons, usage, timing, and optional error.

    Example::

        resp = RuntimeResponse(
            id="resp-001",
            request_id="req-001",
            model_response=ModelResponse(
                model="gpt-4.1-mini",
                message=ModelMessage(role="assistant", content=[TextPart(text="Hello!")]),
            ),
            finish_reason="stop",
            usage=Usage(input_tokens=10, output_tokens=5, total_tokens=15),
        )
        assert resp.finish_reason == "stop"
    """

    id: str
    request_id: str
    protocol_version: str = "llm-runtime-v1.0"
    model_response: ModelResponse
    finish_reason: FinishReason
    stop_reason: StopReason | None = None
    usage: Usage | None = None
    timing: Timing | None = None
    error: RuntimeErrorObject | None = None
    metadata: JsonDict = Field(default_factory=dict)
    provider_response_metadata: JsonDict = Field(default_factory=dict)
    raw: Any | None = None
