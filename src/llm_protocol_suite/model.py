from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import Role


JsonDict = dict[str, Any]


class ProtocolModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        serialize_by_alias=True,
        use_enum_values=True,
    )


class UrlSource(ProtocolModel):
    type: Literal["url"] = "url"
    url: str


class Base64Source(ProtocolModel):
    type: Literal["base64"] = "base64"
    mime_type: str
    data: str


class FileIdSource(ProtocolModel):
    type: Literal["file_id"] = "file_id"
    file_id: str


class PathSource(ProtocolModel):
    type: Literal["path"] = "path"
    path: str


Source = UrlSource | Base64Source | FileIdSource | PathSource


class TextPart(ProtocolModel):
    type: Literal["text"] = "text"
    text: str


class ImagePart(ProtocolModel):
    type: Literal["image"] = "image"
    source: Source
    metadata: JsonDict = Field(default_factory=dict)


class AudioPart(ProtocolModel):
    type: Literal["audio"] = "audio"
    source: Source
    metadata: JsonDict = Field(default_factory=dict)


class FilePart(ProtocolModel):
    type: Literal["file"] = "file"
    source: Source
    metadata: JsonDict = Field(default_factory=dict)


class JsonPart(ProtocolModel):
    type: Literal["json"] = "json"
    data: Any


class ToolResultError(ProtocolModel):
    code: str
    message: str
    retryable: bool = False
    details: JsonDict = Field(default_factory=dict)


class ToolResultPart(ProtocolModel):
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


class ToolDefinition(ProtocolModel):
    name: str
    description: str
    parameters: JsonDict


class ToolCall(ProtocolModel):
    id: str
    type: Literal["function"] = "function"
    name: str
    arguments: JsonDict = Field(default_factory=dict)


class TextResponseFormat(ProtocolModel):
    type: Literal["text"] = "text"


class JsonObjectResponseFormat(ProtocolModel):
    type: Literal["json_object"] = "json_object"


class JsonSchemaDefinition(ProtocolModel):
    name: str
    schema_: JsonDict = Field(alias="schema")
    strict: bool = False

    @property
    def schema(self) -> JsonDict:
        return self.schema_


class JsonSchemaResponseFormat(ProtocolModel):
    type: Literal["json_schema"] = "json_schema"
    json_schema: JsonSchemaDefinition
    on_validation_error: Literal["retry", "repair", "error", "ignore"] = "error"


ResponseFormat = TextResponseFormat | JsonObjectResponseFormat | JsonSchemaResponseFormat


class ModelOptions(ProtocolModel):
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    seed: int | None = None


class ModelMessage(ProtocolModel):
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
    model: str
    messages: list[ModelMessage]
    tools: list[ToolDefinition] = Field(default_factory=list)
    tool_choice: Literal["none", "auto", "required"] | JsonDict | None = "auto"
    response_format: ResponseFormat = Field(default_factory=TextResponseFormat)
    options: ModelOptions = Field(default_factory=ModelOptions)


class ModelResponse(ProtocolModel):
    model: str
    message: ModelMessage
