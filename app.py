import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, DonneeSante
from datetime import datetime, date
import json

app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rootcare-secret-key-2024')

# --- CORRECTION CRUCIALE POUR POSTGRESQL ---
uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    # SQLAlchemy nécessite "postgresql://" au lieu de "postgres://" 
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri or ('sqlite:///' + os.path.join(app.instance_path, 'rootcare.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Connectez-vous pour accéder à cette page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- LOGIQUE DE CALCUL ET STATISTIQUES ---
def calculer_score(data):
    s_alim = s_activ = s_sommeil = s_comport = 0
    s_alim += {"3": 10, "2": 6, "1": 2, "+3": 12}.get(data.get('nb_repas',''), 0)
    s_alim += {"quotidien": 8, "souvent": 6, "parfois": 3, "jamais": 0}.get(data.get('fruits_legumes',''), 0)
    s_alim = min(s_alim, 20)
    s_activ += {"quotidien": 20, "3-5x": 15, "1-2x": 8, "jamais": 0}.get(data.get('activite_physique',''), 0)
    s_sommeil += {"6-8h": 14, "+8h": 10, "-6h": 4}.get(data.get('heures_sommeil',''), 0)
    qualite = int(data.get('qualite_sommeil', 3))
    s_sommeil += {1: 0, 2: 2, 3: 4, 4: 5, 5: 6}.get(qualite, 0)
    s_sommeil = min(s_sommeil, 20)
    s_comport += {"jamais": 10, "occasionnel": 6, "regulier": 0}.get(data.get('tabac',''), 0)
    s_comport += {"jamais": 10, "occasionnel": 6, "regulier": 0}.get(data.get('alcool',''), 0)
    stress = int(data.get('niveau_stress', 3))
    s_comport -= {1: 0, 2: 0, 3: 2, 4: 4, 5: 6}.get(stress, 0)
    s_comport = max(0, min(s_comport, 20))
    total = s_alim + s_activ + s_sommeil + s_comport
    if   total >= 70: niveau = 'Champion'
    elif total >= 50: niveau = 'Actif'
    elif total >= 30: niveau = 'Intermédiaire'
    else:             niveau = 'Débutant'
    return total, niveau, s_alim, s_activ, s_sommeil, s_comport

def generer_conseils(donnee, user):
    conseils = []
    if donnee.activite_physique in ('jamais', '1-2x'):
        conseils.append({'type': 'warning', 'titre': 'Activité physique insuffisante', 'texte': "Essaie 30 minutes de marche rapide par jour."})
    else:
        conseils.append({'type': 'success', 'titre': 'Bonne activité physique !', 'texte': "Continue à maintenir cette habitude."})
    if donnee.heures_sommeil == '-6h':
        conseils.append({'type': 'warning', 'titre': 'Manque de sommeil détecté', 'texte': "Vise 7 à 8 heures chaque nuit."})
    if donnee.nb_repas in ('1', '2'):
        conseils.append({'type': 'info', 'titre': 'Améliore ton alimentation', 'texte': f'Manger seulement {donnee.nb_repas} repas par jour peut causer de la fatigue.'})
    if donnee.eau_par_jour == '-1L':
        conseils.append({'type': 'warning', 'titre': 'Hydratation insuffisante', 'texte': "Bois au moins 1,5 L d'eau par jour."})
    else:
        conseils.append({'type': 'success', 'titre': 'Bonne hydratation !', 'texte': "Tu bois suffisamment d'eau. Continue."})
    if donnee.tabac == 'regulier':
        conseils.append({'type': 'danger', 'titre': 'Tabac — risque élevé', 'texte': "Le tabac est la première cause de maladies évitables."})
    if donnee.niveau_stress >= 4:
        conseils.append({'type': 'warning', 'titre': 'Niveau de stress élevé', 'texte': "Essaie la respiration profonde ou la méditation."})
    return conseils

def get_stats_globales():
    toutes = DonneeSante.query.all()
    if not toutes: return {}
    villes, niveaux, ages, activites = {}, {'Débutant': 0, 'Intermédiaire': 0, 'Actif': 0, 'Champion': 0}, [], {}
    for d in toutes:
        user = User.query.get(d.user_id)
        if user:
            villes[user.ville] = villes.get(user.ville, 0) + 1
            ages.append(user.age)
        niveaux[d.niveau_sante] = niveaux.get(d.niveau_sante, 0) + 1
        activites[d.activite_physique] = activites.get(d.activite_physique, 0) + 1
    score_moyen = round(sum(d.score for d in toutes) / len(toutes), 1)
    return {'villes': villes, 'niveaux': niveaux, 'ages': ages, 'activites': activites, 'score_moyen': score_moyen, 'total': len(toutes)}

# --- ROUTES ---
@app.route('/')
def index():
    total = DonneeSante.query.count()
    villes_count = db.session.query(User.ville).distinct().count()
    score_moyen = db.session.query(db.func.avg(DonneeSante.score)).scalar() or 0
    return render_template('index.html', total=total, villes_count=villes_count, score_moyen=round(score_moyen, 1))

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if current_user.is_authenticated: return redirect(url_for('formulaire'))
    if request.method == 'POST':
        nom, email, mdp, mdp_confirm = request.form.get('nom', '').strip(), request.form.get('email', '').strip(), request.form.get('mot_de_passe', ''), request.form.get('mot_de_passe_confirm', '')
        date_naissance, sexe, ville, profession = request.form.get('date_naissance', ''), request.form.get('sexe', ''), request.form.get('ville', ''), request.form.get('profession', '')
        
        if not all([nom, email, mdp, date_naissance, sexe, ville]):
            flash('Veuillez remplir tous les champs obligatoires.', 'danger')
            return redirect(url_for('inscription'))
        if mdp != mdp_confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('inscription'))
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('inscription'))
        
        try:
            dob = datetime.strptime(date_naissance, '%Y-%m-%d').date()
            age = date.today().year - dob.year - ((date.today().month, date.today().day) < (dob.month, dob.day))
            user = User(nom=nom, email=email, mot_de_passe=generate_password_hash(mdp), date_naissance=dob, sexe=sexe, ville=ville, profession=profession)
            db.session.add(user)
            db.session.commit()
            flash('Compte créé avec succès !', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'inscription : {str(e)}', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('formulaire'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email', '').strip()).first()
        if user and check_password_hash(user.mot_de_passe, request.form.get('mot_de_passe', '')):
            login_user(user)
            return redirect(request.args.get('next') or url_for('formulaire'))
        flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/formulaire', methods=['GET', 'POST'])
@login_required
def formulaire():
    deja_soumis = DonneeSante.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        data = request.form
        score, niveau, s_alim, s_activ, s_sommeil, s_comport = calculer_score(data)
        if deja_soumis:
            d = deja_soumis
            d.nb_repas = data.get('nb_repas'); d.fruits_legumes = data.get('fruits_legumes')
            d.eau_par_jour = data.get('eau_par_jour'); d.alimentation_eq = data.get('alimentation_eq', 'parfois')
            d.activite_physique = data.get('activite_physique')
            d.type_activite = ','.join(request.form.getlist('type_activite'))
            d.heures_sommeil = data.get('heures_sommeil'); d.qualite_sommeil = int(data.get('qualite_sommeil', 3))
            d.tabac = data.get('tabac'); d.alcool = data.get('alcool')
            d.niveau_stress = int(data.get('niveau_stress', 3))
            d.score, d.niveau_sante = score, niveau
            d.score_alimentation, d.score_activite = s_alim, s_activ
            d.score_sommeil, d.score_comportement = s_sommeil, s_comport
            d.date_soumission = datetime.utcnow()
        else:
            d = DonneeSante(user_id=current_user.id, nb_repas=data.get('nb_repas'), fruits_legumes=data.get('fruits_legumes'), eau_par_jour=data.get('eau_par_jour'), alimentation_eq=data.get('alimentation_eq', 'parfois'), activite_physique=data.get('activite_physique'), type_activite=','.join(request.form.getlist('type_activite')), heures_sommeil=data.get('heures_sommeil'), qualite_sommeil=int(data.get('qualite_sommeil', 3)), tabac=data.get('tabac'), alcool=data.get('alcool'), niveau_stress=int(data.get('niveau_stress', 3)), score=score, niveau_sante=niveau, score_alimentation=s_alim, score_activite=s_activ, score_sommeil=s_sommeil, score_comportement=s_comport)
            db.session.add(d)
        db.session.commit()
        return redirect(url_for('espace_user'))
    return render_template('formulaire.html', deja_soumis=deja_soumis)

@app.route('/espace-user')
@login_required
def espace_user():
    ma_donnee = DonneeSante.query.filter_by(user_id=current_user.id).first()
    stats = get_stats_globales()
    return render_template('espace_user.html', donnee=ma_donnee, conseils=generer_conseils(ma_donnee, current_user) if ma_donnee else [], stats=json.dumps(stats), total=DonneeSante.query.count(), score_moyen=stats.get('score_moyen', 0), rang=(DonneeSante.query.filter(DonneeSante.score > ma_donnee.score).count() + 1) if ma_donnee else 0)

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.est_admin: return redirect(url_for('index'))
    return render_template('dashboard.html', donnees=DonneeSante.query.order_by(DonneeSante.date_soumission.desc()).all(), users=User.query.all(), stats=json.dumps(get_stats_globales()), total=DonneeSante.query.count())

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats_globales())

# --- POINT D'ENTRÉE ---
# Note : db.create_all() est conservé ici mais doit être lancé manuellement localement une fois 
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)