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
    finish_reason: FinishReason
    stop_reason: StopReason | None = None
    usage: Usage | None = None
    timing: Timing | None = None
    error: RuntimeErrorObject | None = None
    metadata: JsonDict = Field(default_factory=dict)
    provider_response_metadata: JsonDict = Field(default_factory=dict)
    raw: Any | None = None
