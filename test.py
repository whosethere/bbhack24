import sqlite3
import json

def check_inventory_json():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, inventory FROM first_aid_kits")
    rows = cursor.fetchall()
    
    for row in rows:
        id, name, inventory = row
        if inventory is None:
            print(f"ID: {id}, Name: {name} - Inventory is NULL")
        else:
            try:
                json.loads(inventory)
                print(f"ID: {id}, Name: {name} - JSON OK")
            except json.JSONDecodeError:
                print(f"ID: {id}, Name: {name} - Invalid JSON: {inventory}")
    
    conn.close()

if __name__ == "__main__":
    check_inventory_json()