import sqlite3
import json

def clean_and_update_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM first_aid_kits WHERE id <= 6")
    
    cursor.execute("SELECT id, name, inventory FROM first_aid_kits")
    rows = cursor.fetchall()
    
    for row in rows:
        id, name, inventory = row
        try:
            json_data = json.loads(inventory)
            print(f"ID: {id}, Name: {name} - JSON OK: {json_data}")
        except json.JSONDecodeError:
            print(f"ID: {id}, Name: {name} - Invalid JSON: {inventory}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clean_and_update_database()