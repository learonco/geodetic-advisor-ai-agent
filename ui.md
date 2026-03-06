# Streamlit WebUI Implementation Plan

## Overview
Build a Streamlit app with a two-column layout: left sidebar with LLM chat (35%) using the existing ReAct agent, and right panel with an interactive Folium map (65%) that supports drawing bounding boxes to search CRS, displaying results, and visualizing areas of use. Chat and map interactions will be bidirectional—map actions trigger queries and display results, while LLM responses can update the map.

## Architecture

### Layout Structure
- **Left Column (35%)**: Chat Interface
  - Message history display
  - User input box
  - Agent reasoning/actions display (ReAct format)

- **Right Column (65%)**: Interactive Map
  - Folium map centered on world view
  - Click handlers for bounding box creation
  - CRS area-of-use visualization
  - Search results markers and popups

### Components

#### 1. webui/app.py (Main Entry Point)
- Streamlit page configuration
- Session state initialization (chat history, map data, agent state)
- Two-column layout setup
- Chat interface rendering
- Map rendering with st_folium()
- Event handling for map and chat interactions

#### 2. webui/chat_utils.py (Chat Utilities)
- `invoke_geodetic_agent()`: Wrapper to call geodetic_agent and parse ReAct outputs
- `extract_tool_calls()`: Extract tool calls and results from agent reasoning
- `detect_map_relevant_response()`: Identify responses with map-relevant data
- `format_agent_response()`: Format agent reasoning for display
- Agent initialization with tools from tools/geodesy.py

#### 3. webui/map_utils.py (Map Utilities)
- `create_base_map()`: Initialize Folium map with custom styling
- `add_bbox_rectangle()`: Add bounding box rectangle from coordinate pairs
- `add_crs_areas()`: Convert CRS area-of-use data to Folium GeoJSON layers
- `add_search_results_markers()`: Render search results as Folium markers
- `highlight_crs_polygon()`: Highlight selected CRS on map
- `extract_coordinates_from_clicks()`: Extract lat/lon from map click events

### Data Flow

1. **User Query Flow**:
   - User types message in chat input
   - Message sent to geodetic_agent
   - Agent uses ReAct to reason and call tools
   - Tool results parsed and stored in session state
   - Agent response formatted and displayed in chat

2. **Map Interaction Flow**:
   - User clicks two points on map to define bbox
   - Coordinates captured and displayed as rectangle
   - Automatic message sent to agent: "Find CRS for area [bbox]"
   - Agent invokes search_crs_objects tool
   - Results converted to Folium layers and added to map
   - CRS metadata displayed as popups/markers

3. **Bidirectional Sync**:
   - Map state stored in session_state['map_data']
   - Chat history stored in session_state['chat_history']
   - Agent tool calls logged for map visualization
   - Map updates trigger chat messages and vice versa

## Dependencies

### New Requirements
- `streamlit >=1.28`
- `folium >=0.14`
- `streamlit-folium >=0.19`

### Existing Requirements (verified)
- `langchain >=1.1.0`
- `langchain-google-genai >=3.2.0`
- `pyproj >=3.7.2`
- `httpx` (add to pyproject.toml)

## File Structure
```
geodetic-advisor-ai-agent/
├── webui/
│   ├── __init__.py
│   ├── app.py              # Main Streamlit app
│   ├── chat_utils.py       # Chat utilities & agent wrapper
│   └── map_utils.py        # Map utilities & visualization
├── tools/
│   ├── __init__.py
│   └── geodesy.py
├── agents/
│   ├── __init__.py
│   └── geodetic.py
├── tests/
├── ui.md                   # This file
├── pyproject.toml          # Updated with new dependencies
├── main.py
└── README.md
```

## Usage

```bash
# Install dependencies
pip install -e .

# Run the webapp
streamlit run webui/app.py
```

## Verification Checklist

- [ ] Run `streamlit run webui/app.py` and verify 35/65 layout visible
- [ ] Test chat interaction: send geodetic query, verify agent responds
- [ ] Test map drawing: click two points, verify bbox appears
- [ ] Test CRS search: verify search triggers and results display
- [ ] Test results on map: verify search results appear as markers
- [ ] Test bidirectional sync: draw bbox → verify query in chat
- [ ] Test agent response→map: verify map updates from agent responses
- [ ] Test sample queries: "Find CRS for Madrid", "What projections are used in Brazil?"

## Future Enhancements (Phase 2+)

- Persist chat history to SQLite/JSON
- Export map as image or GeoJSON
- Coordinate transformation visualization
- Custom projection design assistant
- Multi-user session management
- Batch coordinate transformations
- Advanced filtering options (datum, reference frame type)
