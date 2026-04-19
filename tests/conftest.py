"""Fixtures pytest partagées : app, client, utilisateur authentifié."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ajoute le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import create_app
from app.extensions import db
from app.models import User
from config import TestConfig


@pytest.fixture
def app():
    """Instance Flask configurée pour les tests (SQLite in-memory)."""
    flask_app = create_app(TestConfig)
    yield flask_app


@pytest.fixture
def client(app):
    """Test client Flask."""
    return app.test_client()


@pytest.fixture
def user(app):
    """Crée un utilisateur de test et renvoie son id."""
    with app.app_context():
        u = User(email="test@example.com")
        u.set_password("secret")
        db.session.add(u)
        db.session.commit()
        return u.id


@pytest.fixture
def auth_client(client, user):
    """Client déjà authentifié avec un user de test."""
    client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "secret"},
    )
    return client
