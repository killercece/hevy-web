"""Tests endpoints exercices."""

from __future__ import annotations


class TestExercises:
    def test_list_returns_seeded_library(self, auth_client):
        r = auth_client.get("/api/exercises")
        assert r.status_code == 200
        exercises = r.get_json()["exercises"]
        # ~180 exercices seedés
        assert len(exercises) > 100
        # Tous ont un nom et muscleGroup
        for e in exercises[:5]:
            assert e["name"]
            assert "muscleGroup" in e

    def test_filter_by_muscle(self, auth_client):
        r = auth_client.get("/api/exercises?muscle_group=chest")
        assert r.status_code == 200
        exercises = r.get_json()["exercises"]
        assert all(e["muscleGroup"] == "chest" for e in exercises)

    def test_search(self, auth_client):
        r = auth_client.get("/api/exercises?search=bench")
        assert r.status_code == 200
        exercises = r.get_json()["exercises"]
        assert any("Bench" in e["name"] for e in exercises)

    def test_create_custom(self, auth_client):
        r = auth_client.post(
            "/api/exercises",
            json={
                "name": "Kettlebell Halo",
                "muscle_group": "shoulders",
                "equipment": "kettlebell",
                "exercise_type": "reps",
            },
        )
        assert r.status_code == 201
        assert r.get_json()["exercise"]["isCustom"] is True

    def test_unauth_blocked(self, client):
        r = client.get("/api/exercises")
        assert r.status_code == 401
