"""Domain models for the Geodetic Advisor.

Re-exports all public models grouped by domain:
- geodesy: BoundingBox, CRSResult
- agent: ToolCall, AgentResponse
- chat: ChatMessage
"""

from src.models.geodesy import BoundingBox, CRSResult
from src.models.agent import ToolCall, AgentResponse
from src.models.chat import ChatMessage

__all__ = [
    "BoundingBox",
    "CRSResult",
    "ToolCall",
    "AgentResponse",
    "ChatMessage",
]
