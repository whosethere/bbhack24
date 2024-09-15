import sqlite3
import json

def update_inventory():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

   
    standard_inventory = json.dumps({
        'Nożyczki': 1,
        'Środek dezynf.': 1,
        'Szczoteczka': 1,
        'Maść gojąca': 1
    })

    defibrillator_inventory = json.dumps({
        'Defibrylator AED': 1
    })

    
    cursor.execute("""
    UPDATE first_aid_kits
    SET inventory = CASE
        WHEN type = 'Apteczka' THEN ?
        WHEN type = 'Defibrylator' THEN ?
        ELSE inventory
    END
    """, (standard_inventory, defibrillator_inventory))

    
    cursor.execute("SELECT id, name, type, inventory FROM first_aid_kits")
    rows = cursor.fetchall()

    for row in rows:
        id, name, type, inventory = row
        inventory_dict = json.loads(inventory)
        print(f"ID: {id}, Name: {name}, Type: {type}")
        print("Inventory:", inventory_dict)
        print("---")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_inventory()