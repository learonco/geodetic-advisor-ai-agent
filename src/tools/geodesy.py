import httpx

from langchain.tools import tool
from pydantic import BaseModel, Field

from pyproj import CRS, Transformer, aoi, database
from pyproj.enums import PJType

from src.exceptions import (
    AreaNotFoundError,
    CoordinateTransformError,
    EpsgLookupError,
    GeodeticAdvisorError,
    InvalidAreaNameError,
    InvalidCoordinateError,
    InvalidEpsgCodeError,
    InvalidQueryFormatError,
    NominatimConnectionError,
    NominatimError,
    NominatimHttpError,
    NominatimTimeoutError,
)
from src.models.geodesy import BoundingBox, CRSResult


# ---------------------------------------------------------------------------
# Tool input schemas
# ---------------------------------------------------------------------------

class SearchCrsObjectsInput(BaseModel):
    """Input schema for the search_crs_objects tool."""

    bbox: BoundingBox | None = Field(
        None,
        description="Geographic bounding box (west, south, east, north in decimal degrees).",
    )
    object_type: list[str] | None = Field(
        None,
        description=(
            "CRS type filter. Valid values: GEODETIC_REFERENCE_FRAME, PROJECTED_CRS, "
            "GEOGRAPHIC_CRS, VERTICAL_CRS, GEOGRAPHIC_2D_CRS, GEOGRAPHIC_3D_CRS, "
            "COMPOUND_CRS, ENGINEERING_CRS, BOUND_CRS, OTHER_CRS."
        ),
    )
    object_name: str | None = Field(None, description="Filter results by CRS name.")
    object_area_of_use: str | None = Field(None, description="Filter results by area of use name.")


class GetBboxFromAreanameInput(BaseModel):
    """Input schema for the get_bbox_from_areaname tool."""

    area_name: str = Field(description="Name of the geographic area (e.g. 'Madrid', 'Argentina').")


class LookupCrsInput(BaseModel):
    """Input schema for the lookup_crs tool."""

    epsg_code: str = Field(description="EPSG code to look up (e.g. '4326').")


class TransformCoordinatesInput(BaseModel):
    """Input schema for the transform_coordinates tool."""

    query: str = Field(
        description="Coordinates and EPSG codes: x,y,from_epsg,to_epsg (e.g. '-58.417,-34.611,4326,4937')."
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _crs_info_to_result(crs_info) -> CRSResult | None:
    """Convert a pyproj CRSInfo object to a CRSResult model.

    Args:
        crs_info: A pyproj CRSInfo named tuple.

    Returns:
        CRSResult instance, or None if conversion fails.
    """
    try:
        area_bbox = None
        if crs_info.area_of_use:
            try:
                area_bbox = BoundingBox(
                    west=crs_info.area_of_use.west_lon_degree,
                    south=crs_info.area_of_use.south_lat_degree,
                    east=crs_info.area_of_use.east_lon_degree,
                    north=crs_info.area_of_use.north_lat_degree,
                )
            except Exception:
                pass
        return CRSResult(
            epsg_code=crs_info.code,
            crs_name=crs_info.name,
            area_bbox=area_bbox,
        )
    except Exception:
        return None


@tool(args_schema=SearchCrsObjectsInput)
def search_crs_objects(
    bbox: BoundingBox | None = None,
    object_type: list[str] | None = None,
    object_name: str | None = None,
    object_area_of_use: str | None = None,
) -> list[CRSResult] | str:
    """Returns all applicable CRS objects for the given area of interest, including geographic,
    projected, vertical, and other types.
    Use this after getting bbox coordinates from get_bbox_from_areaname. The areaname can be used
    as filter_text to narrow down results.

    Args:
        bbox: Validated geographic bounding box (west, south, east, north).
        object_type: Optional CRS type filter strings (e.g. 'GEODETIC_REFERENCE_FRAME').
        object_name: Optional filter by CRS name.
        object_area_of_use: Optional filter by area of use name.

    Returns:
        List of CRSResult objects applicable to the given area, or an error string on failure.
    """
    try:
        aoi_bbox = None
        if bbox:
            aoi_bbox = aoi.AreaOfInterest(
                west_lon_degree=bbox.west,
                south_lat_degree=bbox.south,
                east_lon_degree=bbox.east,
                north_lat_degree=bbox.north,
            )

        pj_types = None
        if object_type:
            try:
                pj_types = [PJType[t] if isinstance(t, str) else t for t in object_type]
            except KeyError as exc:
                return f"Error: Invalid object_type value: {exc}"

        crs_list = database.query_crs_info(
            area_of_interest=aoi_bbox,
            pj_types=pj_types,
            contains=False,
            allow_deprecated=False,
        )

        if object_name or object_area_of_use:
            crs_list = [
                crs
                for crs in crs_list
                if (not object_name or object_name.lower() in crs.name.lower())
                and (not object_area_of_use or (
                    crs.area_of_use is not None
                    and object_area_of_use.lower() in crs.area_of_use.name.lower()
                ))
            ]

        results = [
            r for r in (_crs_info_to_result(crs) for crs in crs_list) if r is not None
        ]
        return results
    except GeodeticAdvisorError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


@tool(args_schema=GetBboxFromAreanameInput)
def get_bbox_from_areaname(area_name: str) -> dict | str:
    """Searches for a geographic area by name in Nominatim and returns the bounding box.

    Parameters:
        area_name : str
            The name of the geographic area to search for (e.g., "Madrid", "Argentina").

    Returns:
        dict
            A dictionary with keys: west, south, east, north, or an error string on failure.
    """
    try:
        if not area_name or not area_name.strip():
            raise InvalidAreaNameError(area_name)
    except GeodeticAdvisorError as e:
        return f"Error: {e}"

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": area_name,
        "format": "json",
        "limit": 1,
    }
    headers = {
        "User-Agent": "geodetic-advisor-ai-agent",
    }

    try:
        try:
            response = httpx.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
        except httpx.TimeoutException:
            raise NominatimTimeoutError(area_name)
        except httpx.HTTPStatusError as e:
            raise NominatimHttpError(area_name, status_code=e.response.status_code)
        except httpx.RequestError as e:
            raise NominatimConnectionError(area_name, cause=e)

        try:
            results = response.json()
        except Exception as e:
            raise NominatimError(area_name, detail=f"could not parse response — {e}")

        if not results:
            raise AreaNotFoundError(area_name)

        result = results[0]
        if "boundingbox" not in result:
            raise NominatimError(area_name, detail="bounding box information not available")

        try:
            south, north, west, east = result["boundingbox"]
            return {
                "west": float(west),
                "south": float(south),
                "east": float(east),
                "north": float(north)
            }
        except (ValueError, TypeError) as e:
            raise NominatimError(area_name, detail=f"could not parse bounding box values — {e}")
    except GeodeticAdvisorError as e:
        return f"Error: {e}"


@tool(args_schema=LookupCrsInput)
def lookup_crs(epsg_code: str) -> str:
    """Look up CRS metadata using an EPSG code.

    Parameters:
        epsg_code : str
            The EPSG code of the CRS to look up (e.g., "4326").
    Returns:
        str
            A string with the CRS metadata, or an error string on failure.
    """
    try:
        try:
            code = int(epsg_code)
        except (ValueError, TypeError):
            raise InvalidEpsgCodeError(epsg_code)

        if code <= 0:
            raise InvalidEpsgCodeError(epsg_code)

        try:
            crs = CRS.from_epsg(code)
        except Exception as e:
            raise EpsgLookupError(code, detail=str(e)) from e

        return f"EPSG:{epsg_code} - {crs.name}\nDatum: {crs.datum.name}\nArea of use: {crs.area_of_use.name}"
    except GeodeticAdvisorError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


@tool(args_schema=TransformCoordinatesInput)
def transform_coordinates(query: str) -> str:
    """Transform coordinates between two EPSG codes. Format: x,y,from_epsg,to_epsg

    Parameters:
        query : str
            The query string in the format "x,y,from_epsg,to_epsg". Example: "-58.417,-34.611,4326,4937"
    Returns:
        str
            A string with the transformed coordinates, or an error string on failure.
    """
    try:
        parts = [p.strip() for p in query.split(",")]
        if len(parts) < 4:
            raise InvalidQueryFormatError(query, expected="x,y,from_epsg,to_epsg")

        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            raise InvalidCoordinateError("x,y", f"{parts[0]},{parts[1]}")

        from_epsg, to_epsg = parts[2], parts[3]
        for label, code_str in (("from_epsg", from_epsg), ("to_epsg", to_epsg)):
            try:
                code_val = int(code_str)
            except (ValueError, TypeError):
                raise InvalidEpsgCodeError(code_str)
            if code_val <= 0:
                raise InvalidEpsgCodeError(code_str)

        try:
            transformer = Transformer.from_crs(
                f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True
            )
            x2, y2 = transformer.transform(x, y)
        except GeodeticAdvisorError:
            raise
        except Exception as e:
            raise CoordinateTransformError(from_epsg, to_epsg, detail=str(e)) from e

        return f"Transformed coordinates: ({x2:.6f}, {y2:.6f})"
    except GeodeticAdvisorError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"
