import data_validator

schema = {
    "nom": "string",
    "age": "integer",
    "actif": "boolean"
}

# Donnée correcte
d1 = {"nom": "Jean", "age": 30, "actif": True}

# Donnée avec erreurs
d2 = {"nom": "Marie", "age": "abc", "actif": "oui"}

print("✅ Donnée 1 validée :", data_validator.validate_record(d1, schema))
print("✅ Donnée 2 validée :", data_validator.validate_record(d2, schema))
