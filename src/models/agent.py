"""Agent domain models.

This module defines Pydantic models for LLM agent interactions, including
tool calls and agent responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A single tool invocation made by the agent.

    Attributes:
        tool: Name of the tool that was called.
        input: Arguments passed to the tool.
        output: Result returned by the tool (string or list).
    """

    tool: str
    input: dict = Field(default_factory=dict)
    output: str | list = ""


class AgentResponse(BaseModel):
    """Structured response from the geodetic agent.

    Attributes:
        response: Agent's text response to the user.
        tool_calls: List of tools invoked during the response.
        success: Whether the agent completed without error.
        error: Error message if success is False, otherwise None.
    """

    response: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    success: bool
    error: str | None = None
