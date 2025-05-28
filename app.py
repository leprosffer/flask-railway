from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import re
import csv
import io

from flask import Flask, render_template_string, request, redirect, url_for, session, Response, get_flashed_messages, flash,render_template
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv

import session_manager
import schema_manager
import db_manager as file_manager
import data_validator

# --- Chargement des variables d’environnement ---
load_dotenv()

# --- Initialisation de Flask ---
app = Flask(__name__)

# --- Configuration sécurisée de Flask ---
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
if not app.config['SECRET_KEY']:
    raise ValueError("❌ SECRET_KEY est manquant dans le fichier .env")

# --- Initialisation du système de tokens sécurisés ---
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# --- Configuration de Flask-Mail (une seule fois) ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL') == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')  # <-- Ajoute cette ligne

mail = Mail(app)

# --- Vérification basique du format de l'email ---
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

# --- Fonction d’envoi d’email sécurisé ---
def send_email(to, subject, body):
    try:
        msg = Message(subject, sender=app.config["MAIL_USERNAME"], recipients=[to])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        print(f"Erreur lors de l'envoi du mail : {e}")

file_manager.add_missing_columns("utilisateurs", {
    "nom": "TEXT",
    "prenom": "TEXT",
    "genre": "TEXT",
    "adresse_mail": "TEXT",
    "mot_de_passe": "TEXT"
})



# --- Gestion des tokens de confirmation d’email ---
def generate_confirmation_token(email):
    return serializer.dumps(email, salt="email-confirmation")

def confirm_token(token, expiration=3600):
    try:
        return serializer.loads(token, salt="email-confirmation", max_age=expiration)
    except Exception:
        return False

# --- Configuration Admin ---
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# --- Affichage du SECRET_KEY (optionnel pour debug uniquement) ---
print(f"SECRET_KEY chargé : {repr(app.config['SECRET_KEY'])}")



def navbar_html(active=""):
    return f"""
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <a class="navbar-brand" href="{url_for('accueil')}">MonApp</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto">
            <li class="nav-item">
              <a class="nav-link {'active fw-bold' if active == 'accueil' else ''}" href="{url_for('accueil')}">Accueil</a>
            </li>
            <li class="nav-item">
              <a class="nav-link {'active fw-bold' if active == 'login' else ''}" href="{url_for('login')}">Connexion</a>
            </li>
            <li class="nav-item">
              <a class="nav-link {'active fw-bold' if active == 'formulaire' else ''}" href="{url_for('formulaire')}">Inscription</a>
            </li>
            <li class="nav-item">
              <a class="nav-link {'active fw-bold' if active == 'contact' else ''}" href="{url_for('contact')}">Nous contacter</a>
            </li>
            <li class="nav-item">
  <a class="nav-link {'active fw-bold' if active == 'conditions' else ''}" href="{url_for('conditions_utilisation')}">Conditions</a>
</li>
<li class="nav-item">
  <a class="nav-link {'active fw-bold' if active == 'confidentialite' else ''}" href="{url_for('politique_confidentialite')}">Confidentialité</a>
</li>
          </ul>
        </div>
      </div>
    </nav>
    """



# 🧾 HTML pour le formulaire d'inscription
formulaire_html = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Formulaire d'inscription</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    {{ navbar|safe }}
    <div class="container d-flex flex-column justify-content-center align-items-center min-vh-100">
        <div class="card shadow p-4 w-100" style="max-width: 500px;">
            <h2 class="text-center mb-4">Formulaire d'inscription</h2>
            <form method="POST">
                <div class="mb-3">
                    <label for="nom" class="form-label">Nom</label>
                    <input type="text" name="nom" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label for="prenom" class="form-label">Prénom</label>
                    <input type="text" name="prenom" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label for="genre" class="form-label">Genre</label>
                    <select name="genre" class="form-select" required>
                        <option value="">Sélectionner</option>
                        <option value="Homme">Homme</option>
                        <option value="Femme">Femme</option>
                        <option value="Autre">Autre</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label for="adresse_mail" class="form-label">Adresse mail</label>
                    <input type="email" name="adresse_mail" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label for="mot_de_passe" class="form-label">Mot de passe</label>
                    <input type="password" name="mot_de_passe" class="form-control" required>
                </div>
                <div class="d-grid">
                    <input type="submit" value="Envoyer" class="btn btn-primary">
                </div>
            </form>
            <p class="mt-3 text-center">Déjà inscrit ? <a href="{{ url_for('login') }}">Se connecter ici</a></p>
        </div>
    </div>
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def formulaire():
    nom_table = session_manager.get_active_table()
    if not nom_table:
        return "⚠️ Aucune table active définie. Rendez-vous dans le panneau admin pour en sélectionner une."

    schema = schema_manager.load_schema(nom_table)
    if not schema:
        return f"⚠️ Erreur : le schéma pour la table '{nom_table}' est introuvable."

    if request.method == 'POST':
        email = request.form["adresse_mail"].strip().lower()

        # Vérifier email format
        if not is_valid_email(email):
            flash("❌ Adresse email invalide.", "danger")
            return redirect(url_for('formulaire'))

        anciens = file_manager.load_data(nom_table)

        # Vérification d'unicité de l'adresse email
        for utilisateur in anciens:
            if utilisateur.get("email") == email:
                flash("⚠️ Cette adresse e-mail est déjà utilisée.", "warning")
                return redirect(url_for("formulaire"))

        mot_de_passe = request.form["mot_de_passe"]
        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        data = {
            "nom": request.form["nom"],
            "prenom": request.form["prenom"],
            "genre": request.form["genre"],
            "email": email,
            "mot_de_passe": mot_de_passe_hash,
            "email_confirmed": False  # Ajout important
        }

        validated = data_validator.validate_record(data, schema)
        file_manager.save_data(nom_table, anciens + [validated])

        # Génération du token et envoi d’email
        token = generate_confirmation_token(email)
        lien = url_for("confirm_email", token=token, _external=True)
        send_email(email, "Confirmation de votre adresse", f"Confirmez votre adresse en cliquant ici : {lien}")

        flash("✅ Inscription réussie. Veuillez vérifier votre adresse email pour activer votre compte.", "success")
        return redirect(url_for('login'))

    return render_template("formulaire.html")

# ✅ Page pour choisir une table active
@app.route('/choisir', methods=['GET', 'POST'])
def choisir_table():
    if request.method == 'POST':
        nom_table = request.form.get('table')
        if not nom_table:
            return "⚠️ Aucune table sélectionnée."

        if not schema_manager.load_schema(nom_table):
            return f"⚠️ Schéma introuvable pour la table '{nom_table}'."

        session_manager.set_active_table(nom_table)
        return redirect(url_for('formulaire'))

    # Liste des fichiers de schéma
    tables = schema_manager.lister_tables()
    selection_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Choisir une Table</title></head>
    <body>
        <h2>Choisir un formulaire (table active)</h2>
        <form method="POST">
            <select name="table">
                {% for table in tables %}
                <option value="{{ table }}">{{ table }}</option>
                {% endfor %}
            </select>
            <input type="submit" value="Choisir">
        </form>
        <p><a href="{{ url_for('formulaire') }}">⬅️ Revenir au formulaire</a></p>
    </body>
    </html>
    """
    return render_template_string(selection_html, tables=tables)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return "❌ Identifiants incorrects."
    
    return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Connexion Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container d-flex flex-column justify-content-center align-items-center min-vh-100">
        <div class="card shadow p-4 w-100" style="max-width: 400px;">
            <h2 class="text-center mb-4">Connexion Admin</h2>
            <form method="POST">
                <div class="mb-3">
                    <label for="username" class="form-label">Nom d'utilisateur</label>
                    <input type="text" class="form-control" name="username" required>
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label">Mot de passe</label>
                    <input type="password" class="form-control" name="password" required>
                </div>
                <div class="d-grid">
                    <input type="submit" value="Connexion" class="btn btn-success">
                </div>
            </form>
        </div>
    </div>
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
""")

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    tables = file_manager.list_tables()
    active_table = session_manager.get_active_table()

    return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Panneau d'administration</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <div class="text-center mb-4">
            <h2>🧑‍💼 Panneau d'administration</h2>
            <p>Table active : <strong>{{ active_table }}</strong></p>
        </div>

        <div class="table-responsive">
            <h3>Tables existantes :</h3>
            <table class="table table-bordered table-hover bg-white shadow-sm">
                <thead class="table-primary">
                    <tr>
                        <th>Nom de la table</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for table in tables %}
                    <tr>
                        <td>{{ table }}</td>
                        <td>
                            <a href="{{ url_for('admin_set_table', name=table) }}" class="btn btn-sm btn-outline-primary">Utiliser</a>
                            <a href="{{ url_for('admin_view_data') }}?table={{ table }}" class="btn btn-sm btn-outline-secondary">Voir données</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="mt-4 text-center">
            <a href="{{ url_for('admin_add_user') }}" class="btn btn-info mb-2">📝 Ajouter un utilisateur (via formulaire)</a><br>
            <a href="{{ url_for('admin_logout') }}" class="btn btn-danger">🔒 Déconnexion</a>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
""", tables=tables, active_table=active_table)

    if schema_manager.load_schema(table):
        session_manager.set_active_table(table)
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/data')
def admin_view_data():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    if not table:
        return "⚠️ Aucune table active sélectionnée."

    data = file_manager.load_data(table)

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Données de la table {{ table }}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <h2 class="text-center mb-4">📊 Données de la table <strong>{{ table }}</strong></h2>

            {% if data %}
            <div class="table-responsive">
                <table class="table table-bordered table-hover bg-white shadow-sm">
                    <thead class="table-primary">
                        <tr>
                            {% for key in data[0].keys() %}
                                <th>{{ key }}</th>
                            {% endfor %}
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in data %}
                        <tr>
                            {% for value in row.values() %}
                                <td>{{ value }}</td>
                            {% endfor %}
                            <td class="actions">
    <a href="{{ url_for('admin_edit_user', id=row['id']) }}" class="btn btn-sm btn-warning">✏️</a>
    <a href="{{ url_for('admin_delete_user', id=row['id']) }}" class="btn btn-sm btn-danger">🗑️</a>
</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
                <p class="text-center">🔍 Aucune donnée trouvée.</p>
            {% endif %}

            <div class="text-center mt-4">
                <a href="{{ url_for('admin_add_user') }}" class="btn btn-info m-1">➕ Ajouter un utilisateur</a>
                <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary m-1">⬅️ Retour admin</a>
                <a href="{{ url_for('admin_export_csv') }}" class="btn btn-success m-1">⬇️ Exporter en CSV</a>
                <a href="{{ url_for('admin_import_csv') }}" class="btn btn-primary m-1">📤 Importer un CSV</a>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, table=table, data=data)




@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


@app.route('/admin/create', methods=['GET', 'POST'])
def admin_create_table():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        table_name = request.form['table']
        champs = {}
        noms = request.form.getlist('field_name')
        types = request.form.getlist('field_type')

        for n, t in zip(noms, types):
            if n.strip():
                champs[n.strip()] = t.strip()

        try:
            schema_manager.create_schema(table_name, champs)
            file_manager.save_data(table_name, [])
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            return f"Erreur : {e}"

    return render_template_string("""
        <h2>Créer une nouvelle table</h2>
        <form method="POST">
            Nom de la table : <input name="table"><br><br>
            <h4>Champs :</h4>
            {% for i in range(5) %}
                Nom : <input name="field_name"><br>
                Type (string, int, float, bool, email, password): 
                <input name="field_type"><br><br>
            {% endfor %}
            <input type="submit" value="Créer">
        </form>
        <p><a href="{{ url_for('admin_dashboard') }}">⬅️ Retour</a></p>
    """)




@app.route('/admin/add_user', methods=['GET', 'POST'])
def admin_add_user():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    if not table:
        return "⚠️ Aucune table active."

    schema = schema_manager.load_schema(table)
    
    if request.method == 'POST':
        data = {}
        for champ in schema:
            data[champ] = request.form.get(champ)

        validated = data_validator.validate_record(data, schema)
        file_manager.insert_data(table, validated)
        return redirect(url_for('admin_view_data'))

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Ajouter un utilisateur</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <h2 class="mb-4">➕ Ajouter un utilisateur à <strong>{{ table }}</strong></h2>
            <form method="POST" class="bg-white p-4 rounded shadow-sm">
                {% for champ in schema %}
                    <div class="mb-3">
                        <label class="form-label">{{ champ }}</label>
                        <input name="{{ champ }}" class="form-control">
                    </div>
                {% endfor %}
                <button type="submit" class="btn btn-primary w-100">Ajouter</button>
            </form>
            <p class="mt-3"><a href="{{ url_for('admin_dashboard') }}">⬅️ Retour</a></p>
        </div>
    </body>
    </html>
    """, table=table, schema=schema)



@app.route('/admin/delete/<int:id>')
def admin_delete_user(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    if not table:
        return "⚠️ Aucune table active sélectionnée."

    success = file_manager.delete_user(table, id)
    if success:
        return redirect(url_for('admin_view_data'))
    else:
        return "❌ Erreur lors de la suppression de l'utilisateur."



@app.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
def admin_edit_user(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    if not table:
        return "⚠️ Aucune table active."

    schema = schema_manager.load_schema(table)
    data = file_manager.load_data(table)

    utilisateur = next((u for u in data if u["id"] == id), None)
    if not utilisateur:
        return "⚠️ Utilisateur introuvable."

    if request.method == 'POST':
        for champ in schema:
            utilisateur[champ] = request.form.get(champ)

        validated = data_validator.validate_record(utilisateur, schema)
        file_manager.update_data(table, id, validated)
        return redirect(url_for('admin_view_data'))

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Modifier utilisateur</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <h2 class="mb-4">✏️ Modifier l'utilisateur</h2>
            <form method="POST" class="bg-white p-4 rounded shadow-sm">
                {% for champ in schema %}
                    <div class="mb-3">
                        <label class="form-label">{{ champ }}</label>
                        <input name="{{ champ }}" class="form-control" value="{{ utilisateur[champ] }}">
                    </div>
                {% endfor %}
                <button type="submit" class="btn btn-primary w-100">Enregistrer</button>
            </form>
            <p class="mt-3"><a href="{{ url_for('admin_view_data') }}">⬅️ Retour</a></p>
        </div>
    </body>
    </html>
    """, utilisateur=utilisateur, schema=schema)




@app.route('/admin/export')
def admin_export_csv():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    if not table:
        return "⚠️ Aucune table active."

    data = file_manager.load_data(table)
    if not data:
        return "📭 Aucune donnée à exporter."

    # Création du CSV en mémoire
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    # Envoie le CSV en pièce jointe
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            "Content-Disposition": f"attachment; filename={table}.csv"
        }
    )




@app.route('/admin/import', methods=['GET', 'POST'])
def admin_import_csv():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    if not table:
        return "⚠️ Aucune table active."

    schema = schema_manager.load_schema(table)
    if not schema:
        return "⚠️ Schéma introuvable."

    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file:
            return "❌ Aucun fichier envoyé."

        # Lecture du CSV
        try:
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            reader = csv.DictReader(stream)
            new_data = []
            for row in reader:
                validated = data_validator.validate_record(row, schema)
                new_data.append(validated)

            # Ajout à la table
            anciens = file_manager.load_data(table)
            file_manager.save_data(table, anciens + new_data)

            return f"✅ {len(new_data)} enregistrements importés dans '{table}'."
        except Exception as e:
            return f"❌ Erreur lors de l'import : {e}"

    return render_template_string("""
        <h2>Importer un fichier CSV dans '{{ table }}'</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="csv_file" accept=".csv">
            <input type="submit" value="Importer">
        </form>
        <p><a href="{{ url_for('admin_dashboard') }}">⬅️ Retour admin</a></p>
    """, table=table)








@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        mot_de_passe = request.form.get('mot_de_passe', '')

        if not email or not mot_de_passe:
            flash("Veuillez remplir tous les champs.", "warning")
            return redirect(url_for("login"))

        table = "utilisateurs"
        utilisateurs = file_manager.load_data(table)

        for user in utilisateurs:
            if user["email"].strip().lower() == email and check_password_hash(user["mot_de_passe"], mot_de_passe):

                # Vérifie si l'email a été confirmé
                if not user.get("email_confirmed", False):
                    flash("❌ Adresse email non confirmée. Veuillez vérifier votre boîte mail.", "danger")
                    return redirect(url_for("login"))

                session["user_email"] = email
                flash("✅ Connexion réussie.", "success")
                return redirect(url_for('mon_espace'))

        flash("❌ Identifiants incorrects.", "danger")
        return redirect(url_for("login"))

    return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Connexion</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    {{ navbar|safe }}

    <!-- Affichage des messages flash -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="container mt-3">
          {% for category, message in messages %}
            <div class="alert alert-{{ category }} text-center">
              {{ message }}
            </div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <div class="container d-flex justify-content-center align-items-center min-vh-100">
        <div class="card shadow-sm p-4 w-100" style="max-width: 400px;">
            <h2 class="text-center mb-4">&#128272; Connexion utilisateur</h2>
            <form method="POST">
                <div class="mb-3">
                    <label for="email" class="form-label">Adresse email</label>
                    <input name="email" type="email" class="form-control" id="email" required>
                </div>
                <div class="mb-3">
                    <label for="mot_de_passe" class="form-label">Mot de passe</label>
                    <input name="mot_de_passe" type="password" class="form-control" id="mot_de_passe" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Se connecter</button>
            </form>
            <p class="text-center mt-3">
                Pas encore inscrit ?
                <a href="{{ url_for('formulaire') }}">Créer un compte</a>
            </p>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
""", navbar=navbar_html("login"))





@app.route('/mon-espace', methods=['GET', 'POST'])
def mon_espace():
    if "user_email" not in session:
        return redirect(url_for('login'))

    email = session["user_email"]
    table = "utilisateurs"
    data = file_manager.load_data(table)
    utilisateur = next((u for u in data if u["email"].strip().lower() == email.strip().lower()), None)

    if not utilisateur:
        return "⚠️ Utilisateur introuvable."

    # Sécurité : Vérifier que l'email a bien été confirmé
    if not utilisateur.get("email_confirmed", False):
        flash("⚠️ Votre adresse email n’a pas été confirmée. Veuillez vérifier vos emails.", "danger")
        return redirect(url_for("login"))

    if request.method == 'POST':
        budget_str = request.form.get("budget")
        try:
            budget = float(budget_str)
        except ValueError:
            flash("❌ Format de budget invalide.", "danger")
            return redirect(url_for('mon_espace'))

        utilisateur["budget"] = budget
        file_manager.save_data(table, data)
        flash("✅ Budget mis à jour avec succès.", "success")
        return redirect(url_for('mon_espace'))

    return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Mon espace</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    {{ navbar|safe }}

    <!-- Flash messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="container mt-3">
          {% for category, message in messages %}
            <div class="alert alert-{{ category }} text-center">
              {{ message }}
            </div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <div class="container d-flex justify-content-center align-items-center min-vh-100">
        <div class="card shadow-sm p-4" style="width: 100%; max-width: 450px;">
            <h2 class="text-center mb-4">Bienvenue {{ utilisateur["prenom"] }} 👋</h2>
            <p class="text-center">Budget actuel : <strong>{{ utilisateur.get("budget", "Non défini") }}</strong></p>
            <form method="POST">
                <div class="mb-3">
                    <label for="budget" class="form-label"><strong>Votre budget total :</strong></label>
                    <input id="budget" name="budget" type="number" step="0.01" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Enregistrer le budget</button>
            </form>
            <div class="text-center mt-3">
                <a href="{{ url_for('logout') }}" class="btn btn-link text-danger">🔓 Se déconnecter</a>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
""", utilisateur=utilisateur, navbar=navbar_html("mon_espace"))







@app.route("/confirm_email/<token>")
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash("❌ Lien invalide ou expiré.", "danger")
        return redirect(url_for("login"))

    utilisateurs = file_manager.load_data("utilisateurs")
    for user in utilisateurs:
        if user["email"] == email:
            user["email_confirmed"] = True
            break
    file_manager.save_data("utilisateurs", utilisateurs)

    flash("✅ Adresse email confirmée. Vous pouvez maintenant vous connecter.", "success")
    return redirect(url_for("login"))
@app.route('/logout')
def logout():
    session.pop("user_email", None)
    return redirect(url_for('login'))




@app.route('/accueil')
def accueil():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Accueil</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        {{ navbar|safe }}
        <div class="container py-5">
            <div class="text-center">
                <h1>Bienvenue sur MonApp !</h1>
                <p class="lead">Une application simple et efficace pour gérer vos données.</p>
            </div>
        </div>
    </body>
    </html>
    """, navbar=navbar_html("accueil"))

@app.route('/contact')
def contact():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Nous contacter</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        {{ navbar|safe }}
        <div class="container py-5">
            <div class="card shadow p-4">
                <h2 class="mb-3">Nous contacter</h2>
                <p>Pour toute question ou suggestion, écrivez-nous à :</p>
                <ul>
                    <li>Email : support@monapp.fr</li>
                    <li>Téléphone : +33 6 12 34 56 78</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """, navbar=navbar_html("contact"))







@app.route("/confidentialite")
def politique_confidentialite():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Politique de confidentialité</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        {{ navbar|safe }}
        <div class="container py-5">
            <h1>Politique de confidentialité</h1>
            <p>Nous collectons vos données pour améliorer le service...</p>
        </div>
    </body>
    </html>
    """, navbar=navbar_html())



@app.route("/conditions")
def conditions_utilisation():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Conditions d'utilisation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        {{ navbar|safe }}
        <div class="container py-5">
            <h1>Conditions d'utilisation</h1>
            <p>En utilisant ce site, vous acceptez de respecter les règles suivantes...</p>
        </div>
    </body>
    </html>
    """, navbar=navbar_html())




@app.route('/admin/set/<name>')
def admin_set_table(name):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    session_manager.set_active_table(name)
    return redirect(url_for('admin_dashboard'))

import sqlite3
conn = sqlite3.connect("data.db")
cur = conn.cursor()
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables existantes dans data.db :", tables)
conn.close()



#@app.route("/confirm_email/<token>")
#def confirm_email(token):
 #   email = confirm_token(token)
  #  if not email:
   #     flash("⛔ Le lien de confirmation est invalide ou expiré.")
    #    return redirect(url_for("connexion"))
    #session["email_confirmed"] = True
    #flash("✅ Adresse email confirmée avec succès. Vous pouvez vous connecter.")
    #return redirect(url_for("connexion"))


# --- Bloc de lancement Flask ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)