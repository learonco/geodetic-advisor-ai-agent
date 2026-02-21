from src import tools as t

def main():
    print("Hello from geodetic-advisor-ai-agent!")
    # r = t.search_crs_objects.run({'bbox': {'north': -36.0523344, 'west': -71.9666079, 'south': -41.1006358, 'east': -67.9962632}, 'object_type': ['GEODETIC_REFERENCE_FRAME']})
    r = t.search_crs_objects.run({'object_type': ['GEODETIC_REFERENCE_FRAME'], 'object_area_of_use': 'Neuquen'})

    print(r)


if __name__ == "__main__":
    main()
