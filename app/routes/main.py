"""Blueprint des pages principales (rendu Jinja).

Ces routes servent des templates HTML consommés par le Frontend
(Alpine.js + HTMX). Les données sont chargées via l'API /api dans la plupart
des cas ; certaines pages reçoivent un contexte minimal côté serveur pour
éviter un flash vide au premier rendu.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_

from ..extensions import db
from ..models import Routine, RoutineFolder, Workout

main_bp = Blueprint("main", __name__)


# --------------------------------------------------------------------------
# Helpers de formatage pour les templates
# --------------------------------------------------------------------------


def _format_duration(seconds: int | None) -> str:
    """Formatte une durée en 'XhYYm' ou 'YYm'."""
    if not seconds:
        return "—"
    hours, rem = divmod(int(seconds), 3600)
    minutes = rem // 60
    if hours:
        return f"{hours}h{minutes:02d}"
    return f"{minutes}m"


def _format_relative_date(dt: datetime | None) -> str:
    """Renvoie 'Aujourd'hui', 'Hier', 'il y a X jours'."""
    if not dt:
        return "—"
    today = datetime.utcnow().date()
    days = (today - dt.date()).days
    if days == 0:
        return "Aujourd'hui"
    if days == 1:
        return "Hier"
    if days < 7:
        return f"Il y a {days} jours"
    if days < 30:
        weeks = days // 7
        return f"Il y a {weeks} sem."
    return dt.strftime("%d/%m/%Y")


def _format_volume(volume_kg: float, unit: str = "metric") -> str:
    """Formatte un volume avec l'unité utilisateur."""
    if unit == "imperial":
        return f"{int(volume_kg * 2.2046):,} lb".replace(",", " ")
    return f"{int(volume_kg):,} kg".replace(",", " ")


def _routine_view_dict(routine: Routine) -> dict:
    """Adapte un Routine pour les templates (attend .title, .total_sets, etc.).

    Expose aussi les 3 premières vidéos CDN pour l'aperçu sur carte routine.
    """
    total_sets = sum(len(re.sets) for re in routine.exercises)
    exercises = []
    previews: list[str] = []
    for re in routine.exercises:
        name = re.exercise.name if re.exercise else "?"
        video = re.exercise.cdn_video_url if re.exercise else None
        exercises.append({"name": name, "cdn_video_url": video})
        if video and len(previews) < 3:
            previews.append(video)
    return {
        "id": routine.id,
        "title": routine.name,
        "total_sets": total_sets,
        "exercises": exercises,
        "preview_videos": previews,
        "last_performed": None,
        "last_performed_relative": None,
    }


def _workout_view_dict(workout: Workout, unit: str = "metric") -> dict:
    """Adapte un Workout pour les templates."""
    pr_count = sum(
        1 for we in workout.exercises for s in we.sets if s.is_pr and s.completed
    )
    # Résumé exercices (nb sets + meilleur set)
    exercise_summary = []
    for we in workout.exercises:
        completed_sets = [s for s in we.sets if s.completed]
        if not completed_sets:
            continue
        best = max(completed_sets, key=lambda s: (s.weight or 0) * (s.reps or 0))
        best_display = (
            f"{best.weight or 0:g}×{best.reps or 0}"
            if best.weight or best.reps
            else "—"
        )
        exercise_summary.append(
            {
                "name": we.exercise.name if we.exercise else "?",
                "sets_count": len(completed_sets),
                "best_display": best_display,
                "cdn_video_url": (
                    we.exercise.cdn_video_url if we.exercise else None
                ),
            }
        )
    return {
        "id": workout.id,
        "title": workout.name or "Workout",
        "date_relative": _format_relative_date(workout.ended_at or workout.started_at),
        "duration_display": _format_duration(workout.duration_seconds),
        "volume_display": _format_volume(workout.total_volume, unit),
        "total_sets": workout.total_sets,
        "pr_count": pr_count,
        "exercise_summary": exercise_summary,
    }


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------


@main_bp.route("/")
def index():
    """Racine : redirige vers dashboard si auth, sinon login."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login_page"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Tableau de bord : stats rapides + routines + derniers workouts."""
    user = current_user

    # Routines organisées en dossiers
    folders_rows = (
        db.session.query(RoutineFolder)
        .filter_by(user_id=user.id)
        .order_by(RoutineFolder.order_index.asc())
        .all()
    )
    folders = []
    for f in folders_rows:
        routines_in = (
            db.session.query(Routine)
            .filter_by(user_id=user.id, folder_id=f.id)
            .order_by(Routine.order_index.asc())
            .all()
        )
        folders.append(
            {
                "id": f.id,
                "title": f.name,
                "routines": [_routine_view_dict(r) for r in routines_in],
            }
        )

    routines_no_folder_rows = (
        db.session.query(Routine)
        .filter(Routine.user_id == user.id, Routine.folder_id.is_(None))
        .order_by(Routine.order_index.asc(), Routine.updated_at.desc())
        .all()
    )
    routines_no_folder = [_routine_view_dict(r) for r in routines_no_folder_rows]

    # Derniers workouts finis
    recent_workouts_rows = (
        db.session.query(Workout)
        .filter(Workout.user_id == user.id, Workout.ended_at.isnot(None))
        .order_by(Workout.ended_at.desc())
        .limit(5)
        .all()
    )
    recent_workouts = [
        _workout_view_dict(w, user.unit_system) for w in recent_workouts_rows
    ]

    # Stats rapides
    all_finished = (
        db.session.query(Workout)
        .filter(Workout.user_id == user.id, Workout.ended_at.isnot(None))
        .all()
    )
    total_volume = sum(w.total_volume for w in all_finished)
    streak = _compute_streak([w.ended_at for w in all_finished if w.ended_at])

    stats = {
        "workouts_count": len(all_finished),
        "total_volume_display": _format_volume(total_volume, user.unit_system),
        "streak": streak,
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        folders=folders,
        routines_no_folder=routines_no_folder,
        recent_workouts=recent_workouts,
    )


def _compute_streak(dates: list[datetime]) -> int:
    """Nombre de jours consécutifs avec au moins un workout."""
    if not dates:
        return 0
    unique_days = sorted({d.date() for d in dates}, reverse=True)
    today = datetime.utcnow().date()
    if (today - unique_days[0]).days > 1:
        return 0
    streak = 1
    cur = unique_days[0]
    for d in unique_days[1:]:
        if (cur - d).days == 1:
            streak += 1
            cur = d
        else:
            break
    return streak


# -- Routines ---------------------------------------------------------------


@main_bp.route("/routines")
@login_required
def routines_list():
    return render_template("routines/list.html")


@main_bp.route("/routines/new")
@login_required
def routine_new():
    return render_template("routines/edit.html", routine_id=None)


@main_bp.route("/routines/<int:routine_id>")
@login_required
def routine_detail(routine_id: int):
    return render_template("routines/detail.html", routine_id=routine_id)


@main_bp.route("/routines/<int:routine_id>/edit")
@login_required
def routine_edit(routine_id: int):
    return render_template("routines/edit.html", routine_id=routine_id)


# -- Workouts ---------------------------------------------------------------


@main_bp.route("/workout/start")
@main_bp.route("/workout/active")
@login_required
def workout_start():
    """Session d'entraînement en cours (ou à démarrer)."""
    return render_template("workouts/active.html")


@main_bp.route("/workouts")
@login_required
def workout_history():
    return render_template("workouts/history.html")


@main_bp.route("/workouts/<int:workout_id>")
@login_required
def workout_detail(workout_id: int):
    return render_template("workouts/detail.html", workout_id=workout_id)


# -- Exercises --------------------------------------------------------------


@main_bp.route("/exercises")
@login_required
def exercises_list():
    return render_template("exercises/list.html")


@main_bp.route("/exercises/<int:exercise_id>")
@login_required
def exercise_detail(exercise_id: int):
    return render_template("exercises/detail.html", exercise_id=exercise_id)


# -- Profile / Settings -----------------------------------------------------


@main_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@main_bp.route("/settings")
@login_required
def settings():
    return render_template("settings.html")
