# shared/database.py

import sqlite3
import os

def get_database_connection():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database.db'))
    
    conn = sqlite3.connect(db_path)
    return conn