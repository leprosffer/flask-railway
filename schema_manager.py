import file_manager
import file_manager
import os
import json

def create_schema(table_name, fields):
    """
    Crée un nouveau schéma pour une table
    fields doit être un dictionnaire: {"nom": "string", "age": "integer"}
    """
    if file_manager.load_schema(table_name) is not None:
        raise Exception(f"Le schéma de la table '{table_name}' existe déjà.")

    file_manager.save_schema(table_name, fields)
    file_manager.save_data(table_name, [])
    print(f"✅ Schéma de la table '{table_name}' créé avec les champs : {fields}")

def get_schema(table_name):
    schema = file_manager.load_schema(table_name)
    if schema is None:
        raise Exception(f"Le schéma de la table '{table_name}' n'existe pas.")
    return schema

def add_field(table_name, field_name, field_type):
    schema = get_schema(table_name)
    if field_name in schema:
        raise Exception(f"Le champ '{field_name}' existe déjà.")
    schema[field_name] = field_type
    file_manager.save_schema(table_name, schema)
    print(f"✅ Champ '{field_name}' ajouté au schéma de '{table_name}'.")

def delete_field(table_name, field_name):
    schema = get_schema(table_name)
    if field_name not in schema:
        raise Exception(f"Le champ '{field_name}' n'existe pas.")
    del schema[field_name]
    file_manager.save_schema(table_name, schema)
    print(f"✅ Champ '{field_name}' supprimé du schéma de '{table_name}'.")

def list_schema(table_name):
    schema = get_schema(table_name)
    print(f"📋 Schéma de la table '{table_name}':")
    for field, ftype in schema.items():
        print(f"  - {field}: {ftype}")

def load_schema(table_name):
    schema_path = f"schemas/{table_name}.json"
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def supprimer_table(table_name):
    data_path = f"db_data/{table_name}.json"
    schema_path = f"db_data/schema/{table_name}_schema.json"

    if os.path.exists(data_path):
        os.remove(data_path)
        print(f"✅ Données de la table '{table_name}' supprimées.")
    else:
        print(f"⚠️ Fichier de données introuvable pour la table '{table_name}'.")

    if os.path.exists(schema_path):
        os.remove(schema_path)
        print(f"✅ Schéma de la table '{table_name}' supprimé.")
    else:
        print(f"⚠️ Fichier de schéma introuvable pour la table '{table_name}'.")
def lister_tables():
    fichiers = os.listdir("db_data")
    tables = []
    for fichier in fichiers:
        if fichier.endswith("_schema.json"):
            nom_table = fichier.replace("_schema.json", "")
            tables.append(nom_table)
    return tables
