import sqlite3
import os
import json

DB_PATH = "database.db"

def connect():
    return sqlite3.connect(DB_PATH)

def table_exists(table):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def create_table(table, schema):
    conn = connect()
    cur = conn.cursor()
    champs = ', '.join([f"{col} TEXT" for col in schema])
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {champs})")
    conn.commit()
    conn.close()

def load_data(table):
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_data(table, data_list):
    if not data_list:
        return
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table}")  # reset
    for data in data_list:
        cols = ', '.join(data.keys())
        vals = tuple(data.values())
        placeholders = ', '.join(['?'] * len(data))
        cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", vals)
    conn.commit()
    conn.close()

def insert_data(table, data):
    conn = connect()
    cur = conn.cursor()
    cols = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", tuple(data.values()))
    conn.commit()
    conn.close()

def update_data(table, id_val, new_data):
    conn = connect()
    cur = conn.cursor()
    sets = ', '.join([f"{k}=?" for k in new_data])
    values = list(new_data.values()) + [id_val]
    cur.execute(f"UPDATE {table} SET {sets} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_data(table, id_val):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = ?", (id_val,))
    conn.commit()
    conn.close()
