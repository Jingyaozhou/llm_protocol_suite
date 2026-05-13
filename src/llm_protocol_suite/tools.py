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
