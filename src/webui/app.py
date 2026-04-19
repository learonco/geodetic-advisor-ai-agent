"""Main Streamlit app for Geodetic Advisor WebUI."""

import json
import os
import sys
from pathlib import Path

# Add the project root to Python path BEFORE importing modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st  # noqa: E402

from src.models.geodesy import BoundingBox  # noqa: E402
from src.webui.chat_utils import (  # noqa: E402
    detect_map_relevant_response,
    invoke_geodetic_agent,
    format_crs_results,
    parse_agent_results,
)
from src.webui.map_utils import render_map  # noqa: E402

# Suppress Streamlit prompts
os.environ["STREAMLIT_CLIENT_SHOWERRORDETAILS"] = "false"
os.environ["STREAMLIT_CLIENT_TOOLBARMODE"] = "minimal"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Geodetic Advisor",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS — maximize usable space, hide Streamlit chrome
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Collapse the header bar to near-zero height but keep sidebar toggle visible */
[data-testid="stHeader"] {
    height: 2rem !important;
    min-height: 0 !important;
    background: transparent !important;
}
/* Hide decorative line at very top */
[data-testid="stDecoration"] { display: none !important; }
/* Hide the toolbar (hamburger / "..." menu) — not the sidebar button */
[data-testid="stToolbar"]    { display: none !important; }
/* Sidebar toggle stays rendered inside stHeader — do NOT hide it */

/* Hide Streamlit footer */
footer { display: none !important; }

/* Shrink all main container padding to 10 px */
[data-testid="stMainBlockContainer"] {
    padding: 10px !important;
}

/* Remove the gap between columns */
[data-testid="stColumns"] {
    gap: 10px !important;
}

/* Remove inner column padding */
[data-testid="stColumn"] {
    padding: 0 !important;
}

/* Make pydeck chart iframe fill declared height */
[data-testid="stDeckGlJsonChart"],
[data-testid="stDeckGlJsonChart"] iframe {
    height: calc(100vh - 100px) !important;
    min-height: 400px;
}

/* Make the scrollable chat-history container fill column height */
[data-testid="stVerticalBlockBorderWrapper"] > div:first-child {
    height: calc(100vh - 180px) !important;
    min-height: 300px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🗺️ Geodetic Advisor")
    st.caption("Powered by LangChain + Google Gemini")
    st.divider()
    st.markdown(
        "Chat with an AI assistant about **coordinate reference systems**, "
        "map projections, and geodetic transformations."
    )
    st.divider()

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if api_key:
        st.success("✅ API key detected")
    else:
        st.warning("⚠️ No API key found. Set `GOOGLE_API_KEY` in your environment.")

    st.divider()
    st.caption("Data: EPSG Registry via pyproj")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []          # list[dict] role/content for display

if "agent_state" not in st.session_state:
    st.session_state.agent_state = {"last_bbox": None, "last_results": []}

# ---------------------------------------------------------------------------
# Layout: map left (55 %) | chat right (45 %)
# ---------------------------------------------------------------------------
col_map, col_chat = st.columns([0.55, 0.45])

# ============================================================================
# LEFT COLUMN: MAP
# ============================================================================
with col_map:
    last_results = st.session_state.agent_state.get("last_results", [])
    last_bbox_raw = st.session_state.agent_state.get("last_bbox")

    bbox_model: BoundingBox | None = None
    if isinstance(last_bbox_raw, dict):
        try:
            bbox_model = BoundingBox(**last_bbox_raw)
        except Exception:
            bbox_model = None

    st.pydeck_chart(render_map(last_results, bbox_model), use_container_width=True, height=800)

    if last_results:
        st.caption(f"{len(last_results)} CRS result(s) — hover for details.")

# ============================================================================
# RIGHT COLUMN: CHAT
# ============================================================================
with col_chat:
    # Scrollable chat history — fills the column above the input
    history_container = st.container(height=720, border=False)
    with history_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Clear button sits between history and input
    if st.session_state.messages:
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.agent_state = {"last_bbox": None, "last_results": []}
            st.rerun()

    # Chat input — at the bottom of the right column
    user_input = st.chat_input("Ask about CRS, projections, or geodetic transforms…")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking…"):
        result = invoke_geodetic_agent(
            query=user_input,
            chat_history=st.session_state.messages,
        )

    if result.success:
        formatted = format_crs_results(result.response)

        st.session_state.messages.append(
            {"role": "assistant", "content": formatted}
        )

        map_detection = detect_map_relevant_response(
            result.response, result.tool_calls
        )

        if map_detection.get("has_results"):
            crs_results = parse_agent_results(
                result.response,
                [tc.__dict__ for tc in result.tool_calls],
            )
            if crs_results:
                st.session_state.agent_state["last_results"] = crs_results

        if map_detection.get("data_type") == "bbox":
            try:
                bbox_data = json.loads(map_detection["data"])
                st.session_state.agent_state["last_bbox"] = bbox_data
            except (TypeError, ValueError, json.JSONDecodeError):
                pass

        st.rerun()
    else:
        error_msg = f"⚠️ {result.error}"
        st.session_state.messages.append(
            {"role": "assistant", "content": error_msg}
        )
        st.rerun()
