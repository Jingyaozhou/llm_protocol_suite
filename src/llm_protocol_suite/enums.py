"""Enumerations used across the protocol: message roles, content types, and stop/finish reasons."""

from enum import Enum


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    FILE = "file"
    JSON = "json"
    TOOL_RESULT = "tool_result"
    REASONING = "reasoning"


class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"


class StopReason(str, Enum):
    EOS_TOKEN = "eos_token"
    STOP_SEQUENCE = "stop_sequence"
    USER_INTERRUPT = "user_interrupt"
    MAX_TOKENS = "max_tokens"
    TOOL_USE = "tool_use"
    SAFETY_FILTER = "safety_filter"
    PROVIDER_STOP = "provider_stop"
