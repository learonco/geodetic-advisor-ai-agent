"""Map utilities for Folium visualization and interaction."""

import folium
from folium.plugins import Draw
import json
from typing import Tuple, List, Dict, Optional
import re


def create_base_map(center: Tuple[float, float] = (20, 0), zoom: int = 2) -> folium.Map:
    """
    Create a base Folium map with custom styling.

    Args:
        center: Tuple of (latitude, longitude)
        zoom: Initial zoom level

    Returns:
        Folium Map object
    """
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="OpenStreetMap",
        max_bounds=True,
    )

    # Add draw tools
    draw = Draw(
        export=True,
        position='topleft',
        draw_options={
            'polyline': False,
            'circle': False,
            'circlemarker': False,
            'rectangle': True,
            'polygon': False
        }
    )
    draw.add_to(m)

    return m


def add_bbox_rectangle(m: folium.Map, bbox: Dict[str, float], color: str = 'red') -> folium.Map:
    """
    Add a bounding box rectangle to the map.

    Args:
        m: Folium Map object
        bbox: Dictionary with keys 'west', 'south', 'east', 'north'
        color: Color of the rectangle

    Returns:
        Updated Folium Map object
    """
    bounds = [
        [bbox['south'], bbox['west']],
        [bbox['north'], bbox['east']]
    ]

    folium.Rectangle(
        bounds=bounds,
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.2,
        weight=2,
        popup="Search Area"
    ).add_to(m)

    return m


def add_crs_areas(m: folium.Map, crs_info_list: List[Dict]) -> folium.Map:
    """
    Add CRS area-of-use polygons to the map as a feature group.

    Args:
        m: Folium Map object
        crs_info_list: List of CRS info dictionaries from search_crs_objects

    Returns:
        Updated Folium Map object
    """
    fg = folium.FeatureGroup(name="CRS Areas of Use", show=True)

    for crs_info in crs_info_list:
        try:
            # Extract area of use information
            epsg_code = crs_info.get('EPSG_CODE', 'Unknown')
            crs_name = crs_info.get('CRS_NAME', 'Unknown CRS')
            area_name = crs_info.get('AREA_OF_USE', 'Global')

            # Try to get bounding box from area of use
            if 'AREA_BBOX' in crs_info:
                bbox = crs_info['AREA_BBOX']
                bounds = [
                    [bbox['south'], bbox['west']],
                    [bbox['north'], bbox['east']]
                ]

                # Add polygon with semi-transparent fill
                popup_text = f"<b>{crs_name}</b><br>EPSG: {epsg_code}<br>Area: {area_name}"
                folium.Polygon(
                    locations=[
                        [bbox['south'], bbox['west']],
                        [bbox['south'], bbox['east']],
                        [bbox['north'], bbox['east']],
                        [bbox['north'], bbox['west']],
                        [bbox['south'], bbox['west']]
                    ],
                    color='blue',
                    fill=True,
                    fillColor='lightblue',
                    fillOpacity=0.3,
                    weight=1,
                    popup=folium.Popup(popup_text, max_width=250)
                ).add_to(fg)
        except Exception as e:
            # Skip CRS entries without valid area info
            continue

    fg.add_to(m)
    return m


def add_search_results_markers(m: folium.Map, results: List[Dict], color: str = 'green') -> folium.Map:
    """
    Add search result markers to the map.

    Args:
        m: Folium Map object
        results: List of search result dictionaries
        color: Marker color

    Returns:
        Updated Folium Map object
    """
    fg = folium.FeatureGroup(name="Search Results", show=True)

    for i, result in enumerate(results[:20]):  # Limit to 20 markers for performance
        try:
            # Extract center point of area of use if available
            if 'AREA_BBOX' in result:
                bbox = result['AREA_BBOX']
                lat = (bbox['north'] + bbox['south']) / 2
                lon = (bbox['east'] + bbox['west']) / 2
            else:
                # Default to center of world if no bbox
                lat, lon = 0, 0

            epsg_code = result.get('EPSG_CODE', 'Unknown')
            crs_name = result.get('CRS_NAME', 'Unknown')

            popup_html = f"""
            <b>{crs_name}</b><br>
            EPSG: {epsg_code}<br>
            <i>Click for details</i>
            """

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color=color, icon='info-sign'),
                tooltip=f"{epsg_code}: {crs_name}"
            ).add_to(fg)
        except Exception as e:
            continue

    fg.add_to(m)
    return m


def highlight_crs_polygon(m: folium.Map, crs_epsg: str, crs_info: Dict) -> folium.Map:
    """
    Highlight a specific CRS polygon on the map.

    Args:
        m: Folium Map object
        crs_epsg: EPSG code of CRS to highlight
        crs_info: CRS information dictionary

    Returns:
        Updated Folium Map object
    """
    try:
        if 'AREA_BBOX' in crs_info:
            bbox = crs_info['AREA_BBOX']
            bounds = [
                [bbox['south'], bbox['west']],
                [bbox['north'], bbox['east']]
            ]

            # Add highlighted polygon
            folium.Polygon(
                locations=[
                    [bbox['south'], bbox['west']],
                    [bbox['south'], bbox['east']],
                    [bbox['north'], bbox['east']],
                    [bbox['north'], bbox['west']],
                    [bbox['south'], bbox['west']]
                ],
                color='red',
                fill=True,
                fillColor='yellow',
                fillOpacity=0.5,
                weight=3,
                popup=f"EPSG: {crs_epsg}"
            ).add_to(m)

            # Fit map to bounds
            m.fit_bounds(bounds)
    except Exception as e:
        pass

    return m


def extract_coordinates_from_clicks(map_data: Dict) -> Optional[Tuple[float, float]]:
    """
    Extract coordinates from map click events.

    Args:
        map_data: Data from st_folium() containing map events

    Returns:
        Tuple of (latitude, longitude) or None if no click data available
    """
    try:
        if map_data and 'last_clicked' in map_data:
            click = map_data['last_clicked']
            if click:
                return (click['lat'], click['lng'])
    except Exception as e:
        pass

    return None


def extract_bbox_from_geometry(geometry: Dict) -> Optional[Dict]:
    """
    Extract bounding box from a GeoJSON geometry.

    Args:
        geometry: GeoJSON geometry object

    Returns:
        Dictionary with 'west', 'south', 'east', 'north' keys or None
    """
    try:
        if geometry['type'] == 'Rectangle':
            coords = geometry.get('coordinates', [])
            if coords:
                lats = [c[1] for c in coords[0]]
                lons = [c[0] for c in coords[0]]
                return {
                    'west': min(lons),
                    'south': min(lats),
                    'east': max(lons),
                    'north': max(lats)
                }
    except Exception as e:
        pass

    return None


def parse_crs_search_results(response_text: str) -> List[Dict]:
    """
    Parse CRS search results from agent response text.
    Attempts to extract EPSG codes and CRS information.

    Args:
        response_text: Agent response text

    Returns:
        List of CRS info dictionaries
    """
    results = []

    # Look for EPSG patterns in text
    epsg_pattern = r'EPSG:?(\d+)'
    matches = re.finditer(epsg_pattern, response_text, re.IGNORECASE)

    for match in matches:
        epsg_code = match.group(1)
        results.append({
            'EPSG_CODE': epsg_code,
            'CRS_NAME': f'EPSG:{epsg_code}'
        })

    return results


def create_comparison_map(bbox1: Dict, bbox2: Dict) -> folium.Map:
    """
    Create a map comparing two bounding boxes for coordinate transformation.

    Args:
        bbox1: First bounding box (from coordinate)
        bbox2: Second bounding box (to coordinate)

    Returns:
        Folium Map object with both boxes
    """
    m = create_base_map()
    m = add_bbox_rectangle(m, bbox1, color='red')
    m = add_bbox_rectangle(m, bbox2, color='green')
    return m
