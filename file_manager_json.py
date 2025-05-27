import sqlite3
import os
import json
DB_PATH = "data.db"

def connect():
    return sqlite3.connect(DB_PATH)

def list_tables():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def load_data(table):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table}")
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        return data
    except sqlite3.Error:
        return []
    finally:
        conn.close()

def save_data(table, data):
    """Efface et remplace toutes les données d'une table (utiliser avec précaution)."""
    if not data:
        return

    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table}")
    champs = data[0].keys()
    for record in data:
        values = tuple(record[ch] for ch in champs)
        placeholders = ", ".join(["?"] * len(champs))
        champs_str = ", ".join(champs)
        cursor.execute(f"INSERT INTO {table} ({champs_str}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()

def insert_data(table, record):
    conn = connect()
    cursor = conn.cursor()
    champs = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    cursor.execute(f"INSERT INTO {table} ({champs}) VALUES ({placeholders})", tuple(record.values()))
    conn.commit()
    conn.close()

def update_data(table, id, record):
    conn = connect()
    cursor = conn.cursor()
    champs = ", ".join([f"{k}=?" for k in record.keys()])
    valeurs = list(record.values())
    valeurs.append(id)
    cursor.execute(f"UPDATE {table} SET {champs} WHERE id=?", valeurs)
    conn.commit()
    conn.close()

def delete_data(table, id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id=?", (id,))
    conn.commit()
    conn.close()

def load_schema(table_name):
    schema_path = os.path.join("schemas", f"{table_name}.json")
    print(">>> Recherche du schéma :", schema_path)  # Debug temporaire
    if not os.path.exists(schema_path):
        return None
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)