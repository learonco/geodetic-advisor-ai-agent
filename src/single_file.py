import os

import httpx
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pyproj import CRS, Transformer, aoi, database
from pyproj.enums import PJType


@tool
def search_crs_by_bbox(bbox: dict,
                       object_type: PJType | list[PJType] | None=None,
                       filter_text: str=None) -> list:
    """Returns all applicable CRS objects for the given area of interest, including geographic,
    projected, vertical, and other types.
    Use this after getting bbox coordinates from get_bbox_from_areaname. The areaname can be user as filter_text to narrow down results.

    Parameters:
        bbox: dict
            A dictionary object representing the geographic area with keys: west, south, east, north.
        object_type : pyproj.enums.PJType or list[pyproj.enums.PJType] or None
            Optional filter for specific CRS types. Defaults to None.
        filter_text : str, optional
            A string to filter results by area name. Defaults to None.

    Returns:
        list
            A list of CRS objects applicable to the given area.
    """
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

    if filter_text:
        crs_list = [
            crs
            for crs in crs_list
            if filter_text.lower() in crs.area_of_use.name.lower()
        ]

    return crs_list


@tool
def get_bbox_from_areaname(area_name: str) -> dict:
    """Searches for a geographic area by name in Nominatim and returns the bounding box.

    Parameters:
        area_name : str
            The name of the geographic area to search for (e.g., "Madrid", "Argentina").

    Returns:
        dict
            A dictionary with keys: west, south, east, north.
    """
    # Query Nominatim API
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": area_name,
        "format": "json",
        "limit": 1,
    }
    headers = {
        "User-Agent": "geodetic-advisor-ai-agent",
    }

    response = httpx.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    results = response.json()
    if not results:
        raise ValueError(f"Area '{area_name}' not found in Nominatim.")

    # Nominatim returns boundingbox as [south, north, west, east]
    result = results[0]
    if "boundingbox" not in result:
        raise ValueError(f"Bounding box information not available for '{area_name}'.")

    south, north, west, east = result["boundingbox"]

    # Return as dictionary for better LLM handling
    return {
        "west": float(west),
        "south": float(south),
        "east": float(east),
        "north": float(north)
    }


@tool
def lookup_crs(epsg_code: str) -> str:
    """Look up CRS metadata using an EPSG code.

    Parameters:
        epsg_code : str
            The EPSG code of the CRS to look up (e.g., "4326").
    Returns:
        str
            A string with the CRS metadata.
    """
    try:
        crs = CRS.from_epsg(int(epsg_code))
        return f"EPSG:{epsg_code} - {crs.name}\nDatum: {crs.datum.name}\nArea of use: {crs.area_of_use.name}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def transform_coordinates(query: str) -> str:
    """Transform coordinates between two EPSG codes. Format: x,y,from_epsg,to_epsg

    Parameters:
        query : str
            The query string in the format "x,y,from_epsg,to_epsg". Example: "-58.417,-34.611,4326,4937"
    Returns:
        str
            A string with the transformed coordinates.
    """
    try:
        parts = query.split(",")
        x, y = float(parts[0]), float(parts[1])
        from_epsg, to_epsg = parts[2], parts[3]
        transformer = Transformer.from_crs(
            f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True
        )
        x2, y2 = transformer.transform(x, y)
        return f"Transformed coordinates: ({x2:.6f}, {y2:.6f})"
    except Exception as e:
        return f"Error: {str(e)}"


llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

tools = [lookup_crs, transform_coordinates, get_bbox_from_areaname, search_crs_by_bbox]

geodetic_agent = create_agent(
    tools=tools,
    model=llm,
    debug=False,
    system_prompt=(
        """You are a geodetic advisor, with deep knowledge of geodesy, cartography, and geospatial positioning.
        Use the EPSG Geodetic Parameter Registry and the provided tools to answer questions about coordinate reference systems, transformations, and geodetic metadata.

        Example:
        - If the user ask for a CRS or other geodetic object related to a specific area, first use get_bbox_from_areaname to get the bounding box, then use search_crs_by_bbox to find applicable CRS objects for that area.
        - If the user ask for a specific EPSG code, use lookup_crs to get its metadata.
        - If the user ask for coordinate transformation, use transform_coordinates with the format x,y,from_epsg,to_epsg.
        """
    ),
)


# response = geodetic_agent.invoke(
#     {"messages": [{"role": "user", "content": "What is EPSG:4326?"}]}
# )
# print(response['messages'][2].content)

# response = geodetic_agent.invoke(
#     { "messages": [ { "role": "user", "content": "Transform -58.417,-34.611 from EPSG:4326 to EPSG:4937" } ] }
# )
# print(response['messages'][2].content)

response = geodetic_agent.invoke({
    "messages": [
        {"role": "user",
         "content": "Create a list of all the applicable geodetic reference frames for Argentina."}
    ]
})

print(response["messages"])
