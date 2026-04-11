import httpx

from langchain.tools import tool

from pyproj import CRS, Transformer, aoi, database
from pyproj.enums import PJType


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
            try:
                aoi_bbox = aoi.AreaOfInterest(
                    west_lon_degree=float(bbox['west']),
                    south_lat_degree=float(bbox['south']),
                    east_lon_degree=float(bbox['east']),
                    north_lat_degree=float(bbox['north'])
                )
            except (TypeError, ValueError, KeyError) as e:
                return f"Error: invalid bbox values — {e}"

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
        response = httpx.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except httpx.TimeoutException:
        return f"Error: request to Nominatim timed out while searching for '{area_name}'."
    except httpx.HTTPStatusError as e:
        return f"Error: Nominatim returned HTTP {e.response.status_code} for '{area_name}'."
    except httpx.RequestError as e:
        return f"Error: network error while contacting Nominatim — {e}"

    try:
        results = response.json()
    except Exception as e:
        return f"Error: could not parse Nominatim response — {e}"

    if not results:
        return f"Error: area '{area_name}' not found in Nominatim."

    result = results[0]
    if "boundingbox" not in result:
        return f"Error: bounding box information not available for '{area_name}'."

    try:
        south, north, west, east = result["boundingbox"]
        return {
            "west": float(west),
            "south": float(south),
            "east": float(east),
            "north": float(north)
        }
    except (ValueError, TypeError) as e:
        return f"Error: could not parse bounding box values for '{area_name}' — {e}"


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
        code = int(epsg_code)
    except (ValueError, TypeError):
        return f"Error: '{epsg_code}' is not a valid integer EPSG code."

    try:
        crs = CRS.from_epsg(code)
        return f"EPSG:{epsg_code} - {crs.name}\nDatum: {crs.datum.name}\nArea of use: {crs.area_of_use.name}"
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
            return "Error: query must have format 'x,y,from_epsg,to_epsg' (e.g. '-58.4,-34.6,4326,3857')."

        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            return f"Error: coordinates '{parts[0]}' and '{parts[1]}' must be numeric values."

        from_epsg, to_epsg = parts[2], parts[3]
        transformer = Transformer.from_crs(
            f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True
        )
        x2, y2 = transformer.transform(x, y)
        return f"Transformed coordinates: ({x2:.6f}, {y2:.6f})"
    except Exception as e:
        return f"Error: {e}"
