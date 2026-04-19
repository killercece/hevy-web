"""Tests workflow workout : création, ajout sets, finish + PR."""

from __future__ import annotations


def _create_exercise(app, name="Squat", muscle="legs"):
    from app.extensions import db
    from app.models import Exercise

    with app.app_context():
        ex = Exercise(name=name, muscle_group=muscle, equipment="barbell")
        db.session.add(ex)
        db.session.commit()
        return ex.id


class TestWorkoutFlow:
    def test_create_empty_workout(self, auth_client):
        r = auth_client.post("/api/workouts", json={"name": "Quick Session"})
        assert r.status_code == 201
        w = r.get_json()["workout"]
        assert w["name"] == "Quick Session"
        assert w["is_finished"] is False

    def test_full_workflow(self, auth_client, app):
        ex_id = _create_exercise(app)

        # 1. Créer workout vide
        r = auth_client.post("/api/workouts", json={"name": "Leg Day"})
        workout_id = r.get_json()["workout"]["id"]

        # 2. Ajouter exercice
        r = auth_client.post(
            f"/api/workouts/{workout_id}/exercises",
            json={"exercise_id": ex_id},
        )
        assert r.status_code == 201
        we_id = r.get_json()["exercise"]["id"]

        # 3. Ajouter 2 sets
        r = auth_client.post(
            f"/api/workouts/{workout_id}/sets",
            json={
                "workout_exercise_id": we_id,
                "reps": 10,
                "weight": 100,
                "completed": True,
            },
        )
        assert r.status_code == 201

        r = auth_client.post(
            f"/api/workouts/{workout_id}/sets",
            json={
                "workout_exercise_id": we_id,
                "reps": 8,
                "weight": 110,
                "completed": True,
            },
        )
        assert r.status_code == 201

        # 4. Finish
        r = auth_client.post(f"/api/workouts/{workout_id}/finish")
        assert r.status_code == 200
        data = r.get_json()
        assert data["workout"]["is_finished"] is True
        # Premier workout = premier PR détecté
        assert len(data["new_prs"]) >= 1

    def test_finish_twice_fails(self, auth_client):
        r = auth_client.post("/api/workouts", json={"name": "X"})
        workout_id = r.get_json()["workout"]["id"]
        auth_client.post(f"/api/workouts/{workout_id}/finish")
        r = auth_client.post(f"/api/workouts/{workout_id}/finish")
        assert r.status_code == 409


class TestPRDetection:
    def test_pr_detected_on_heavier_weight(self, auth_client, app):
        ex_id = _create_exercise(app)

        # Workout 1 : squat 100kg × 10
        r = auth_client.post("/api/workouts", json={})
        w1 = r.get_json()["workout"]["id"]
        r = auth_client.post(
            f"/api/workouts/{w1}/exercises", json={"exercise_id": ex_id}
        )
        we = r.get_json()["exercise"]["id"]
        auth_client.post(
            f"/api/workouts/{w1}/sets",
            json={
                "workout_exercise_id": we,
                "reps": 10,
                "weight": 100,
                "completed": True,
            },
        )
        r1 = auth_client.post(f"/api/workouts/{w1}/finish")
        prs1 = r1.get_json()["new_prs"]
        assert len(prs1) >= 1

        # Workout 2 : squat 120kg × 8 → nouveau PR poids
        r = auth_client.post("/api/workouts", json={})
        w2 = r.get_json()["workout"]["id"]
        r = auth_client.post(
            f"/api/workouts/{w2}/exercises", json={"exercise_id": ex_id}
        )
        we2 = r.get_json()["exercise"]["id"]
        auth_client.post(
            f"/api/workouts/{w2}/sets",
            json={
                "workout_exercise_id": we2,
                "reps": 8,
                "weight": 120,
                "completed": True,
            },
        )
        r2 = auth_client.post(f"/api/workouts/{w2}/finish")
        prs2 = r2.get_json()["new_prs"]
        pr_types = {pr["pr_type"] for pr in prs2}
        assert "weight" in pr_types

    def test_no_new_pr_on_worse_performance(self, auth_client, app):
        ex_id = _create_exercise(app)

        r = auth_client.post("/api/workouts", json={})
        w1 = r.get_json()["workout"]["id"]
        r = auth_client.post(
            f"/api/workouts/{w1}/exercises", json={"exercise_id": ex_id}
        )
        we = r.get_json()["exercise"]["id"]
        auth_client.post(
            f"/api/workouts/{w1}/sets",
            json={
                "workout_exercise_id": we,
                "reps": 10,
                "weight": 100,
                "completed": True,
            },
        )
        auth_client.post(f"/api/workouts/{w1}/finish")

        # Workout 2 : performance moindre → aucun nouveau PR
        r = auth_client.post("/api/workouts", json={})
        w2 = r.get_json()["workout"]["id"]
        r = auth_client.post(
            f"/api/workouts/{w2}/exercises", json={"exercise_id": ex_id}
        )
        we2 = r.get_json()["exercise"]["id"]
        auth_client.post(
            f"/api/workouts/{w2}/sets",
            json={
                "workout_exercise_id": we2,
                "reps": 5,
                "weight": 80,
                "completed": True,
            },
        )
        r2 = auth_client.post(f"/api/workouts/{w2}/finish")
        assert r2.get_json()["new_prs"] == []
