import math
from itertools import accumulate


def calculate_distance(coord1, coord2):
    """
    calculates the absolute surface distance in meters between 2 coordinates
    on earth using the Haversine Formula (Since the earth is round u cannot use pythagoreas theoram)

    Each coordinate must be passed as an array: [Long, Lat] matching the IUDX dataset
    """
    #Earth's Avg Radius in Meters
    EARTH_RADIUS = 6371000

    # 1: Unpacking our Long and Lat from the array
    long1, lat1 = coord1[0], coord1[1]
    long2, lat2 = coord2[0], coord2[1]

    # 2: Converting Degrees to Radians to match python's math module
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delata_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(long2 - long1)

    # 3: Apply the values to Haversine Formula
    a = (math.sin(delata_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2) ** 2))

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Now we return the total distance in meters
    return EARTH_RADIUS * c

def interpolate_points(coord1, coord2, progress):
    """
    Finds an intermediate coordinate [lat, long] between coord1 and coord 2
    based on a progress decimal (0.0 to 1.0)

    if progress is 0.5 it returns the exact midpoint coordinate.
    """

    # 1: Unpacking starting and ending coordinates
    long1, lat1 = coord1[0], coord1[1]
    long2, lat2 = coord2[0], coord2[1]

    # 2: Liner interpolation formula:
    # Current = Start + Progress * (End - Start)
    interp_long = long1 + progress * (long2 - long1)
    interp_lat = lat1 + progress * (lat2 - lat1)

    return [interp_long, interp_lat]

def calculate_curved_position(coordinates, progress_fraction):
    """
    This function calculates the exact coordinate [Long, Lat] along a curved path
    (a list of multiple coordinates) given a total progress fraction (0.0 to 1.0)
    """

    # Guard clauses for edge cases
    if progress_fraction <= 0.0:
        return coordinates[0]
    if progress_fraction >= 1.0:
        return coordinates[-1]

    # 1: Calculate the distance of every individual sub-segment along the curve
    segment_distances = []
    for i in range(len(coordinates)-1):
        dist = calculate_distance(coordinates[i], coordinates[i+1])
        segment_distances.append(dist)

    # 2: Sum them up to get the complete length of the curved track
    total_track_distance = sum(segment_distances)

    # 3: Determine how many meters down the track the train has moved
    target_distance = total_track_distance * progress_fraction

    # 4: Traverse the segments to find where the target distance lands
    accumulated_distance = 0.0

    for i, seg_dist in enumerate(segment_distances):
        # Check if the target distance falls within the current segment loop
        if accumulated_distance + seg_dist >= target_distance:
            # Calculate the remaining distance needed within this specific segment
            remaining_distance = target_distance - accumulated_distance

            # Find the local progress % for this isolated segment slice
            local_progress = remaining_distance / seg_dist if seg_dist > 0 else 0.0

            # Isolate the segment's starting and ending coordinates
            start_point = coordinates[i]
            end_point = coordinates[i+1]

            # Perform the straight-line interpolation on this tiny micro-segment
            return interpolate_points(start_point, end_point, local_progress)

        # Move our baseline forward if the train has completely passed the segment
        accumulated_distance += seg_dist

    # Fallback default safety case
    return coordinates[-1]



if __name__ == "__main__":
    # Test coordinates for 2 adjacent Bangalore Metro Stations

    # Point 1: Baiyappanahalli (BYPH)
    station_byph = [77.652653, 12.990325]

    # Point 2: Swami Vivekananda Road (SVRD)
    station_svrd = [77.63879, 12.985484]

    # Test 1: Calculate the distance between the 2 points
    meters = calculate_distance(station_byph, station_svrd)
    print(f"1. Total Track Distance: {meters: .2f} meters")

    # Test 2: Find the midpoint coordinates using interpolation (0.5 means 50% of the way)
    midpoint = interpolate_points(station_byph,station_svrd, 0.5)
    print(f"2. Computed Midpoint Coordinates: {midpoint}")

    # Test 3: Verify midpoint math by calculating the distance to the midpoint
    dist_to_mid = calculate_distance(station_byph, midpoint)
    print(f"3. Distance to midpoint: {dist_to_mid: .2f} meters (Should be half the total distance)")

    # Mock track segment that curves: Point A -> Point B -> Point C
    # It goes north and then turns east

    mock_curve = [
        [77.5000, 12.9000],  # Point A (Start)
        [77.5000, 12.9100],  # Point B (The Curve Bend)
        [77.5100, 12.9100]  # Point C (End)
    ]

    # Test our curve tracker at 75% total journey progress
    # It should have completely passed Point B and should be halfway between B and C
    pos_75 = calculate_curved_position(mock_curve, 0.75)
    print(f"Calculated Coordinates at 75% Progress: {pos_75}")


