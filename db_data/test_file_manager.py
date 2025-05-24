import file_manager

# Données et schéma fictifs
table = "utilisateurs"
data = [{"id": 1, "nom": "Alice"}, {"id": 2, "nom": "Bob"}]
schema = {"id": "integer", "nom": "string"}

# Sauvegarder les données et le schéma
file_manager.save_data(table, data)
file_manager.save_schema(table, schema)

# Recharger et afficher
print("=== Données ===")
print(file_manager.load_data(table))

print("=== Schéma ===")
print(file_manager.load_schema(table))
