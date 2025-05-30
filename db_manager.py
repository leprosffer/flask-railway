import os
import json
import mysql.connector
from urllib.parse import urlparse

def connect():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise Exception("La variable d'environnement DATABASE_URL n'est pas définie")

    url = urlparse(db_url)
    config = {
        "host": url.hostname,
        "user": url.username,
        "password": url.password,
        "database": url.path.lstrip('/'),
        "port": url.port or 3306
    }

    return mysql.connector.connect(**config)

def load_data(table):
    table = table.strip()
    conn = connect()
    cur = conn.cursor(dictionary=True)
    cur.execute(f"SELECT * FROM `{table}`")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_missing_columns(table_name, required_columns):
    conn = connect()
    cur = conn.cursor()

    db_name = urlparse(os.getenv("DATABASE_URL")).path.lstrip('/')

    cur.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
    """, (db_name, table_name))
    
    existing_columns = [row[0] for row in cur.fetchall()]

    for col, col_type in required_columns.items():
        if col not in existing_columns:
            sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{col}` {col_type}"
            cur.execute(sql)

    conn.commit()
    conn.close()

def save_data(table, data):
    table = table.strip()
    if not data:
        return

    conn = connect()
    cur = conn.cursor()

    cur.execute(f"DELETE FROM `{table}`")

    for record in data:
        champs = ", ".join(f"`{k}`" for k in record.keys())
        valeurs = tuple(record.values())
        placeholders = ", ".join(["%s"] * len(valeurs))
        cur.execute(f"INSERT INTO `{table}` ({champs}) VALUES ({placeholders})", valeurs)

    conn.commit()
    conn.close()

def insert_data(table, record):
    table = table.strip()
    conn = connect()
    cur = conn.cursor()
    champs = ", ".join(f"`{k}`" for k in record.keys())
    placeholders = ", ".join(["%s"] * len(record))
    cur.execute(f"INSERT INTO `{table}` ({champs}) VALUES ({placeholders})", tuple(record.values()))
    conn.commit()
    conn.close()

def update_data(table, user_id, new_data):
    table = table.strip()
    conn = connect()
    cur = conn.cursor()
    champs = ", ".join(f"`{k}` = %s" for k in new_data.keys())
    valeurs = list(new_data.values())
    valeurs.append(user_id)
    cur.execute(f"UPDATE `{table}` SET {champs} WHERE id = %s", valeurs)
    conn.commit()
    conn.close()