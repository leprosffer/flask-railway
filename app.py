from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_mail import Mail, Message
from utils import is_valid_email, send_email  # tu peux supprimer la redéfinition si déjà dans utils
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

import db_manager as file_manager  # ton accès MySQL centralisé

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
if not app.config['SECRET_KEY']:
    raise ValueError("❌ SECRET_KEY est manquant dans le fichier .env")

# Flask-Mail config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Préparation des colonnes dans la table utilisateurs
file_manager.add_missing_columns("utilisateurs", {
    "nom": "TEXT",
    "prenom": "TEXT",
    "genre": "TEXT",
    "adresse_mail": "TEXT",
    "mot_de_passe": "TEXT"
})

def generate_confirmation_token(email):
    return serializer.dumps(email, salt="email-confirmation")

def confirm_token(token, expiration=3600):
    try:
        return serializer.loads(token, salt="email-confirmation", max_age=expiration)
    except Exception:
        return False


# Navbar HTML simplifiée

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

# --- FORMULAIRE D'INSCRIPTION UTILISATEUR ---
@app.route('/', methods=['GET', 'POST'])
def formulaire():
    nom_table = session.get("active_table")
    if not nom_table:
        return "⚠️ Aucune table active définie. Rendez-vous dans le panneau admin."

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        email = request.form["adresse_mail"].strip().lower()
        if not is_valid_email(email):
            flash("❌ Adresse email invalide.", "danger")
            return redirect(url_for('formulaire'))

        cursor.execute(f"SELECT * FROM `{nom_table}` WHERE email = %s", (email,))
        if cursor.fetchone():
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
            "email_confirmed": False
        }

        placeholders = ', '.join(['%s'] * len(data))
        colonnes = ', '.join(data.keys())
        valeurs = tuple(data.values())

        cursor.execute(f"INSERT INTO `{nom_table}` ({colonnes}) VALUES ({placeholders})", valeurs)
        db.commit()

        token = generate_confirmation_token(email)
        lien = url_for("confirm_email", token=token, _external=True)
        send_email(email, "Confirmation de votre adresse", f"Confirmez votre adresse : {lien}")

        flash("✅ Inscription réussie. Vérifiez votre boîte email.", "success")
        return redirect(url_for('login'))

    return render_template("formulaire.html", active="formulaire")

# --- CHOIX DE LA TABLE ACTIVE ---
@app.route('/choisir', methods=['GET', 'POST'])
def choisir_table():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        nom_table = request.form.get('table')
        if nom_table not in tables:
            return f"⚠️ Schéma introuvable pour la table '{nom_table}'."
        session["active_table"] = nom_table
        return redirect(url_for("formulaire"))

    return render_template("choisir_table.html", tables=tables)

# --- CONNEXION ADMIN ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash("❌ Identifiants incorrects.", "danger")
        return redirect(url_for('admin_login'))
    return render_template("admin_login.html", active="admin")

# --- TABLEAU DE BORD ADMIN ---
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    active_table = session.get("active_table")

    return render_template("admin_dashboard.html", tables=tables, active_table=active_table, active="admin")

# --- VISION DES DONNÉES ADMIN ---
@app.route('/admin/data')
def admin_view_data():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session.get("active_table")
    if not table:
        return "⚠️ Aucune table active sélectionnée."

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM `{table}`")
    data = cursor.fetchall()

    return render_template("admin_view_data.html", table=table, data=data)

# --- DÉCONNEXION ADMIN ---
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


@app.route('/admin/create_table', methods=['GET', 'POST'])
def admin_create_table():
    if not session.get('admin_logged_in'):
        flash("Accès réservé à l'administrateur.", "danger")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        table_name = request.form.get('table_name').strip()
        fields = request.form.get('fields').strip()

        if not table_name or not fields:
            flash("Tous les champs sont requis.", "warning")
            return redirect(url_for('admin_create_table'))

        try:
            field_list = [f.strip() for f in fields.split(',')]
            columns_sql = ", ".join([f"`{col}` TEXT" for col in field_list])
            cursor = mysql.connection.cursor()
            cursor.execute(f"CREATE TABLE IF NOT EXISTS `{table_name}` (id INT AUTO_INCREMENT PRIMARY KEY, {columns_sql})")
            mysql.connection.commit()
            cursor.close()

            flash(f"La table '{table_name}' a été créée avec succès.", "success")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f"Erreur lors de la création de la table : {e}", "danger")

    return render_template("admin_create_table.html")

@app.route('/admin/add_user', methods=['GET', 'POST']) 
def admin_add_user():
    if not session.get('admin'): 
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    if not table:
        return "⚠️ Aucune table active."

    schema = schema_manager.load_schema(table)

    if request.method == 'POST':
        data = {champ: request.form.get(champ) for champ in schema}
        validated = data_validator.validate_record(data, schema)
        file_manager.insert_data(table, validated)
        return redirect(url_for('admin_view_data'))  # ✅ maintenant dans le bon bloc

    return render_template_string("""

<!DOCTYPE html><html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>➕ Ajouter un utilisateur</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <h2 class="text-center mb-4">➕ Ajouter un utilisateur à <strong>{{ table }}</strong></h2>
        <form method="POST" class="card p-4 shadow-sm bg-white">
            {% for champ in schema %}
                <div class="mb-3">
                    <label for="{{ champ }}" class="form-label">🔹 {{ champ }}</label>
                    <input type="text" name="{{ champ }}" id="{{ champ }}" class="form-control" required>
                </div>
            {% endfor %}
            <div class="d-grid gap-2 mt-4">
                <button type="submit" class="btn btn-success">✅ Enregistrer</button>
                <a href="{{ url_for('admin_view_data') }}" class="btn btn-secondary">⬅️ Retour aux données</a>
            </div>
        </form>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
""", table=table, schema=schema)@app.route('/admin/delete/int:id')
@app.route('/admin/delete_user/<int:id>')
def admin_delete_user(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    if not table:
        return "⚠️ Aucune table active sélectionnée."

    success = file_manager.delete_user(table, id)
    return redirect(url_for('admin_view_data')) if success else "❌ Erreur lors de la suppression de l'utilisateur."


@app.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
def admin_edit_user(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    table = session_manager.get_active_table()
    if not table:
        return "⚠️ Aucune table active."

    schema = schema_manager.load_schema(table)
    utilisateur = file_manager.get_user_by_id(table, id)
    if not utilisateur:
        return "⚠️ Utilisateur introuvable."

    if request.method == 'POST':
        for champ in schema:
            utilisateur[champ] = request.form.get(champ)
        validated = data_validator.validate_record(utilisateur, schema)
        file_manager.update_data(table, id, validated)
        return redirect(url_for('admin_view_data'))

    return render_template_string("""

<!DOCTYPE html><html lang="fr">
<head>
    <meta charset="UTF-8" />
    <title>✏️ Modifier utilisateur</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
</head>
<body class="bg-light">
    <div class="container py-5">
        <h2 class="text-center mb-4">✏️ Modifier l'utilisateur</h2>
        <form method="POST" class="card p-4 shadow-sm bg-white">
            {% for champ in schema %}
                <div class="mb-3">
                    <label for="{{ champ }}" class="form-label">🔹 {{ champ }}</label>
                    <input type="text" id="{{ champ }}" name="{{ champ }}" class="form-control" value="{{ utilisateur[champ] }}" required />
                </div>
            {% endfor %}
            <div class="d-grid gap-2 mt-4">
                <button type="submit" class="btn btn-primary">💾 Enregistrer</button>
                <a href="{{ url_for('admin_view_data') }}" class="btn btn-secondary">⬅️ Retour aux données</a>
            </div>
        </form>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
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

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename={table}.csv"}
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

        try:
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            reader = csv.DictReader(stream)
            new_data = [data_validator.validate_record(row, schema) for row in reader]
            file_manager.save_data(table, file_manager.load_data(table) + new_data)
            return f"✅ {len(new_data)} enregistrements importés dans '{table}'."
        except Exception as e:
            return f"❌ Erreur lors de l'import : {e}"

    return render_template_string(
        """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8" />
    <title>📥 Importer CSV dans '{{ table }}'</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
</head>
<body class="bg-light">
    <div class="container py-5">
        <h2 class="text-center mb-4">📥 Importer un fichier CSV dans <strong>{{ table }}</strong></h2>
        <form method="POST" enctype="multipart/form-data" class="card p-4 shadow-sm bg-white">
            <div class="mb-3">
                <input type="file" name="csv_file" accept=".csv" class="form-control" required />
            </div>
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary">⬆️ Importer</button>
                <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary">⬅️ Retour admin</a>
            </div>
        </form>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>""",
        table=table
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': email = request.form.get('email', '').strip().lower()
    mot_de_passe = request.form.get('mot_de_passe', '')

    if not email or not mot_de_passe:
        flash("Veuillez remplir tous les champs.", "warning")
        return redirect(url_for("login"))

    table = "utilisateurs"
    utilisateurs = file_manager.load_data(table)

    for user in utilisateurs:
        if user["email"].strip().lower() == email and check_password_hash(user["mot_de_passe"], mot_de_passe):
            if not user.get("email_confirmed", False):
                flash("❌ Adresse email non confirmée.", "danger")
                return redirect(url_for("login"))
            session["user_email"] = email
            flash("✅ Connexion réussie.", "success")
            return redirect(url_for('mon_espace'))

    flash("❌ Identifiants incorrects.", "danger")
    return redirect(url_for("login"))

    return render_template("login.html", active="login")




@app.route('/mon-espace', methods=['GET', 'POST'])
def mon_espace():
    if "user_email" not in session:
        return redirect(url_for('login'))

    email = session["user_email"]
    table = "utilisateurs"
    data = file_manager.load_data(table)
    utilisateur = next((u for u in data if u["email"].strip().lower() == email.strip().lower()), None)

    if not utilisateur:
        return "⚠️ Utilisateur introuvable.", 404

    if not utilisateur.get("email_confirmed", False):
        flash("⚠️ Votre adresse email n’a pas été confirmée. Veuillez vérifier vos emails.", "danger")
        return redirect(url_for("login"))

    # Initialiser champs si absents
    utilisateur.setdefault("budget", 0)
    utilisateur.setdefault("depenses", [])
    utilisateur.setdefault("economies", 0)
    utilisateur.setdefault("historique_economies", [])
    utilisateur.setdefault("investissements", [])

    if request.method == 'POST':
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action = request.form.get("action")

        try:
            if action == "set_budget":
                budget = float(request.form.get("new_budget"))
                utilisateur["budget"] = budget
                file_manager.save_data(table, data)
                flash(f"✅ Budget mis à jour avec succès ({now}).", "success")

            elif action == "add_depense":
                montant = float(request.form.get("depense_montant"))
                categorie = request.form.get("depense_categorie")
                date = datetime.now().strftime("%Y-%m-%d")
                total_depense = sum(d["montant"] for d in utilisateur["depenses"])
                if total_depense + montant > utilisateur["budget"]:
                    flash("⚠️ Cette dépense dépasse votre budget.", "danger")
                else:
                    utilisateur["depenses"].append({
                        "montant": montant,
                        "categorie": categorie,
                        "date": date,
                        "heure": now
                    })
                    file_manager.save_data(table, data)
                    flash(f"✅ Dépense ajoutée ({now}).", "success")

            elif action == "add_economie":
                montant = float(request.form.get("economie_montant"))
                if montant > utilisateur["budget"]:
                    flash("⚠️ Vous ne pouvez pas épargner plus que votre budget.", "danger")
                else:
                    utilisateur["budget"] -= montant
                    utilisateur["economies"] += montant
                    utilisateur["historique_economies"].append({
                        "action": "ajout",
                        "montant": montant,
                        "date": now
                    })
                    file_manager.save_data(table, data)
                    flash(f"✅ Vous avez économisé {montant} € le {now}.", "success")

            elif action == "remove_economie":
                montant = float(request.form.get("economie_montant"))
                if montant > utilisateur["economies"]:
                    flash("⚠️ Pas assez d'économies.", "danger")
                else:
                    utilisateur["budget"] += montant
                    utilisateur["economies"] -= montant
                    utilisateur["historique_economies"].append({
                        "action": "retrait",
                        "montant": montant,
                        "date": now
                    })
                    file_manager.save_data(table, data)
                    flash(f"✅ Vous avez réintroduit {montant} € depuis vos économies ({now}).", "success")

            elif action == "add_investissement":
                montant = float(request.form.get("investissement_montant"))
                domaine = request.form.get("investissement_domaine")
                if montant > utilisateur["budget"]:
                    flash("⚠️ Montant supérieur au budget disponible.", "danger")
                else:
                    utilisateur["budget"] -= montant
                    utilisateur["investissements"].append({
                        "montant": montant,
                        "domaine": domaine,
                        "date": now
                    })
                    file_manager.save_data(table, data)
                    flash(f"✅ Investissement de {montant} € dans {domaine} effectué ({now}).", "success")

        except ValueError:
            flash("❌ Format invalide pour les valeurs saisies.", "danger")
        except Exception as e:
            flash(f"❌ Erreur inattendue : {str(e)}", "danger")

        return redirect(url_for("mon_espace"))

    # Préparer données graphiques
    depenses_graph = [(d["montant"], d["categorie"], d["date"]) for d in utilisateur["depenses"]]
    investissements_graph = [(i["montant"], i["domaine"], i["date"]) for i in utilisateur["investissements"]]
    economies_graph = [(h["montant"], h["date"]) for h in utilisateur["historique_economies"]]

    return render_template("mon_espace.html",
                           utilisateur=utilisateur,
                           budget=utilisateur["budget"],
                           depenses=depenses_graph,
                           economies=economies_graph,
                           investissements=investissements_graph,
                           active="mon_espace")


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
            file_manager.save_data("utilisateurs", utilisateurs)
            flash("✅ Adresse email confirmée. Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for("login"))

    flash("❌ Adresse email introuvable.", "danger")
    return redirect(url_for("login"))


@app.route('/logout')
def logout():
    session.pop("user_email", None)
    session.pop("admin", None)
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for('login'))


@app.route('/accueil')
def accueil():
    return render_template("accueil.html", active="accueil")


@app.route("/contact")
def contact():
    return render_template("contact.html", active="contact")


@app.route("/confidentialite")
def politique_confidentialite():
    return render_template("confidentialite.html", active="confidentialite")


@app.route("/conditions")
def conditions_utilisation():
    return render_template("conditions.html", active="conditions")


@app.route('/admin/set/<name>')
def admin_set_table(name):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    session_manager.set_active_table(name)
    flash(f"✅ Table active définie sur : {name}", "success")
    return redirect(url_for('admin_dashboard'))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)