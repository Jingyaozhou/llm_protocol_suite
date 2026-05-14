"""Core data models for LLM messages, content parts, tools, and requests/responses.

All models inherit from :class:`ProtocolModel` which forbids extra fields,
serialises by alias, and uses enum values.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import Role


JsonDict = dict[str, Any]
"""Type alias: ``dict[str, Any]``, used for JSON-compatible objects."""


class ProtocolModel(BaseModel):
    """Base class for all protocol models.

    Forbids extra fields, serialises by alias, and uses enum values.

    Example::

        class MyModel(ProtocolModel):
            name: str

        m = MyModel(name="test")
        assert m.model_dump() == {"name": "test"}
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        serialize_by_alias=True,
        use_enum_values=True,
    )


class UrlSource(ProtocolModel):
    """A resource referenced by URL.

    Example::

        source = UrlSource(url="https://example.com/img.png")
        assert source.type == "url"
    """

    type: Literal["url"] = "url"
    url: str


class Base64Source(ProtocolModel):
    """A resource encoded as base64.

    Example::

        source = Base64Source(mime_type="image/png", data="iVBOR...")
        assert source.type == "base64"
    """

    type: Literal["base64"] = "base64"
    mime_type: str
    data: str


class FileIdSource(ProtocolModel):
    """A resource referenced by a provider file ID.

    Example::

        source = FileIdSource(file_id="file-abc123")
        assert source.type == "file_id"
    """

    type: Literal["file_id"] = "file_id"
    file_id: str


class PathSource(ProtocolModel):
    """A resource referenced by a local filesystem path.

    Example::

        source = PathSource(path="/tmp/audio.mp3")
        assert source.type == "path"
    """

    type: Literal["path"] = "path"
    path: str


Source = UrlSource | Base64Source | FileIdSource | PathSource
"""Union of all resource source types: :class:`UrlSource` | :class:`Base64Source` | :class:`FileIdSource` | :class:`PathSource`."""


class TextPart(ProtocolModel):
    """Plain text content part.

    Example::

        part = TextPart(text="Hello, world!")
        assert part.type == "text"
    """

    type: Literal["text"] = "text"
    text: str


class ImagePart(ProtocolModel):
    """Image content part with a source (URL, base64, file ID, or path).

    Example::

        img = ImagePart(source=UrlSource(url="https://example.com/cat.png"))
        assert img.type == "image"
    """

    type: Literal["image"] = "image"
    source: Source
    metadata: JsonDict = Field(default_factory=dict)


class AudioPart(ProtocolModel):
    """Audio content part with a source.

    Example::

        audio = AudioPart(source=Base64Source(mime_type="audio/mp3", data="//uQx"))
        assert audio.type == "audio"
    """

    type: Literal["audio"] = "audio"
    source: Source
    metadata: JsonDict = Field(default_factory=dict)


class FilePart(ProtocolModel):
    """Generic file content part with a source.

    Example::

        file = FilePart(source=FileIdSource(file_id="file-abc"))
        assert file.type == "file"
    """

    type: Literal["file"] = "file"
    source: Source
    metadata: JsonDict = Field(default_factory=dict)


class JsonPart(ProtocolModel):
    """Structured JSON content part.

    Example::

        part = JsonPart(data={"key": "value"})
        assert part.type == "json"
    """

    type: Literal["json"] = "json"
    data: Any


class ToolResultError(ProtocolModel):
    """Error details for a failed tool result.

    Example::

        err = ToolResultError(code="TIMEOUT", message="Tool timed out", retryable=True)
        assert err.retryable is True
    """

    code: str
    message: str
    retryable: bool = False
    details: JsonDict = Field(default_factory=dict)


class ToolResultPart(ProtocolModel):
    """Tool execution result content part.

    ``ok=True`` requires ``data`` and forbids ``error``;
    ``ok=False`` requires ``error`` and forbids ``data``.

    Example::

        success = ToolResultPart(ok=True, data={"temp": 22})
        failure = ToolResultPart(
            ok=False,
            error=ToolResultError(code="ERR", message="failed"),
        )
    """

    type: Literal["tool_result"] = "tool_result"
    ok: bool
    data: Any | None = None
    error: ToolResultError | None = None

    @model_validator(mode="after")
    def validate_result_shape(self) -> "ToolResultPart":
        if self.ok and self.error is not None:
            raise ValueError("successful tool_result cannot include error")
        if not self.ok and self.error is None:
            raise ValueError("failed tool_result must include error")
        return self


class ReasoningPart(ProtocolModel):
    """Model reasoning / chain-of-thought content part.

    Example::

        part = ReasoningPart(text="Let me think step by step...")
        assert part.type == "reasoning"
    """

    type: Literal["reasoning"] = "reasoning"
    text: str


ContentPart = (
    TextPart
    | ImagePart
    | AudioPart
    | FilePart
    | JsonPart
    | ToolResultPart
    | ReasoningPart
)
"""Union of all content part types used in :attr:`ModelMessage.content`."""


class ToolDefinition(ProtocolModel):
    """Schema definition for a tool the model may invoke.

    Example::

        tool = ToolDefinition(
            name="get_weather",
            description="Get current weather for a city.",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        )
    """

    name: str
    description: str
    parameters: JsonDict


class ToolCall(ProtocolModel):
    """A single tool call from the model.

    ``arguments`` is always a dict (not a JSON string); adapters handle
    serialisation to/from string formats.

    Example::

        call = ToolCall(id="call_1", name="get_weather", arguments={"city": "Beijing"})
        assert call.arguments["city"] == "Beijing"
    """

    id: str
    type: Literal["function"] = "function"
    name: str
    arguments: JsonDict = Field(default_factory=dict)


class TextResponseFormat(ProtocolModel):
    """Request plain text output (the default response format).

    Example::

        fmt = TextResponseFormat()
        assert fmt.type == "text"
    """

    type: Literal["text"] = "text"


class JsonObjectResponseFormat(ProtocolModel):
    """Request a JSON object output without a fixed schema.

    Example::

        fmt = JsonObjectResponseFormat()
        assert fmt.type == "json_object"
    """

    type: Literal["json_object"] = "json_object"


class JsonSchemaDefinition(ProtocolModel):
    """A named JSON Schema used inside a ``json_schema`` response format.

    Construct with ``schema=`` (alias) and access via the ``schema`` property::

        defn = JsonSchemaDefinition(
            name="weather",
            schema={"type": "object", "properties": {"temp": {"type": "number"}}},
        )
        assert defn.schema["type"] == "object"
    """

    name: str
    schema_: JsonDict = Field(alias="schema")
    strict: bool = False

    @property
    def schema(self) -> JsonDict:
        return self.schema_


class JsonSchemaResponseFormat(ProtocolModel):
    """Request output conforming to a specific JSON Schema.

    Example::

        fmt = JsonSchemaResponseFormat(
            json_schema=JsonSchemaDefinition(
                name="result",
                schema={"type": "object", "properties": {"answer": {"type": "string"}}},
            ),
        )
        assert fmt.type == "json_schema"
    """

    type: Literal["json_schema"] = "json_schema"
    json_schema: JsonSchemaDefinition
    on_validation_error: Literal["retry", "repair", "error", "ignore"] = "error"


ResponseFormat = TextResponseFormat | JsonObjectResponseFormat | JsonSchemaResponseFormat
"""Union of all response format types: :class:`TextResponseFormat` | :class:`JsonObjectResponseFormat` | :class:`JsonSchemaResponseFormat`."""


class ModelOptions(ProtocolModel):
    """Generation parameters forwarded to the model provider.

    Example::

        opts = ModelOptions(temperature=0.7, max_tokens=1024)
        assert opts.temperature == 0.7
    """

    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    seed: int | None = None


class ModelMessage(ProtocolModel):
    """A single message in a conversation.

    Role-field constraints enforced by validators:

    * ``tool_calls`` is only valid when ``role="assistant"``.
    * ``tool_call_id`` is only valid when ``role="tool"``.
    * ``role="tool"`` requires ``tool_call_id``.

    Example::

        user_msg = ModelMessage(role="user", content=[TextPart(text="Hello")])
        assistant_msg = ModelMessage(
            role="assistant",
            content=[],
            tool_calls=[ToolCall(id="call_1", name="search", arguments={"q": "test"})],
        )
        tool_msg = ModelMessage(
            role="tool",
            content=[ToolResultPart(ok=True, data={"result": "found"})],
            tool_call_id="call_1",
        )
    """

    role: Role
    content: list[ContentPart] = Field(default_factory=list)
    name: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None

    @model_validator(mode="after")
    def validate_role_fields(self) -> "ModelMessage":
        if self.tool_call_id is not None and self.role != Role.TOOL:
            raise ValueError("tool_call_id is only valid for tool messages")
        if self.tool_calls is not None and self.role != Role.ASSISTANT:
            raise ValueError("tool_calls is only valid for assistant messages")
        if self.role == Role.TOOL and self.tool_call_id is None:
            raise ValueError("tool messages require tool_call_id")
        return self


class ModelRequest(ProtocolModel):
    """A complete request to an LLM model.

    Example::

        request = ModelRequest(
            model="deepseek-chat",
            messages=[ModelMessage(role="user", content=[TextPart(text="Hello")])],
            tools=[
                ToolDefinition(
                    name="get_weather",
                    description="Get weather.",
                    parameters={"type": "object", "properties": {"city": {"type": "string"}}},
                )
            ],
            options=ModelOptions(temperature=0.7),
        )
        assert request.model == "deepseek-chat"
    """

    model: str
    messages: list[ModelMessage]
    tools: list[ToolDefinition] = Field(default_factory=list)
    tool_choice: Literal["none", "auto", "required"] | JsonDict | None = "auto"
    response_format: ResponseFormat = Field(default_factory=TextResponseFormat)
    options: ModelOptions = Field(default_factory=ModelOptions)


class ModelResponse(ProtocolModel):
    """A response from an LLM model.

    Example::

        resp = ModelResponse(
            model="deepseek-chat",
            message=ModelMessage(role="assistant", content=[TextPart(text="Hi there!")]),
        )
        assert resp.message.content[0].text == "Hi there!"
    """

    model: str
    message: ModelMessage
