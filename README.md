# 🚇 Namma Metro Live Spatial-Temporal Tracker

An open-source simulation dashboard for Bengaluru's Namma Metro network. This project maps temporal transit timetables onto non-linear geographical track vectors (`LineString` format), calculating vehicle positions natively in Python.

## 🏗️ System Architecture
- **Backend Infrastructure:** FastAPI engine managing real-time schedule evaluations and tracking calculations.
- **Frontend Dashboard:** Streamlit web app providing interactive GIS visualization layers through Folium.
- **Core Algorithms:** Multi-segment vector interpolation using the Haversine formula to maintain true-to-track curve alignment.

## 📊 Phase Execution Roadmap
- [ ] **Phase 1:** Establish clean system repository configuration & architectural stubs.
- [ ] **Phase 2:** Build geometric calculation engine supporting path traversal distances.
- [ ] **Phase 3:** Integrate official IUDX Smart City pipelines (Routes, Stations, and Timetables).
- [ ] **Phase 4:** Deploy localized focus tracking camera features (Google Maps-style navigation interaction).
