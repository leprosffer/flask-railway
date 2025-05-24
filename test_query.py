import query_engine

donnees = [
    {"nom": "Alice", "age": 25},
    {"nom": "Bob", "age": 30},
    {"nom": "Alice", "age": 22}
]

# Filtrage
print("🔍 Filtrage nom = Alice :")
print(query_engine.filter_data(donnees, {"nom": "Alice"}))

# Projection
print("📋 Projection sur le champ 'nom' :")
print(query_engine.project_fields(donnees, ["nom"]))

# Tri
print("⬆️ Tri par âge :")
print(query_engine.sort_data(donnees, "age"))

# Pagination
print("📄 Pagination page 1, taille 2 :")
print(query_engine.paginate_data(donnees, page=1, page_size=2))
