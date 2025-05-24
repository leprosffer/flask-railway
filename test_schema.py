import schema_manager

# Création d'une table "personnes" avec nom et âge
schema_manager.create_schema("personnes", {
    "nom": "string",
    "age": "integer"
})

# Affichage du schéma
schema_manager.list_schema("personnes")
