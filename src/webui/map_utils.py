"""Map utilities for pydeck visualization."""

from typing import Optional

import pydeck as pdk

from src.models.geodesy import BoundingBox, CRSResult

# Default world-view when no bbox is provided
_DEFAULT_VIEW = pdk.ViewState(latitude=20, longitude=0, zoom=1, pitch=0)

_POLYGON_FILL_COLOR = [100, 149, 237, 120]   # cornflower-blue, semi-transparent
_POLYGON_LINE_COLOR = [70, 105, 200, 200]
_MARKER_COLOR = [220, 50, 50, 200]           # red markers
_GEOJSON_FILL_COLOR = [255, 165, 0, 150]     # orange, semi-transparent
_GEOJSON_LINE_COLOR = [255, 140, 0, 230]


def build_crs_polygon_layer(results: list[CRSResult]) -> pdk.Layer:
    """Build a PolygonLayer showing CRS area-of-use extents.

    Args:
        results: List of CRSResult objects to display.

    Returns:
        A pydeck Layer of type PolygonLayer.
    """
    data = []
    for r in results:
        if r.area_bbox is None:
            continue
        b = r.area_bbox
        # Closed polygon ring: 5 points (SW, SE, NE, NW, SW)
        polygon = [
            [b.west, b.south],
            [b.east, b.south],
            [b.east, b.north],
            [b.west, b.north],
            [b.west, b.south],
        ]
        data.append({
            "epsg_code": r.epsg_code,
            "crs_name": r.crs_name,
            "polygon": polygon,
            "properties": {"epsg_code": r.epsg_code, "crs_name": r.crs_name},
        })

    return pdk.Layer(
        "PolygonLayer",
        data=data,
        get_polygon="polygon",
        get_fill_color=_POLYGON_FILL_COLOR,
        get_line_color=_POLYGON_LINE_COLOR,
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )


def build_crs_marker_layer(results: list[CRSResult]) -> pdk.Layer:
    """Build a ScatterplotLayer placing a marker at each CRS centroid.

    Results without a bounding box get a marker at [0, 0].

    Args:
        results: List of CRSResult objects to display.

    Returns:
        A pydeck Layer of type ScatterplotLayer.
    """
    data = []
    for r in results:
        if r.area_bbox is not None:
            b = r.area_bbox
            lon = (b.west + b.east) / 2
            lat = (b.south + b.north) / 2
        else:
            lon, lat = 0.0, 0.0
        data.append({
            "epsg_code": r.epsg_code,
            "crs_name": r.crs_name,
            "lon": lon,
            "lat": lat,
            "properties": {"epsg_code": r.epsg_code, "crs_name": r.crs_name},
        })

    return pdk.Layer(
        "ScatterplotLayer",
        data=data,
        get_position=["lon", "lat"],
        get_color=_MARKER_COLOR,
        get_radius=150_000,
        radius_min_pixels=4,
        radius_max_pixels=16,
        pickable=True,
        auto_highlight=True,
    )


def build_geojson_layer(geojson_dict: dict) -> pdk.Layer:
    """Build a GeoJsonLayer from a GeoJSON dict.

    Args:
        geojson_dict: A parsed GeoJSON object (any RFC 7946 type).

    Returns:
        A pydeck Layer of type GeoJsonLayer.
    """
    return pdk.Layer(
        "GeoJsonLayer",
        data=geojson_dict,
        filled=True,
        stroked=True,
        get_fill_color=_GEOJSON_FILL_COLOR,
        get_line_color=_GEOJSON_LINE_COLOR,
        line_width_min_pixels=2,
        pickable=True,
        auto_highlight=True,
    )


def render_map(
    results: list[CRSResult],
    bbox: Optional[BoundingBox],
    geojson: Optional[dict] = None,
) -> pdk.Deck:
    """Render a pydeck Deck with CRS polygons and markers.

    If *bbox* is provided the initial view is centred on it; otherwise the
    view defaults to a world-level overview.

    Args:
        results: CRS results to visualise.
        bbox: Optional bounding box to centre the view on.
        geojson: Optional parsed GeoJSON dict to overlay as a GeoJsonLayer.

    Returns:
        A pdk.Deck ready to pass to ``st.pydeck_chart``.
    """
    if bbox is not None:
        view = pdk.ViewState(
            latitude=(bbox.south + bbox.north) / 2,
            longitude=(bbox.west + bbox.east) / 2,
            zoom=4,
            pitch=0,
        )
    else:
        view = _DEFAULT_VIEW

    polygon_layer = build_crs_polygon_layer(results)
    marker_layer = build_crs_marker_layer(results)
    layers = [polygon_layer, marker_layer]
    if geojson is not None:
        layers.append(build_geojson_layer(geojson))

    return pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style="dark",
        tooltip={
            "text": "Authority Code: EPSG:{epsg_code}\nCRS Name: {crs_name}",
        },
    )

