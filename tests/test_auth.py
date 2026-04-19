"""Tests d'authentification."""

from __future__ import annotations


class TestAuth:
    def test_register_api(self, client):
        r = client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "pwd12345"},
        )
        assert r.status_code == 201
        data = r.get_json()
        assert data["user"]["email"] == "new@example.com"

    def test_register_missing_fields(self, client):
        r = client.post("/api/auth/register", json={"email": ""})
        assert r.status_code == 400

    def test_register_duplicate(self, client, user):
        r = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "x"},
        )
        assert r.status_code == 409

    def test_login_success(self, client, user):
        r = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "secret"},
        )
        assert r.status_code == 200
        assert r.get_json()["user"]["email"] == "test@example.com"

    def test_login_invalid(self, client, user):
        r = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
        )
        assert r.status_code == 401

    def test_me_requires_auth(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_me_returns_user(self, auth_client):
        r = auth_client.get("/api/auth/me")
        assert r.status_code == 200
        assert r.get_json()["user"]["email"] == "test@example.com"

    def test_logout(self, auth_client):
        r = auth_client.post("/api/auth/logout")
        assert r.status_code == 200
        # Après logout, /auth/me doit être 401
        r = auth_client.get("/api/auth/me")
        assert r.status_code == 401
