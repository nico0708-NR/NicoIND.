"""
NicoIND — modules/auth.py
Autenticación: login, logout, registro, perfil.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from models import db, User, AuditLog

auth_bp = Blueprint("auth", __name__)


def _audit(action, desc, user):
    try:
        db.session.add(AuditLog(
            company_id=user.company_id, user_id=user.id,
            action=action, module="auth",
            description=desc, ip_address=request.remote_addr))
        db.session.commit()
    except Exception:
        db.session.rollback()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=bool(request.form.get("remember")))
            user.last_login = datetime.utcnow()
            db.session.commit()
            _audit("LOGIN", f"Inicio de sesión exitoso: {user.username}", user)
            flash(f"¡Bienvenido, {user.full_name or user.username}!", "success")
            nxt = request.args.get("next")
            return redirect(nxt or url_for("dashboard.index"))
        flash("Credenciales incorrectas. Verifica usuario y contraseña.", "danger")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        username  = request.form.get("username", "").strip()
        email     = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password  = request.form.get("password", "")
        confirm   = request.form.get("confirm", "")
        if len(username) < 3:
            flash("El usuario debe tener al menos 3 caracteres.", "danger")
        elif len(password) < 5:
            flash("La contraseña debe tener al menos 5 caracteres.", "danger")
        elif password != confirm:
            flash("Las contraseñas no coinciden.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Ese nombre de usuario ya existe.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Ese email ya está registrado.", "danger")
        else:
            from models import Company
            company = Company.query.first()
            if not company:
                flash("No hay empresas configuradas. Contacta al administrador.", "danger")
                return render_template("login.html")
            u = User(company_id=company.id, username=username,
                     email=email, full_name=full_name, role="analyst")
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash("¡Cuenta creada exitosamente! Inicia sesión.", "success")
            return redirect(url_for("auth.login"))
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    _audit("LOGOUT", f"Cierre de sesión: {current_user.username}", current_user)
    logout_user()
    flash("Sesión cerrada correctamente. ¡Hasta pronto!", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", current_user.full_name)
        current_user.email     = request.form.get("email", current_user.email)
        new_pwd = request.form.get("new_password", "").strip()
        if new_pwd:
            if len(new_pwd) < 5:
                flash("La contraseña debe tener al menos 5 caracteres.", "danger")
                return redirect(url_for("auth.profile"))
            current_user.set_password(new_pwd)
        db.session.commit()
        _audit("UPDATE", "Perfil actualizado", current_user)
        flash("Perfil actualizado correctamente.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("admin/profile.html")
