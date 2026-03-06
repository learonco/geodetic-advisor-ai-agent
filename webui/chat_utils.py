"""Chat utilities for interacting with the geodetic agent."""

from langchain_core.messages import HumanMessage, AIMessage
from agents.geodetic import geodetic_agent
from typing import Any, Optional


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
        result = geodetic_agent.invoke({"messages": messages})

        # Extract the last AI message (agent's response)
        agent_response = ""
        if "messages" in result:
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
        return f"**Agent:** {content}"
    else:
        return content
