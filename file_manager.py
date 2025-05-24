import os
import json

DB_PATH = "db_data"

def get_table_path(table_name):
    return os.path.join(DB_PATH, f"{table_name}.json")

def get_schema_path(table_name):
    return os.path.join(DB_PATH, f"{table_name}_schema.json")

def save_data(table_name, data):
    with open(get_table_path(table_name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_data(table_name):
    path = get_table_path(table_name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_schema(table_name, schema):
    with open(get_schema_path(table_name), "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

def load_schema(table_name):
    path = get_schema_path(table_name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def delete_table(table_name):
    os.remove(get_table_path(table_name))
    os.remove(get_schema_path(table_name))


def list_tables():
    """Liste toutes les tables (fichiers .json sans _schema)"""
    if not os.path.exists(DB_PATH):
        return []
    return [f.replace(".json", "") for f in os.listdir(DB_PATH)
            if f.endswith(".json") and not f.endswith("_schema.json")]
