#!/usr/bin/env python3
"""Test script for clickable results feature."""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.webui.chat_utils import parse_agent_results

def test_parse_agent_results_from_text():
    """Test parsing results from text response."""
    response = """
    I found several CRS suitable for your area:
    1. EPSG:4326 - WGS 84 (Geographic)
    2. EPSG:3857 - WGS 84 / Pseudo-Mercator (Projected)
    3. EPSG:4979 - WGS 84 (3D Geographic)
    """

    results = parse_agent_results(response)

    print("Test 1: Parse results from text")
    print(f"Found {len(results)} results")
    for result in results:
        print(f"  - {result.epsg_code}: {result.crs_name}")

    assert len(results) >= 3, "Should find at least 3 EPSG codes"
    print("✅ Test 1 passed!\n")


def test_parse_agent_results_from_tool_calls():
    """Test parsing results from tool call outputs."""
    response = "Found 2 CRS for your area."

    tool_calls = [
        {
            "tool": "search_crs_objects",
            "output": json.dumps([
                {
                    "EPSG_CODE": "4326",
                    "CRS_NAME": "WGS 84",
                    "AREA_OF_USE": "World",
                    "AREA_BBOX": {
                        "west": -180,
                        "south": -90,
                        "east": 180,
                        "north": 90
                    }
                },
                {
                    "EPSG_CODE": "3857",
                    "CRS_NAME": "Web Mercator",
                    "AREA_OF_USE": "World",
                    "AREA_BBOX": {
                        "west": -180,
                        "south": -85.051129,
                        "east": 180,
                        "north": 85.051129
                    }
                }
            ])
        }
    ]

    results = parse_agent_results(response, tool_calls)

    print("Test 2: Parse results from tool calls")
    print(f"Found {len(results)} results")
    for result in results:
        print(f"  - {result.epsg_code}: {result.crs_name}")
        if result.area_bbox:
            bbox = result.area_bbox
            print(f"    Area: {bbox.west:.1f}°W to {bbox.east:.1f}°E, {bbox.south:.1f}°S to {bbox.north:.1f}°N")

    assert len(results) == 2, "Should find exactly 2 results from tool output"
    assert results[0].epsg_code == '4326', "First result should be EPSG:4326"
    assert results[0].area_bbox is not None, "Result should have bounding box"
    print("✅ Test 2 passed!\n")


def test_parse_agent_results_mixed():
    """Test parsing with both text and tool calls."""
    response = "I found EPSG:4326, EPSG:3857, and EPSG:4979 for your area."

    tool_calls = [
        {
            "tool": "search_crs_objects",
            "output": json.dumps([
                {
                    "EPSG_CODE": "4326",
                    "CRS_NAME": "WGS 84",
                    "AREA_OF_USE": "World",
                    "AREA_BBOX": {
                        "west": -180,
                        "south": -90,
                        "east": 180,
                        "north": 90
                    }
                }
            ])
        }
    ]

    results = parse_agent_results(response, tool_calls)

    print("Test 3: Parse results from mixed sources (tool + text)")
    print(f"Found {len(results)} results")
    for result in results:
        print(f"  - {result.epsg_code}: {result.crs_name}")

    # Should have tool result + additional text results (without duplicates)
    assert len(results) >= 3, "Should find at least 3 results combining tool and text"
    assert results[0].epsg_code == '4326', "First result from tool should be present"
    print("✅ Test 3 passed!\n")


def test_map_functions():
    """Test that map utility functions that exist can be imported correctly."""
    import src.webui.map_utils  # noqa: F401

    print("Test 4: Import map utility functions")
    print("  - map_utils: imported ✓")
    print("✅ Test 4 passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Clickable Results Implementation")
    print("=" * 60)
    print()

    try:
        test_parse_agent_results_from_text()
        test_parse_agent_results_from_tool_calls()
        test_parse_agent_results_mixed()
        test_map_functions()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
