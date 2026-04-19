#!/usr/bin/env bash
# Script de lancement en mode développement
set -e

cd "$(dirname "$0")"

# Création venv si absent
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activation et installation des dépendances
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Copie .env.example vers .env si absent
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Fichier .env créé depuis .env.example - pensez à l'éditer !"
fi

# Init DB / migrations si besoin
export FLASK_APP=wsgi.py
export FLASK_ENV=development

# Lancement serveur dev
echo "Démarrage de Hevy-Web sur http://localhost:5000"
python wsgi.py
