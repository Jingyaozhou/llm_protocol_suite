"""JSON Schema export for all core protocol models."""

from typing import Any

from .model import ModelMessage, ModelRequest, ModelResponse, ToolCall, ToolDefinition
from .runtime import RuntimeRequest, RuntimeResponse
from .tools import ToolExecutionPolicy, ToolExecutionRecord


def export_json_schemas() -> dict[str, dict[str, Any]]:
    """Export JSON Schemas for all core protocol models.

    Returns a dict mapping model name → its JSON Schema.

    Example::

        schemas = export_json_schemas()
        assert "ModelRequest" in schemas
        assert schemas["ModelRequest"]["type"] == "object"
    """
    models = [
        ModelMessage,
        ModelRequest,
        ModelResponse,
        ToolCall,
        ToolDefinition,
        RuntimeRequest,
        RuntimeResponse,
        ToolExecutionPolicy,
        ToolExecutionRecord,
    ]
    return {model.__name__: model.model_json_schema() for model in models}
