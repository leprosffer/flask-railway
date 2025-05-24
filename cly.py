import file_manager
import schema_manager
import data_validator
import query_engine
import session_manager
from session_manager import get_active_table


def afficher_menu():
    print("\n=== Menu Principal ===")
    print("1. Créer une table")
    print("2. Ajouter un enregistrement")
    print("3. Voir les données")
    print("4. Voir la structure d'une table")
    print("5. Quitter")
    print("6. Supprimer une table")
    print("7. 📋 Créer un formulaire utilisateur prédéfini")
    print("8. ➕ Ajouter un utilisateur via formulaire")
    print("9. choisir de table a rendre actif pour la sauvegarde des donnees")

def creer_table():
    nom_table = input("Nom de la table : ")
    champs = {}
    while True:
        nom_champ = input("Nom du champ (laisser vide pour terminer) : ")
        if not nom_champ:
            break
        type_champ = input(f"Type de {nom_champ} (string, int, float, bool, email, password) : ")
        champs[nom_champ] = type_champ

    if not champs:
        print("⚠️ Impossible de créer une table sans champs.")
        return

    try:
        schema_manager.create_schema(nom_table, champs)
        file_manager.save_data(nom_table, [])
        print(f"✅ Schéma de la table '{nom_table}' créé avec les champs : {champs}")
        print("✅ Table créée avec succès.")
    except Exception as e:
        print(f"❌ Erreur : {e}")

def ajouter_enregistrement():
    nom_table = input("Nom de la table : ")
    schema = schema_manager.load_schema(nom_table)
    if not schema:
        print("⚠️ Table introuvable.")
        return
    enregistrement = {}
    for champ, type_attendu in schema.items():
        valeur = input(f"{champ} ({type_attendu}) : ")
        enregistrement[champ] = data_validator.validate_value(valeur, type_attendu)
    file_manager.save_data(nom_table, file_manager.load_data(nom_table) + [enregistrement])
    print("✅ Enregistrement ajouté.")

def formulaire_utilisateur():
    nom_table = input("🔤 Nom de la nouvelle table pour le formulaire : ")

    # Champs prédéfinis
    champs = {
        "nom": "string",
        "prenom": "string",
        "genre": "string",
        "adresse_mail": "email",
        "mot_de_passe": "password"
    }

    try:
        schema_manager.create_schema(nom_table, champs)
        file_manager.save_data(nom_table, [])
        print(f"✅ Formulaire créé sous la table '{nom_table}'.")
    except Exception as e:
        print(f"⚠️ Impossible de créer la table : {e}")



def ajouter_utilisateur():
    nom_table = input("📦 Nom de la table à utiliser pour ajouter l'utilisateur : ")

    schema = schema_manager.load_schema(nom_table)
    if not schema:
        print("⚠️ Table introuvable.")
        return

    enregistrement = {}
    for champ, type_attendu in schema.items():
        valeur = input(f"{champ} ({type_attendu}) : ")
        enregistrement[champ] = data_validator.validate_value(valeur, type_attendu)

    data = file_manager.load_data(nom_table)
    data.append(enregistrement)
    file_manager.save_data(nom_table, data)
    print("✅ Utilisateur ajouté avec succès.")
    nom_table = get_active_table()
    if not nom_table:
        print("⚠️ Aucune table active sélectionnée. Utilisez l'option 9 pour en choisir une.")
        return




def voir_donnees():
    nom_table = input("Nom de la table : ")
    data = file_manager.load_data(nom_table)
    if not data:
        print("⚠️ Aucune donnée trouvée.")
        return
    for i, item in enumerate(data, start=1):
        print(f"{i}. {item}")

def voir_structure():
    nom_table = input("Nom de la table : ")
    schema = schema_manager.load_schema(nom_table)
    if not schema:
        print("⚠️ Schéma introuvable.")
        return
    print("📐 Structure de la table :")
    for champ, type_ in schema.items():
        print(f" - {champ} : {type_}")

def lancer_interface():
    while True:
        afficher_menu()
        choix = input("Entrez votre choix : ")
        if choix == "1":
            creer_table()
        elif choix == "2":
            ajouter_enregistrement()
        elif choix == "3":
            voir_donnees()
        elif choix == "4":
            voir_structure()
        elif choix == "5":
            print("👋 Au revoir !")
            break
        elif choix == "6":
            nom_table = input("Nom de la table à supprimer : ")
            schema_manager.supprimer_table(nom_table)
        elif choix == "7":
            formulaire_utilisateur()
        elif choix == "8":
            ajouter_utilisateur()
        elif choix == "9":
            nom = input("Nom de la table à utiliser comme formulaire actif : ")
            session_manager.set_active_table(nom)
            print(f"✅ Table '{nom}' sélectionnée comme formulaire actif.")
        else:
            print("❌ Choix invalide.")

if __name__ == "__main__":
    lancer_interface()
