import json
import os
from backend.engine import calculate_distance

def load_raw_geojson():
    """Reads the raw metro data file from the data folder"""
    #find the absolute path to our project directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "raw_metro_data.json")

    with open(file_path, "r") as f:
        data = json.load(f)
    return data

def extract_line_coordinates(geojson_data, line_name_keyword):
    """
    Searches the feature array for a LineString matching our line keyword
    and returns its clean track coordinate list.
    """
    for feature in geojson_data["features"]:
        #Exctract properties and geometry blocks
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        name = properties.get("Name", "")
        geom_type = geometry.get("type", "")

        #Look for specific line track sequence
        if geom_type == "LineString" and line_name_keyword in name:
            raw_coords = geometry.get("coordinates", [])

            #Clean coordinates: Strip the 3rd altitude value (0.0) from the data
            clean_coords = [[pt[0], pt[1]] for pt in raw_coords]
            return clean_coords
    return None

def extract_stations(geojson_data):
    """
    Scans the entire feature list for Point geometries representing stations
    and maps them into a clean lookup dictionary: {"Station Name" : [Log, Lat]}
    """
    station_lookup = {}

    for feature in geojson_data["features"]:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        name = properties.get("Name", "")
        geom_type = geometry.get("type", "")

        #We only need standalone point features that represent stations
        if geom_type == "Point" and name:
            #Safety feature: Skip structural markers like depots or ramps
            if "Depot" in name or "Ramp" in name or "*" in name:
                continue

            raw_coords = geometry.get("coordinates", [])

            #Extract the long and lat, ignoring the 3rd index of altitude
            if len(raw_coords) >= 2:
                clean_coords = [raw_coords[0], raw_coords[1]]
                station_lookup[name] = clean_coords
    return station_lookup

def map_stations_to_track_indices(track_coordinates, station_lookup):
    """
    Correlates station nodes to their nearest physical index position
    along the fine-grained track LineString array using nearest-neighbor sweep
    Returns a dictionary: { "Station Name": Integer_Index_Number }
    """

    mapped_indices = {}
    #Loop every station name and its true coordinate location
    for station_name, station_coords in station_lookup.items():
        best_index = -1
        minimum_distance = float('inf') #Start with infinity as baseline maximum

        #Sweep across every single vector node on the rail track line
        for index, track_coords in enumerate(track_coordinates):
            dist = calculate_distance(station_coords, track_coords)

            #if this track point is closer to the platform than the previous matches, lock it in
            if dist< minimum_distance:
                minimum_distance = dist
                best_index = index

        #Safety filter: Only map the station if it actually sits near this specific line track
        # (e.g., Anjanapura Station wont match a Purple Line track because it's kms away)
        if minimum_distance < 300: #300 meters maximum tolerance threshold
            mapped_indices[station_name] = best_index
    return mapped_indices

if __name__ == "__main__":
    #Test our parser standalone
    raw_data = load_raw_geojson()

    #Extract the main Purple Line tracks
    purple_tracks = extract_line_coordinates(raw_data, "Mysore Road - Baiyappanahalli")

    print("---Parser Test Suite---")

    #1. Test Track Extraction
    purple_tracks = extract_line_coordinates(raw_data, "Mysore Road - Baiyappanahalli")
    if purple_tracks:
        print(f"1. Track Extraction: {len(purple_tracks)} nodes found")
    else:
        print("1. Track Extraction Failed")


    #2. Test Station Directory Harvesting
    stations = extract_stations(raw_data)
    print(f"2. Station Harvesting: {len(stations)} total stations parsed")

    #3. Test Index Mapping
    purple_station_indices = map_stations_to_track_indices(purple_tracks, stations)

    #printing sequence of stations exactly as they appear along the tracks
    #we sort them by their index location value so they read West to East
    sorted_sequence = sorted(purple_station_indices.items(), key=lambda item: item[1])


    print("\n --- Verified Purple Line Station Sequence Over Track Vectors --- ")
    for name, idx in sorted_sequence:
        print(f"   Index #{idx:03d} -> {name}")


    # #Checking a few specific stations to verify the dictonary mapping keys
    # test_keys = ["Majestic", "Indiranagar", "Whitefield", "MG Road"]
    # print("3. Sample Station Coordinate Verification: ")
    # for key in test_keys:
    #     if key in stations:
    #         print(f"   - {key} -> {stations[key]}")
    #     else:
    #         print(f"   - {key} -> NOT FOUND")
    #
