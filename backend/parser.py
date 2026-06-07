import json
import os

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

if __name__ == "__main__":
    #Test our parser standalone
    raw_data = load_raw_geojson()

    #Extract the main Purple Line tracks
    purple_tracks = extract_line_coordinates(raw_data, "Mysore Road - Baiyappanahalli")

    print("---Parser Test Suite---")
    if purple_tracks:
        print(f"Successfully extracted Purple Line path")
        print(f"Total Track vector nodes found: {len(purple_tracks)}")
        print(f"First Track Coordinates: {purple_tracks[0]}")
        print(f"Last Track Coordinates: {purple_tracks[-1]}")
    else:
        print("Could not find matching LineString in dataset")
