from fastapi import FastAPI
import os
import json
from datetime import datetime

#import our custom spatial utilities and parser hooks
from backend.engine import calculate_curved_position, time_to_seconds
from backend.parser import load_raw_geojson, extract_line_coordinates, extract_stations, map_stations_to_track_indices

app = FastAPI(title="Namma Metro Live Simulator Engine")

#Cache our geographical truths to memory so we dont read the disk on every single clock tick
RAW_GEOJSON = load_raw_geojson()
PURPLE_TRACKS = extract_line_coordinates(RAW_GEOJSON, "Purple")
STATIONS_DIRECTORY = extract_stations(RAW_GEOJSON)
PURPLE_INDEX_MAP = map_stations_to_track_indices(PURPLE_TRACKS, STATIONS_DIRECTORY)

# Place this right after line 16 in backend/main.py
if PURPLE_TRACKS is None:
    raise RuntimeError("CRITICAL ERROR: Parser failed to extract 'Purple Line' track coordinates! Check your string filters.")

def load_timetable():
    """Helper to safely read our custom timetable schedule from the data folder"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    timetable_path = os.path.join(base_dir, "data", "timetable.json")
    with open(timetable_path, "r") as f:
        return json.load(f)

@app.get("/api/v1/live-trains")
def get_simulated_train_positions(custom_time: str = None):
    """
    Main evaluation endpoint. Scans all schedules, evaluates train states,
    slices geometries by index thresholds, and returns real-time coordinates
    """
    #1. Establish our clock time parameter (Use system time if no custom string is provided)
    if custom_time:
        query_time_str = custom_time
    else:
        query_time_str = datetime.now().strftime("%H:%M:%S")

    now_seconds = time_to_seconds(query_time_str)
    timetable = load_timetable()
    active_trains_payload = []

    #2. Iterate through every scheduled train trip in our database
    for trip in timetable:
        stops = trip["stops"]
        trip_start_seconds = time_to_seconds(stops[0]["arrival"])
        trip_end_seconds = time_to_seconds(stops[-1]["arrival"])

        # Safety Clause: Skip this train if it hasn't left the depot or has already finished its run
        if not (trip_start_seconds <= now_seconds <= trip_end_seconds):
            continue

        #3. Analyze Individual station stop legs to locate the train's active phase
        for i in range(len(stops) - 1):
            station_a = stops[i]
            station_b = stops[i+1]

            arr_a = time_to_seconds(station_a["arrival"])
            dep_a = time_to_seconds(station_a["departure"])
            arr_b = time_to_seconds(station_b["arrival"])

            #Phase A: Is the train currently halted at Station A's platform?
            if arr_a <= now_seconds <= dep_a:
                station_name = station_a["station_name"]
                track_idx = PURPLE_INDEX_MAP[station_name]
                coords = PURPLE_TRACKS[track_idx]

                active_trains_payload.append({
                    "trip_id": trip["trip_id"],
                    "status": f"Halted at {station_name}",
                    "coordinates": {"lat": coords[1], "lon": coords[0]}
                })
                break #Phase found: break out of the inner loop for this trip

            #Phase B: Is the train actively in transit down the track between STATION A and STATION B
            elif dep_a < now_seconds < arr_b:
                #Calculate the temporal progress metrics
                total_leg_time = arr_b - dep_a
                elapsed_leg_time = now_seconds - dep_a
                progress_fraction = elapsed_leg_time / total_leg_time

                #Fetch calibrated index parameters for our boundry platforms
                idx_a = PURPLE_INDEX_MAP[station_a["station_name"]]
                idx_b = PURPLE_INDEX_MAP[station_b["station_name"]]

                #Slice our master 151 track nodes down to just the segment between our 2 active stations
                leg_coordinates = PURPLE_TRACKS[idx_a : idx_b +1]

                #If the schedule direction matches our track array , interpolate normally
                #otherwise reverse it (handles future birectional configurations)
                if idx_a > idx_b:
                    leg_coordinates = leg_coordinates[::-1]

                #Execute multi-segment spatial curve math utility
                coords = calculate_curved_position(leg_coordinates, progress_fraction)

                active_trains_payload.append({
                    "trip_id": trip["trip_id"],
                    "status": f"In Transit: {station_a['station_name']} -> {station_b['station_name']}",
                    "coordinates": {"lat": coords[1], "long": coords[0]}
                })
                break
    return {
        "system_clock": query_time_str,
        "active_train_count": len(active_trains_payload),
        "trains": active_trains_payload
    }


