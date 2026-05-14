"""Exceptions raised by the LLM Protocol Suite."""


class LLMProtocolSuiteError(Exception):
    """Base exception for llm-protocol-suite."""


class AdapterNormalizationError(LLMProtocolSuiteError):
    """Raised when provider data cannot be normalized into the internal protocol."""
