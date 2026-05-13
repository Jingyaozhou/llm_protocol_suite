import pytest
from pydantic import ValidationError

from llm_protocol_suite import (
    Base64Source,
    ModelMessage,
    ModelRequest,
    TextPart,
    ToolCall,
    ToolDefinition,
)


def test_text_message_requires_content_list():
    message = ModelMessage(role="user", content=[TextPart(text="hello")])

    assert message.model_dump()["content"][0]["type"] == "text"


def test_tool_call_arguments_must_be_dict():
    with pytest.raises(ValidationError):
        ToolCall(id="call_1", name="get_weather", arguments='{"city": "Beijing"}')


def test_tool_call_id_only_allowed_on_tool_messages():
    with pytest.raises(ValidationError):
        ModelMessage(role="assistant", content=[], tool_call_id="call_1")


def test_tool_calls_only_allowed_on_assistant_messages():
    with pytest.raises(ValidationError):
        ModelMessage(
            role="user",
            content=[],
            tool_calls=[ToolCall(id="call_1", name="get_weather", arguments={})],
        )


def test_base64_source_requires_mime_type():
    with pytest.raises(ValidationError):
        Base64Source(data="abc")


def test_model_request_round_trip():
    request = ModelRequest(
        model="deepseek-chat",
        messages=[ModelMessage(role="user", content=[TextPart(text="hi")])],
        tools=[
            ToolDefinition(
                name="get_weather",
                description="Get weather.",
                parameters={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            )
        ],
        tool_choice="auto",
    )

    restored = ModelRequest.model_validate(request.model_dump())

    assert restored.model == "deepseek-chat"
    assert restored.messages[0].content[0].text == "hi"
