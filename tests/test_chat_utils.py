"""Unit tests for webui/chat_utils.py."""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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


class TestDetectMapRelevantResponseGeoJson:
    _GEOJSON_STR = json.dumps({
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-65.0, -40.0], [-60.0, -40.0],
                        [-60.0, -35.0], [-65.0, -35.0],
                        [-65.0, -40.0],
                    ]],
                },
                "properties": {"name": "POSGAR 2007"},
            }
        ],
    })

    def test_plot_geojson_tool_call_sets_geojson_data_type(self):
        cu = _load_chat_utils()
        tool_calls = [{"tool": "plot_geojson", "output": self._GEOJSON_STR}]
        result = cu.detect_map_relevant_response("Here is the area.", tool_calls)
        assert result["data_type"] == "geojson"

    def test_plot_geojson_tool_call_has_map_data(self):
        cu = _load_chat_utils()
        tool_calls = [{"tool": "plot_geojson", "output": self._GEOJSON_STR}]
        result = cu.detect_map_relevant_response("Here is the area.", tool_calls)
        assert result["has_map_data"] is True

    def test_plot_geojson_data_is_parsed_dict(self):
        cu = _load_chat_utils()
        tool_calls = [{"tool": "plot_geojson", "output": self._GEOJSON_STR}]
        result = cu.detect_map_relevant_response("Here is the area.", tool_calls)
        assert isinstance(result["data"], dict)
        assert result["data"]["type"] == "FeatureCollection"

    def test_plot_geojson_tool_call_object_format(self):
        """ToolCall objects (not dicts) are also handled."""
        from src.models.agent import ToolCall
        cu = _load_chat_utils()
        tool_calls = [ToolCall(tool="plot_geojson", input={}, output=self._GEOJSON_STR)]
        result = cu.detect_map_relevant_response("Here is the area.", tool_calls)
        assert result["data_type"] == "geojson"


class TestExtractToolCalls:
    """Tests that extract_tool_calls populates tool outputs from ToolMessages."""

    _GEOJSON_STR = json.dumps({"type": "FeatureCollection", "features": []})

    def _make_ai_message(self, tool_call_id: str, tool_name: str, args: dict):
        from langchain_core.messages import AIMessage
        tc = {"id": tool_call_id, "name": tool_name, "args": args, "type": "tool_call"}
        return AIMessage(content="", tool_calls=[tc])

    def _make_tool_message(self, tool_call_id: str, content: str):
        from langchain_core.messages import ToolMessage
        return ToolMessage(content=content, tool_call_id=tool_call_id)

    def test_output_populated_from_tool_message(self):
        cu = _load_chat_utils()
        ai_msg = self._make_ai_message("id1", "plot_geojson", {"geojson": self._GEOJSON_STR})
        tm = self._make_tool_message("id1", self._GEOJSON_STR)
        result = cu.extract_tool_calls({"messages": [ai_msg, tm]})
        assert len(result) == 1
        assert result[0].tool == "plot_geojson"
        assert result[0].output == self._GEOJSON_STR

    def test_output_empty_when_no_tool_message(self):
        cu = _load_chat_utils()
        ai_msg = self._make_ai_message("id2", "lookup_crs", {"epsg_code": "5340"})
        result = cu.extract_tool_calls({"messages": [ai_msg]})
        assert len(result) == 1
        assert result[0].output == ""

    def test_multiple_tool_calls_matched_correctly(self):
        cu = _load_chat_utils()
        ai_msg = self._make_ai_message("id3", "search_crs_objects", {"object_name": "POSGAR 2007"})
        ai_msg2 = self._make_ai_message("id4", "plot_geojson", {"geojson": self._GEOJSON_STR})
        tm3 = self._make_tool_message("id3", "search output")
        tm4 = self._make_tool_message("id4", self._GEOJSON_STR)
        result = cu.extract_tool_calls({"messages": [ai_msg, tm3, ai_msg2, tm4]})
        assert len(result) == 2
        assert result[0].tool == "search_crs_objects"
        assert result[0].output == "search output"
        assert result[1].tool == "plot_geojson"
        assert result[1].output == self._GEOJSON_STR
