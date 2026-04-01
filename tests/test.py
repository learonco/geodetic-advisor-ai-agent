import sys
from pathlib import Path

# Add the project root to the path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools import geodesy

r = geodesy.search_crs_objects.run({'bbox': {'north': -36.0523344, 'west': -71.9666079, 'south': -41.1006358, 'east': -67.9962632}, 'object_type': ['GEODETIC_REFERENCE_FRAME']})

print(r)