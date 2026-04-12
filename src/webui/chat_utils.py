"""Chat utilities for interacting with the geodetic agent."""

from langchain_core.messages import HumanMessage, AIMessage
from src.agents.geodetic import geodetic_agent
from typing import Any, Optional
import re

from src.exceptions import AgentInvocationError, GeodeticAdvisorError, ResponseParsingError


def invoke_geodetic_agent(query: str, chat_history: list = None) -> dict:
    """
    Invoke the geodetic agent with a user query.

    Args:
        query: User query string
        chat_history: Optional list of previous messages for context

    Returns:
        dict with keys:
            - 'response': Agent's text response
            - 'tool_calls': List of tool calls made by agent
            - 'tool_results': Results from tool calls
            - 'reasoning': Agent's internal reasoning
    """
    try:
        # Convert chat history to messages format expected by LangGraph agent
        messages = []
        if chat_history:
            for msg in chat_history:
                if isinstance(msg, dict):
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

        # Add current query
        messages.append(HumanMessage(content=query))

        # Invoke agent with messages
        try:
            result = geodetic_agent.invoke({"messages": messages})
        except Exception as e:
            raise AgentInvocationError(query, cause=e) from e

        # Extract the last AI message (agent's response)
        if not isinstance(result, dict) or "messages" not in result:
            raise ResponseParsingError(result, detail="expected dict with 'messages' key")

        agent_response = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                # Handle both string and list content
                if isinstance(msg.content, str):
                    agent_response = msg.content
                elif isinstance(msg.content, list):
                    # Extract text from list of content blocks
                    text_parts = []
                    for content_block in msg.content:
                        if isinstance(content_block, dict) and content_block.get("type") == "text":
                            text_parts.append(content_block.get("text", ""))
                        elif isinstance(content_block, str):
                            text_parts.append(content_block)
                    agent_response = " ".join(text_parts)

                if agent_response:
                    break

        return {
            "response": agent_response if agent_response else "No response from agent",
            "tool_calls": extract_tool_calls(result),
            "tool_results": extract_tool_results(result),
            "reasoning": [],
            "success": True
        }
    except GeodeticAdvisorError as e:
        return {
            "response": str(e),
            "tool_calls": [],
            "tool_results": [],
            "reasoning": [],
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "response": f"Error invoking agent: {str(e)}",
            "tool_calls": [],
            "tool_results": [],
            "reasoning": [],
            "success": False,
            "error": str(e)
        }


def extract_tool_calls(agent_result: dict) -> list:
    """
    Extract tool calls from agent result.

    Args:
        agent_result: Result dictionary from agent invocation

    Returns:
        List of tool call dictionaries with 'tool', 'input', 'output' keys
    """
    tool_calls = []

    try:
        if "messages" in agent_result:
            for msg in agent_result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        try:
                            # Handle both dictionary and object formats
                            if isinstance(tool_call, dict):
                                tool_name = tool_call.get("name", "unknown")
                                tool_args = tool_call.get("args", {})
                            else:
                                # Handle object with attributes
                                tool_name = getattr(tool_call, "name", "unknown")
                                tool_args = getattr(tool_call, "args", {})

                            tool_calls.append({
                                "tool": tool_name,
                                "input": tool_args,
                                "output": ""
                            })
                        except Exception as e:
                            continue
    except Exception as e:
        pass

    return tool_calls


def extract_tool_results(agent_result: dict) -> list:
    """
    Extract tool results from agent result.

    Args:
        agent_result: Result dictionary from agent invocation

    Returns:
        List of tool result dictionaries
    """
    results = []

    if "messages" in agent_result:
        for msg in agent_result["messages"]:
            if hasattr(msg, "name") and msg.name:
                results.append({
                    "tool": msg.name,
                    "result": msg.content if hasattr(msg, "content") else str(msg)
                })

    return results


def detect_map_relevant_response(agent_response: str, tool_calls: list) -> dict:
    """
    Detect if agent response contains map-relevant information.

    Args:
        agent_response: Agent's text response
        tool_calls: List of tool calls made

    Returns:
        dict with:
            - 'has_map_data': Boolean indicating if map data should be updated
            - 'data_type': Type of data ('crs_results', 'coordinates', 'bbox', None)
            - 'data': Extracted map data
    """
    # Ensure agent_response is a string
    if not isinstance(agent_response, str):
        agent_response = str(agent_response) if agent_response else ""

    map_keywords = ["coordinate", "crs", "projection", "epsg", "area", "longitude", "latitude", "bbox"]
    response_lower = agent_response.lower()

    has_map_data = any(keyword in response_lower for keyword in map_keywords)
    data_type = None
    data = None

    # Check tool calls for map-relevant tools
    if tool_calls:
        for tool_call in tool_calls:
            try:
                # Handle both dictionary and object formats
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get("tool", "")
                    output = tool_call.get("output", "")
                else:
                    tool_name = getattr(tool_call, "tool", "")
                    output = getattr(tool_call, "output", "")

                if tool_name == "search_crs_objects":
                    data_type = "crs_results"
                    data = output
                elif tool_name == "transform_coordinates":
                    data_type = "coordinates"
                    data = output
                elif tool_name == "get_bbox_from_areaname":
                    data_type = "bbox"
                    data = output
            except Exception:
                continue

    return {
        "has_map_data": has_map_data,
        "data_type": data_type,
        "data": data
    }


def format_agent_response(response: str, tool_calls: list) -> str:
    """
    Format agent response for display in chat.

    Args:
        response: Agent's text response
        tool_calls: List of tool calls made

    Returns:
        Formatted response string with tool call information
    """
    if not tool_calls:
        return response

    formatted = f"**Agent Response:**\n\n{response}\n\n"
    formatted += "**Tools Used:**\n"

    for i, call in enumerate(tool_calls, 1):
        try:
            # Handle both dictionary and object formats
            if isinstance(call, dict):
                tool_name = call.get("tool", "unknown")
                tool_input = call.get("input", {})
                tool_output = call.get("output", "")
            else:
                tool_name = getattr(call, "tool", "unknown")
                tool_input = getattr(call, "input", {})
                tool_output = getattr(call, "output", "")

            formatted += f"\n{i}. **{tool_name}**\n"
            formatted += f"   - Input: `{str(tool_input)[:100]}...`\n"
            formatted += f"   - Output: `{str(tool_output)[:100]}...`\n"
        except Exception:
            continue

    return formatted


def format_message_for_display(role: str, content: str) -> str:
    """
    Format a message for display in the chat interface.

    Args:
        role: 'user' or 'assistant'
        content: Message content

    Returns:
        Formatted message string
    """
    if role == "user":
        return f"**You:** {content}"
    elif role == "assistant":
        return f"**Agent:** {format_crs_results(content)}"
    else:
        return content


def format_crs_results(text: str) -> str:
    """
    Format CRS results in the response to show only name and authority code.
    Pattern: NAME (AUTHORITY:CODE) - one per line

    Supports any authority (EPSG, ESRI, IGNF, OGC, etc.)
    Removes "Area of use" information from results.

    Attempts to parse various CRS result formats and standardize them.

    Args:
        text: The agent's response text

    Returns:
        Formatted text with cleaned up CRS results
    """
    if not text:
        return text

    lines = text.split('\n')
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue

        # Skip lines that start with "Area of Use:" entirely
        if re.match(r'^Area\s+of\s+Use:', line, re.IGNORECASE):
            continue

        # Remove inline "Area of use" information - content like "(Area of use: ..)"
        line_cleaned = re.sub(r'\s*\(Area\s+of\s+use:\s*[^)]*\)', '', line, flags=re.IGNORECASE)

        # Also handle "Area of Use:" text that appears after CRS code on the same line
        # Takes everything before "Area of Use:" if it exists
        if 'Area of Use:' in line_cleaned or 'Area of use:' in line_cleaned:
            line_cleaned = re.split(r'Area\s+of\s+Use:', line_cleaned, flags=re.IGNORECASE)[0].strip()

        # Pattern 1: "NAME (AUTHORITY:CODE)" - already in correct format
        # Matches any authority code (EPSG, ESRI, IGNF, OGC, etc.)
        if re.match(r'^.+\s*\([A-Z]+:\d+\)\s*$', line_cleaned):
            formatted_lines.append(line_cleaned)
            continue

        # Pattern 2: "AUTHORITY:CODE - NAME" format from the agent
        # Match any authority code followed by colon and digits/alphanumerics
        authority_match = re.search(r'([A-Z]+):(\d+)\s*-\s*(.+?)(?:\n|$)', line_cleaned)
        if authority_match:
            authority = authority_match.group(1)
            code = authority_match.group(2)
            name = authority_match.group(3).strip()
            # Remove common suffixes (parenthetical content)
            name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
            formatted_lines.append(f"{name} ({authority}:{code})")
            continue

        # Pattern 3: Lines containing CRS info with embedded authority codes
        # Extract all authority codes and their associated names
        crs_pattern = r'([A-Za-z0-9\s\-\+\/\.,]+?)\s*\(([A-Z]+):(\d+)\)|([A-Z]+):(\d+)\s*[-–]\s*([A-Za-z0-9\s\-\+\/\.,]+)'
        matches = re.finditer(crs_pattern, line_cleaned)

        found_match = False
        for match in matches:
            if match.group(1) and match.group(2) and match.group(3):
                # Format 1: Name (AUTHORITY:Code)
                name = match.group(1).strip()
                # Remove parenthetical content from the name
                name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
                authority = match.group(2)
                code = match.group(3)
                formatted_lines.append(f"{name} ({authority}:{code})")
                found_match = True
            elif match.group(4) and match.group(5) and match.group(6):
                # Format 2: AUTHORITY:Code - Name
                authority = match.group(4)
                code = match.group(5)
                name = match.group(6).strip()
                # Remove parenthetical content from the name
                name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
                formatted_lines.append(f"{name} ({authority}:{code})")
                found_match = True

        # If no CRS pattern found, don't add the line (skip non-CRS lines)
        if not found_match and line_cleaned:
            # Only add if it doesn't look like metadata/description text
            if not re.match(r'^(Area|Region|Note|Info|Description)', line_cleaned, re.IGNORECASE):
                formatted_lines.append(line_cleaned)

    return '\n'.join(formatted_lines)


def parse_agent_results(response: str, tool_calls: list = None) -> list:
    """
    Parse agent results and extract CRS entries with EPSG codes and bounding boxes.

    Searches both the text response (for inline EPSG mentions) and tool call
    outputs (for structured search_crs_objects results).  Tool call data takes
    precedence: if a result is found in tool output it will carry the full
    bounding box; text-only hits will have area_bbox=None.

    Args:
        response: Agent's text response string.
        tool_calls: Optional list of tool call dicts with 'tool' and 'output' keys.

    Returns:
        List of dicts, each with:
            - 'epsg_code': str  (e.g. '4326')
            - 'crs_name':  str
            - 'area_bbox': dict | None  (keys: west, south, east, north)
    """
    import json

    results: list[dict] = []
    seen_codes: set[str] = set()

    # --- 1. Extract structured results from tool calls (highest fidelity) ---
    if tool_calls:
        for call in tool_calls:
            try:
                tool_name = call.get("tool", "") if isinstance(call, dict) else getattr(call, "tool", "")
                output = call.get("output", "") if isinstance(call, dict) else getattr(call, "output", "")

                if tool_name != "search_crs_objects" or not output:
                    continue

                records = json.loads(output) if isinstance(output, str) else output
                if not isinstance(records, list):
                    continue

                for record in records:
                    code = str(record.get("EPSG_CODE", "")).strip()
                    name = str(record.get("CRS_NAME", "")).strip()
                    bbox_raw = record.get("AREA_BBOX")

                    bbox = None
                    if isinstance(bbox_raw, dict):
                        try:
                            bbox = {
                                "west": float(bbox_raw["west"]),
                                "south": float(bbox_raw["south"]),
                                "east": float(bbox_raw["east"]),
                                "north": float(bbox_raw["north"]),
                            }
                        except (KeyError, ValueError, TypeError):
                            pass

                    if code and code not in seen_codes:
                        results.append({"epsg_code": code, "crs_name": name, "area_bbox": bbox})
                        seen_codes.add(code)
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue

    # --- 2. Extract EPSG codes mentioned in the text response ---
    if response:
        for match in re.finditer(r'EPSG\s*:\s*(\d+)', response, re.IGNORECASE):
            code = match.group(1)
            if code not in seen_codes:
                # Try to extract a name from surrounding text, e.g. "WGS 84 (EPSG:4326)"
                start = max(0, match.start() - 60)
                surrounding = response[start:match.start()]
                name_match = re.search(r'([A-Za-z0-9][\w\s\-\+\/\.]*?)\s*[\(\-]?\s*$', surrounding)
                name = name_match.group(1).strip() if name_match else f"EPSG:{code}"
                results.append({"epsg_code": code, "crs_name": name, "area_bbox": None})
                seen_codes.add(code)

    return results
