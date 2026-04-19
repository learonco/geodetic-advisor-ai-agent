"""Chat domain models.

This module defines Pydantic models for the conversation layer, representing
messages exchanged between the user and the assistant.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.models.agent import ToolCall


class ChatMessage(BaseModel):
    """A single message in the conversation history.

    Attributes:
        role: Sender role — either "user" or "assistant".
        content: Text content of the message.
        tool_calls: Tool invocations associated with this message (assistant only).
    """

    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
