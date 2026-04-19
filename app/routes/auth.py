"""Blueprint d'authentification (pages + POST dédiés).

Routes pages : /login (GET), /login (POST via login_submit endpoint),
                /register (GET), /register (POST via register_submit), /logout
Le Frontend pointe vers des endpoints séparés GET/POST pour matcher ses
url_for — on expose donc login_page/login_submit et register_page/register_submit.
"""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"], endpoint="login_page")
def login_page():
    """Affiche la page de connexion."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("auth/login.html")


@auth_bp.route("/login", methods=["POST"], endpoint="login_submit")
def login_submit():
    """Traite la soumission du formulaire de connexion."""
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    remember = bool(request.form.get("remember"))

    user = db.session.query(User).filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user, remember=remember)
        next_url = request.args.get("next")
        return redirect(next_url or url_for("main.dashboard"))

    flash("Email ou mot de passe incorrect.", "error")
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/register", methods=["GET"], endpoint="register_page")
def register_page():
    """Affiche la page d'inscription."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html")


@auth_bp.route("/register", methods=["POST"], endpoint="register_submit")
def register_submit():
    """Traite la soumission du formulaire d'inscription."""
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    password2 = request.form.get("password2") or ""

    if not email or not password:
        flash("Email et mot de passe requis.", "error")
        return redirect(url_for("auth.register_page"))
    if password != password2:
        flash("Les mots de passe ne correspondent pas.", "error")
        return redirect(url_for("auth.register_page"))
    if db.session.query(User).filter_by(email=email).first():
        flash("Cet email est déjà utilisé.", "error")
        return redirect(url_for("auth.register_page"))

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for("main.dashboard"))


@auth_bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    """Déconnexion."""
    logout_user()
    return redirect(url_for("auth.login_page"))
