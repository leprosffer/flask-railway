import re

def validate_value(value, expected_type):
    try:
        if expected_type in ("string", "str"):
            return str(value)
        elif expected_type in ("integer", "int"):
            return int(value)
        elif expected_type == "float":
            return float(value)
        elif expected_type in ("boolean", "bool"):
            return str(value).lower() in ("true", "1", "yes", "oui")
        elif expected_type == "email":
            if re.match(r"[^@]+@[^@]+\.[^@]+", value):
                return value
            else:
                print(f"[⚠️] Email invalide : {value}")
                return None
        elif expected_type == "password":
            if len(value) >= 6:
                return value
            else:
                print(f"[⚠️] Mot de passe trop court : {value}")
                return None
        else:
            raise ValueError(f"Type inconnu : {expected_type}")
    except (ValueError, TypeError):
        print(f"[⚠️] Type incorrect : {value} n’est pas un {expected_type}. Utilisation de None.")
        return None

def validate_record(record, schema):
    validated = {}
    for field, field_type in schema.items():
        if field in record:
            validated[field] = validate_value(record[field], field_type)
        else:
            validated[field] = None  # Valeur manquante = None
    return validated
