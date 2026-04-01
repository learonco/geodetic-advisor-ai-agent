"""Unit tests for src/tools/geodesy.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestSearchCrsObjects:
    def test_returns_list_with_valid_bbox(self):
        from src.tools.geodesy import search_crs_objects

        bbox = {"north": -36.05, "west": -71.97, "south": -41.10, "east": -67.99}
        result = search_crs_objects.run({"bbox": bbox, "object_type": ["GEODETIC_REFERENCE_FRAME"]})
        assert isinstance(result, list)

    def test_returns_list_with_name_filter(self):
        from src.tools.geodesy import search_crs_objects

        bbox = {"north": -36.05, "west": -71.97, "south": -41.10, "east": -67.99}
        result = search_crs_objects.run({"bbox": bbox, "object_name": "WGS"})
        assert isinstance(result, list)

    def test_object_name_filter_narrows_results(self):
        from src.tools.geodesy import search_crs_objects

        bbox = {"north": 90.0, "west": -180.0, "south": -90.0, "east": 180.0}
        all_results = search_crs_objects.run({"bbox": bbox})
        filtered = search_crs_objects.run({"bbox": bbox, "object_name": "WGS 84"})
        assert isinstance(filtered, list)
        assert len(filtered) <= len(all_results)
        for item in filtered:
            assert "WGS 84" in item.name or "WGS84" in item.name.replace(" ", "")


class TestGetBboxFromAreaname:
    def test_returns_dict_with_cardinal_keys(self):
        """Mocks the Nominatim HTTP call; verifies return shape."""
        from src.tools.geodesy import get_bbox_from_areaname

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "boundingbox": ["-41.10", "-36.05", "-71.97", "-67.99"],
                "display_name": "Neuquén, Argentina",
            }
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            result = get_bbox_from_areaname.run({"area_name": "Neuquen"})

        assert isinstance(result, dict)
        for key in ("west", "south", "east", "north"):
            assert key in result
            assert isinstance(result[key], float)

    def test_raises_on_empty_nominatim_response(self):
        from src.tools.geodesy import get_bbox_from_areaname

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            with pytest.raises(ValueError, match="not found"):
                get_bbox_from_areaname.run({"area_name": "NonExistentPlace12345"})


class TestLookupCrs:
    def test_known_epsg_returns_metadata(self):
        from src.tools.geodesy import lookup_crs

        result = lookup_crs.run({"epsg_code": "4326"})
        assert "4326" in result
        assert "WGS 84" in result

    def test_invalid_epsg_returns_error_string(self):
        from src.tools.geodesy import lookup_crs

        result = lookup_crs.run({"epsg_code": "9999999"})
        assert result.startswith("Error:")


class TestTransformCoordinates:
    def test_identity_transform_returns_same_coords(self):
        from src.tools.geodesy import transform_coordinates

        result = transform_coordinates.run({"query": "0.0,0.0,4326,4326"})
        assert "0.000000" in result

    def test_valid_transform_wgs84_to_web_mercator(self):
        from src.tools.geodesy import transform_coordinates

        result = transform_coordinates.run({"query": "-58.417,-34.611,4326,3857"})
        assert "Transformed coordinates" in result

    def test_bad_input_returns_error_string(self):
        from src.tools.geodesy import transform_coordinates

        result = transform_coordinates.run({"query": "not,valid,input"})
        assert result.startswith("Error:")
