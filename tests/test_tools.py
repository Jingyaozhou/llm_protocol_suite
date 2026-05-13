from llm_protocol_suite import RetryPolicy, ToolApproval, ToolExecutionPolicy, ToolExecutionRecord


def test_tool_execution_policy_defaults():
    policy = ToolExecutionPolicy()

    assert policy.enabled is True
    assert policy.parallel is True
    assert policy.timeout_ms == 30000
    assert policy.max_retries == 1
    assert isinstance(policy.retry_policy, RetryPolicy)


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
