from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import Flask, render_template_string, request, redirect, url_for, session, Response
import session_manager
import schema_manager
import db_manager as file_manager
import data_validator
import csv
import io
import os


app = Flask(__name__)
app.secret_key = "secret_key_change_me"  # 🔒 pour sécuriser la session

# Identifiants admin (modifiables)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


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
            <p class="mt-3 text-center">Déjà inscrit ? <a href="/login">Se connecter ici</a></p>
        </div>
    </div>
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ✅ Page d'accueil : formulaire dynamique
@app.route('/', methods=['GET', 'POST'])
def formulaire():
    if request.method == 'POST':
        nom_table = session_manager.get_active_table()
        if not nom_table:
            return "⚠️ Aucune table active définie."

        schema = schema_manager.load_schema(nom_table)
        if not schema:
            return f"⚠️ Schéma introuvable pour la table '{nom_table}'."

        email = request.form["adresse_mail"]
        anciens = file_manager.load_data(nom_table)

        # Vérification d'unicité de l'adresse email
        for utilisateur in anciens:
            if utilisateur.get("email") == email:
                return "⚠️ Cette adresse e-mail est déjà utilisée."

        mot_de_passe = request.form["mot_de_passe"]
        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        data = {
            "nom": request.form["nom"],
            "prenom": request.form["prenom"],
            "genre": request.form["genre"],
            "email": email,
            "mot_de_passe": mot_de_passe_hash
        }

        validated = data_validator.validate_record(data, schema)
        file_manager.save_data(nom_table, anciens + [validated])
        return f"✅ Données ajoutées à la table '{nom_table}' avec succès !"

    return render_template_string(formulaire_html)

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
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')

        table = "utilisateurs"
        utilisateurs = file_manager.load_data(table)

        for user in utilisateurs:
            if user["email"] == email and check_password_hash(user["mot_de_passe"], mot_de_passe):
                session["user_email"] = email
                return redirect(url_for('mon_espace'))

        return "❌ Identifiants incorrects."

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
    <div class="container d-flex justify-content-center align-items-center min-vh-100">
        <div class="card shadow-sm p-4" style="width: 100%; max-width: 400px;">
            <h2 class="text-center mb-4">🔐 Connexion utilisateur</h2>
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

    utilisateur = next((u for u in data if u["email"] == email), None)
    if not utilisateur:
        return "⚠️ Utilisateur introuvable."

    if request.method == 'POST':
        budget_str = request.form.get("budget")
        try:
            budget = float(budget_str)
        except ValueError:
            return "❌ Format de budget invalide."

        utilisateur["budget"] = budget
        file_manager.save_data(table, data)
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
""", utilisateur=utilisateur)




@app.route('/')
def accueil():
    return render_template_string("""
    <head>
      <meta charset="UTF-8">
      <title>Accueil</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    </head>
    <body>
      {{ navbar|safe }}
      <div class="container mt-4">
        <h1>Bienvenue sur MonApp !</h1>
        <p>Application de gestion d’utilisateurs et de budget.</p>
      </div>
    </body>
    """, navbar=navbar_html())




@app.route('/logout')
def logout():
    session.pop("user_email", None)
    return redirect(url_for('login'))



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



def navbar_html(active=""):
    def nav_item(name, endpoint):
        if active == endpoint:
            return f'<li class="nav-item"><a class="nav-link active" aria-current="page" href="#">{name}</a></li>'
        return f'<li class="nav-item"><a class="nav-link" href="{{{{ url_for(\'{endpoint}\') }}}}">{name}</a></li>'

    return f"""
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <a class="navbar-brand" href="{{{{ url_for('accueil') }}}}">MonApp</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto">
            {nav_item('Accueil', 'accueil')}
            {nav_item('Connexion', 'login')}
            {nav_item('Inscription', 'formulaire')}
            {nav_item('Mon espace', 'mon_espace')}
            {nav_item('Nous contacter', 'contact')}
          </ul>
        </div>
      </div>
    </nav>
    """






if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)