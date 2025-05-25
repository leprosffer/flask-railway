import sqlite3
import os
import json


DB_PATH = "data.db"

def load_data(table):
    table = table.strip()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

def save_data(table, data):
    table = table.strip()
    if not data:
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(f"DELETE FROM {table}")

    for record in data:
        champs = ", ".join(record.keys())
        valeurs = tuple(record.values())
        placeholders = ", ".join(["?"] * len(valeurs))
        cur.execute(f"INSERT INTO {table} ({champs}) VALUES ({placeholders})", valeurs)

    conn.commit()
    conn.close()

def delete_user_by_id(table, user_id):
    table = table.strip()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def edit_user_by_id(table, user_id, new_data):
    table = table.strip()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    keys = ", ".join([f"{k}=?" for k in new_data])
    values = list(new_data.values()) + [user_id]
    cur.execute(f"UPDATE {table} SET {keys} WHERE id = ?", values)
    conn.commit()
    conn.close()

def get_user_by_id(table, user_id):
    table = table.strip()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))
    return None

def add_user(table, data):
    table = table.strip()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    champs = ", ".join(data.keys())
    valeurs = tuple(data.values())
    placeholders = ", ".join(["?"] * len(valeurs))
    cur.execute(f"INSERT INTO {table} ({champs}) VALUES ({placeholders})", valeurs)
    conn.commit()
    conn.close()
