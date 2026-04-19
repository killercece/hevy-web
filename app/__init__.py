"""Application factory Flask pour Hevy-Web.

Structure :
- create_app(config_class) : instancie l'app avec sa config
- extensions : db (SQLAlchemy), login_manager (Flask-Login), migrate (Alembic)
- blueprints : auth, main (pages), api (JSON)
"""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from config import get_config

from .extensions import db, login_manager, migrate


def create_app(config_class=None) -> Flask:
    """Crée et retourne une instance Flask configurée."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Chargement de la config
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # S'assurer que le dossier data/ existe (pour SQLite)
    data_dir = Path(app.root_path).parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"
    login_manager.login_message = "Connectez-vous pour accéder à cette page."
    login_manager.login_message_category = "info"

    # Handler unauthorized : 401 JSON pour /api, redirect pour les pages
    @login_manager.unauthorized_handler
    def _unauthorized():
        from flask import jsonify, redirect, request, url_for

        if request.path.startswith("/api/"):
            return jsonify(error="unauthorized", message="Connexion requise"), 401
        return redirect(url_for("auth.login_page", next=request.url))

    # Enregistrement des blueprints
    from .routes.api import api_bp
    from .routes.auth import auth_bp
    from .routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # User loader Flask-Login
    from .models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # Création des tables + seed au premier lancement
    # NB: Tolère les races entre workers gunicorn (SQLite concurrent CREATE TABLE)
    with app.app_context():
        from sqlalchemy.exc import IntegrityError, OperationalError

        try:
            db.create_all()
        except (OperationalError, IntegrityError):
            db.session.rollback()
        try:
            _apply_light_migrations(app)
        except (OperationalError, IntegrityError):
            db.session.rollback()
        try:
            _bootstrap_initial_data(app)
        except (OperationalError, IntegrityError):
            db.session.rollback()

    # Handlers d'erreur JSON pour l'API
    _register_error_handlers(app)

    return app


def _apply_light_migrations(app: Flask) -> None:
    """Migrations SQLite légères en runtime (idempotent).

    On ajoute les colonnes absentes via ALTER TABLE. Permet d'évoluer le
    schéma sans Alembic pour les simples ajouts.
    """
    from sqlalchemy import inspect, text

    insp = inspect(db.engine)
    if "exercise" not in insp.get_table_names():
        return

    existing = {c["name"] for c in insp.get_columns("exercise")}
    to_add: list[tuple[str, str]] = []
    if "cdn_video_id" not in existing:
        to_add.append(("cdn_video_id", "VARCHAR(16)"))
    if "cdn_video_slug" not in existing:
        to_add.append(("cdn_video_slug", "VARCHAR(255)"))

    for col, ddl in to_add:
        try:
            with db.engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE exercise ADD COLUMN {col} {ddl}"))
            app.logger.info("Colonne %s ajoutée à exercise.", col)
        except Exception as exc:  # noqa: BLE001
            app.logger.warning("Migration exercise.%s: %s", col, exc)


def _bootstrap_initial_data(app: Flask) -> None:
    """Seed initial : user admin + bibliothèque d'exercices (idempotent)."""
    from .models import Exercise, User
    from .utils.seed_exercises import seed_exercises, sync_cdn_videos

    # User admin par défaut si aucun utilisateur
    if not db.session.query(User).first():
        admin = User(
            email=app.config["ADMIN_EMAIL"],
            unit_system=app.config["DEFAULT_UNIT_SYSTEM"],
        )
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        app.logger.info(
            "Admin par défaut créé : %s (mdp: %s)",
            app.config["ADMIN_EMAIL"],
            app.config["ADMIN_PASSWORD"],
        )

    # Seed exercices si table vide, sinon sync des vidéos CDN
    if not db.session.query(Exercise).first():
        inserted = seed_exercises(db.session)
        app.logger.info("Bibliothèque seedée : %d exercices.", inserted)
    else:
        updated, added = sync_cdn_videos(db.session)
        if updated or added:
            app.logger.info(
                "Sync CDN : %d vidéos attachées, %d nouveaux exercices.",
                updated,
                added,
            )


def _register_error_handlers(app: Flask) -> None:
    """Enregistre des handlers d'erreur JSON pour les routes /api."""
    from flask import jsonify, request

    @app.errorhandler(404)
    def not_found(err):
        if request.path.startswith("/api/"):
            return jsonify(error="not_found", message=str(err)), 404
        return err, 404

    @app.errorhandler(400)
    def bad_request(err):
        if request.path.startswith("/api/"):
            return jsonify(error="bad_request", message=str(err)), 400
        return err, 400

    @app.errorhandler(401)
    def unauthorized(err):
        if request.path.startswith("/api/"):
            return jsonify(error="unauthorized", message="Connexion requise"), 401
        return err, 401
