from src.tools import search_crs_objects

r = search_crs_objects.run({'bbox': {'north': -36.0523344, 'west': -71.9666079, 'south': -41.1006358, 'east': -67.9962632}, 'object_type': ['GEODETIC_REFERENCE_FRAME']})

print(r)