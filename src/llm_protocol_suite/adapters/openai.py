import json
from typing import Any

from llm_protocol_suite.exceptions import AdapterNormalizationError
from llm_protocol_suite.model import (
    FilePart,
    ImagePart,
    JsonPart,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ReasoningPart,
    TextPart,
    ToolCall,
    ToolDefinition,
    ToolResultPart,
)
from llm_protocol_suite.runtime import RuntimeRequest


def to_openai_chat_request(request: ModelRequest | RuntimeRequest) -> dict[str, Any]:
    model_request = request.model_request if isinstance(request, RuntimeRequest) else request
    payload: dict[str, Any] = {
        "model": model_request.model,
        "messages": [_message_to_openai(message) for message in model_request.messages],
    }
    if model_request.tools:
        payload["tools"] = [_tool_to_openai(tool) for tool in model_request.tools]
    if model_request.tool_choice is not None:
        payload["tool_choice"] = model_request.tool_choice
    payload.update(model_request.options.model_dump(exclude_none=True))
    return payload


def from_openai_chat_response(response: dict[str, Any]) -> ModelResponse:
    try:
        choice = response["choices"][0]
        message_data = choice["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AdapterNormalizationError("OpenAI response is missing choices[0].message") from exc

    tool_calls = _normalize_tool_calls(message_data.get("tool_calls") or [])
    content = _normalize_content(message_data.get("content"))
    message = ModelMessage(
        role=message_data.get("role", "assistant"),
        content=content,
        tool_calls=tool_calls or None,
        name=message_data.get("name"),
    )
    return ModelResponse(model=response.get("model", ""), message=message)


def _message_to_openai(message: ModelMessage) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "role": message.role,
        "content": [_content_part_to_openai(part) for part in message.content],
    }
    if message.name is not None:
        payload["name"] = message.name
    if message.tool_calls is not None:
        payload["tool_calls"] = [_tool_call_to_openai(call) for call in message.tool_calls]
    if message.tool_call_id is not None:
        payload["tool_call_id"] = message.tool_call_id
    return payload


def _content_part_to_openai(part: Any) -> dict[str, Any]:
    if isinstance(part, TextPart):
        return {"type": "text", "text": part.text}
    if isinstance(part, ImagePart):
        return {"type": "image_url", "image_url": _source_to_openai_image(part.source)}
    if isinstance(part, FilePart):
        return {"type": "file", "file": part.source.model_dump()}
    if isinstance(part, JsonPart):
        return {"type": "text", "text": json.dumps(part.data, ensure_ascii=False)}
    if isinstance(part, ToolResultPart):
        return {"type": "text", "text": json.dumps(part.model_dump(), ensure_ascii=False)}
    if isinstance(part, ReasoningPart):
        return {"type": "text", "text": part.text}
    return part.model_dump()


def _source_to_openai_image(source: Any) -> dict[str, str]:
    if source.type == "url":
        return {"url": source.url}
    if source.type == "base64":
        return {"url": f"data:{source.mime_type};base64,{source.data}"}
    raise AdapterNormalizationError("OpenAI image content requires url or base64 source")


def _tool_to_openai(tool: ToolDefinition) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def _tool_call_to_openai(call: ToolCall) -> dict[str, Any]:
    return {
        "id": call.id,
        "type": call.type,
        "function": {
            "name": call.name,
            "arguments": json.dumps(call.arguments, ensure_ascii=False),
        },
    }


def _normalize_content(content: Any) -> list[TextPart]:
    if content is None:
        return []
    if isinstance(content, str):
        return [TextPart(text=content)]
    if isinstance(content, list):
        parts: list[TextPart] = []
        for item in content:
            if not isinstance(item, dict):
                raise AdapterNormalizationError("OpenAI content list items must be objects")
            if item.get("type") == "text":
                parts.append(TextPart(text=item.get("text", "")))
        return parts
    raise AdapterNormalizationError("Unsupported OpenAI message content")


def _normalize_tool_calls(tool_calls: list[dict[str, Any]]) -> list[ToolCall]:
    normalized: list[ToolCall] = []
    seen_ids: set[str] = set()
    for index, raw_call in enumerate(tool_calls):
        call_id = raw_call.get("id") or f"llmps_call_{index}"
        if call_id in seen_ids:
            raise AdapterNormalizationError(f"Duplicate tool call id: {call_id}")
        seen_ids.add(call_id)

        function = raw_call.get("function") or {}
        arguments_text = function.get("arguments") or "{}"
        try:
            arguments = json.loads(arguments_text)
        except json.JSONDecodeError as exc:
            raise AdapterNormalizationError(f"Invalid JSON arguments for tool call {call_id}") from exc
        if not isinstance(arguments, dict):
            raise AdapterNormalizationError(f"Tool call {call_id} arguments must decode to an object")

        normalized.append(
            ToolCall(
                id=call_id,
                type=raw_call.get("type", "function"),
                name=function.get("name", ""),
                arguments=arguments,
            )
        )
    return normalized
