import random
from datetime import date
from app import app, db, User, DonneeSante
from werkzeug.security import generate_password_hash

# Listes pour une diversité totale (Nord, Sud, Est, Ouest, Littoral)
noms_cm = [
    "Abogo", "Tchuente", "Biyong", "Hamadou", "Ngando", 
    "Foning", "Minka", "Eteki", "Bouba", "Yonta",
    "Mbarga", "Ndjana", "Tchakounté", "Nana", "Simo", 
    "Batchaya", "Mvondo", "Nkou", "Lekeufack", "Moussa",
    "Onana", "Bekolo", "Nguini", "Tchameni", "Ateba", 
    "Fokou", "Djoko", "Siewe", "Biya", "Kengne"
]

prenoms_cm = [
    "Arnaud", "Sidonie", "Rodrigue", "Fadimatou", "Gilles", 
    "Thérèse", "Paulin", "Célestine", "Ibrahim", "Mireille",
    "Fabrice", "Estelle", "Christian", "Carine", "Ludovic", 
    "Sandrine", "Prosper", "Bernadette", "Guy", "Oumarou",
    "Valentin", "Clarisse", "Serge", "Edwige", "Yannick", 
    "Nadège", "Bertrand", "Josiane", "Arthur", "Sorelle"
]

villes = ["Yaoundé", "Douala", "Bafoussam", "Garoua", "Maroua", "Ngaoundéré", "Bamenda", "Kribi", "Dschang", "Ebolowa", "Bertoua", "Buéa"]
professions = ["Commerçant", "Infirmier", "Étudiant", "Enseignant", "Ingénieur", "Développeur", "Agriculteur", "Comptable"]

def seed_complete_30():
    with app.app_context():
        print("Début de l'insertion de 30 nouveaux profils...")
        
        for i in range(30):
            # Création d'un nom et d'un email unique
            nom_p = noms_cm[i]
            prenom_p = prenoms_cm[i]
            nom_complet = f"{nom_p} {prenom_p}"
            
            # Email unique pour éviter les erreurs de base de données (UNIQUE constraint)
            email_unique = f"{nom_p.lower()}.{prenom_p.lower()}{i+100}@rootcare.cm"
            
            # 1. Création de l'utilisateur
            user = User(
                nom=nom_complet,
                email=email_unique,
                mot_de_passe=generate_password_hash("password123"),
                date_naissance=date(random.randint(1978, 2005), random.randint(1, 12), random.randint(1, 28)),
                sexe=random.choice(["Masculin", "Féminin"]),
                ville=random.choice(villes),
                profession=random.choice(professions)
            )
            
            db.session.add(user)
            db.session.commit() # On commit pour récupérer l'ID de l'utilisateur

            # 2. Simulation de scores pour les graphiques radar
            # (Basé sur ton modèle DonneeSante)
            s_alim = random.randint(10, 20)
            s_activ = random.randint(8, 20)
            s_sommeil = random.randint(7, 20)
            s_comport = random.randint(11, 20)
            total_score = s_alim + s_activ + s_sommeil + s_comport

            if total_score < 45: niveau = "Débutant"
            elif total_score < 65: niveau = "Intermédiaire"
            elif total_score < 85: niveau = "Actif"
            else: niveau = "Champion"

            # 3. Création de la fiche de santé associée
            donnee = DonneeSante(
                user_id=user.id,
                nb_repas=random.choice(["2", "3", "+3"]),
                fruits_legumes=random.choice(["parfois", "souvent", "quotidien"]),
                eau_par_jour=random.choice(["1-2L", "+2L"]),
                alimentation_eq=random.choice(["oui", "parfois"]),
                activite_physique=random.choice(["1-2x", "3-5x", "quotidien"]),
                type_activite=random.choice(["Marche", "Football", "Course", "Danse"]),
                heures_sommeil=random.choice(["6-8h", "+8h"]),
                qualite_sommeil=random.randint(3, 5),
                tabac="jamais",
                alcool=random.choice(["jamais", "occasionnel"]),
                niveau_stress=random.randint(1, 4),
                score=total_score,
                niveau_sante=niveau,
                score_alimentation=s_alim,
                score_activite=s_activ,
                score_sommeil=s_sommeil,
                score_comportement=s_comport
            )
            
            db.session.add(donnee)

        db.session.commit()
        print(f"Succès : 30 nouveaux participants ajoutés avec des emails uniques.")

if __name__ == "__main__":
    # Si tu veux vider la table avant, ajoute db.drop_all() au début du script
    seed_complete_30()