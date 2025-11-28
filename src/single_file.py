import os
from langchain.tools import tool
from pyproj import CRS, Transformer
from langchain.agents import initialize_agent
from langchain_google_genai import ChatGoogleGenerativeAI


def lookup_crs(epsg_code: str) -> str:
    try:
        crs = CRS.from_epsg(int(epsg_code))
        return f"EPSG:{epsg_code} - {crs.name}\nDatum: {crs.datum.name}\nArea of use: {crs.area_of_use.name}"
    except Exception as e:
        return f"Error: {str(e)}"

crs_lookup_tool = tool.from_function(
    name="CRS Lookup",
    description="Look up CRS metadata using an EPSG code",
    func=lookup_crs
)


def transform_coordinates(query: str) -> str:
    try:
        parts = query.split(",")
        x, y = float(parts[0]), float(parts[1])
        from_epsg, to_epsg = parts[2], parts[3]
        transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
        x2, y2 = transformer.transform(x, y)
        return f"Transformed coordinates: ({x2:.6f}, {y2:.6f})"
    except Exception as e:
        return f"Error: {str(e)}"

transform_tool = tool.from_function(
    name="Coordinate Transformer",
    description="Transform coordinates between two EPSG codes. Format: x,y,from_epsg,to_epsg",
    func=transform_coordinates
)



llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

tools = [crs_lookup_tool, transform_tool]

geodetic_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="zero-shot-react-description",
    verbose=True
)


response = geodetic_agent.run("What is EPSG:4326?")
print(response)

response = geodetic_agent.run("Transform -58.417,-34.611 from EPSG:4326 to EPSG:4937")
print(response)