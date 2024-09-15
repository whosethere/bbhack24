import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import sys
import os
from geopy.distance import geodesic
import json
import sqlite3

# Dodanie ścieżki do katalogu głównego projektu
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)
st.write(f"Dodana ścieżka projektu: {project_root}")

# Sprawdź, czy plik database.py istnieje
database_file = os.path.join(project_root, 'shared', 'database.py')
if os.path.exists(database_file):
    st.write(f"Plik database.py istnieje: {database_file}")
else:
    st.error(f"Plik database.py nie istnieje w ścieżce: {database_file}")

# Spróbuj zaimportować moduł database
try:
    from shared.database import get_database_connection
    st.write("Moduł 'database' zaimportowany pomyślnie")
except ImportError as e:
    st.error(f"Błąd importu modułu 'database': {str(e)}")
    st.error("Sprawdź, czy plik database.py znajduje się w katalogu 'shared' i czy nie zawiera błędów.")

def load_data():
    try:
        conn = get_database_connection()
        df = pd.read_sql_query("SELECT * FROM first_aid_kits", conn)
        conn.close()
        
        def safe_json_loads(x):
            try:
                return json.loads(x) if x else {}
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON data: {x}")
                return {}

        df['inventory'] = df['inventory'].apply(safe_json_loads)
        
        # Dodaj debugowanie
        print("Loaded data:")
        print(df[['name', 'type', 'inventory']])
        
        return df
    except Exception as e:
        st.error(f"Błąd podczas ładowania danych: {str(e)}")
        return pd.DataFrame()

def find_nearest_first_aid_kit(lat, lon, df):
    distances = df.apply(lambda row: geodesic((lat, lon), (row['latitude'], row['longitude'])).km, axis=1)
    nearest_index = distances.idxmin()
    return df.loc[nearest_index]

def create_initial_map(user_lat, user_lon):
    m = folium.Map(location=[user_lat, user_lon], zoom_start=12)
    
    # Add marker for user location
    folium.Marker(
        [user_lat, user_lon],
        popup="Twoja lokalizacja",
        icon=folium.Icon(color='green', icon='user', prefix='fa')
    ).add_to(m)
    
    return m

def update_map_with_nearest_kit(m, user_lat, user_lon, nearest_kit):
    # Add marker for nearest first aid kit
    folium.Marker(
        [nearest_kit['latitude'], nearest_kit['longitude']],
        popup=f"{nearest_kit['name']} ({nearest_kit['type']})",
        icon=folium.Icon(color='red', icon='plus', prefix='fa')
    ).add_to(m)
    
    # Draw a straight line between user location and nearest kit
    line_coordinates = [
        [user_lat, user_lon],
        [nearest_kit['latitude'], nearest_kit['longitude']]
    ]
    folium.PolyLine(
        line_coordinates,
        color="blue",
        weight=2.5,
        opacity=1
    ).add_to(m)
    
    # Fit the map to show both markers
    m.fit_bounds([
        [user_lat, user_lon],
        [nearest_kit['latitude'], nearest_kit['longitude']]
    ])
    
    return m

def main():
    st.title("Znajdź najbliższą apteczkę")

    # Hardcoded user location
    user_lat, user_lon = 49.680458, 18.810936  # 49°40'58.4"N 18°49'08.4"E

    # Initialize map
    if 'map' not in st.session_state:
        st.session_state.map = create_initial_map(user_lat, user_lon)

    # Display map
    st_map = st_folium(st.session_state.map, width=800, height=600, key="map")

    df = load_data()
    
    if st.button("Znajdź najbliższą apteczkę"):
        if not df.empty:
            nearest_kit = find_nearest_first_aid_kit(user_lat, user_lon, df)
            
            # Update map
            st.session_state.map = update_map_with_nearest_kit(st.session_state.map, user_lat, user_lon, nearest_kit)
            
            # Store the nearest kit information in session state
            st.session_state.nearest_kit = nearest_kit
            
            # Refresh map
            st.rerun()
        else:
            st.error("Nie można znaleźć najbliższej apteczki. Brak danych.")
    
    # Display information about the nearest first aid kit if it has been found
    if 'nearest_kit' in st.session_state:
        nearest_kit = st.session_state.nearest_kit
        st.write(f"Najbliższa apteczka: {nearest_kit['name']}")
        st.write(f"Typ: {nearest_kit['type']}")
        st.write(f"Status: {nearest_kit['status']}")
        st.write(f"Odległość: {geodesic((user_lat, user_lon), (nearest_kit['latitude'], nearest_kit['longitude'])).km:.2f} km")
        
        # Display inventory
        st.write("Zawartość apteczki:")
        for item, count in nearest_kit['inventory'].items():
            st.write(f"- {item}: {count}")

if __name__ == "__main__":
    main()