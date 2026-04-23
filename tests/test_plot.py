"""Unit tests for src/tools/plot.py."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


_FEATURE_COLLECTION = json.dumps({
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-65.0, -40.0],
                    [-60.0, -40.0],
                    [-60.0, -35.0],
                    [-65.0, -35.0],
                    [-65.0, -40.0],
                ]],
            },
            "properties": {"name": "POSGAR 2007 area"},
        }
    ],
})

_POLYGON_GEOMETRY = json.dumps({
    "type": "Polygon",
    "coordinates": [[
        [-65.0, -40.0],
        [-60.0, -40.0],
        [-60.0, -35.0],
        [-65.0, -35.0],
        [-65.0, -40.0],
    ]],
})

_POINT_GEOMETRY = json.dumps({
    "type": "Point",
    "coordinates": [-64.0, -38.0],
})

_FEATURE = json.dumps({
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [-64.0, -38.0],
    },
    "properties": {"name": "Buenos Aires"},
})


class TestPlotGeoJson:
    def test_valid_feature_collection_returns_geojson_string(self):
        from src.tools.plot import plot_geojson

        result = plot_geojson.run({"geojson": _FEATURE_COLLECTION})
        assert result == _FEATURE_COLLECTION

    def test_valid_polygon_geometry_returns_geojson_string(self):
        from src.tools.plot import plot_geojson

        result = plot_geojson.run({"geojson": _POLYGON_GEOMETRY})
        assert result == _POLYGON_GEOMETRY

    def test_valid_point_geometry_returns_geojson_string(self):
        from src.tools.plot import plot_geojson

        result = plot_geojson.run({"geojson": _POINT_GEOMETRY})
        assert result == _POINT_GEOMETRY

    def test_valid_feature_returns_geojson_string(self):
        from src.tools.plot import plot_geojson

        result = plot_geojson.run({"geojson": _FEATURE})
        assert result == _FEATURE

    def test_invalid_json_returns_error_string(self):
        from src.tools.plot import plot_geojson

        result = plot_geojson.run({"geojson": "not valid json {"})
        assert result.startswith("Error:")

    def test_valid_json_missing_type_returns_error_string(self):
        from src.tools.plot import plot_geojson

        result = plot_geojson.run({"geojson": '{"coordinates": [0, 0]}'})
        assert result.startswith("Error:")

    def test_unknown_geojson_type_returns_error_string(self):
        from src.tools.plot import plot_geojson

        result = plot_geojson.run({"geojson": '{"type": "Rectangle", "coordinates": []}'})
        assert result.startswith("Error:")

    def test_tool_has_run_method(self):
        from src.tools.plot import plot_geojson

        assert hasattr(plot_geojson, "run")
        assert callable(plot_geojson.run)
