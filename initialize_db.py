import sqlite3
import json

def initialize_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create table for first aid kits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS first_aid_kits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT,
            inventory TEXT
        )
    ''')

    # Create table for incidents
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            description TEXT,
            photo BLOB,
            latitude REAL,
            longitude REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create table for obstacles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS obstacles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL,
            longitude REAL,
            description TEXT,
            geometry TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Predefined first aid kits and defibrillators with inventory
    predefined_kits = [
        {
            'name': 'Apteczka na Szlaku - Czantoria',
            'type': 'Apteczka',
            'latitude': 49.6828878,
            'longitude': 18.8189942,
            'status': 'Dostępna',
            'inventory': json.dumps({
                'Nożyczki': '1',
                'Środek dezynf.': '1',
                'Szczoteczka': '1',
                'Maść gojąca': '1'
            })
        },
        {
            'name': 'Apteczka na Szlaku - Soszów',
            'type': 'Apteczka',
            'latitude': 49.6393022,
            'longitude': 18.8134625,
            'status': 'Dostępna',
            'inventory': json.dumps({
                'Nożyczki': '1',
                'Środek dezynf.': '1',
                'Szczoteczka': '1',
                'Maść gojąca': '1'
            })
        },
        {
            'name': 'Defibrylator - Soszów',
            'type': 'Defibrylator',
            'latitude': 49.6393022,
            'longitude': 18.8134625,
            'status': 'Dostępny',
            'inventory': json.dumps({
                'Defibrylator AED': '1'
            })
        },
        {
            'name': 'Apteczka na Szlaku - Barania',
            'type': 'Apteczka',
            'latitude': 49.6114197,
            'longitude': 19.0107375,
            'status': 'Dostępna',
            'inventory': json.dumps({
                'Nożyczki': '1',
                'Środek dezynf.': '1',
                'Szczoteczka': '1',
                'Maść gojąca': '1'
            })
        },
        {
            'name': 'Apteczka na Szlaku - Przysłop',
            'type': 'Apteczka',
            'latitude': 49.5961014,
            'longitude': 18.9835514,
            'status': 'Dostępna',
            'inventory': json.dumps({
                'Nożyczki': '1',
                'Środek dezynf.': '1',
                'Szczoteczka': '1',
                'Maść gojąca': '1'
            })
        },
        {
            'name': 'Defibrylator - Przysłop',
            'type': 'Defibrylator',
            'latitude': 49.5961014,
            'longitude': 18.9835514,
            'status': 'Dostępny',
            'inventory': json.dumps({
                'Defibrylator AED': '1'
            })
        }
    ]


    for kit in predefined_kits:
        cursor.execute('''
            INSERT OR REPLACE INTO first_aid_kits (name, type, latitude, longitude, status, inventory)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (kit['name'], kit['type'], kit['latitude'], kit['longitude'], kit['status'], kit['inventory']))

    # Commit changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    print("Baza danych została zainicjalizowana i wstępne dane zostały dodane.")

def initialize_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Tworzenie tabel
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS first_aid_kits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT
        );

        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kit_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (kit_id) REFERENCES first_aid_kits(id)
        );

        CREATE INDEX IF NOT EXISTS idx_inventory_kit_id ON inventory_items(kit_id);
    ''')

    # Dodawanie przykładowych danych
    cursor.executemany('''
        INSERT OR REPLACE INTO first_aid_kits (name, type, latitude, longitude, status)
        VALUES (?, ?, ?, ?, ?)
    ''', [
        ('Apteczka na Szlaku - Czantoria', 'Apteczka', 49.6828878, 18.8189942, 'Dostępna'),
        ('Apteczka na Szlaku - Soszów', 'Apteczka', 49.6393022, 18.8134625, 'Dostępna'),
        ('Defibrylator - Soszów', 'Defibrylator', 49.6393022, 18.8134625, 'Dostępny'),
        # Dodaj pozostałe apteczki...
    ])

    # Dodawanie przykładowego inwentarza
    cursor.executemany('''
        INSERT OR REPLACE INTO inventory_items (kit_id, item_name, quantity, unit)
        VALUES ((SELECT id FROM first_aid_kits WHERE name = ?), ?, ?, ?)
    ''', [
        ('Apteczka na Szlaku - Czantoria', 'Nożyczki', 1, 'szt'),
        ('Apteczka na Szlaku - Czantoria', 'Środek dezynf.', 1, 'szt'),
        ('Apteczka na Szlaku - Czantoria', 'Szczoteczka', 1, 'szt'),
        ('Apteczka na Szlaku - Czantoria', 'Maść gojąca', 1, 'szt'),
        # Dodaj pozostałe elementy inwentarza dla innych apteczek...
    ])

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    print("Baza danych została zainicjalizowana i wstępne dane zostały dodane.")