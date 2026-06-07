# frontend/app.py
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Namma Metro Live Simulator", layout="wide")

st.title("🚇 Namma Metro Live Spatial-Temporal Dashboard")
st.markdown("Real-time position engine tracking transit curvature using multi-segment vector interpolation.")

# 1. Sidebar Control Panel for Time Manipulation
st.sidebar.header("⏱️ Simulation Controller")
time_input = st.sidebar.text_input("Set Simulation Time (HH:MM:SS)", value="16:04:30")

# 2. Query our running FastAPI backend engine
BACKEND_URL = f"http://127.0.0.1:8000/api/v1/live-trains?custom_time={time_input}"

try:
    response = requests.get(BACKEND_URL).json()
    system_clock = response.get("system_clock", time_input)
    trains = response.get("trains", [])

    st.sidebar.success(f"System Clock: {system_clock}")
    st.sidebar.metric(label="Active Trains En Route", value=len(trains))

    # 3. Initialize our core Folium Map Canvas centered on central Bengaluru (Majestic)
    map_center = [12.975697, 77.572967]
    m = folium.Map(location=map_center, zoom_start=13, tiles="cartodbpositron")

    # 4. Plot our active train positions onto the map canvas layers
    if trains:
        for train in trains:
            lat = train["coordinates"]["lat"]
            lon = train["coordinates"]["long"]  # Maps to backend 'long' key
            status = train["status"]
            trip_id = train["trip_id"]

            # Create a localized informational popup box asset
            popup_content = f"<b>Trip:</b> {trip_id}<br><b>Status:</b> {status}"

            # Draw a custom pulsing-style marker onto the map
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=trip_id,
                icon=folium.Icon(color="purple", icon="train", prefix="fa")
            ).add_to(m)

            st.info(f"🛰️ Active Vector Relay ➔ **{trip_id}** | {status} | Coordinates: `[{lat:.5f}, {lon:.5f}]`")
    else:
        st.warning("💤 No active trains scheduled on the tracks for this timestamp window.")

    # 5. Render the final map object widget on the Streamlit dashboard workspace canvas
    st_folium(m, width=1100, height=600)

except requests.exceptions.ConnectionError:
    st.error("❌ Connection Refused: Ensure your backend uvicorn server is running on port 8000!")