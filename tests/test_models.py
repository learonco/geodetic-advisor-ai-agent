"""Unit tests for src/models/ domain models."""

import pytest
from pydantic import ValidationError

from src.models.geodesy import BoundingBox, CRSResult
from src.models.agent import ToolCall, AgentResponse
from src.models.chat import ChatMessage


# ---------------------------------------------------------------------------
# BoundingBox
# ---------------------------------------------------------------------------

class TestBoundingBox:
    def test_valid_global_bbox(self):
        bbox = BoundingBox(west=-180.0, south=-90.0, east=180.0, north=90.0)
        assert bbox.west == -180.0
        assert bbox.north == 90.0

    def test_valid_regional_bbox(self):
        bbox = BoundingBox(west=-71.97, south=-41.10, east=-67.99, north=-36.05)
        assert bbox.south == -41.10

    def test_south_exceeds_range_raises(self):
        with pytest.raises(ValidationError):
            BoundingBox(west=0.0, south=-91.0, east=10.0, north=10.0)

    def test_north_exceeds_range_raises(self):
        with pytest.raises(ValidationError):
            BoundingBox(west=0.0, south=0.0, east=10.0, north=91.0)

    def test_west_exceeds_range_raises(self):
        with pytest.raises(ValidationError):
            BoundingBox(west=-181.0, south=0.0, east=10.0, north=10.0)

    def test_east_exceeds_range_raises(self):
        with pytest.raises(ValidationError):
            BoundingBox(west=0.0, south=0.0, east=181.0, north=10.0)

    def test_south_greater_than_north_raises(self):
        with pytest.raises(ValidationError):
            BoundingBox(west=0.0, south=10.0, east=10.0, north=5.0)

    def test_serializes_to_dict(self):
        bbox = BoundingBox(west=-10.0, south=-10.0, east=10.0, north=10.0)
        d = bbox.model_dump()
        assert set(d.keys()) == {"west", "south", "east", "north"}

    def test_from_dict(self):
        data = {"west": -10.0, "south": -10.0, "east": 10.0, "north": 10.0}
        bbox = BoundingBox.model_validate(data)
        assert bbox.east == 10.0


# ---------------------------------------------------------------------------
# CRSResult
# ---------------------------------------------------------------------------

class TestCRSResult:
    def test_valid_with_bbox(self):
        bbox = BoundingBox(west=-180.0, south=-90.0, east=180.0, north=90.0)
        result = CRSResult(epsg_code="4326", crs_name="WGS 84", area_bbox=bbox)
        assert result.epsg_code == "4326"
        assert result.area_bbox is not None

    def test_valid_without_bbox(self):
        result = CRSResult(epsg_code="4326", crs_name="WGS 84")
        assert result.area_bbox is None

    def test_missing_epsg_code_raises(self):
        with pytest.raises(ValidationError):
            CRSResult(crs_name="WGS 84")

    def test_missing_crs_name_raises(self):
        with pytest.raises(ValidationError):
            CRSResult(epsg_code="4326")

    def test_serializes_to_dict(self):
        result = CRSResult(epsg_code="3857", crs_name="Web Mercator")
        d = result.model_dump()
        assert d["epsg_code"] == "3857"
        assert d["area_bbox"] is None

    def test_nested_bbox_serialization(self):
        bbox = BoundingBox(west=-180.0, south=-90.0, east=180.0, north=90.0)
        result = CRSResult(epsg_code="4326", crs_name="WGS 84", area_bbox=bbox)
        d = result.model_dump()
        assert d["area_bbox"]["west"] == -180.0


# ---------------------------------------------------------------------------
# ToolCall
# ---------------------------------------------------------------------------

class TestToolCall:
    def test_valid_tool_call(self):
        tc = ToolCall(tool="search_crs_objects", input={"bbox": {}}, output="result")
        assert tc.tool == "search_crs_objects"

    def test_output_can_be_list(self):
        tc = ToolCall(tool="search_crs_objects", input={}, output=["a", "b"])
        assert isinstance(tc.output, list)

    def test_output_can_be_string(self):
        tc = ToolCall(tool="lookup_crs", input={"epsg_code": "4326"}, output="WGS 84")
        assert isinstance(tc.output, str)

    def test_missing_tool_raises(self):
        with pytest.raises(ValidationError):
            ToolCall(input={}, output="")

    def test_default_empty_input(self):
        tc = ToolCall(tool="lookup_crs", output="")
        assert tc.input == {}


# ---------------------------------------------------------------------------
# AgentResponse
# ---------------------------------------------------------------------------

class TestAgentResponse:
    def test_successful_response(self):
        tc = ToolCall(tool="lookup_crs", input={}, output="WGS 84")
        resp = AgentResponse(response="Found WGS 84", tool_calls=[tc], success=True)
        assert resp.success is True
        assert resp.error is None

    def test_failed_response(self):
        resp = AgentResponse(response="Error", tool_calls=[], success=False, error="timeout")
        assert resp.success is False
        assert resp.error == "timeout"

    def test_defaults(self):
        resp = AgentResponse(response="ok", success=True)
        assert resp.tool_calls == []
        assert resp.error is None

    def test_missing_response_raises(self):
        with pytest.raises(ValidationError):
            AgentResponse(success=True)

    def test_missing_success_raises(self):
        with pytest.raises(ValidationError):
            AgentResponse(response="ok")


# ---------------------------------------------------------------------------
# ChatMessage
# ---------------------------------------------------------------------------

class TestChatMessage:
    def test_user_message(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"

    def test_assistant_message(self):
        msg = ChatMessage(role="assistant", content="Hi there")
        assert msg.role == "assistant"

    def test_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="system", content="oops")

    def test_default_empty_tool_calls(self):
        msg = ChatMessage(role="user", content="query")
        assert msg.tool_calls == []

    def test_with_tool_calls(self):
        tc = ToolCall(tool="lookup_crs", input={}, output="WGS 84")
        msg = ChatMessage(role="assistant", content="Found it", tool_calls=[tc])
        assert len(msg.tool_calls) == 1

    def test_missing_content_raises(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="user")

    def test_serializes_role(self):
        msg = ChatMessage(role="user", content="test")
        d = msg.model_dump()
        assert d["role"] == "user"
