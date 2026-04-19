"""Unit tests for webui/map_utils.py (pydeck-based)."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.geodesy import BoundingBox, CRSResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(
    epsg: str, name: str, west: float, south: float, east: float, north: float
) -> CRSResult:
    return CRSResult(
        epsg_code=epsg,
        crs_name=name,
        area_bbox=BoundingBox(west=west, south=south, east=east, north=north),
    )


def _make_result_no_bbox(epsg: str, name: str) -> CRSResult:
    return CRSResult(epsg_code=epsg, crs_name=name, area_bbox=None)


# ---------------------------------------------------------------------------
# build_crs_polygon_layer
# ---------------------------------------------------------------------------

class TestBuildCrsPolygonLayer:
    def test_returns_pydeck_layer(self):
        import pydeck as pdk
        from src.webui.map_utils import build_crs_polygon_layer

        results = [_make_result("4326", "WGS 84", -180, -90, 180, 90)]
        layer = build_crs_polygon_layer(results)
        assert isinstance(layer, pdk.Layer)

    def test_layer_type_is_polygon(self):
        from src.webui.map_utils import build_crs_polygon_layer

        results = [_make_result("4326", "WGS 84", -180, -90, 180, 90)]
        layer = build_crs_polygon_layer(results)
        assert "Polygon" in layer.type

    def test_empty_results_returns_layer(self):
        import pydeck as pdk
        from src.webui.map_utils import build_crs_polygon_layer

        layer = build_crs_polygon_layer([])
        assert isinstance(layer, pdk.Layer)

    def test_results_without_bbox_skipped(self):
        import pydeck as pdk
        from src.webui.map_utils import build_crs_polygon_layer

        results = [_make_result_no_bbox("4326", "WGS 84")]
        layer = build_crs_polygon_layer(results)
        assert isinstance(layer, pdk.Layer)
        assert layer.data == [] or len(layer.data) == 0

    def test_multiple_results_all_included(self):
        from src.webui.map_utils import build_crs_polygon_layer

        results = [
            _make_result("4326", "WGS 84", -180, -90, 180, 90),
            _make_result("3857", "Web Mercator", -180, -85, 180, 85),
        ]
        layer = build_crs_polygon_layer(results)
        assert len(layer.data) == 2

    def test_layer_data_has_epsg_field(self):
        from src.webui.map_utils import build_crs_polygon_layer

        results = [_make_result("4326", "WGS 84", -180, -90, 180, 90)]
        layer = build_crs_polygon_layer(results)
        assert layer.data[0]["epsg_code"] == "4326"

    def test_layer_data_has_polygon_coords(self):
        from src.webui.map_utils import build_crs_polygon_layer

        results = [_make_result("4326", "WGS 84", -10, -10, 10, 10)]
        layer = build_crs_polygon_layer(results)
        assert "polygon" in layer.data[0]
        assert len(layer.data[0]["polygon"]) == 5  # closed ring


# ---------------------------------------------------------------------------
# build_crs_marker_layer
# ---------------------------------------------------------------------------

class TestBuildCrsMarkerLayer:
    def test_returns_pydeck_layer(self):
        import pydeck as pdk
        from src.webui.map_utils import build_crs_marker_layer

        results = [_make_result("4326", "WGS 84", -180, -90, 180, 90)]
        layer = build_crs_marker_layer(results)
        assert isinstance(layer, pdk.Layer)

    def test_layer_type_is_scatterplot(self):
        from src.webui.map_utils import build_crs_marker_layer

        results = [_make_result("4326", "WGS 84", -180, -90, 180, 90)]
        layer = build_crs_marker_layer(results)
        assert "Scatterplot" in layer.type

    def test_empty_results_returns_layer(self):
        import pydeck as pdk
        from src.webui.map_utils import build_crs_marker_layer

        layer = build_crs_marker_layer([])
        assert isinstance(layer, pdk.Layer)

    def test_results_without_bbox_still_included(self):
        from src.webui.map_utils import build_crs_marker_layer

        results = [_make_result_no_bbox("4326", "WGS 84")]
        layer = build_crs_marker_layer(results)
        # Results without bbox get centroid at [0, 0]
        assert len(layer.data) == 1

    def test_centroid_computed_correctly(self):
        from src.webui.map_utils import build_crs_marker_layer

        results = [_make_result("4326", "WGS 84", -10, -20, 10, 20)]
        layer = build_crs_marker_layer(results)
        assert layer.data[0]["lon"] == pytest.approx(0.0)
        assert layer.data[0]["lat"] == pytest.approx(0.0)

    def test_layer_data_has_name_field(self):
        from src.webui.map_utils import build_crs_marker_layer

        results = [_make_result("4326", "WGS 84", -180, -90, 180, 90)]
        layer = build_crs_marker_layer(results)
        assert layer.data[0]["crs_name"] == "WGS 84"


# ---------------------------------------------------------------------------
# render_map
# ---------------------------------------------------------------------------

class TestRenderMap:
    def test_returns_pydeck_deck(self):
        import pydeck as pdk
        from src.webui.map_utils import render_map

        deck = render_map([], None)
        assert isinstance(deck, pdk.Deck)

    def test_with_results_returns_deck(self):
        import pydeck as pdk
        from src.webui.map_utils import render_map

        results = [_make_result("4326", "WGS 84", -180, -90, 180, 90)]
        deck = render_map(results, None)
        assert isinstance(deck, pdk.Deck)

    def test_with_bbox_centers_view(self):
        import pydeck as pdk
        from src.webui.map_utils import render_map

        bbox = BoundingBox(west=-10, south=-20, east=10, north=20)
        deck = render_map([], bbox)
        assert isinstance(deck, pdk.Deck)
        assert deck.initial_view_state.longitude == pytest.approx(0.0)
        assert deck.initial_view_state.latitude == pytest.approx(0.0)

    def test_without_bbox_uses_world_view(self):
        import pydeck as pdk
        from src.webui.map_utils import render_map

        deck = render_map([], None)
        assert isinstance(deck, pdk.Deck)
        # Default world view zoom ~2
        assert deck.initial_view_state.zoom == pytest.approx(2, abs=1)

    def test_deck_has_two_layers(self):
        from src.webui.map_utils import render_map

        results = [_make_result("4326", "WGS 84", -180, -90, 180, 90)]
        deck = render_map(results, None)
        # Polygon layer + Scatterplot layer
        assert len(deck.layers) == 2

    def test_tooltip_defined(self):
        from src.webui.map_utils import render_map

        deck = render_map([], None)
        # pydeck stores tooltip as _tooltip internally
        assert deck._tooltip is not None
