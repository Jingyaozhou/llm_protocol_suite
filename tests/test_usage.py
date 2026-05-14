import subprocess
import sys

from llm_protocol_suite import help_for, list_topics, llm_usage


def test_llm_usage_includes_core_classes_and_rules():
    usage = llm_usage()

    assert "ModelRequest" in usage
    assert "ModelMessage" in usage
    assert "ToolCall" in usage
    assert "RuntimeRequest" in usage
    assert "to_openai_chat_request" in usage
    assert "ToolCall.arguments is always a dict" in usage
    assert "ModelMessage.content is always a list" in usage


def test_help_for_topic_returns_focused_usage():
    text = help_for("tool_call")

    assert "ToolCall" in text
    assert "arguments={\"city\": \"Beijing\"}" in text


def test_list_topics_includes_index_and_openai_adapter():
    topics = list_topics()

    assert "index" in topics
    assert "openai_adapter" in topics


def test_module_cli_outputs_usage():
    result = subprocess.run(
        [sys.executable, "-m", "llm_protocol_suite", "usage", "tool_call"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "ToolCall" in result.stdout
    assert "arguments" in result.stdout
