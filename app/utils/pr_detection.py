"""Détection des Personal Records (PR).

4 types de PR gérés :
- weight  : poids max jamais soulevé (pour cet exercice)
- reps    : reps max pour un poids donné (même poids, plus de reps)
- volume  : volume max (weight × reps) sur un set
- e1rm    : e1RM max estimé (formule Epley)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from ..extensions import db
from ..models import PersonalRecord, Workout, WorkoutExercise, WorkoutSet
from .calculations import e1rm


def detect_prs_for_workout(workout: Workout) -> list[PersonalRecord]:
    """Parcourt tous les sets complétés d'un workout et détecte les PR.

    Pour chaque set nouveau-record :
      - marque workout_set.is_pr = True
      - crée une entrée PersonalRecord
    Retourne la liste des nouveaux PR créés.
    """
    new_prs: list[PersonalRecord] = []
    user_id = workout.user_id

    for we in workout.exercises:
        exercise_id = we.exercise_id
        for s in we.sets:
            if not s.completed or not s.weight or not s.reps:
                continue
            new_prs.extend(_check_set_for_prs(s, user_id, exercise_id))

    db.session.flush()
    return new_prs


def _check_set_for_prs(
    workout_set: WorkoutSet, user_id: int, exercise_id: int
) -> list[PersonalRecord]:
    """Vérifie si un set constitue un nouveau PR sur un ou plusieurs critères."""
    created: list[PersonalRecord] = []
    now = workout_set.completed_at or datetime.utcnow()

    # -- PR Poids max (indépendant des reps) ------------------------------
    current_max_weight = _current_pr_value(user_id, exercise_id, "weight")
    if workout_set.weight > current_max_weight:
        pr = PersonalRecord(
            user_id=user_id,
            exercise_id=exercise_id,
            pr_type="weight",
            value=workout_set.weight,
            reps=workout_set.reps,
            weight=workout_set.weight,
            workout_set_id=workout_set.id,
            achieved_at=now,
        )
        db.session.add(pr)
        created.append(pr)
        workout_set.is_pr = True

    # -- PR Volume (weight × reps sur un set unique) ----------------------
    set_volume = workout_set.weight * workout_set.reps
    current_max_volume = _current_pr_value(user_id, exercise_id, "volume")
    if set_volume > current_max_volume:
        pr = PersonalRecord(
            user_id=user_id,
            exercise_id=exercise_id,
            pr_type="volume",
            value=set_volume,
            reps=workout_set.reps,
            weight=workout_set.weight,
            workout_set_id=workout_set.id,
            achieved_at=now,
        )
        db.session.add(pr)
        created.append(pr)
        workout_set.is_pr = True

    # -- PR e1RM ---------------------------------------------------------
    set_e1rm = e1rm(workout_set.weight, workout_set.reps)
    current_max_e1rm = _current_pr_value(user_id, exercise_id, "e1rm")
    if set_e1rm > current_max_e1rm:
        pr = PersonalRecord(
            user_id=user_id,
            exercise_id=exercise_id,
            pr_type="e1rm",
            value=set_e1rm,
            reps=workout_set.reps,
            weight=workout_set.weight,
            workout_set_id=workout_set.id,
            achieved_at=now,
        )
        db.session.add(pr)
        created.append(pr)
        workout_set.is_pr = True

    # -- PR Reps @ poids (plus de reps pour un poids >= à un précédent) ---
    # On considère un PR "reps" si reps > max(reps historique pour poids identique)
    max_reps_at_weight = (
        db.session.query(func.max(WorkoutSet.reps))
        .join(WorkoutExercise, WorkoutSet.workout_exercise_id == WorkoutExercise.id)
        .join(Workout, WorkoutExercise.workout_id == Workout.id)
        .filter(
            Workout.user_id == user_id,
            WorkoutExercise.exercise_id == exercise_id,
            WorkoutSet.weight == workout_set.weight,
            WorkoutSet.completed.is_(True),
            WorkoutSet.id != workout_set.id,
        )
        .scalar()
    )
    if max_reps_at_weight is None or workout_set.reps > max_reps_at_weight:
        current_reps_pr = _current_pr_value(user_id, exercise_id, "reps")
        # On ne crée le PR "reps" que si ce n'est pas déjà enregistré pour ce set
        if workout_set.reps > current_reps_pr:
            pr = PersonalRecord(
                user_id=user_id,
                exercise_id=exercise_id,
                pr_type="reps",
                value=float(workout_set.reps),
                reps=workout_set.reps,
                weight=workout_set.weight,
                workout_set_id=workout_set.id,
                achieved_at=now,
            )
            db.session.add(pr)
            created.append(pr)
            workout_set.is_pr = True

    return created


def _current_pr_value(user_id: int, exercise_id: int, pr_type: str) -> float:
    """Retourne la valeur max actuelle d'un PR pour (user, exercise, type).

    Renvoie 0.0 si aucun PR enregistré.
    """
    val = (
        db.session.query(func.max(PersonalRecord.value))
        .filter(
            PersonalRecord.user_id == user_id,
            PersonalRecord.exercise_id == exercise_id,
            PersonalRecord.pr_type == pr_type,
        )
        .scalar()
    )
    return float(val) if val is not None else 0.0
