from llm_protocol_suite import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RuntimeErrorObject,
    RuntimeRequest,
    RuntimeResponse,
    TextPart,
    ToolExecutionPolicy,
    Usage,
)


def test_runtime_request_wraps_model_request():
    request = RuntimeRequest(
        id="req_1",
        model_request=ModelRequest(
            model="deepseek-chat",
            messages=[ModelMessage(role="user", content=[TextPart(text="hi")])],
        ),
        tool_execution=ToolExecutionPolicy(enabled=False),
    )

    assert request.protocol_version == "llm-runtime-v1.0"
    assert request.model_request.messages[0].content[0].text == "hi"


def test_runtime_response_allows_provider_error():
    response = RuntimeResponse(
        id="resp_1",
        request_id="req_1",
        model_response=ModelResponse(
            model="deepseek-chat",
            message=ModelMessage(role="assistant", content=[]),
        ),
        finish_reason="provider_error",
        stop_reason="provider_stop",
        usage=Usage(input_tokens=0, output_tokens=0, total_tokens=0),
        error=RuntimeErrorObject(
            code="PROVIDER_TIMEOUT",
            message="Provider request timeout.",
            type="timeout",
            retryable=True,
        ),
    )

    assert response.error.retryable is True
