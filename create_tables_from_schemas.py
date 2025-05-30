import os
import json
import mysql.connector
from urllib.parse import urlparse

# Connexion à la base MySQL Railway
def connect():
    url = urlparse(os.getenv("DATABASE_URL"))
    return mysql.connector.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        database=url.path.lstrip("/"),
        port=url.port or 3306
    )

# Conversion types JSON -> MySQL
def json_type_to_mysql(json_type):
    mapping = {
        "string": "VARCHAR(255)",
        "int": "INT",
        "integer": "INT",
        "float": "FLOAT",
        "boolean": "BOOLEAN",
        "email": "VARCHAR(255)",
        "password": "VARCHAR(255)",
        "list": "JSON",
        "dict": "JSON"
    }
    return mapping.get(json_type.lower(), "TEXT")

# Création d'une table MySQL à partir d'un schéma JSON
def create_table_from_schema(table_name, schema):
    columns = ["id INT AUTO_INCREMENT PRIMARY KEY"]
    for field, field_type in schema.items():
        mysql_type = json_type_to_mysql(field_type)
        columns.append(f"`{field}` {mysql_type}")
    column_definitions = ", ".join(columns)

    sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({column_definitions})"

    conn = connect()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    conn.close()
    print(f"✅ Table `{table_name}` créée ou déjà existante.")

# Parcourir tous les fichiers dans le dossier schemas/
def main():
    schema_dir = "schemas"
    for filename in os.listdir(schema_dir):
        if filename.endswith(".json"):
            table_name = filename.replace(".json", "")
            with open(os.path.join(schema_dir, filename), "r", encoding="utf-8") as f:
                schema = json.load(f)
                create_table_from_schema(table_name, schema)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
