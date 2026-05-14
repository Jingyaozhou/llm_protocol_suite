"""Tool execution policy, approval, retry, and execution-record models."""

from typing import Any, Literal

from pydantic import Field

from .model import ProtocolModel


JsonDict = dict[str, Any]


class RetryPolicy(ProtocolModel):
    """Retry backoff strategy for tool execution.

    Example::

        policy = RetryPolicy(backoff="exponential", initial_delay_ms=500, max_delay_ms=5000)
        assert policy.backoff == "exponential"
    """

    backoff: Literal["none", "fixed", "exponential"] = "exponential"
    initial_delay_ms: int = 200
    max_delay_ms: int = 2000


class ToolExecutionPolicy(ProtocolModel):
    """Controls how tools are executed during a model run.

    Example::

        policy = ToolExecutionPolicy(
            parallel=True,
            timeout_ms=10000,
            approval_required_tools=["delete_file"],
        )
        assert policy.max_retries == 1
    """

    enabled: bool = True
    parallel: bool = True
    timeout_ms: int = 30000
    max_retries: int = 1
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    approval_required_tools: list[str] = Field(default_factory=list)
    default_approval_required: bool = False


class ToolApproval(ProtocolModel):
    """Approval state for a tool that requires human confirmation.

    Example::

        approval = ToolApproval(required=True, status="approved")
        assert approval.status == "approved"
    """

    required: bool
    status: Literal["not_required", "pending", "approved", "rejected", "expired"]


class ToolExecutionRecord(ProtocolModel):
    """Audit record tracking the lifecycle of a single tool invocation.

    Example::

        record = ToolExecutionRecord(
            tool_call_id="call_1",
            name="get_weather",
            status="success",
            attempt=1,
            max_retries=1,
            latency_ms=340,
        )
        assert record.status == "success"
    """

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
