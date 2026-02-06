import os

import httpx
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pyproj import CRS, Transformer, aoi, database


@tool
def search_crs_by_area(area_name, object_type="all", filter_text=None):
    """
    Searches for CRS applicable to a given area.

    Parameters
    ----------
    area_name : str or pyproj.aoi.AreaOfInterest
        The name of the area or AreaOfInterest object to search for.
    object_type : str, optional
        The type of CRS or other database object to search for.
        Can be "all", "geographic", "projected", or other CRS types supported by pyproj.
        Defaults to "all".
    filter_text : str, optional
        A string of text to filter the results by, performing a case-insensitive
        search on the `area_of_use` attribute of each CRS. Defaults to None.

    Returns
    -------
    list
        A list of CRS objects that are applicable to the given area and CRS type.
    """

    if object_type == "all":
        crs_list = database.query_crs_info(area_of_interest=area_name, contains=False)
    else:
        crs_list = database.query_crs_info(
            area_of_interest=area_name, pj_types=object_type.upper(), contains=False
        )

    if filter_text:
        crs_list = [
            crs
            for crs in crs_list
            if filter_text.lower() in crs.area_of_use.name.lower()
        ]

    return crs_list


@tool
def get_bbox_by_area_name(area_name: str) -> aoi.AreaOfInterest:
    """Searches for a geographic area by name in Nominatim and returns the bounding box.

    Parameters
    ----------
    area_name : str
        The name of the geographic area to search for (e.g., "New York", "France", etc.).

    Returns
    -------
    pyproj.aoi.AreaOfInterest
        The bounding box of the area as an AreaOfInterest object.
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

    # Get the bounding box from the first result
    # Nominatim returns boundingbox as [south, north, west, east]
    result = results[0]
    if "boundingbox" not in result:
        raise ValueError(f"Bounding box information not available for '{area_name}'.")

    south, north, west, east = result["boundingbox"]

    # Create and return AreaOfInterest object
    # AreaOfInterest expects (west, south, east, north)
    return aoi.AreaOfInterest(
        west_lon_degree=float(west),
        south_lat_degree=float(south),
        east_lon_degree=float(east),
        north_lat_degree=float(north),
    )


@tool
def lookup_crs(epsg_code: str) -> str:
    """Look up CRS metadata using an EPSG code."""
    try:
        crs = CRS.from_epsg(int(epsg_code))
        return f"EPSG:{epsg_code} - {crs.name}\nDatum: {crs.datum.name}\nArea of use: {crs.area_of_use.name}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def transform_coordinates(query: str) -> str:
    """Transform coordinates between two EPSG codes. Format: x,y,from_epsg,to_epsg"""
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

tools = [lookup_crs, transform_coordinates, search_crs_by_area, get_bbox_by_area_name]

geodetic_agent = create_agent(
    tools=tools,
    model=llm,
    # agent_type="zero-shot-react-description",
    # verbose=True,
    system_prompt=(
        "You are a geodetic advisor. Use the provided tools to answer user queries."
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
        {"role": "user", "content": "Which are the local datums for Argentina?"}
    ]
})

print(response["messages"][2].content)
