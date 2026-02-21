import os
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from tools import (
    get_bbox_from_areaname,
    lookup_crs,
    search_crs_objects,
    transform_coordinates,
)

llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

tools = [lookup_crs, transform_coordinates, get_bbox_from_areaname, search_crs_objects]

geodetic_agent = create_agent(
    tools=tools,
    model=llm,
    debug=False,
    system_prompt=(
        """You are a geodetic advisor, with deep knowledge of geodesy, cartography, and geospatial positioning.
        Use the EPSG Geodetic Parameter Registry and the provided tools to answer questions about coordinate reference systems, transformations, and geodetic metadata.

        Example:
        - If the user ask for a any CRS or other geodetic object by a specific area,
            irst use get_bbox_from_areaname to get the bounding box,
            then use search_crs_objects to find applicable CRS objects for that area.
        - If the user ask for a any CRS or other geodetic object by its name,
            use search_crs_objects and use the name provided in the object_name parameter.
        - If the user ask for a any CRS or other geodetic object by its area of use,
            then use search_crs_objects using the text provided in the object_area_of_use parameter;
            optionally use the bounding box as well to narrow down results using function get_bbox_from_areaname to get the bounding box
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
         "content": "List the names of the applicable datums for Neuquen."}
    ]
})

# response = geodetic_agent.invoke({
#     "messages": [
#         {"role": "user",
#          "content": "Get me the details of the datum Campo Inchauspe."}
#     ]
# })

print(response["messages"])
