"""Main Streamlit app for Geodetic Advisor WebUI."""

import os
import sys
from pathlib import Path

# Add the project root to Python path BEFORE importing modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from src.webui.chat_utils import (
    detect_map_relevant_response,
    invoke_geodetic_agent,
    format_crs_results,
    parse_agent_results,
)
from src.webui.map_utils import render_map

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
    * {
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stHeader"] {
        display: none;
    }
    [data-testid="stMainBlockContainer"] {
        padding: 16px 32px 32px 32px !important;
        margin: 0 !important;
    }
    [data-testid="stVerticalBlock"] {
        padding: 0 !important;
        margin: 0 !important;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    [data-testid="stColumn"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    p, span, div {
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    section {
        padding: 0 !important;
        margin: 0 !important;
    }
    div[data-testid="stForm"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    .main {
        display: flex;
        flex-direction: row;
        margin: 0 !important;
        padding: 0 !important;
        gap: 5px;
    }
    [data-testid="stColumns"] > [data-testid="column"]:nth-child(1) {
        border-right: 2px solid #ddd;
        height: 640px;
        overflow-y: auto;
        max-width: 100%;
    }
    [data-testid="stColumns"] > [data-testid="column"]:nth-child(1) [data-testid="stVerticalBlock"] {
        max-width: 100%;
        width: 100%;
    }
    [data-testid="stColumns"] > [data-testid="column"]:nth-child(1) p,
    [data-testid="stColumns"] > [data-testid="column"]:nth-child(1) span {
        max-width: 100%;
        word-break: break-word;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent_state" not in st.session_state:
    st.session_state.agent_state = {"last_bbox": None, "last_results": []}


# Title and description
st.title("🗺️ Geodetic Advisor AI")
st.markdown("""
Chat with an AI assistant about coordinate reference systems, map projections, and geodetic transformations.
Use the map on the right to interact with spatial data.
""")


# Create two columns
col_chat, col_map = st.columns([0.5, 0.5])


# ============================================================================
# LEFT COLUMN: CHAT INTERFACE
# ============================================================================
with col_chat:
    st.subheader("Chat")

    # Display chat history
    chat_container = st.container()

    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            role = message["role"]
            content = message["content"]

            if role == "user":
                st.write(f"**You:** {content}")
            else:
                formatted_content = format_crs_results(content)
                st.write(f"**Agent:** {formatted_content}")

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

            if result.success:
                # Extract tool calls
                tool_calls = result.tool_calls

                # Format and add agent response to history
                agent_response = result.response
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": agent_response,
                    "tool_calls": tool_calls
                })

                # Check if response has map-relevant data
                map_detection = detect_map_relevant_response(agent_response, tool_calls)

                # Store results for map rendering
                if map_detection.get("has_results"):
                    crs_results = parse_agent_results(agent_response, [tc.__dict__ for tc in tool_calls])
                    if crs_results:
                        st.session_state.agent_state["last_results"] = crs_results

                if map_detection["data_type"] == "bbox":
                    try:
                        import json
                        bbox_data = json.loads(map_detection["data"])
                        st.session_state.agent_state["last_bbox"] = bbox_data
                    except (TypeError, ValueError, json.JSONDecodeError):
                        pass

                st.rerun()
            else:
                st.error(f"Error: {result.error}")

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
    st.subheader("🗺️ Map View")

    last_results = st.session_state.agent_state.get("last_results", [])
    last_bbox = st.session_state.agent_state.get("last_bbox")

    from src.models.geodesy import BoundingBox
    bbox_model: BoundingBox | None = None
    if last_bbox and isinstance(last_bbox, dict):
        try:
            bbox_model = BoundingBox(**last_bbox)
        except Exception:
            bbox_model = None

    deck = render_map(last_results, bbox_model)
    st.pydeck_chart(deck, use_container_width=True)

    if last_results:
        st.caption(f"Showing {len(last_results)} CRS result(s). Hover polygons for details.")
    else:
        st.caption("Ask the agent about a location to see CRS areas on the map.")


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px;">
    <p>Geodetic Advisor AI • Powered by LangChain + Google Gemini • Data from EPSG Registry</p>
</div>
""", unsafe_allow_html=True)
