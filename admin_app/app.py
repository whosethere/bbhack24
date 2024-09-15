import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime

# Funkcja do połączenia z bazą danych
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Funkcja do pobrania wszystkich apteczek
def get_all_first_aid_kits():
    conn = get_db_connection()
    kits = conn.execute('SELECT * FROM first_aid_kits').fetchall()
    conn.close()
    return kits

# Funkcja do pobrania inwentarza dla danej apteczki
def get_kit_inventory(kit_id):
    conn = get_db_connection()
    inventory = conn.execute('SELECT * FROM inventory_items WHERE kit_id = ?', (kit_id,)).fetchall()
    conn.close()
    return inventory

# Funkcja do aktualizacji statusu apteczki
def update_kit_status(kit_id, new_status):
    conn = get_db_connection()
    conn.execute('UPDATE first_aid_kits SET status = ? WHERE id = ?', (new_status, kit_id))
    conn.commit()
    conn.close()

# Funkcja do aktualizacji inwentarza apteczki
def update_kit_inventory(kit_id, new_inventory):
    conn = get_db_connection()
    for item in new_inventory:
        conn.execute('''
            INSERT OR REPLACE INTO inventory_items (kit_id, item_name, quantity, unit, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (kit_id, item['item_name'], item['quantity'], item['unit'], datetime.now()))
    conn.commit()
    conn.close()

# Konfiguracja strony Streamlit
st.set_page_config(page_title="Panel Admina - Apteczki", layout="wide")
st.title("Panel Administratora - Apteczki na Szlaku")

# Pobierz wszystkie apteczki
kits = get_all_first_aid_kits()

# Wyświetl tabelę z apteczkami
st.subheader("Lista Apteczek i Defibrylatorów")
df = pd.DataFrame(kits)
st.dataframe(df)

# Wybór apteczki do edycji
selected_kit_id = st.selectbox("Wybierz apteczkę do edycji", options=[kit['id'] for kit in kits], format_func=lambda x: next(kit['name'] for kit in kits if kit['id'] == x))

# Edycja wybranej apteczki
if selected_kit_id:
    st.subheader(f"Edycja apteczki: {next(kit['name'] for kit in kits if kit['id'] == selected_kit_id)}")
    
    selected_kit = next(kit for kit in kits if kit['id'] == selected_kit_id)
    
    # Edycja statusu
    new_status = st.text_input("Status", value=selected_kit['status'])
    if st.button("Aktualizuj status"):
        update_kit_status(selected_kit_id, new_status)
        st.success("Status zaktualizowany!")
    
    # Edycja inwentarza
    st.subheader("Inwentarz")
    inventory = get_kit_inventory(selected_kit_id)
    new_inventory = []
    for item in inventory:
        col1, col2, col3 = st.columns(3)
        with col1:
            item_name = st.text_input("Nazwa przedmiotu", value=item['item_name'], key=f"name_{item['id']}")
        with col2:
            quantity = st.number_input("Ilość", value=item['quantity'], min_value=0, key=f"quantity_{item['id']}")
        with col3:
            unit = st.text_input("Jednostka", value=item['unit'], key=f"unit_{item['id']}")
        new_inventory.append({"item_name": item_name, "quantity": quantity, "unit": unit})
    
    if st.button("Dodaj nowy przedmiot"):
        new_inventory.append({"item_name": "", "quantity": 0, "unit": ""})
    
    if st.button("Aktualizuj inwentarz"):
        update_kit_inventory(selected_kit_id, new_inventory)
        st.success("Inwentarz zaktualizowany!")

# Mapa z lokalizacjami apteczek
st.subheader("Mapa Apteczek i Defibrylatorów")
map_data = pd.DataFrame({
    'lat': [kit['latitude'] for kit in kits],
    'lon': [kit['longitude'] for kit in kits],
    'name': [kit['name'] for kit in kits]
})
st.map(map_data)

# Dodatkowe opcje administracyjne
st.subheader("Opcje administracyjne")

# Dodawanie nowej apteczki
if st.checkbox("Dodaj nową apteczkę"):
    new_kit_name = st.text_input("Nazwa nowej apteczki")
    new_kit_type = st.selectbox("Typ", options=["Apteczka", "Defibrylator"])
    new_kit_lat = st.number_input("Szerokość geograficzna", format="%.7f")
    new_kit_lon = st.number_input("Długość geograficzna", format="%.7f")
    new_kit_status = st.text_input("Status")
    
    if st.button("Dodaj apteczkę"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO first_aid_kits (name, type, latitude, longitude, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (new_kit_name, new_kit_type, new_kit_lat, new_kit_lon, new_kit_status))
        conn.commit()
        conn.close()
        st.success("Nowa apteczka dodana!")

# Usuwanie apteczki
if st.checkbox("Usuń apteczkę"):
    kit_to_delete = st.selectbox("Wybierz apteczkę do usunięcia", options=[kit['id'] for kit in kits], format_func=lambda x: next(kit['name'] for kit in kits if kit['id'] == x))
    if st.button("Usuń wybraną apteczkę"):
        conn = get_db_connection()
        conn.execute('DELETE FROM first_aid_kits WHERE id = ?', (kit_to_delete,))
        conn.execute('DELETE FROM inventory_items WHERE kit_id = ?', (kit_to_delete,))
        conn.commit()
        conn.close()
        st.success("Apteczka usunięta!")