"""Plotting tools for map visualization."""

from typing import Union

from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Geometry
from langchain.tools import tool
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

# ---------------------------------------------------------------------------
# GeoJSON type adapter — built once at module level for efficiency.
# Covers all RFC 7946 top-level types: Feature, FeatureCollection, and all
# seven geometry types (via the Geometry union).
# ---------------------------------------------------------------------------

_GeoJSON = Union[Feature, FeatureCollection, Geometry]
_adapter: TypeAdapter = TypeAdapter(_GeoJSON)


# ---------------------------------------------------------------------------
# Tool input schema
# ---------------------------------------------------------------------------

class PlotGeoJsonInput(BaseModel):
    """Input schema for the plot_geojson tool."""

    geojson: str = Field(
        description=(
            "A valid GeoJSON string (RFC 7946). Supported top-level types: "
            "Feature, FeatureCollection, Point, MultiPoint, LineString, "
            "MultiLineString, Polygon, MultiPolygon, GeometryCollection."
        )
    )


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

@tool(args_schema=PlotGeoJsonInput)
def plot_geojson(geojson: str) -> str:
    """Plot a GeoJSON object on the map.

    Use this tool when the user asks to visualise or show a geographic area,
    boundary, or geometry on the map. Construct a valid GeoJSON string from
    the available data (e.g. area-of-use bounding box from lookup_crs or
    search_crs_objects) and pass it here.

    Args:
        geojson: A valid GeoJSON string (RFC 7946).

    Returns:
        The original GeoJSON string if valid, or an error string prefixed
        with "Error:" if the input cannot be parsed or fails validation.
    """
    try:
        _adapter.validate_json(geojson)
    except ValidationError as e:
        return f"Error: {e}"
    return geojson
