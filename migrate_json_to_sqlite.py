import os
import json
import sqlite3
from schema_manager import load_schema
from file_manager import list_tables

DB_PATH = "data.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = list_tables()
    print("Tables JSON à migrer :", tables)  # <- ligne de vérification

    for table in tables:
        print(f"Migration de la table : {table}")
        schema = load_schema(table)
        if not schema:
            print(f"❌ Schéma introuvable pour {table}, ignoré.")
            continue

        # Création de la table SQL
        columns_sql = ", ".join([f"{champ} TEXT" for champ in schema])
        columns_sql = "id INTEGER PRIMARY KEY AUTOINCREMENT, " + columns_sql
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        cursor.execute(f"CREATE TABLE {table} ({columns_sql})")

        # Lecture des données JSON
        data_path = f"db_data/{table}.json"
        if not os.path.exists(data_path):
            continue

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for record in data:
            champs = ", ".join(record.keys())
            valeurs = tuple(record.values())
            placeholders = ", ".join(["?"] * len(valeurs))
            cursor.execute(f"INSERT INTO {table} ({champs}) VALUES ({placeholders})", valeurs)

    conn.commit()
    conn.close()
    print("✅ Migration terminée avec succès.")

if __name__ == "__main__":
    migrate()
