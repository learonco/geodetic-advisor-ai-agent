"""Main Streamlit app for Geodetic Advisor WebUI."""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from streamlit_folium import st_folium
import folium
from webui.chat_utils import (
    invoke_geodetic_agent,
    extract_tool_calls,
    detect_map_relevant_response,
    format_agent_response,
    format_message_for_display
)
from webui.map_utils import (
    create_base_map,
    add_bbox_rectangle,
    extract_coordinates_from_clicks,
    extract_bbox_from_geometry,
    parse_crs_search_results
)

# Suppress Streamlit warnings and prompts
os.environ["STREAMLIT_CLIENT_SHOWERRORDETAILS"] = "false"
os.environ["STREAMLIT_CLIENT_TOOLBARMODE"] = "minimal"


# Page configuration
st.set_page_config(
    page_title="Geodetic Advisor AI",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for layout
st.markdown("""
<style>
    .main {
        display: flex;
        flex-direction: row;
    }
    .chat-section {
        width: 35%;
        border-right: 2px solid #ddd;
        padding: 20px;
    }
    .map-section {
        width: 65%;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent_state" not in st.session_state:
    st.session_state.agent_state = {"last_bbox": None, "last_results": []}

if "map_data" not in st.session_state:
    st.session_state.map_data = {"bbox_points": []}

if "bbox_coordinates" not in st.session_state:
    st.session_state.bbox_coordinates = []

if "processed_drawings" not in st.session_state:
    st.session_state.processed_drawings = set()

if "selected_crs_types" not in st.session_state:
    st.session_state.selected_crs_types = ["All Types"]


# Title and description
st.title("🗺️ Geodetic Advisor AI")
st.markdown("""
Chat with an AI assistant about coordinate reference systems, map projections, and geodetic transformations.
Use the map on the right to interact with spatial data.
""")


# Create two columns
col_chat, col_map = st.columns([0.35, 0.65])


# ============================================================================
# LEFT COLUMN: CHAT INTERFACE
# ============================================================================
with col_chat:
    st.subheader("💬 Chat")

    # Display chat history
    chat_container = st.container()

    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            role = message["role"]
            content = message["content"]

            if role == "user":
                st.write(f"**You:** {content}")
            else:
                st.write(f"**Agent:** {content}")

            # Add a small divider
            st.divider()

    # Input area
    st.markdown("---")

    # User input
    user_input = st.text_input(
        "Ask a question about CRS, projections, or geodetic systems:",
        key="user_input_field",
        placeholder="e.g., 'Find CRS for Spain' or 'What projection is used in Brazil?'"
    )

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        send_btn = st.button("📤 Send", type="primary", use_container_width=True)

    with col_btn2:
        clear_btn = st.button("🗑️ Clear History", use_container_width=True)

    # Handle send button
    if send_btn and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })

        # Show loading indicator
        with st.spinner("Agent thinking..."):
            # Invoke agent
            result = invoke_geodetic_agent(
                query=user_input,
                chat_history=st.session_state.chat_history
            )

            if result["success"]:
                # Extract tool calls
                tool_calls = extract_tool_calls(result)

                # Format and add agent response to history
                agent_response = result["response"]
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": agent_response,
                    "tool_calls": tool_calls
                })

                # Check if response has map-relevant data
                map_detection = detect_map_relevant_response(agent_response, tool_calls)

                # Store in agent state for map interaction
                if map_detection["data_type"] == "bbox":
                    try:
                        # Parse bbox from tool output
                        import json
                        bbox_data = json.loads(map_detection["data"])
                        st.session_state.agent_state["last_bbox"] = bbox_data
                    except:
                        pass

                st.rerun()
            else:
                st.error(f"Error: {result['error']}")

    # Handle clear history button
    if clear_btn:
        st.session_state.chat_history = []
        st.session_state.agent_state = {"last_bbox": None, "last_results": []}
        st.rerun()

    # Display API status
    st.markdown("---")
    st.caption("✅ API Status: Connected")


# ============================================================================
# RIGHT COLUMN: MAP INTERFACE
# ============================================================================
with col_map:
    st.subheader("🗺️  Interactive Map")

    # Instructions
    st.info("💡 **How to use the map:**\n- Use the Draw tool (top-left) to draw a rectangle for CRS search\n- Click on markers to see CRS details")

    # CRS Type Filter
    st.markdown("**Filter CRS Types:**")
    crs_type_options = [
        "All Types",
        "Projected CRS",
        "Geographic CRS",
        "Vertical CRS",
        "Compound CRS",
        "Geodetic Reference Frame"
    ]

    selected_types = st.multiselect(
        "Select CRS types to include in search:",
        options=crs_type_options,
        default=["All Types"],
        key="crs_type_filter"
    )

    # Store in session state
    st.session_state.selected_crs_types = selected_types if selected_types else ["All Types"]

    # Create base map
    m = create_base_map(center=(20, 0), zoom=2)

    # Add last bbox if exists
    if st.session_state.agent_state.get("last_bbox"):
        bbox = st.session_state.agent_state["last_bbox"]
        m = add_bbox_rectangle(m, bbox, color='red')

    # Render map and get interaction data
    map_data = st_folium(m, width=700, height=600)

    # Process map interactions
    if map_data and "all_drawings" in map_data and map_data["all_drawings"]:
        drawings = map_data["all_drawings"]

        for idx, drawing in enumerate(drawings):
            # streamlit-folium returns rectangles as GeoJSON Features with Polygon geometry
            if drawing.get("type") == "Feature":
                geometry = drawing.get("geometry", {})

                # Check if it's a polygon (rectangle)
                if geometry.get("type") == "Polygon":
                    drawing_id = f"{idx}_{id(drawing)}"

                    if drawing_id not in st.session_state.processed_drawings:
                        try:
                            # Extract coordinates from polygon
                            coords = geometry.get("coordinates", [[]])[0]

                            if coords:
                                lons = [c[0] for c in coords]
                                lats = [c[1] for c in coords]

                                bbox = {
                                    "west": min(lons),
                                    "south": min(lats),
                                    "east": max(lons),
                                    "north": max(lats)
                                }

                                # Mark as processed
                                st.session_state.processed_drawings.add(drawing_id)

                                # Store bbox
                                st.session_state.agent_state["last_bbox"] = bbox

                                # Trigger agent query
                                bbox_str = f"[W:{bbox['west']:.2f}, S:{bbox['south']:.2f}, E:{bbox['east']:.2f}, N:{bbox['north']:.2f}]"

                                # Include selected CRS types in query
                                crs_types_str = ""
                                if st.session_state.selected_crs_types and st.session_state.selected_crs_types != ["All Types"]:
                                    types_list = ", ".join(st.session_state.selected_crs_types)
                                    crs_types_str = f" Filter by types: {types_list}."

                                query = f"Find CRS and projections applicable to area: {bbox_str}{crs_types_str}"

                                # Add to chat history
                                st.session_state.chat_history.append({
                                    "role": "user",
                                    "content": query
                                })

                                # Invoke agent
                                with st.spinner("Searching for CRS in selected area..."):
                                    result = invoke_geodetic_agent(
                                        query=query,
                                        chat_history=st.session_state.chat_history
                                    )

                                    if result["success"]:
                                        tool_calls = extract_tool_calls(result)
                                        agent_response = result["response"]

                                        st.session_state.chat_history.append({
                                            "role": "assistant",
                                            "content": agent_response,
                                            "tool_calls": tool_calls
                                        })
                                        st.rerun()
                                    else:
                                        st.error(f"Agent error: {result.get('error')}")
                        except Exception as e:
                            st.error(f"Error processing rectangle: {str(e)}")

    # Display map controls info
    st.caption("🎨 Use the drawing tools in the map to create search areas")


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px;">
    <p>Geodetic Advisor AI • Powered by LangChain + Google Gemini • Data from EPSG Registry</p>
</div>
""", unsafe_allow_html=True)
