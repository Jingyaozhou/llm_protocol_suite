from llm_protocol_suite.schema import export_json_schemas


def test_export_json_schemas_contains_core_models():
    schemas = export_json_schemas()

    assert "ModelRequest" in schemas
    assert "RuntimeRequest" in schemas
    assert "ToolExecutionPolicy" in schemas
    assert schemas["ModelRequest"]["type"] == "object"
