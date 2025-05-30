import mysql.connector
from dotenv import load_dotenv
from urllib.parse import urlparse
import os
import json

load_dotenv()

def get_connection():
    db_url = os.getenv("DATABASE_URL")
    result = urlparse(db_url)

    return mysql.connector.connect(
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port,
        database=result.path[1:]
    )

def list_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables

def load_data(table):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT * FROM {table}")
        data = cursor.fetchall()
        return data
    except mysql.connector.Error:
        return []
    finally:
        cursor.close()
        conn.close()

def insert_data(table, record):
    conn = get_connection()
    cursor = conn.cursor()
    champs = ", ".join(record.keys())
    placeholders = ", ".join(["%s"] * len(record))
    valeurs = tuple(record.values())
    cursor.execute(f"INSERT INTO {table} ({champs}) VALUES ({placeholders})", valeurs)
    conn.commit()
    cursor.close()
    conn.close()

def update_data(table, id, record):
    conn = get_connection()
    cursor = conn.cursor()
    champs = ", ".join([f"{k}=%s" for k in record.keys()])
    valeurs = list(record.values())
    valeurs.append(id)
    cursor.execute(f"UPDATE {table} SET {champs} WHERE id=%s", valeurs)
    conn.commit()
    cursor.close()
    conn.close()

def delete_data(table, id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

def get_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, prenom FROM utilisateurs")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        nom VARCHAR(255),
        prenom VARCHAR(255),
        genre VARCHAR(50),
        adresse_mail VARCHAR(255) UNIQUE,
        mot_de_passe TEXT
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def save_data(table, data):
    if not data:
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table}")
    champs = data[0].keys()
    for record in data:
        values = tuple(record[ch] for ch in champs)
        placeholders = ", ".join(["%s"] * len(champs))
        champs_str = ", ".join(champs)
        cursor.execute(f"INSERT INTO {table} ({champs_str}) VALUES ({placeholders})", values)
    conn.commit()
    cursor.close()
    conn.close()

def load_schema(table_name):
    schema_path = os.path.join("schemas", f"{table_name}.json")
    print(">>> Recherche du schéma :", schema_path)  # Debug temporaire
    if not os.path.exists(schema_path):
        return None
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)