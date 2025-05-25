import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import Flask, render_template_string, request, redirect, url_for, session, Response
import session_manager
import schema_manager
import file_manager
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
<html>
<head>
    <title>Formulaire Utilisateur</title>
   <style>
    body {
        font-family: Arial, sans-serif;
        background: #f4f4f4;
        margin: 0;
        padding: 40px;
        text-align: center;
    }

    h2 {
        color: #333;
        margin-bottom: 20px;
    }

    form {
        display: inline-block;
        text-align: left;
        background: white;
        padding: 20px;
        border-radius: 8px;
        min-width: 320px;
        max-width: 400px;
        width: 100%;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }

    input[type="text"],
    input[type="email"],
    input[type="password"],
    input[type="number"],
    select {
        width: 100%;
        padding: 10px;
        margin: 8px 0 16px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    input[type="submit"] {
        background: #007bff;
        color: white;
        border: none;
        padding: 12px;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
    }

    input[type="submit"]:hover {
        background: #0056b3;
    }

    p {
        margin-top: 15px;
    }

    a {
        color: #007bff;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    .logout {
        margin-top: 30px;
        display: inline-block;
    }

    .logout a {
        color: #ff6600;
    }
</style>
</head>
<body>
    <h2>Formulaire d'inscription</h2>
    <form method="POST">
        Nom : <input type="text" name="nom"><br>
        Prénom : <input type="text" name="prenom"><br>
        Genre :
        <select name="genre">
            <option value="Homme">Homme</option>
            <option value="Femme">Femme</option>
            <option value="Autre">Autre</option>
        </select><br>
        Adresse mail : <input type="email" name="adresse_mail"><br>
        Mot de passe : <input type="password" name="mot_de_passe"><br>
        <input type="submit" value="Envoyer">
    </form>
    <p>Déjà inscrit ? <a href="/login">Se connecter ici</a></p>
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

        data = {
            "nom": request.form["nom"],
            "prenom": request.form["prenom"],
            "genre": request.form["genre"],
            "email": request.form["adresse_mail"],
            "mot_de_passe": request.form["mot_de_passe"]
        }

        validated = data_validator.validate_record(data, schema)
        anciens = file_manager.load_data(nom_table)
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

    <style>
        body {
            background: #f4f4f4;
            font-family: Arial;
            text-align: center;
            padding: 40px;
        }

        form {
            background: white;
            display: inline-block;
            text-align: left;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            max-width: 400px;
            width: 100%;
        }

        label {
            display: block;
            margin-top: 10px;
            margin-bottom: 5px;
        }

        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #ccc;
            margin-bottom: 15px;
        }

        input[type="submit"] {
            background: #28a745;
            color: white;
            padding: 10px;
            width: 100%;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        input[type="submit"]:hover {
            background: #218838;
        }
    </style>
        <h2>Connexion Admin</h2>
        <form method="POST">
            Nom d'utilisateur : <input name="username"><br>
            Mot de passe : <input type="password" name="password"><br>
            <input type="submit" value="Connexion">
        </form>
    """)

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    tables = file_manager.list_tables()
    active_table = session_manager.get_active_table()

    return render_template_string("""
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f8f9fa;
                padding: 40px;
                text-align: center;
            }

            table {
                margin: auto;
                border-collapse: collapse;
                width: 80%;
                background: white;
                box-shadow: 0 0 8px rgba(0,0,0,0.1);
            }

            th, td {
                padding: 12px;
                border: 1px solid #ddd;
            }

            th {
                background-color: #007bff;
                color: white;
            }

            a {
                color: #007bff;
                text-decoration: none;
            }

            a:hover {
                text-decoration: underline;
            }

            .admin-actions {
                margin-top: 20px;
            }

            .admin-actions a {
                display: inline-block;
                margin: 10px;
                padding: 10px 15px;
                background: #e9ecef;
                border-radius: 4px;
            }
        </style>

        <h2>🧑‍💼 Panneau d'administration</h2>
        <p>Table active : <strong>{{ active_table }}</strong></p>

        <h3>Tables existantes :</h3>
        <table>
            <tr>
                <th>Nom de la table</th>
                <th>Actions</th>
            </tr>
            {% for table in tables %}
            <tr>
                <td>{{ table }}</td>
                <td>
                    [<a href="{{ url_for('admin_set_table', name=table) }}">Utiliser</a>] |
                    [<a href="{{ url_for('admin_view_data') }}?table={{ table }}">Voir données</a>]
                </td>
            </tr>
            {% endfor %}
        </table>

        <div class="admin-actions">
            <p>📝 <a href="{{ url_for('admin_add_user') }}">Ajouter un utilisateur (via formulaire)</a></p>
            <p>🔒 <a href="{{ url_for('admin_logout') }}">Déconnexion</a></p>
        </div>
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

        <style>
    body {
        font-family: Arial, sans-serif;
        background: #f4f4f4;
        margin: 0;
        padding: 20px;
    }

    h2 {
        color: #333;
    }

    form {
        background: white;
        padding: 20px;
        border-radius: 8px;
        max-width: 400px;
        margin: auto;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }

    input[type="text"],
    input[type="email"],
    input[type="password"],
    input[type="number"],
    select {
        width: 100%;
        padding: 10px;
        margin: 8px 0 16px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    input[type="submit"] {
        background: #007bff;
        color: white;
        border: none;
        padding: 12px;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
    }

    input[type="submit"]:hover {
        background: #0056b3;
    }

    .table-container {
        max-width: 90%;
        margin: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        box-shadow: 0 0 5px rgba(0,0,0,0.1);
    }

    th, td {
        padding: 12px;
        border: 1px solid #ddd;
        text-align: left;
    }

    th {
        background-color: #007bff;
        color: white;
    }

    a {
        color: #007bff;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    .actions {
        white-space: nowrap;
    }
</style>

        <h2>Données de la table '{{ table }}'</h2>
        {% if data %}
            <table border="1">
                <tr>
                    {% for key in data[0].keys() %}
                    <th>{{ key }}</th>
                    {% endfor %}
                    <th>Actions</th>
                </tr>
                {% for row in data %}
                <tr>
                    {% for value in row.values() %}
                    <td>{{ value }}</td>
                    {% endfor %}
                    <td>
                        <a href="{{ url_for('admin_edit_user', index=loop.index0) }}">✏️ Modifier</a> |
                        <a href="{{ url_for('admin_delete_user', index=loop.index0) }}">🗑️ Supprimer</a>
                    </td>
                </tr>
                {% endfor %}
            </table>
        {% else %}
            <p>🔍 Aucune donnée trouvée.</p>
        {% endif %}
        <p><a href="{{ url_for('admin_add_user') }}">➕ Ajouter un utilisateur</a></p>
        <p><a href="{{ url_for('admin_dashboard') }}">⬅️ Retour admin</a></p>
        <p><a href="{{ url_for('admin_export_csv') }}">⬇️ Exporter en CSV</a></p>

        <p><a href="{{ url_for('admin_import_csv') }}">📤 Importer un CSV</a></p>

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
        file_manager.save_data(table, file_manager.load_data(table) + [validated])
        return redirect(url_for('admin_view_data'))

    return render_template_string("""
        <h2>Ajouter un utilisateur à '{{ table }}'</h2>
        <form method="POST">
            {% for champ in schema %}
                {{ champ }} : <input name="{{ champ }}"><br>
            {% endfor %}
            <input type="submit" value="Ajouter">
        </form>
        <p><a href="{{ url_for('admin_dashboard') }}">⬅️ Retour</a></p>
    """, table=table, schema=schema)




@app.route('/admin/delete_user/<int:index>')
def admin_delete_user(index):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    data = file_manager.load_data(table)
    if index < len(data):
        del data[index]
        file_manager.save_data(table, data)

    return redirect(url_for('admin_view_data'))




@app.route('/admin/edit_user/<int:index>', methods=['GET', 'POST'])
def admin_edit_user(index):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    schema = schema_manager.load_schema(table)
    data = file_manager.load_data(table)

    if index >= len(data):
        return "Index invalide"

    if request.method == 'POST':
        modifie = {}
        for champ in schema:
            modifie[champ] = request.form.get(champ)
        validated = data_validator.validate_record(modifie, schema)
        data[index] = validated
        file_manager.save_data(table, data)
        return redirect(url_for('admin_view_data'))

    record = data[index]
    return render_template_string("""
        <h2>Modifier utilisateur #{{ index }}</h2>
        <form method="POST">
            {% for champ in schema %}
                {{ champ }} : <input name="{{ champ }}" value="{{ record[champ] }}"><br>
            {% endfor %}
            <input type="submit" value="Enregistrer">
        </form>
        <p><a href="{{ url_for('admin_view_data') }}">⬅️ Retour</a></p>
    """, index=index, schema=schema, record=record)




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

        # Recherche dans la table utilisateurs
        table = "utilisateurs"
        utilisateurs = file_manager.load_data(table)

        for user in utilisateurs:
            if user["email"] == email and user["mot_de_passe"] == mot_de_passe:
                session["user_email"] = email
                return redirect(url_for('mon_espace'))

        return "❌ Identifiants incorrects."

    return render_template_string("""
        <style>
    body {
        font-family: Arial, sans-serif;
        background: #f4f4f4;
        margin: 0;
        padding: 40px;
        text-align: center;
    }

    h2 {
        color: #333;
        margin-bottom: 20px;
    }

    form {
        display: inline-block;
        text-align: left;
        background: white;
        padding: 20px;
        border-radius: 8px;
        min-width: 320px;
        max-width: 400px;
        width: 100%;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }

    input[type="text"],
    input[type="email"],
    input[type="password"],
    input[type="number"],
    select {
        width: 100%;
        padding: 10px;
        margin: 8px 0 16px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    input[type="submit"] {
        background: #007bff;
        color: white;
        border: none;
        padding: 12px;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
    }

    input[type="submit"]:hover {
        background: #0056b3;
    }

    p {
        margin-top: 15px;
    }

    a {
        color: #007bff;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    .logout {
        margin-top: 30px;
        display: inline-block;
    }

    .logout a {
        color: #ff6600;
    }
</style>
        <h2>Connexion utilisateur</h2>
        <form method="POST">
            Email : <input name="email" type="email"><br>
            Mot de passe : <input name="mot_de_passe" type="password"><br>
            <input type="submit" value="Se connecter">
        </form>
        <p>Pas encore inscrit ? <a href="{{ url_for('formulaire') }}">Créer un compte</a></p>
    """)





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

       <style>
    body {
        font-family: Arial, sans-serif;
        background: #f4f4f4;
        margin: 0;
        padding: 40px;
        text-align: center;
    }

    h2 {
        color: #333;
        margin-bottom: 20px;
    }

    form {
        display: inline-block;
        text-align: left;
        background: white;
        padding: 20px;
        border-radius: 8px;
        min-width: 320px;
        max-width: 400px;
        width: 100%;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }

    input[type="text"],
    input[type="email"],
    input[type="password"],
    input[type="number"],
    select {
        width: 100%;
        padding: 10px;
        margin: 8px 0 16px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    input[type="submit"] {
        background: #007bff;
        color: white;
        border: none;
        padding: 12px;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
    }

    input[type="submit"]:hover {
        background: #0056b3;
    }

    p {
        margin-top: 15px;
    }

    a {
        color: #007bff;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    .logout {
        margin-top: 30px;
        display: inline-block;
    }

    .logout a {
        color: #ff6600;
    }

    input[name="budget"] {
    font-size: 1.2rem;
    padding: 14px;
    border: 2px solid #007bff;
    border-radius: 6px;
    margin-bottom: 20px;
}
</style>

        <h2>Bienvenue {{ utilisateur["prenom"] }} 👋</h2>
        <p>Budget actuel : {{ utilisateur.get("budget", "Non défini") }}</p>
        <form method="POST">
            <label for="budget"><strong>Votre budget total :</strong></label> : <input id="budget" name="budget" type="number" step="0.01">
            <input type="submit" value="Enregistrer le budget">
        </form>
        <p><a href="{{ url_for('logout') }}">🔓 Se déconnecter</a></p>
    """, utilisateur=utilisateur)




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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
