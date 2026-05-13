import json

import pytest

from llm_protocol_suite import ModelMessage, ModelRequest, TextPart, ToolCall, ToolDefinition
from llm_protocol_suite.adapters.openai import from_openai_chat_response, to_openai_chat_request
from llm_protocol_suite.exceptions import AdapterNormalizationError


def test_to_openai_chat_request_serializes_tool_arguments():
    request = ModelRequest(
        model="gpt-4.1-mini",
        messages=[
            ModelMessage(role="user", content=[TextPart(text="weather?")]),
            ModelMessage(
                role="assistant",
                content=[],
                tool_calls=[ToolCall(id="call_1", name="get_weather", arguments={"city": "Beijing"})],
            ),
        ],
        tools=[
            ToolDefinition(
                name="get_weather",
                description="Get weather.",
                parameters={"type": "object", "properties": {"city": {"type": "string"}}},
            )
        ],
    )

    payload = to_openai_chat_request(request)

    assert payload["model"] == "gpt-4.1-mini"
    assert payload["messages"][0]["content"][0]["text"] == "weather?"
    arguments = payload["messages"][1]["tool_calls"][0]["function"]["arguments"]
    assert json.loads(arguments) == {"city": "Beijing"}


def test_from_openai_chat_response_normalizes_tool_arguments():
    response = {
        "model": "gpt-4.1-mini",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city": "Beijing"}',
                            },
                        }
                    ],
                }
            }
        ],
    }

    normalized = from_openai_chat_response(response)

    assert normalized.message.tool_calls[0].arguments == {"city": "Beijing"}


def test_from_openai_chat_response_rejects_duplicate_tool_ids():
    response = {
        "model": "gpt-4.1-mini",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_1", "function": {"name": "a", "arguments": "{}"}},
                        {"id": "call_1", "function": {"name": "b", "arguments": "{}"}},
                    ],
                }
            }
        ],
    }

    with pytest.raises(AdapterNormalizationError):
        from_openai_chat_response(response)


def test_from_openai_chat_response_rejects_invalid_arguments_json():
    response = {
        "model": "gpt-4.1-mini",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_1", "function": {"name": "a", "arguments": "not-json"}}
                    ],
                }
            }
        ],
    }

    with pytest.raises(AdapterNormalizationError):
        from_openai_chat_response(response)
