"""Modèles SQLAlchemy Hevy-Web.

Hiérarchie :
- User : utilisateur de l'app (multi-user prévu)
- Exercise : bibliothèque d'exercices (système + custom user)
- RoutineFolder / Routine : templates d'entraînement
- RoutineExercise / RoutineSet : lignes de routine
- Workout / WorkoutExercise / WorkoutSet : séances réelles
- PersonalRecord : records personnels détectés
"""

from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Index
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


# --------------------------------------------------------------------------
# User
# --------------------------------------------------------------------------


class User(UserMixin, db.Model):
    """Utilisateur de l'application."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    unit_system = db.Column(db.String(16), default="metric", nullable=False)
    rest_timer_default = db.Column(db.Integer, default=90, nullable=False)
    sound_enabled = db.Column(db.Boolean, default=True, nullable=False)
    vibration_enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    exercises = relationship(
        "Exercise", back_populates="user", cascade="all, delete-orphan"
    )
    folders = relationship(
        "RoutineFolder", back_populates="user", cascade="all, delete-orphan"
    )
    routines = relationship(
        "Routine", back_populates="user", cascade="all, delete-orphan"
    )
    workouts = relationship(
        "Workout", back_populates="user", cascade="all, delete-orphan"
    )
    personal_records = relationship(
        "PersonalRecord", back_populates="user", cascade="all, delete-orphan"
    )

    # -- auth helpers -----------------------------------------------------
    def set_password(self, password: str) -> None:
        """Hashe et stocke le mot de passe."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Vérifie un mot de passe en clair contre le hash stocké."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "unit_system": self.unit_system,
            "rest_timer_default": self.rest_timer_default,
            "sound_enabled": self.sound_enabled,
            "vibration_enabled": self.vibration_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# --------------------------------------------------------------------------
# Exercise
# --------------------------------------------------------------------------


class Exercise(db.Model):
    """Exercice (système ou personnalisé par un user)."""

    __tablename__ = "exercise"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    muscle_group = db.Column(db.String(64), index=True)  # legs, chest, back, ...
    equipment = db.Column(db.String(64), index=True)  # barbell, dumbbell, ...
    exercise_type = db.Column(
        db.String(32), default="weight", nullable=False
    )  # weight|reps|duration|distance
    instructions = db.Column(db.Text)
    image_url = db.Column(db.String(512))
    cdn_video_id = db.Column(db.String(16), nullable=True)  # ID 8 chiffres Hevy CDN
    cdn_video_slug = db.Column(db.String(255), nullable=True)  # Nom-With-Hyphens_Muscle
    is_custom = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )

    user = relationship("User", back_populates="exercises")
    routine_exercises = relationship(
        "RoutineExercise", back_populates="exercise", cascade="all, delete-orphan"
    )
    workout_exercises = relationship(
        "WorkoutExercise", back_populates="exercise", cascade="all, delete-orphan"
    )
    personal_records = relationship(
        "PersonalRecord", back_populates="exercise", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_exercise_muscle", "muscle_group"),
        Index("idx_exercise_custom_user", "is_custom", "user_id"),
    )

    # Base URL du CDN vidéos Hevy public
    CDN_BASE_URL = "https://d2l9nsnmtah87f.cloudfront.net/exercise-assets"

    @property
    def cdn_video_url(self) -> str | None:
        """URL complète de la vidéo CDN si on a l'ID et le slug.

        Format attendu : {BASE}/{ID8}-{Name-With-Hyphens}_{Muscle}.mp4
        """
        if not self.cdn_video_id or not self.cdn_video_slug:
            return None
        return f"{self.CDN_BASE_URL}/{self.cdn_video_id}-{self.cdn_video_slug}.mp4"

    @property
    def cdn_thumb_url(self) -> str | None:
        """Thumbnail placeholder : on renvoie l'URL de la vidéo (le <video poster> extrait la 1re frame)."""
        return self.cdn_video_url

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "muscle_group": self.muscle_group,
            "equipment": self.equipment,
            "exercise_type": self.exercise_type,
            "instructions": self.instructions,
            "image_url": self.image_url,
            "cdn_video_id": self.cdn_video_id,
            "cdn_video_url": self.cdn_video_url,
            "is_custom": self.is_custom,
            "user_id": self.user_id,
        }


# --------------------------------------------------------------------------
# Routines
# --------------------------------------------------------------------------


class RoutineFolder(db.Model):
    """Dossier regroupant des routines."""

    __tablename__ = "routine_folder"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    order_index = db.Column(db.Integer, default=0, nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="folders")
    routines = relationship(
        "Routine", back_populates="folder", cascade="save-update, merge"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "order_index": self.order_index,
            "user_id": self.user_id,
        }


class Routine(db.Model):
    """Routine = template d'entraînement réutilisable."""

    __tablename__ = "routine"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    folder_id = db.Column(
        db.Integer,
        db.ForeignKey("routine_folder.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_index = db.Column(db.Integer, default=0, nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="routines")
    folder = relationship("RoutineFolder", back_populates="routines")
    exercises = relationship(
        "RoutineExercise",
        back_populates="routine",
        cascade="all, delete-orphan",
        order_by="RoutineExercise.order_index",
    )

    def to_dict(self, include_exercises: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "folder_id": self.folder_id,
            "order_index": self.order_index,
            "user_id": self.user_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_exercises:
            data["exercises"] = [re.to_dict(True) for re in self.exercises]
        return data


class RoutineExercise(db.Model):
    """Exercice dans une routine (ordre + sets template)."""

    __tablename__ = "routine_exercise"

    id = db.Column(db.Integer, primary_key=True)
    routine_id = db.Column(
        db.Integer,
        db.ForeignKey("routine.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("exercise.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_index = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text)
    rest_seconds = db.Column(db.Integer, default=90)

    routine = relationship("Routine", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="routine_exercises")
    sets = relationship(
        "RoutineSet",
        back_populates="routine_exercise",
        cascade="all, delete-orphan",
        order_by="RoutineSet.order_index",
    )

    def to_dict(self, include_sets: bool = False) -> dict:
        data = {
            "id": self.id,
            "routine_id": self.routine_id,
            "exercise_id": self.exercise_id,
            "exercise": self.exercise.to_dict() if self.exercise else None,
            "order_index": self.order_index,
            "notes": self.notes,
            "rest_seconds": self.rest_seconds,
        }
        if include_sets:
            data["sets"] = [s.to_dict() for s in self.sets]
        return data


class RoutineSet(db.Model):
    """Set template dans une routine."""

    __tablename__ = "routine_set"

    id = db.Column(db.Integer, primary_key=True)
    routine_exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("routine_exercise.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_index = db.Column(db.Integer, default=0, nullable=False)
    set_type = db.Column(db.String(16), default="normal", nullable=False)
    target_reps = db.Column(db.Integer)
    target_weight = db.Column(db.Float)
    target_rpe = db.Column(db.Float)

    routine_exercise = relationship("RoutineExercise", back_populates="sets")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_index": self.order_index,
            "set_type": self.set_type,
            "target_reps": self.target_reps,
            "target_weight": self.target_weight,
            "target_rpe": self.target_rpe,
        }


# --------------------------------------------------------------------------
# Workouts (sessions réelles)
# --------------------------------------------------------------------------


class Workout(db.Model):
    """Séance d'entraînement réelle (historique)."""

    __tablename__ = "workout"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(255))
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True, index=True)
    duration_seconds = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    routine_id = db.Column(
        db.Integer,
        db.ForeignKey("routine.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user = relationship("User", back_populates="workouts")
    routine = relationship("Routine")
    exercises = relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="WorkoutExercise.order_index",
    )

    __table_args__ = (Index("idx_workout_user_ended", "user_id", "ended_at"),)

    @property
    def is_finished(self) -> bool:
        return self.ended_at is not None

    @property
    def total_volume(self) -> float:
        """Volume total = Σ weight × reps pour sets completés."""
        total = 0.0
        for we in self.exercises:
            for s in we.sets:
                if s.completed and s.weight and s.reps:
                    total += s.weight * s.reps
        return total

    @property
    def total_sets(self) -> int:
        return sum(1 for we in self.exercises for s in we.sets if s.completed)

    @property
    def total_reps(self) -> int:
        return sum(
            s.reps or 0
            for we in self.exercises
            for s in we.sets
            if s.completed
        )

    def to_dict(self, include_exercises: bool = False) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "notes": self.notes,
            "routine_id": self.routine_id,
            "is_finished": self.is_finished,
            "total_volume": self.total_volume,
            "total_sets": self.total_sets,
            "total_reps": self.total_reps,
        }
        if include_exercises:
            data["exercises"] = [we.to_dict(True) for we in self.exercises]
        return data


class WorkoutExercise(db.Model):
    """Exercice dans une séance."""

    __tablename__ = "workout_exercise"

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer,
        db.ForeignKey("workout.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("exercise.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_index = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text)

    workout = relationship("Workout", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="workout_exercises")
    sets = relationship(
        "WorkoutSet",
        back_populates="workout_exercise",
        cascade="all, delete-orphan",
        order_by="WorkoutSet.order_index",
    )

    def to_dict(self, include_sets: bool = False) -> dict:
        data = {
            "id": self.id,
            "workout_id": self.workout_id,
            "exercise_id": self.exercise_id,
            "exercise": self.exercise.to_dict() if self.exercise else None,
            "order_index": self.order_index,
            "notes": self.notes,
        }
        if include_sets:
            data["sets"] = [s.to_dict() for s in self.sets]
        return data


class WorkoutSet(db.Model):
    """Set réellement effectué dans une séance."""

    __tablename__ = "workout_set"

    id = db.Column(db.Integer, primary_key=True)
    workout_exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("workout_exercise.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_index = db.Column(db.Integer, default=0, nullable=False)
    set_type = db.Column(
        db.String(16), default="normal", nullable=False
    )  # normal|warmup|drop|failure
    reps = db.Column(db.Integer)
    weight = db.Column(db.Float)
    rpe = db.Column(db.Float)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    is_pr = db.Column(db.Boolean, default=False, nullable=False)
    notes = db.Column(db.Text)
    completed_at = db.Column(db.DateTime)

    workout_exercise = relationship("WorkoutExercise", back_populates="sets")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workout_exercise_id": self.workout_exercise_id,
            "order_index": self.order_index,
            "set_type": self.set_type,
            "reps": self.reps,
            "weight": self.weight,
            "rpe": self.rpe,
            "completed": self.completed,
            "is_pr": self.is_pr,
            "notes": self.notes,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


# --------------------------------------------------------------------------
# Personal Records
# --------------------------------------------------------------------------


class PersonalRecord(db.Model):
    """Record personnel détecté sur un exercice."""

    __tablename__ = "personal_record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("exercise.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pr_type = db.Column(
        db.String(16), nullable=False
    )  # weight|reps|volume|e1rm
    value = db.Column(db.Float, nullable=False)
    reps = db.Column(db.Integer)
    weight = db.Column(db.Float)
    workout_set_id = db.Column(
        db.Integer,
        db.ForeignKey("workout_set.id", ondelete="SET NULL"),
        nullable=True,
    )
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="personal_records")
    exercise = relationship("Exercise", back_populates="personal_records")

    __table_args__ = (
        Index("idx_pr_user_exercise_type", "user_id", "exercise_id", "pr_type"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "exercise_id": self.exercise_id,
            "pr_type": self.pr_type,
            "value": self.value,
            "reps": self.reps,
            "weight": self.weight,
            "workout_set_id": self.workout_set_id,
            "achieved_at": (
                self.achieved_at.isoformat() if self.achieved_at else None
            ),
        }
