import httpx

from langchain.tools import tool

from pyproj import CRS, Transformer, aoi, database
from pyproj.enums import PJType

from src.exceptions import (
    CoordinateTransformError,
    CrsSearchError,
    EpsgLookupError,
    GeodeticAdvisorError,
    InvalidBboxError,
    InvalidCoordinateError,
    InvalidEpsgCodeError,
    InvalidQueryFormatError,
    NominatimConnectionError,
    NominatimError,
    NominatimHttpError,
    NominatimTimeoutError,
    AreaNotFoundError,
)


@tool
def search_crs_objects(bbox: dict=None,
                       object_type: PJType | list[PJType] | None=None,
                       object_name: str=None,
                       object_area_of_use: str=None) -> list | str:
    """Returns all applicable CRS objects for the given area of interest, including geographic,
    projected, vertical, and other types.
    Use this after getting bbox coordinates from get_bbox_from_areaname. The areaname can be user as filter_text to narrow down results.

    Parameters:
        bbox: dict
            A dictionary object representing the geographic area with keys: west, south, east, north.
        object_type : pyproj.enums.PJType or list[pyproj.enums.PJType] or None
            Optional filter for specific CRS types. Defaults to None.
        object_name : str, optional
            A string to filter results by CRS name. Defaults to None.
        object_area_of_use : str, optional
            A string to filter results by area of use. Defaults to None.

    Returns:
        list
            A list of CRS objects applicable to the given area, or an error string on failure.
    """
    try:
        aoi_bbox = None
        if bbox:
            for field in ('west', 'south', 'east', 'north'):
                if field not in bbox:
                    raise InvalidBboxError(field, None)
                try:
                    float(bbox[field])
                except (TypeError, ValueError):
                    raise InvalidBboxError(field, bbox[field])
            aoi_bbox = aoi.AreaOfInterest(
                west_lon_degree=float(bbox['west']),
                south_lat_degree=float(bbox['south']),
                east_lon_degree=float(bbox['east']),
                north_lat_degree=float(bbox['north'])
            )

        crs_list = database.query_crs_info(
            area_of_interest=aoi_bbox,
            pj_types=object_type,
            contains=False,
            allow_deprecated=False
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

        return crs_list
    except GeodeticAdvisorError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_bbox_from_areaname(area_name: str) -> dict | str:
    """Searches for a geographic area by name in Nominatim and returns the bounding box.

    Parameters:
        area_name : str
            The name of the geographic area to search for (e.g., "Madrid", "Argentina").

    Returns:
        dict
            A dictionary with keys: west, south, east, north, or an error string on failure.
    """
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


@tool
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

        try:
            crs = CRS.from_epsg(code)
        except Exception as e:
            raise EpsgLookupError(code, detail=str(e)) from e

        return f"EPSG:{epsg_code} - {crs.name}\nDatum: {crs.datum.name}\nArea of use: {crs.area_of_use.name}"
    except GeodeticAdvisorError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


@tool
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
