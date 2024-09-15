import streamlit as st
import pandas as pd
import sys
import os
import json
from PIL import Image
import io
import asyncio

# Dodaj ścieżkę do katalogu głównego projektu
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
    
    # Sprawdź, czy połączenie z bazą danych działa
    try:
        conn = get_database_connection()
        conn.close()
        st.write("Połączenie z bazą danych działa poprawnie")
    except Exception as e:
        st.error(f"Błąd podczas łączenia z bazą danych: {str(e)}")
except ImportError as e:
    st.error(f"Błąd importu modułu 'database': {str(e)}")
    st.error("Sprawdź, czy plik database.py znajduje się w katalogu 'shared' i czy nie zawiera błędów.")

# Import funkcji API do analizy poziomu napełnienia butelki
try:
    from bottle_analysis_api import analyze_bottle_fill_level
    st.write("Funkcja analyze_bottle_fill_level zaimportowana pomyślnie")
except ImportError as e:
    st.error(f"Błąd importu funkcji analyze_bottle_fill_level: {str(e)}")
    st.error("Sprawdź, czy plik bottle_analysis_api.py znajduje się we właściwym katalogu.")

def load_first_aid_kits():
    conn = get_database_connection()
    try:
        query = '''
        SELECT fak.*, 
               json_group_object(ii.item_name, json_object('quantity', ii.quantity, 'unit', ii.unit)) as inventory
        FROM first_aid_kits fak
        LEFT JOIN inventory_items ii ON fak.id = ii.kit_id
        GROUP BY fak.id
        '''
        df = pd.read_sql_query(query, conn)
        
        def parse_inventory(inventory_json):
            try:
                return json.loads(inventory_json)
            except json.JSONDecodeError:
                st.error(f"Błąd dekodowania JSON: {inventory_json}")
                return {}

        df['inventory'] = df['inventory'].apply(parse_inventory)
        return df
    finally:
        conn.close()

def update_inventory_item(kit_id, item_name, new_quantity):
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO inventory_items (kit_id, item_name, quantity, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (kit_id, item_name, new_quantity))
        
        conn.commit()
        st.write(f"Zaktualizowano {item_name} dla apteczki o ID {kit_id}")
        
        # Sprawdź, czy update się powiódł
        cursor.execute('''
            SELECT quantity, unit FROM inventory_items 
            WHERE kit_id = ? AND item_name = ?
        ''', (kit_id, item_name))
        result = cursor.fetchone()
        
        if result:
            st.write(f"Nowa ilość {item_name}: {result['quantity']} {result['unit']}")
            return True
        else:
            st.error(f"Nie znaleziono elementu {item_name} dla apteczki o ID {kit_id}")
            return False
    except Exception as e:
        st.error(f"Błąd podczas aktualizacji bazy danych: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def load_first_aid_kits():
    conn = get_database_connection()
    df = pd.read_sql_query("SELECT * FROM first_aid_kits", conn)
    conn.close()

    def parse_inventory(inventory_json):
        try:
            return json.loads(inventory_json)
        except json.JSONDecodeError:
            st.error(f"Błąd dekodowania JSON: {inventory_json}")
            return {}

    df['inventory'] = df['inventory'].apply(parse_inventory)
    return df

def update_first_aid_kit_inventory(kit_id, new_inventory):
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        # Serializuj słownik do JSON
        inventory_json = json.dumps(new_inventory)
        
        st.write(f"Debug: JSON do zapisu: {inventory_json}")
        
        cursor.execute(
            "UPDATE first_aid_kits SET inventory = ? WHERE id = ?",
            (inventory_json, kit_id)
        )
        conn.commit()
        st.write(f"Zaktualizowano inwentarz dla apteczki o ID {kit_id}")
        
        # Sprawdź, czy update się powiódł
        cursor.execute("SELECT inventory FROM first_aid_kits WHERE id = ?", (kit_id,))
        result = cursor.fetchone()
        if result:
            updated_inventory = result[0]
            st.write(f"Debug: Odczytany inwentarz po aktualizacji: {updated_inventory}")
        else:
            st.error(f"Nie znaleziono apteczki o ID {kit_id} po aktualizacji")
    except Exception as e:
        st.error(f"Błąd podczas aktualizacji bazy danych: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    
    return updated_inventory if 'updated_inventory' in locals() else None

async def main():
    st.title("Aktualizacja stanu środka do dezynfekcji")

    try:
        # Wczytaj dane apteczek
        first_aid_kits = load_first_aid_kits()

        # Wybierz apteczkę
        selected_kit = st.selectbox(
            "Wybierz apteczkę:",
            options=first_aid_kits['name'].tolist()
        )

        # Znajdź id wybranej apteczki
        kit_id = first_aid_kits[first_aid_kits['name'] == selected_kit]['id'].values[0]
        st.write(f"Debug: Wybrane ID apteczki: {kit_id}")

        # Prześlij zdjęcie
        uploaded_file = st.file_uploader("Prześlij zdjęcie środka do dezynfekcji", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            # Wyświetl przesłane zdjęcie
            image = Image.open(uploaded_file)
            st.image(image, caption="Przesłane zdjęcie", use_column_width=True)

            if st.button("Analizuj stan środka do dezynfekcji"):
                # Konwertuj obraz na bajty
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()

                # Analizuj obraz używając API
                fill_level = await analyze_bottle_fill_level(img_byte_arr)
                st.write(f"Otrzymany poziom napełnienia: {fill_level}")

                # Aktualizacja bazy danych
                if update_inventory_item(kit_id, 'Środek dezynf.', fill_level):
                    st.success("Stan środka do dezynfekcji został pomyślnie zaktualizowany w bazie danych.")
                else:
                    st.error("Wystąpił problem z aktualizacją bazy danych.")

                # Ponowne wczytanie danych z bazy
                updated_kits = load_first_aid_kits()
                updated_kit = updated_kits[updated_kits['id'] == kit_id]
                
                if not updated_kit.empty:
                    updated_inventory = updated_kit['inventory'].values[0]
                    st.write(f"Aktualny stan inwentarza:")
                    for item, details in updated_inventory.items():
                        st.write(f"- {item}: {details['quantity']} {details['unit']}")
                else:
                    st.error(f"Nie znaleziono apteczki o ID {kit_id} po aktualizacji")

    except Exception as e:
        st.error(f"Wystąpił nieoczekiwany błąd: {str(e)}")
        st.write(f"Debug: Pełny błąd: {str(e)}")
        import traceback
        st.write(f"Debug: Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())