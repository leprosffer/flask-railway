import sqlite3
import os
import json

DB_PATH = "data.db"

# -------------------------------
# Connexion
# -------------------------------

def connect():
    return sqlite3.connect(DB_PATH)

# -------------------------------
# Lecture des données
# -------------------------------

def load_data(table):
    table = table.strip()
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]





def add_missing_columns(table_name, required_columns):
    conn = connect()
    cur = conn.cursor()

    # Récupérer les colonnes existantes
    cur.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in cur.fetchall()]

    # Ajouter les colonnes manquantes
    for col, col_type in required_columns.items():
        if col not in existing_columns:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {col_type}")

    conn.commit()
    conn.close()




# -------------------------------
# Écriture (remplacement complet)
# -------------------------------

def save_data(table, data):
    table = table.strip()
    if not data:
        return

    conn = connect()
    cur = conn.cursor()

    cur.execute(f"DELETE FROM {table}")  # Efface tout

    for record in data:
        champs = ", ".join(record.keys())
        valeurs = tuple(record.values())
        placeholders = ", ".join(["?"] * len(valeurs))
        cur.execute(f"INSERT INTO {table} ({champs}) VALUES ({placeholders})", valeurs)

    conn.commit()
    conn.close()

# -------------------------------
# Insertion d’un enregistrement
# -------------------------------

def insert_data(table, record):
    table = table.strip()
    conn = connect()
    cur = conn.cursor()
    champs = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    cur.execute(f"INSERT INTO {table} ({champs}) VALUES ({placeholders})", tuple(record.values()))
    conn.commit()
    conn.close()

# -------------------------------
# Mise à jour d’un enregistrement
# -------------------------------

def update_data(table, user_id, new_data):
    table = table.strip()
    conn = connect()
    cur = conn.cursor()
    champs = ", ".join([f"{k}=?" for k in new_data.keys()])
    valeurs = list(new_data.values())
    valeurs.append(user_id)
    cur.execute(f"UPDATE {table} SET {champs} WHERE id = ?", valeurs)
    conn.commit()
    conn.close()

# -------------------------------
# Suppression d’un utilisateur
# -------------------------------

def delete_user(table, user_id):
    table = table.strip()
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(f"DELETE FROM {table} WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de la suppression : {e}")
        return False
    finally:
        conn.close()

# -------------------------------
# Récupération d’un utilisateur
# -------------------------------

def get_user_by_id(table, user_id):
    table = table.strip()
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))
    return None

# -------------------------------
# Liste des tables
# -------------------------------

def list_tables():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return tables

# -------------------------------
# Schéma (stocké dans fichiers JSON)
# -------------------------------

def save_schema(table_name, schema):
    schema_path = f"schemas/{table_name}.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)