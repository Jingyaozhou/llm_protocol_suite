"""LLM-oriented usage guide helpers.

The functions in this module expose short, task-oriented package usage
documentation at runtime. They are intended for LLM coding agents and other
tools that can import an installed package but should not inspect source files.
"""

from importlib import resources


_USAGE_PACKAGE = "llm_protocol_suite._usage"
_TOPICS = {
    "index": "index.md",
    "openai_adapter": "openai_adapter.md",
    "runtime": "runtime.md",
    "tool_call": "tool_call.md",
}


def list_topics() -> list[str]:
    """Return available LLM usage topics."""
    return sorted(_TOPICS)


def help_for(topic: str = "index") -> str:
    """Return focused usage help for a topic.

    Args:
        topic: Topic name from :func:`list_topics`. Defaults to ``"index"``.

    Raises:
        KeyError: If the topic is unknown.
    """
    normalized = topic.strip().lower().replace("-", "_")
    try:
        filename = _TOPICS[normalized]
    except KeyError as exc:
        available = ", ".join(list_topics())
        raise KeyError(f"Unknown usage topic {topic!r}. Available topics: {available}") from exc

    return resources.files(_USAGE_PACKAGE).joinpath(filename).read_text(encoding="utf-8")


def llm_usage() -> str:
    """Return the default compact usage guide for LLM agents."""
    return help_for("index")
