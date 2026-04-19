"""Blueprint API JSON (préfixe /api).

Expose toutes les ressources : auth, exercises, routines, folders, workouts,
sets, stats. Les payloads sont documentés dans API.md.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import and_, func, or_

from ..extensions import db
from ..models import (
    Exercise,
    PersonalRecord,
    Routine,
    RoutineExercise,
    RoutineFolder,
    RoutineSet,
    User,
    Workout,
    WorkoutExercise,
    WorkoutSet,
)
from ..utils.calculations import e1rm
from ..utils.pr_detection import detect_prs_for_workout

api_bp = Blueprint("api", __name__)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _json() -> dict:
    """Renvoie le body JSON ou un dict vide."""
    return request.get_json(silent=True) or {}


def _owned_or_404(model, obj_id: int, user_id_field: str = "user_id"):
    """Récupère un objet owned par l'utilisateur courant, sinon 404."""
    obj = db.session.get(model, obj_id)
    if obj is None:
        abort(404)
    if getattr(obj, user_id_field, None) != current_user.id:
        abort(404)
    return obj


# --------------------------------------------------------------------------
# AUTH
# --------------------------------------------------------------------------


@api_bp.post("/auth/register")
def api_register():
    data = _json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify(error="missing_fields"), 400
    if db.session.query(User).filter_by(email=email).first():
        return jsonify(error="email_taken"), 409
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify(user=user.to_dict()), 201


@api_bp.post("/auth/login")
def api_login():
    data = _json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = db.session.query(User).filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(error="invalid_credentials"), 401
    login_user(user, remember=bool(data.get("remember")))
    return jsonify(user=user.to_dict())


@api_bp.post("/auth/logout")
@login_required
def api_logout():
    logout_user()
    return jsonify(ok=True)


@api_bp.get("/auth/me")
@login_required
def api_me():
    return jsonify(user=current_user.to_dict())


# --------------------------------------------------------------------------
# SETTINGS (prefs utilisateur)
# --------------------------------------------------------------------------


@api_bp.get("/settings")
@login_required
def get_settings():
    """Retourne les préférences de l'utilisateur courant."""
    return jsonify(
        settings={
            "unit_system": current_user.unit_system,
            "rest_timer_default": current_user.rest_timer_default,
            "sound_enabled": current_user.sound_enabled,
            "vibration_enabled": current_user.vibration_enabled,
        }
    )


@api_bp.put("/settings")
@login_required
def update_settings():
    """Met à jour les préférences utilisateur."""
    data = _json()
    for field in (
        "unit_system",
        "rest_timer_default",
        "sound_enabled",
        "vibration_enabled",
    ):
        if field in data:
            setattr(current_user, field, data[field])
    db.session.commit()
    return jsonify(
        settings={
            "unit_system": current_user.unit_system,
            "rest_timer_default": current_user.rest_timer_default,
            "sound_enabled": current_user.sound_enabled,
            "vibration_enabled": current_user.vibration_enabled,
        }
    )


# --------------------------------------------------------------------------
# EXPORT / IMPORT
# --------------------------------------------------------------------------


@api_bp.get("/export")
@login_required
def export_data():
    """Export JSON complet des données utilisateur (format simple)."""
    routines = (
        db.session.query(Routine).filter_by(user_id=current_user.id).all()
    )
    workouts = db.session.query(Workout).filter_by(user_id=current_user.id).all()
    custom_exercises = (
        db.session.query(Exercise)
        .filter_by(user_id=current_user.id, is_custom=True)
        .all()
    )
    payload = {
        "user": current_user.to_dict(),
        "routines": [_routine_hevy_format(r) for r in routines],
        "workouts": [_workout_hevy_format(w) for w in workouts],
        "custom_exercises": [_exercise_hevy_format(e) for e in custom_exercises],
        "exported_at": datetime.utcnow().isoformat(),
    }
    return jsonify(payload)


@api_bp.post("/import")
@login_required
def import_data():
    """Import JSON (stub basique — remplace rien, ajoute)."""
    data = _json()
    imported = {"routines": 0, "workouts": 0, "custom_exercises": 0}

    # Exercices custom
    for ex in data.get("custom_exercises") or []:
        e = Exercise(
            name=ex.get("name") or "Import",
            muscle_group=ex.get("muscleGroup") or ex.get("muscle_group"),
            equipment=ex.get("equipment"),
            exercise_type=ex.get("exerciseType")
            or ex.get("exercise_type")
            or "weight",
            instructions=ex.get("instructions"),
            is_custom=True,
            user_id=current_user.id,
        )
        db.session.add(e)
        imported["custom_exercises"] += 1

    db.session.commit()
    return jsonify(ok=True, imported=imported)


# --------------------------------------------------------------------------
# EXERCISES
# --------------------------------------------------------------------------


def _exercise_hevy_format(e: Exercise) -> dict:
    """Format camelCase pour le Frontend (compat conventions Hevy)."""
    return {
        "id": e.id,
        "name": e.name,
        "muscleGroup": e.muscle_group,
        "muscle_group": e.muscle_group,  # alias snake_case
        "equipment": e.equipment,
        "exerciseType": e.exercise_type,
        "exercise_type": e.exercise_type,
        "instructions": e.instructions,
        "imageUrl": e.image_url,
        "image_url": e.image_url,
        "isCustom": e.is_custom,
        "is_custom": e.is_custom,
        "user_id": e.user_id,
    }


@api_bp.get("/exercises")
@login_required
def list_exercises():
    """Liste les exercices visibles (système + custom du user)."""
    q = db.session.query(Exercise).filter(
        or_(Exercise.is_custom.is_(False), Exercise.user_id == current_user.id)
    )

    if muscle := request.args.get("muscle_group"):
        q = q.filter(Exercise.muscle_group == muscle)
    if equipment := request.args.get("equipment"):
        q = q.filter(Exercise.equipment == equipment)
    if search := request.args.get("search"):
        q = q.filter(Exercise.name.ilike(f"%{search}%"))

    q = q.order_by(Exercise.name.asc())
    exercises = q.all()
    return jsonify(exercises=[_exercise_hevy_format(e) for e in exercises])


@api_bp.post("/exercises")
@login_required
def create_exercise():
    data = _json()
    if not data.get("name"):
        return jsonify(error="missing_name"), 400
    ex = Exercise(
        name=data["name"].strip(),
        muscle_group=data.get("muscle_group"),
        equipment=data.get("equipment"),
        exercise_type=data.get("exercise_type", "weight"),
        instructions=data.get("instructions"),
        is_custom=True,
        user_id=current_user.id,
    )
    db.session.add(ex)
    db.session.commit()
    return jsonify(exercise=_exercise_hevy_format(ex)), 201


@api_bp.get("/exercises/<int:exercise_id>")
@login_required
def get_exercise(exercise_id: int):
    ex = db.session.get(Exercise, exercise_id)
    if not ex or (ex.is_custom and ex.user_id != current_user.id):
        abort(404)
    return jsonify(exercise=_exercise_hevy_format(ex))


@api_bp.get("/exercises/<int:exercise_id>/history")
@login_required
def exercise_history(exercise_id: int):
    """Derniers workouts du user où cet exercice a été pratiqué.

    Format : { history: [ {date, workout_id, workout_name, sets} ] }
    date est un timestamp ms (compat Hevy).
    """
    limit = min(int(request.args.get("limit", 20)), 100)
    rows = (
        db.session.query(Workout, WorkoutExercise)
        .join(WorkoutExercise, WorkoutExercise.workout_id == Workout.id)
        .filter(
            Workout.user_id == current_user.id,
            WorkoutExercise.exercise_id == exercise_id,
            Workout.ended_at.isnot(None),
        )
        .order_by(Workout.ended_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for workout, we in rows:
        result.append(
            {
                "workout_id": workout.id,
                "workout_name": workout.name,
                "date": (
                    int(workout.ended_at.timestamp() * 1000)
                    if workout.ended_at
                    else None
                ),
                "ended_at": (
                    workout.ended_at.isoformat() if workout.ended_at else None
                ),
                "sets": [
                    {
                        "reps": s.reps,
                        "weight": s.weight,
                        "rpe": s.rpe,
                        "type": s.set_type,
                        "is_pr": s.is_pr,
                    }
                    for s in we.sets
                    if s.completed
                ],
            }
        )
    return jsonify(history=result)


@api_bp.get("/exercises/<int:exercise_id>/prs")
@login_required
def exercise_prs(exercise_id: int):
    """PR records pour un exercice du user courant."""
    prs = (
        db.session.query(PersonalRecord)
        .filter_by(user_id=current_user.id, exercise_id=exercise_id)
        .order_by(PersonalRecord.pr_type, PersonalRecord.achieved_at.desc())
        .all()
    )
    # Max par type
    best_per_type: dict[str, PersonalRecord] = {}
    for pr in prs:
        if pr.pr_type not in best_per_type or pr.value > best_per_type[pr.pr_type].value:
            best_per_type[pr.pr_type] = pr
    # Format pour le Frontend : prs = best par type (weight, reps, volume, e1rm)
    formatted_best: dict[str, dict] = {}
    for k, v in best_per_type.items():
        formatted_best[k] = {
            "value": round(v.value, 2),
            "unit": "kg" if current_user.unit_system == "metric" else "lb",
            "reps": v.reps,
            "weight": v.weight,
            "achieved_at": v.achieved_at.isoformat() if v.achieved_at else None,
        }

    return jsonify(
        prs=formatted_best,
        best=formatted_best,  # alias
        all=[p.to_dict() for p in prs],
    )


@api_bp.get("/exercises/<int:exercise_id>/stats")
@login_required
def exercise_stats(exercise_id: int):
    """Stats pour graphs : e1RM et volume dans le temps."""
    rows = (
        db.session.query(WorkoutSet, Workout.ended_at)
        .join(
            WorkoutExercise, WorkoutSet.workout_exercise_id == WorkoutExercise.id
        )
        .join(Workout, WorkoutExercise.workout_id == Workout.id)
        .filter(
            Workout.user_id == current_user.id,
            WorkoutExercise.exercise_id == exercise_id,
            WorkoutSet.completed.is_(True),
            Workout.ended_at.isnot(None),
        )
        .order_by(Workout.ended_at.asc())
        .all()
    )

    # Agrégation par workout (date) : max e1RM du jour + volume du jour
    by_day: dict[str, dict] = {}
    for s, ended_at in rows:
        day = ended_at.date().isoformat()
        e1 = e1rm(s.weight, s.reps)
        vol = (s.weight or 0) * (s.reps or 0)
        entry = by_day.setdefault(
            day, {"date": day, "max_e1rm": 0.0, "volume": 0.0, "max_weight": 0.0}
        )
        entry["max_e1rm"] = max(entry["max_e1rm"], e1)
        entry["volume"] += vol
        entry["max_weight"] = max(entry["max_weight"], s.weight or 0)

    series = sorted(by_day.values(), key=lambda x: x["date"])
    return jsonify(series=series)


# --------------------------------------------------------------------------
# ROUTINE FOLDERS
# --------------------------------------------------------------------------


@api_bp.get("/folders")
@login_required
def list_folders():
    folders = (
        db.session.query(RoutineFolder)
        .filter_by(user_id=current_user.id)
        .order_by(RoutineFolder.order_index.asc())
        .all()
    )
    return jsonify(folders=[f.to_dict() for f in folders])


@api_bp.post("/folders")
@login_required
def create_folder():
    data = _json()
    if not data.get("name"):
        return jsonify(error="missing_name"), 400
    folder = RoutineFolder(
        name=data["name"].strip(),
        order_index=data.get("order_index", 0),
        user_id=current_user.id,
    )
    db.session.add(folder)
    db.session.commit()
    return jsonify(folder=folder.to_dict()), 201


@api_bp.patch("/folders/<int:folder_id>")
@login_required
def update_folder(folder_id: int):
    folder = _owned_or_404(RoutineFolder, folder_id)
    data = _json()
    if "name" in data:
        folder.name = data["name"].strip()
    if "order_index" in data:
        folder.order_index = int(data["order_index"])
    db.session.commit()
    return jsonify(folder=folder.to_dict())


@api_bp.delete("/folders/<int:folder_id>")
@login_required
def delete_folder(folder_id: int):
    folder = _owned_or_404(RoutineFolder, folder_id)
    # Détacher les routines (folder_id -> NULL)
    db.session.query(Routine).filter_by(folder_id=folder.id).update(
        {"folder_id": None}
    )
    db.session.delete(folder)
    db.session.commit()
    return jsonify(ok=True)


# --------------------------------------------------------------------------
# ROUTINES
# --------------------------------------------------------------------------


def _routine_hevy_format(r: Routine, include_sets: bool = True) -> dict:
    """Format de routine pour le Frontend (title + exercises flat)."""
    exercises = []
    for re in r.exercises:
        sets_data = [
            {
                "id": s.id,
                "order_index": s.order_index,
                "set_type": s.set_type,
                "target_reps": s.target_reps,
                "target_weight": s.target_weight,
                "target_rpe": s.target_rpe,
            }
            for s in re.sets
        ]
        exercises.append(
            {
                "id": re.id,
                "exerciseId": re.exercise_id,
                "exercise_id": re.exercise_id,
                "name": re.exercise.name if re.exercise else "?",
                "muscleGroup": re.exercise.muscle_group if re.exercise else None,
                "equipment": re.exercise.equipment if re.exercise else None,
                "order_index": re.order_index,
                "notes": re.notes,
                "rest_seconds": re.rest_seconds,
                "sets": sets_data if include_sets else len(sets_data),
            }
        )
    return {
        "id": r.id,
        "title": r.name,
        "name": r.name,
        "folder_id": r.folder_id,
        "folderId": r.folder_id,
        "order_index": r.order_index,
        "notes": r.notes,
        "total_sets": sum(len(re.sets) for re in r.exercises),
        "exercises": exercises,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@api_bp.get("/routines")
@login_required
def list_routines():
    routines = (
        db.session.query(Routine)
        .filter_by(user_id=current_user.id)
        .order_by(Routine.order_index.asc(), Routine.updated_at.desc())
        .all()
    )
    return jsonify(routines=[_routine_hevy_format(r) for r in routines])


@api_bp.post("/routines")
@login_required
def create_routine():
    data = _json()
    if not data.get("name"):
        return jsonify(error="missing_name"), 400

    routine = Routine(
        name=data["name"].strip(),
        folder_id=data.get("folder_id"),
        order_index=data.get("order_index", 0),
        notes=data.get("notes"),
        user_id=current_user.id,
    )
    db.session.add(routine)
    db.session.flush()

    # Exercices + sets optionnels
    for idx, rex in enumerate(data.get("exercises") or []):
        re = RoutineExercise(
            routine_id=routine.id,
            exercise_id=rex["exercise_id"],
            order_index=rex.get("order_index", idx),
            notes=rex.get("notes"),
            rest_seconds=rex.get("rest_seconds", 90),
        )
        db.session.add(re)
        db.session.flush()
        for sidx, s in enumerate(rex.get("sets") or []):
            db.session.add(
                RoutineSet(
                    routine_exercise_id=re.id,
                    order_index=s.get("order_index", sidx),
                    set_type=s.get("set_type", "normal"),
                    target_reps=s.get("target_reps"),
                    target_weight=s.get("target_weight"),
                    target_rpe=s.get("target_rpe"),
                )
            )
    db.session.commit()
    return jsonify(routine=_routine_hevy_format(routine)), 201


@api_bp.get("/routines/<int:routine_id>")
@login_required
def get_routine(routine_id: int):
    routine = _owned_or_404(Routine, routine_id)
    return jsonify(routine=_routine_hevy_format(routine))


@api_bp.patch("/routines/<int:routine_id>")
@login_required
def update_routine(routine_id: int):
    routine = _owned_or_404(Routine, routine_id)
    data = _json()

    for field in ("name", "notes"):
        if field in data:
            setattr(routine, field, data[field])
    if "folder_id" in data:
        routine.folder_id = data["folder_id"]
    if "order_index" in data:
        routine.order_index = int(data["order_index"])

    # Si exercises fourni → remplace entièrement la structure
    if "exercises" in data:
        # Purge ancienne structure
        for re in list(routine.exercises):
            db.session.delete(re)
        db.session.flush()
        for idx, rex in enumerate(data.get("exercises") or []):
            re = RoutineExercise(
                routine_id=routine.id,
                exercise_id=rex["exercise_id"],
                order_index=rex.get("order_index", idx),
                notes=rex.get("notes"),
                rest_seconds=rex.get("rest_seconds", 90),
            )
            db.session.add(re)
            db.session.flush()
            for sidx, s in enumerate(rex.get("sets") or []):
                db.session.add(
                    RoutineSet(
                        routine_exercise_id=re.id,
                        order_index=s.get("order_index", sidx),
                        set_type=s.get("set_type", "normal"),
                        target_reps=s.get("target_reps"),
                        target_weight=s.get("target_weight"),
                        target_rpe=s.get("target_rpe"),
                    )
                )

    db.session.commit()
    return jsonify(routine=_routine_hevy_format(routine))


@api_bp.delete("/routines/<int:routine_id>")
@login_required
def delete_routine(routine_id: int):
    routine = _owned_or_404(Routine, routine_id)
    db.session.delete(routine)
    db.session.commit()
    return jsonify(ok=True)


@api_bp.post("/routines/<int:routine_id>/duplicate")
@login_required
def duplicate_routine(routine_id: int):
    """Duplique une routine (nom + " (copie)")."""
    src = _owned_or_404(Routine, routine_id)
    dup = Routine(
        name=f"{src.name} (copie)",
        folder_id=src.folder_id,
        order_index=src.order_index,
        notes=src.notes,
        user_id=current_user.id,
    )
    db.session.add(dup)
    db.session.flush()
    for re in src.exercises:
        new_re = RoutineExercise(
            routine_id=dup.id,
            exercise_id=re.exercise_id,
            order_index=re.order_index,
            notes=re.notes,
            rest_seconds=re.rest_seconds,
        )
        db.session.add(new_re)
        db.session.flush()
        for s in re.sets:
            db.session.add(
                RoutineSet(
                    routine_exercise_id=new_re.id,
                    order_index=s.order_index,
                    set_type=s.set_type,
                    target_reps=s.target_reps,
                    target_weight=s.target_weight,
                    target_rpe=s.target_rpe,
                )
            )
    db.session.commit()
    return jsonify(routine=_routine_hevy_format(dup)), 201


@api_bp.post("/routines/<int:routine_id>/start")
@login_required
def start_routine(routine_id: int):
    """Crée un workout à partir d'une routine (exercices + sets pré-remplis)."""
    routine = _owned_or_404(Routine, routine_id)
    workout = Workout(
        user_id=current_user.id,
        name=routine.name,
        started_at=datetime.utcnow(),
        routine_id=routine.id,
    )
    db.session.add(workout)
    db.session.flush()

    for re in routine.exercises:
        we = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=re.exercise_id,
            order_index=re.order_index,
            notes=re.notes,
        )
        db.session.add(we)
        db.session.flush()
        for s in re.sets:
            db.session.add(
                WorkoutSet(
                    workout_exercise_id=we.id,
                    order_index=s.order_index,
                    set_type=s.set_type,
                    reps=s.target_reps,
                    weight=s.target_weight,
                    rpe=s.target_rpe,
                    completed=False,
                )
            )
    db.session.commit()
    return jsonify(workout=workout.to_dict(include_exercises=True)), 201


# --------------------------------------------------------------------------
# WORKOUTS
# --------------------------------------------------------------------------


@api_bp.get("/workouts")
@login_required
def list_workouts():
    """Liste paginée des workouts, triés par ended_at desc.

    Format de réponse compatible avec le Frontend :
    - items : liste enrichie (format Hevy-like avec exerciseHistory)
    - has_more : pagination
    - total, page, per_page : meta
    - stats : overview (workouts count, volume total, durée totale)
    """
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(int(request.args.get("per_page", 20)), 100)

    q = (
        db.session.query(Workout)
        .filter_by(user_id=current_user.id)
        .order_by(Workout.ended_at.desc().nullslast(), Workout.started_at.desc())
    )

    if date_from := request.args.get("from"):
        q = q.filter(Workout.started_at >= date_from)
    if date_to := request.args.get("to"):
        q = q.filter(Workout.started_at <= date_to)
    if request.args.get("finished_only") == "1":
        q = q.filter(Workout.ended_at.isnot(None))

    total = q.count()
    items = q.limit(per_page).offset((page - 1) * per_page).all()

    # Format enrichi compatible Frontend
    enriched = [_workout_hevy_format(w) for w in items]

    # Stats globales (pour affichage en header d'historique)
    all_finished = (
        db.session.query(Workout)
        .filter(Workout.user_id == current_user.id, Workout.ended_at.isnot(None))
        .all()
    )
    total_volume = sum(w.total_volume for w in all_finished)
    total_duration = sum(w.duration_seconds or 0 for w in all_finished)
    stats = {
        "workouts_count": len(all_finished),
        "total_volume_display": _fmt_volume(total_volume, current_user.unit_system),
        "total_duration_display": _fmt_duration(total_duration),
    }

    has_more = (page * per_page) < total

    return jsonify(
        items=enriched,
        workouts=enriched,  # alias legacy
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
        stats=stats,
    )


def _workout_hevy_format(w: Workout) -> dict:
    """Format de workout compatible conventions Hevy + front."""
    pr_count = sum(
        1 for we in w.exercises for s in we.sets if s.is_pr and s.completed
    )
    exercise_history = []
    for we in w.exercises:
        sets_data = [
            {
                "reps": s.reps,
                "weight": s.weight,
                "rpe": s.rpe,
                "completed": s.completed,
                "type": s.set_type,
                "notes": s.notes,
                "is_pr": s.is_pr,
            }
            for s in we.sets
        ]
        exercise_history.append(
            {
                "exerciseId": we.exercise_id,
                "name": we.exercise.name if we.exercise else "?",
                "muscleGroup": we.exercise.muscle_group if we.exercise else None,
                "sets": sets_data,
            }
        )
    return {
        "id": w.id,
        "title": w.name or "Workout",
        "start_time": int(w.started_at.timestamp() * 1000) if w.started_at else None,
        "end_time": int(w.ended_at.timestamp() * 1000) if w.ended_at else None,
        "durationSeconds": w.duration_seconds or 0,
        "totalVolume": w.total_volume,
        "totalSets": w.total_sets,
        "totalReps": w.total_reps,
        "notes": w.notes,
        "pr_count": pr_count,
        "exerciseHistory": exercise_history,
        "date_relative": _fmt_relative(w.ended_at or w.started_at),
    }


def _fmt_duration(seconds: int) -> str:
    if not seconds:
        return "0h"
    h, rem = divmod(int(seconds), 3600)
    m = rem // 60
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def _fmt_volume(volume_kg: float, unit: str = "metric") -> str:
    if unit == "imperial":
        return f"{int(volume_kg * 2.2046):,} lb".replace(",", " ")
    if volume_kg >= 1000:
        return f"{volume_kg / 1000:.1f}t".replace(".", ",")
    return f"{int(volume_kg):,} kg".replace(",", " ")


def _fmt_relative(dt: datetime | None) -> str:
    if not dt:
        return ""
    today = datetime.utcnow().date()
    days = (today - dt.date()).days
    if days == 0:
        return "Aujourd'hui"
    if days == 1:
        return "Hier"
    if days < 7:
        return f"Il y a {days} j"
    if days < 30:
        return f"Il y a {days // 7} sem."
    return dt.strftime("%d/%m/%Y")


@api_bp.post("/workouts")
@login_required
def create_workout():
    """Crée un workout vide (ou avec exercices pré-remplis)."""
    data = _json()
    workout = Workout(
        user_id=current_user.id,
        name=data.get("name") or "Workout",
        notes=data.get("notes"),
        routine_id=data.get("routine_id"),
    )
    db.session.add(workout)
    db.session.flush()

    for idx, wex in enumerate(data.get("exercises") or []):
        we = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=wex["exercise_id"],
            order_index=wex.get("order_index", idx),
            notes=wex.get("notes"),
        )
        db.session.add(we)
        db.session.flush()
        for sidx, s in enumerate(wex.get("sets") or []):
            db.session.add(
                WorkoutSet(
                    workout_exercise_id=we.id,
                    order_index=s.get("order_index", sidx),
                    set_type=s.get("set_type", "normal"),
                    reps=s.get("reps"),
                    weight=s.get("weight"),
                    rpe=s.get("rpe"),
                    completed=s.get("completed", False),
                )
            )

    db.session.commit()
    return jsonify(workout=workout.to_dict(include_exercises=True)), 201


@api_bp.get("/workouts/active")
@login_required
def get_active_workout():
    """Retourne le workout en cours (si existe)."""
    workout = (
        db.session.query(Workout)
        .filter_by(user_id=current_user.id, ended_at=None)
        .order_by(Workout.started_at.desc())
        .first()
    )
    if not workout:
        return jsonify(workout=None)
    return jsonify(workout=workout.to_dict(include_exercises=True))


@api_bp.get("/workouts/<int:workout_id>")
@login_required
def get_workout(workout_id: int):
    workout = _owned_or_404(Workout, workout_id)
    # Format enrichi Hevy-like pour le Frontend + objet brut
    return jsonify(workout=_workout_hevy_format(workout), raw=workout.to_dict(include_exercises=True))


@api_bp.patch("/workouts/<int:workout_id>")
@login_required
def update_workout(workout_id: int):
    workout = _owned_or_404(Workout, workout_id)
    data = _json()
    for field in ("name", "notes"):
        if field in data:
            setattr(workout, field, data[field])
    db.session.commit()
    return jsonify(workout=workout.to_dict())


@api_bp.delete("/workouts/<int:workout_id>")
@login_required
def delete_workout(workout_id: int):
    workout = _owned_or_404(Workout, workout_id)
    db.session.delete(workout)
    db.session.commit()
    return jsonify(ok=True)


@api_bp.post("/workouts/<int:workout_id>/exercises")
@login_required
def add_workout_exercise(workout_id: int):
    """Ajoute un exercice à un workout en cours."""
    workout = _owned_or_404(Workout, workout_id)
    data = _json()
    if not data.get("exercise_id"):
        return jsonify(error="missing_exercise_id"), 400
    max_order = (
        db.session.query(func.max(WorkoutExercise.order_index))
        .filter_by(workout_id=workout.id)
        .scalar()
        or -1
    )
    we = WorkoutExercise(
        workout_id=workout.id,
        exercise_id=data["exercise_id"],
        order_index=max_order + 1,
        notes=data.get("notes"),
    )
    db.session.add(we)
    db.session.commit()
    return jsonify(exercise=we.to_dict(include_sets=True)), 201


@api_bp.post("/workouts/<int:workout_id>/sets")
@login_required
def add_workout_set(workout_id: int):
    """Ajoute un set à un exercice du workout."""
    workout = _owned_or_404(Workout, workout_id)
    data = _json()
    we_id = data.get("workout_exercise_id")
    if not we_id:
        return jsonify(error="missing_workout_exercise_id"), 400

    we = db.session.get(WorkoutExercise, we_id)
    if not we or we.workout_id != workout.id:
        abort(404)

    max_order = (
        db.session.query(func.max(WorkoutSet.order_index))
        .filter_by(workout_exercise_id=we.id)
        .scalar()
        or -1
    )
    s = WorkoutSet(
        workout_exercise_id=we.id,
        order_index=data.get("order_index", max_order + 1),
        set_type=data.get("set_type", "normal"),
        reps=data.get("reps"),
        weight=data.get("weight"),
        rpe=data.get("rpe"),
        completed=data.get("completed", False),
        notes=data.get("notes"),
        completed_at=datetime.utcnow() if data.get("completed") else None,
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(set=s.to_dict()), 201


@api_bp.patch("/sets/<int:set_id>")
@login_required
def update_set(set_id: int):
    """Met à jour un set (reps, weight, completed, etc.)."""
    s = db.session.get(WorkoutSet, set_id)
    if not s:
        abort(404)
    # Vérifier ownership via le workout
    workout = s.workout_exercise.workout
    if workout.user_id != current_user.id:
        abort(404)

    data = _json()
    was_completed = s.completed

    for field in ("reps", "weight", "rpe", "set_type", "notes", "order_index"):
        if field in data:
            setattr(s, field, data[field])
    if "completed" in data:
        s.completed = bool(data["completed"])
        if s.completed and not was_completed:
            s.completed_at = datetime.utcnow()

    db.session.commit()
    return jsonify(set=s.to_dict())


@api_bp.delete("/sets/<int:set_id>")
@login_required
def delete_set(set_id: int):
    s = db.session.get(WorkoutSet, set_id)
    if not s:
        abort(404)
    if s.workout_exercise.workout.user_id != current_user.id:
        abort(404)
    db.session.delete(s)
    db.session.commit()
    return jsonify(ok=True)


@api_bp.post("/workouts/<int:workout_id>/finish")
@login_required
def finish_workout(workout_id: int):
    """Termine un workout : calcule durée, détecte PRs, enregistre."""
    workout = _owned_or_404(Workout, workout_id)
    if workout.ended_at is not None:
        return jsonify(error="already_finished"), 409

    workout.ended_at = datetime.utcnow()
    if workout.started_at:
        workout.duration_seconds = int(
            (workout.ended_at - workout.started_at).total_seconds()
        )
    db.session.flush()

    new_prs = detect_prs_for_workout(workout)
    db.session.commit()

    return jsonify(
        workout=workout.to_dict(include_exercises=True),
        new_prs=[p.to_dict() for p in new_prs],
    )


# --------------------------------------------------------------------------
# STATS
# --------------------------------------------------------------------------


@api_bp.get("/stats")
@login_required
def stats_summary():
    """Résumé rapide des stats utilisateur (alias de /stats/overview)."""
    return _stats_overview_payload()


@api_bp.get("/prs/recent")
@login_required
def prs_recent():
    """Derniers PR obtenus (pour page profil)."""
    limit = min(int(request.args.get("limit", 5)), 50)
    prs = (
        db.session.query(PersonalRecord, Exercise)
        .join(Exercise, PersonalRecord.exercise_id == Exercise.id)
        .filter(PersonalRecord.user_id == current_user.id)
        .order_by(PersonalRecord.achieved_at.desc())
        .limit(limit)
        .all()
    )
    items = []
    for pr, ex in prs:
        items.append(
            {
                "id": pr.id,
                "exercise_name": ex.name,
                "pr_type": pr.pr_type,
                "value": round(pr.value, 2),
                "reps": pr.reps,
                "weight": pr.weight,
                "unit": "kg" if current_user.unit_system == "metric" else "lb",
                "date": (
                    int(pr.achieved_at.timestamp() * 1000) if pr.achieved_at else None
                ),
            }
        )
    return jsonify(items=items, prs=items)


def _stats_overview_payload():
    finished_workouts = (
        db.session.query(Workout)
        .filter(Workout.user_id == current_user.id, Workout.ended_at.isnot(None))
        .all()
    )
    total_workouts = len(finished_workouts)
    total_volume = sum(w.total_volume for w in finished_workouts)
    total_sets = sum(w.total_sets for w in finished_workouts)
    total_reps = sum(w.total_reps for w in finished_workouts)
    total_duration = sum(w.duration_seconds or 0 for w in finished_workouts)

    dates = sorted(
        {w.ended_at.date() for w in finished_workouts if w.ended_at}, reverse=True
    )
    streak = 0
    today = datetime.utcnow().date()
    if dates:
        cur = dates[0]
        if (today - cur).days <= 1:
            streak = 1
            for d in dates[1:]:
                if (cur - d).days == 1:
                    streak += 1
                    cur = d
                else:
                    break

    prs_count = (
        db.session.query(func.count(PersonalRecord.id))
        .filter(PersonalRecord.user_id == current_user.id)
        .scalar()
        or 0
    )

    return jsonify(
        total_workouts=total_workouts,
        workouts_count=total_workouts,
        total_volume=total_volume,
        total_volume_display=_fmt_volume(total_volume, current_user.unit_system),
        total_duration_display=_fmt_duration(total_duration),
        total_sets=total_sets,
        total_reps=total_reps,
        prs_count=prs_count,
        streak=streak,
    )


@api_bp.get("/stats/overview")
@login_required
def stats_overview():
    """Stats globales : total workouts, volume, streak."""
    finished_workouts = (
        db.session.query(Workout)
        .filter(Workout.user_id == current_user.id, Workout.ended_at.isnot(None))
        .all()
    )

    total_workouts = len(finished_workouts)
    total_volume = sum(w.total_volume for w in finished_workouts)
    total_sets = sum(w.total_sets for w in finished_workouts)
    total_reps = sum(w.total_reps for w in finished_workouts)

    # Streak (jours consécutifs avec au moins un workout)
    dates = sorted(
        {w.ended_at.date() for w in finished_workouts if w.ended_at}, reverse=True
    )
    streak = 0
    today = datetime.utcnow().date()
    if dates:
        cur = dates[0]
        # streak ne commence que si la dernière séance = aujourd'hui ou hier
        if (today - cur).days <= 1:
            streak = 1
            for d in dates[1:]:
                if (cur - d).days == 1:
                    streak += 1
                    cur = d
                else:
                    break

    return jsonify(
        total_workouts=total_workouts,
        total_volume=total_volume,
        total_sets=total_sets,
        total_reps=total_reps,
        streak=streak,
    )


@api_bp.get("/stats/calendar")
@login_required
def stats_calendar():
    """Jours avec workout : soit par mois (?month=YYYY-MM), soit par N dernières semaines (?weeks=4).

    Format de sortie :
    - days : jours couverts (day = numéro du jour, date ISO, count, volume,
      duration_seconds, level 0-4 pour heatmap en mode weeks)
    - month : label ("YYYY-MM" ou "last N weeks")
    """
    today = datetime.utcnow().date()
    weeks_param = request.args.get("weeks")

    if weeks_param:
        try:
            weeks = max(1, min(int(weeks_param), 52))
        except ValueError:
            return jsonify(error="invalid_weeks"), 400
        first = today - timedelta(days=weeks * 7 - 1)
        last = today + timedelta(days=1)
        label = f"last {weeks} weeks"
    else:
        month_str = request.args.get("month")
        try:
            if month_str:
                first = datetime.strptime(month_str, "%Y-%m").date()
            else:
                first = today.replace(day=1)
        except ValueError:
            return jsonify(error="invalid_month_format"), 400
        if first.month == 12:
            last = first.replace(year=first.year + 1, month=1)
        else:
            last = first.replace(month=first.month + 1)
        label = first.strftime("%Y-%m")

    workouts = (
        db.session.query(Workout)
        .filter(
            Workout.user_id == current_user.id,
            Workout.ended_at.isnot(None),
            Workout.ended_at >= first,
            Workout.ended_at < last,
        )
        .all()
    )

    by_day: dict[str, dict] = {}
    for w in workouts:
        if not w.ended_at:
            continue
        iso = w.ended_at.date().isoformat()
        entry = by_day.setdefault(
            iso,
            {
                "date": iso,
                "day": w.ended_at.day,
                "count": 0,
                "volume": 0.0,
                "duration_seconds": 0,
            },
        )
        entry["count"] += 1
        entry["volume"] += w.total_volume
        entry["duration_seconds"] += w.duration_seconds or 0

    # Mode weeks : on matérialise tous les jours (y compris ceux sans workout)
    # et on calcule un level 0-4 pour la heatmap du profil
    if weeks_param:
        max_vol = max((d["volume"] for d in by_day.values()), default=1) or 1
        days = []
        cur = first
        while cur <= today:
            iso = cur.isoformat()
            d = by_day.get(
                iso,
                {
                    "date": iso,
                    "day": cur.day,
                    "count": 0,
                    "volume": 0.0,
                    "duration_seconds": 0,
                },
            )
            if d["count"] == 0:
                d["level"] = 0
            else:
                ratio = d["volume"] / max_vol
                d["level"] = min(4, max(1, int(ratio * 4) + 1))
            days.append(d)
            cur += timedelta(days=1)
        return jsonify(month=label, days=days)

    return jsonify(month=label, days=list(by_day.values()))
