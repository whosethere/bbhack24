import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import sys
import os
import gpxpy
from folium.plugins import AntPath, Draw
import sqlite3
import json
import requests
import numpy as np

# Dodanie ścieżki do modułów współdzielonych
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared')))

# Import modułu do obsługi bazy danych
from database import get_database_connection

def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
    print(url)
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_weather_grid(sw, ne, grid_size=5):
    lats = np.linspace(sw[0], ne[0], grid_size)
    lons = np.linspace(sw[1], ne[1], grid_size)
    grid = []
    for lat in lats:
        for lon in lons:
            data = get_weather_data(lat, lon)
            if data:
                grid.append({
                    'lat': lat,
                    'lon': lon,
                    'temp': data['current']['temperature_2m'],
                    'wind': data['current']['wind_speed_10m']
                })
    return grid

def load_data():
    conn = get_database_connection()
    df = pd.read_sql_query("SELECT * FROM first_aid_kits", conn)
    conn.close()
    return df

def load_gpx(file_path):
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    return points

def save_obstacle_polygon(coordinates, description):
    conn = get_database_connection()
    cursor = conn.cursor()
    geometry = json.dumps({
        "type": "Polygon",
        "coordinates": coordinates
    })
    cursor.execute("""
    INSERT INTO obstacles (geometry, description)
    VALUES (?, ?)
    """, (geometry, description))
    conn.commit()
    conn.close()

def save_obstacle_marker(lat, lon, description):
    conn = get_database_connection()
    cursor = conn.cursor()
    geometry = json.dumps({
        "type": "Point",
        "coordinates": [lat, lon]
    })
    cursor.execute("""
    INSERT INTO obstacles (geometry, description)
    VALUES (?, ?)
    """, (geometry, description))
    conn.commit()
    conn.close()

def load_obstacles():
    conn = get_database_connection()
    df = pd.read_sql_query("SELECT * FROM obstacles", conn)
    conn.close()
    return df

def main():
    st.set_page_config(layout="wide")

    st.markdown("""
    <style>
    @media (max-width: 800px) {
        .stApp {
            padding: 0 !important;
        }
        .reportview-container .main .block-container {
            padding: 0 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("Apteczka na Szlaku")
    st.sidebar.subheader("Filtry i wybór trasy")

    df = load_data()
    obstacles_df = load_obstacles()

    gpx_files = os.listdir('routes')
    selected_route = st.sidebar.selectbox("Wybierz trasę", [''] + gpx_files, index=0)

    apteczka_filter = st.sidebar.checkbox('Pokaż Apteczki', value=True)
    defibrylator_filter = st.sidebar.checkbox('Pokaż Defibrylatory', value=False)
    obstacles_filter = st.sidebar.checkbox('Pokaż Utrudnienia', value=True)
    weather_filter = st.sidebar.checkbox('Pokaż warunki pogodowe', value=False)

    # Filter data based on selected options
    if apteczka_filter and defibrylator_filter:
        filtered_df = df
    elif apteczka_filter:
        filtered_df = df[df['type'] == 'Apteczka']
    elif defibrylator_filter:
        filtered_df = df[df['type'] == 'Defibrylator']
    else:
        filtered_df = pd.DataFrame(columns=df.columns)

    # Set the map center to the new coordinates
    map_center = [49.6460, 18.8694]

    m = folium.Map(location=map_center, zoom_start=11)

    # Add markers for first aid kits and defibrillators
    for idx, row in filtered_df.iterrows():
        if row['type'] == 'Apteczka':
            icon_color = 'red'
            icon = 'plus'
        else:
            icon_color = 'blue'
            icon = 'bolt'

        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['name']} ({row['type']})\nStatus: {row['status']}",
            icon=folium.Icon(color=icon_color, icon=icon, prefix='fa')
        ).add_to(m)

    # Display obstacles, including markers and polygons
    if obstacles_filter:
        for idx, row in obstacles_df.iterrows():
            if 'geometry' in row and row['geometry']:
                try:
                    geometry = json.loads(row['geometry'])
                    if geometry['type'] == 'Point':
                        lon, lat = geometry['coordinates']
                        folium.Marker(
                            location=[lat, lon],
                            popup=f"Utrudnienie: {row['description']}",
                            icon=folium.Icon(color='orange', icon='warning-sign', prefix='fa')
                        ).add_to(m)
                    elif geometry['type'] == 'Polygon':
                        folium.GeoJson(
                            geometry,
                            name=f"Utrudnienie: {row['description']}",
                            tooltip=f"Utrudnienie: {row['description']}",
                            style_function=lambda x: {'fillColor': 'orange', 'color': 'orange'}
                        ).add_to(m)
                except json.JSONDecodeError as e:
                    print(f"Error parsing geometry JSON: {e}")
            elif 'latitude' in row and 'longitude' in row:
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=f"Utrudnienie: {row['description']}",
                    icon=folium.Icon(color='orange', icon='warning-sign', prefix='fa')
                ).add_to(m)

    if weather_filter:
        bounds = m.get_bounds()
        sw = bounds[0]  # [lat, lon] południowo-zachodniego rogu
        ne = bounds[1]  # [lat, lon] północno-wschodniego rogu
        weather_grid = get_weather_grid(sw, ne)
        for point in weather_grid:
            folium.Marker(
                location=[point['lat'], point['lon']],
                popup=f"Temperatura: {point['temp']}°C<br>Prędkość wiatru: {point['wind']} km/h",
                icon=folium.Icon(color='green', icon='cloud', prefix='fa')
            ).add_to(m)

    if selected_route:
        route_points = load_gpx(os.path.join('routes', selected_route))
        AntPath(route_points, color="green", weight=2.5, opacity=0.8).add_to(m)

        if route_points:
            sw = [min(p[0] for p in route_points), min(p[1] for p in route_points)]
            ne = [max(p[0] for p in route_points), max(p[1] for p in route_points)]
            m.fit_bounds([sw, ne])

    draw = Draw(
        draw_options={
            'polyline': False,
            'polygon': False,
            'circle': False,
            'rectangle': False,
            'marker': True,  # Allow marker addition
            'circlemarker': False,
        },
        edit_options={
            'edit': False,
            'remove': False,
        },
    )
    m.add_child(draw)

    st.markdown("## Mapa lokalizacji apteczek, defibrylatorów i utrudnień")
    map_data = st_folium(m, width=1600, height=650, key="map")

    # Handle marker addition and limit to one
    if map_data and 'last_active_drawing' in map_data and map_data['last_active_drawing']:
        draw_data = map_data['last_active_drawing']
        geometry = draw_data['geometry']
        if geometry['type'] == 'Point':
            lat, lon = geometry['coordinates']
            st.session_state.new_obstacle = {'type': 'marker', 'coordinates': [lat, lon]}

    if 'new_obstacle' in st.session_state:
        with st.form("obstacle_form"):
            st.write("Dodawanie utrudnienia na trasie")
            description = st.text_input("Opis utrudnienia")
            submitted = st.form_submit_button("Zgłoś utrudnienie")
            if submitted:
                coordinates = st.session_state.new_obstacle['coordinates']
                save_obstacle_marker(coordinates[0], coordinates[1], description)
                st.success("Utrudnienie zostało zgłoszone!")
                del st.session_state.new_obstacle
                st.rerun()

if __name__ == "__main__":
    main()
