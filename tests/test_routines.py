"""Tests CRUD routines + start."""

from __future__ import annotations


class TestRoutines:
    def _create_exercise(self, app):
        from app.extensions import db
        from app.models import Exercise

        with app.app_context():
            ex = Exercise(
                name="Bench Press", muscle_group="chest", equipment="barbell"
            )
            db.session.add(ex)
            db.session.commit()
            return ex.id

    def test_create_routine(self, auth_client, app):
        ex_id = self._create_exercise(app)
        r = auth_client.post(
            "/api/routines",
            json={
                "name": "Push Day",
                "exercises": [
                    {
                        "exercise_id": ex_id,
                        "sets": [
                            {"target_reps": 10, "target_weight": 80},
                            {"target_reps": 8, "target_weight": 85},
                        ],
                    }
                ],
            },
        )
        assert r.status_code == 201
        data = r.get_json()["routine"]
        assert data["title"] == "Push Day"
        assert len(data["exercises"]) == 1
        assert len(data["exercises"][0]["sets"]) == 2

    def test_list_routines(self, auth_client, app):
        ex_id = self._create_exercise(app)
        auth_client.post("/api/routines", json={"name": "R1"})
        auth_client.post("/api/routines", json={"name": "R2"})
        r = auth_client.get("/api/routines")
        assert r.status_code == 200
        assert len(r.get_json()["routines"]) == 2

    def test_delete_routine(self, auth_client, app):
        r = auth_client.post("/api/routines", json={"name": "ToDelete"})
        routine_id = r.get_json()["routine"]["id"]
        r = auth_client.delete(f"/api/routines/{routine_id}")
        assert r.status_code == 200
        r = auth_client.get(f"/api/routines/{routine_id}")
        assert r.status_code == 404

    def test_start_routine_creates_workout(self, auth_client, app):
        ex_id = self._create_exercise(app)
        r = auth_client.post(
            "/api/routines",
            json={
                "name": "Test",
                "exercises": [
                    {
                        "exercise_id": ex_id,
                        "sets": [{"target_reps": 10, "target_weight": 80}],
                    }
                ],
            },
        )
        routine_id = r.get_json()["routine"]["id"]

        r = auth_client.post(f"/api/routines/{routine_id}/start")
        assert r.status_code == 201
        workout = r.get_json()["workout"]
        assert workout["name"] == "Test"
        assert workout["routine_id"] == routine_id
        assert len(workout["exercises"]) == 1
