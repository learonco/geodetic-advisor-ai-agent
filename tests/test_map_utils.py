"""Unit tests for webui/map_utils.py."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestMapUtils:
    def _get_module(self):
        import src.webui.map_utils as mu
        return mu

    def test_create_base_map_returns_folium_map(self):
        import folium
        mu = self._get_module()
        m = mu.create_base_map()
        assert isinstance(m, folium.Map)

    def test_add_bbox_rectangle_returns_map(self):
        import folium
        mu = self._get_module()
        m = mu.create_base_map()
        bbox = {"west": -71.97, "south": -41.10, "east": -67.99, "north": -36.05}
        m2 = mu.add_bbox_rectangle(m, bbox)
        assert isinstance(m2, folium.Map)

    def test_extract_bbox_from_geometry_rectangle(self):
        mu = self._get_module()
        # map_utils.extract_bbox_from_geometry handles 'Rectangle' GeoJSON type
        geometry = {
            "type": "Rectangle",
            "coordinates": [[
                [-71.97, -41.10],
                [-71.97, -36.05],
                [-67.99, -36.05],
                [-67.99, -41.10],
                [-71.97, -41.10],
            ]],
        }
        bbox = mu.extract_bbox_from_geometry(geometry)
        assert bbox is not None
        assert abs(bbox["west"] - (-71.97)) < 0.01
        assert abs(bbox["east"] - (-67.99)) < 0.01

    def test_parse_crs_search_results_extracts_epsg(self):
        mu = self._get_module()
        text = "Found CRS: EPSG:4326, EPSG:3857"
        codes = mu.parse_crs_search_results(text)
        assert "4326" in codes or "EPSG:4326" in str(codes)
