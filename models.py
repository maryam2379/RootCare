from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id               = db.Column(db.Integer, primary_key=True)
    nom              = db.Column(db.String(100), nullable=False)
    email            = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe     = db.Column(db.String(200), nullable=False)
    date_naissance   = db.Column(db.Date, nullable=False)
    sexe             = db.Column(db.String(10), nullable=False)
    ville            = db.Column(db.String(100), nullable=False)
    profession       = db.Column(db.String(100), nullable=True)
    est_admin        = db.Column(db.Boolean, default=False)
    date_creation    = db.Column(db.DateTime, default=datetime.utcnow)

    donnees = db.relationship('DonneeSante', backref='auteur', lazy=True)

    @property
    def age(self):
        today = date.today()
        d = self.date_naissance
        return today.year - d.year - ((today.month, today.day) < (d.month, d.day))

    def __repr__(self):
        return f'<User {self.email}>'


class DonneeSante(db.Model):
    __tablename__ = 'donnees_sante'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Alimentation
    nb_repas          = db.Column(db.String(20), nullable=False)
    fruits_legumes    = db.Column(db.String(30), nullable=False)
    eau_par_jour      = db.Column(db.String(20), nullable=False)
    alimentation_eq   = db.Column(db.String(20), nullable=False)

    # Activité & Sommeil
    activite_physique = db.Column(db.String(30), nullable=False)
    type_activite     = db.Column(db.String(100), nullable=True)
    heures_sommeil    = db.Column(db.String(20), nullable=False)
    qualite_sommeil   = db.Column(db.Integer, nullable=False)

    # Comportements
    tabac             = db.Column(db.String(20), nullable=False)
    alcool            = db.Column(db.String(20), nullable=False)
    niveau_stress     = db.Column(db.Integer, nullable=False)

    # Score & Niveau
    score             = db.Column(db.Integer, default=0)
    niveau_sante      = db.Column(db.String(20), default='Débutant')

    # Scores détaillés
    score_alimentation = db.Column(db.Integer, default=0)
    score_activite     = db.Column(db.Integer, default=0)
    score_sommeil      = db.Column(db.Integer, default=0)
    score_comportement = db.Column(db.Integer, default=0)

    date_soumission   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DonneeSante user={self.user_id} score={self.score}>'