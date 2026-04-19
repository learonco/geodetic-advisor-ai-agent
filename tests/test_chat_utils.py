"""Unit tests for webui/chat_utils.py."""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_chat_utils():
    """Import chat_utils with the module-level geodetic_agent patched."""
    with patch("src.agents.geodetic.geodetic_agent", new=MagicMock()):
        import src.webui.chat_utils as cu
        importlib.reload(cu)
        return cu


class TestFormatCrsResults:
    def test_empty_string_passthrough(self):
        cu = _load_chat_utils()
        assert cu.format_crs_results("") == ""

    def test_none_passthrough(self):
        cu = _load_chat_utils()
        assert cu.format_crs_results(None) is None

    def test_area_of_use_line_removed(self):
        cu = _load_chat_utils()
        text = "WGS 84 (EPSG:4326)\nArea of Use: World"
        result = cu.format_crs_results(text)
        assert "Area of Use" not in result

    def test_authority_code_format_preserved(self):
        cu = _load_chat_utils()
        text = "WGS 84 (EPSG:4326)"
        result = cu.format_crs_results(text)
        assert "EPSG:4326" in result


class TestParseAgentResults:
    def test_parse_epsg_from_text(self):
        cu = _load_chat_utils()
        response = "I found EPSG:4326, EPSG:3857 and EPSG:4979 for your area."
        results = cu.parse_agent_results(response)
        codes = {r.epsg_code for r in results}
        assert {"4326", "3857", "4979"}.issubset(codes)

    def test_parse_from_tool_calls(self):
        cu = _load_chat_utils()
        tool_calls = [
            {
                "tool": "search_crs_objects",
                "output": json.dumps([
                    {"epsg_code": "4326", "crs_name": "WGS 84",
                     "area_bbox": {"west": -180.0, "south": -90.0, "east": 180.0, "north": 90.0}},
                    {"epsg_code": "3857", "crs_name": "Web Mercator",
                     "area_bbox": {"west": -180.0, "south": -85.0, "east": 180.0, "north": 85.0}},
                ]),
            }
        ]
        results = cu.parse_agent_results("Found 2 CRS.", tool_calls)
        assert len(results) == 2
        assert results[0].epsg_code == "4326"
        assert results[0].area_bbox is not None
        assert results[0].area_bbox.west == -180.0

    def test_no_duplicate_codes(self):
        """EPSG codes in both text and tool output must appear only once."""
        cu = _load_chat_utils()
        tool_calls = [
            {
                "tool": "search_crs_objects",
                "output": json.dumps([
                    {"epsg_code": "4326", "crs_name": "WGS 84", "area_bbox": None},
                ]),
            }
        ]
        results = cu.parse_agent_results("EPSG:4326", tool_calls)
        codes = [r.epsg_code for r in results]
        assert codes.count("4326") == 1

    def test_empty_response_returns_empty_list(self):
        cu = _load_chat_utils()
        results = cu.parse_agent_results("")
        assert results == []

    def test_mixed_text_and_tool_calls(self):
        cu = _load_chat_utils()
        tool_calls = [
            {
                "tool": "search_crs_objects",
                "output": json.dumps([
                    {"epsg_code": "4326", "crs_name": "WGS 84",
                     "area_bbox": {"west": -180.0, "south": -90.0, "east": 180.0, "north": 90.0}},
                ]),
            }
        ]
        # Text also mentions 4979 (not in tool output)
        results = cu.parse_agent_results("EPSG:4326 and EPSG:4979", tool_calls)
        codes = {r.epsg_code for r in results}
        assert "4326" in codes
        assert "4979" in codes


class TestDetectMapRelevantResponse:
    def test_crs_keyword_triggers_map_data(self):
        cu = _load_chat_utils()
        result = cu.detect_map_relevant_response("Found some CRS results", [])
        assert result["has_map_data"] is True

    def test_irrelevant_response_no_map_data(self):
        cu = _load_chat_utils()
        result = cu.detect_map_relevant_response("Hello, how can I help?", [])
        assert result["has_map_data"] is False

    def test_tool_call_sets_data_type(self):
        cu = _load_chat_utils()
        tool_calls = [{"tool": "search_crs_objects", "output": "[]"}]
        result = cu.detect_map_relevant_response("some response", tool_calls)
        assert result["data_type"] == "crs_results"
