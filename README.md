# Hevy-Web

Clone web de l'application [Hevy](https://www.hevyapp.com/) (tracker de musculation) en Flask.

## Stack technique

- **Backend** : Flask 3 + SQLAlchemy + SQLite + Flask-Login + Flask-Migrate
- **Frontend** : Jinja2 + Alpine.js + HTMX + Chart.js (servi par Flask)
- **Tests** : pytest + Flask test client
- **Déploiement** : compatible [pydeploy](/projects/pydeploy) via `wsgi.py` + gunicorn

## Fonctionnalités

- Authentification par session (multi-utilisateur)
- Bibliothèque de ~180 exercices pré-chargés (muscle, équipement, type)
- Routines : création, édition, dossiers, duplication, démarrage
- Séances (workouts) : timer live, sets (normal/warmup/drop/failure), RPE, notes
- Détection automatique de 4 types de PR : poids max, reps max, volume, e1RM
- Statistiques : volume total, streak, historique par exercice, graphiques
- Export/import JSON des données

## Installation

Prérequis : Python 3.11+.

```bash
cd /projects/hevy-web
./run.sh
```

Le script :
- Crée un `venv/` si nécessaire
- Installe les dépendances (`requirements.txt`)
- Copie `.env.example` → `.env` au premier lancement
- Seede 178 exercices + un utilisateur admin par défaut (`admin@local` / `admin`)
- Lance le serveur dev sur [http://localhost:5000](http://localhost:5000)

**Change le mot de passe admin dès le premier login !**

## Structure

```
hevy-web/
├── app/
│   ├── __init__.py        # Application factory (create_app)
│   ├── extensions.py      # db, login_manager, migrate
│   ├── models.py          # User, Exercise, Routine, Workout, PersonalRecord, ...
│   ├── routes/
│   │   ├── auth.py        # /login, /register, /logout
│   │   ├── main.py        # pages HTML (Jinja)
│   │   └── api.py         # /api/* JSON
│   ├── utils/
│   │   ├── calculations.py   # e1RM, volume, conversions kg/lb
│   │   ├── pr_detection.py   # détection des PR au finish
│   │   ├── timer.py          # constants repos
│   │   └── seed_exercises.py # bibliothèque d'exercices
│   ├── templates/         # Jinja2 (Frontend)
│   └── static/            # CSS/JS (Frontend)
├── tests/                 # pytest
├── data/                  # SQLite (gitignoré)
├── migrations/            # Alembic
├── config.py              # DevConfig, TestConfig, ProdConfig
├── wsgi.py                # Entry point WSGI (gunicorn/pydeploy)
├── requirements.txt
├── run.sh                 # Lance le dev server
└── pytest.ini
```

## Lancer les tests

```bash
source venv/bin/activate
pytest
```

33 tests couvrent : auth, CRUD routines, workflow workouts, détection PR, calculs e1RM/volume.

## API

Voir [API.md](./API.md) pour la liste complète des endpoints et payloads.

Aperçu rapide :

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/login` | Connexion |
| GET | `/api/exercises` | Liste bibliothèque (filtres muscle/equipment/search) |
| POST | `/api/routines` | Crée routine |
| POST | `/api/routines/<id>/start` | Démarre workout depuis routine |
| POST | `/api/workouts/<id>/sets` | Ajoute set live |
| POST | `/api/workouts/<id>/finish` | Termine séance + détecte PR |
| GET | `/api/stats` | Stats globales utilisateur |

## Déploiement pydeploy

Le projet est compatible pydeploy tel quel (wsgi.py expose `app`). Pour déployer :

1. Push sur GitHub (public ou privé)
2. Créer un site via `pydeploy create_site` avec le repo URL
3. Variables d'environnement requises : `SECRET_KEY`, éventuellement `ADMIN_EMAIL`/`ADMIN_PASSWORD`
4. Pydeploy lance `gunicorn wsgi:app` automatiquement

## Licence

Projet éducatif, inspiré de Hevy (pas affilié). Code sous licence MIT.
