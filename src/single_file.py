import os

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pyproj import CRS, Transformer


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
    model="models/gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

tools = [lookup_crs, transform_coordinates]

geodetic_agent = create_agent(
    tools=tools,
    model=llm,
    # agent_type="zero-shot-react-description",
    # verbose=True,
    system_prompt=(
        "You are a geodetic advisor. Use the provided tools to answer user queries."
    ),
)


response = geodetic_agent.invoke(
    {"messages": [{"role": "user", "content": "What is EPSG:4326?"}]}
)
print(response['messages'][2].content)

response = geodetic_agent.invoke(
    { "messages": [ { "role": "user", "content": "Transform -58.417,-34.611 from EPSG:4326 to EPSG:4937", } ] }
)
print(response['messages'][2].content)
