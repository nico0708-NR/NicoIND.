"""
NicoIND — modules/admin.py
Panel de administración: usuarios, empresa, auditoría.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from models import db, User, Company, AuditLog

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def deco(*args, **kwargs):
        if current_user.role not in ("superadmin", "admin"):
            abort(403)
        return f(*args, **kwargs)
    return deco


def _audit(action, desc):
    db.session.add(AuditLog(
        company_id=current_user.company_id, user_id=current_user.id,
        action=action, module="admin", description=desc,
        ip_address=request.remote_addr))


@admin_bp.route("/admin")
@admin_required
def index():
    cmp_id = current_user.company_id
    users   = User.query.filter_by(company_id=cmp_id).all()
    company = Company.query.get(cmp_id)
    today   = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    logs    = AuditLog.query.filter_by(company_id=cmp_id)\
                            .order_by(AuditLog.created_at.desc()).limit(20).all()
    stats = {
        "users":        len(users),
        "active_users": sum(1 for u in users if u.is_active),
        "admins":       sum(1 for u in users if u.role in ("admin","superadmin")),
        "logs_today":   AuditLog.query.filter(
            AuditLog.company_id == cmp_id,
            AuditLog.created_at >= today).count(),
    }
    return render_template("admin/index.html",
                           users=users, company=company, logs=logs, stats=stats)


@admin_bp.route("/admin/users")
@admin_required
def users():
    all_users = User.query.filter_by(company_id=current_user.company_id)\
                          .order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/admin/users/add", methods=["POST"])
@admin_required
def add_user():
    username  = request.form.get("username","").strip()
    email     = request.form.get("email","").strip()
    full_name = request.form.get("full_name","").strip()
    role      = request.form.get("role","analyst")
    password  = request.form.get("password","nicond123").strip()

    if not username or not email:
        flash("Usuario y email son obligatorios.", "danger")
        return redirect(url_for("admin.users"))

    if User.query.filter_by(username=username).first():
        flash("Ese nombre de usuario ya existe.", "danger")
        return redirect(url_for("admin.users"))

    if User.query.filter_by(email=email).first():
        flash("Ese email ya está registrado.", "danger")
        return redirect(url_for("admin.users"))

    u = User(company_id=current_user.company_id, username=username,
             email=email, full_name=full_name, role=role)
    u.set_password(password or "nicond123")
    db.session.add(u)
    _audit("CREATE", f"Usuario creado: {username} [{role}]")
    db.session.commit()
    flash(f"Usuario '{username}' creado. Contraseña: {password or 'nicond123'}", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/admin/users/<int:uid>/toggle", methods=["POST"])
@admin_required
def toggle_user(uid):
    u = User.query.filter_by(id=uid, company_id=current_user.company_id).first_or_404()
    if u.id == current_user.id:
        flash("No puedes desactivarte a ti mismo.", "danger")
    else:
        u.is_active = not u.is_active
        _audit("UPDATE", f"Usuario {'activado' if u.is_active else 'desactivado'}: {u.username}")
        db.session.commit()
        flash(f"Usuario {u.username} {'activado' if u.is_active else 'desactivado'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/admin/users/<int:uid>/reset", methods=["POST"])
@admin_required
def reset_password(uid):
    u   = User.query.filter_by(id=uid, company_id=current_user.company_id).first_or_404()
    pwd = request.form.get("new_password","nicond123").strip()
    u.set_password(pwd)
    _audit("UPDATE", f"Contraseña restablecida: {u.username}")
    db.session.commit()
    flash(f"Contraseña de '{u.username}' restablecida a: {pwd}", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/admin/audit")
@admin_required
def audit_log():
    page = request.args.get("page", 1, type=int)
    mod  = request.args.get("module","all")
    q    = AuditLog.query.filter_by(company_id=current_user.company_id)
    if mod != "all":
        q = q.filter_by(module=mod)
    logs = q.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False)
    modules = [r[0] for r in db.session.query(AuditLog.module).filter_by(
        company_id=current_user.company_id).distinct().all()]
    return render_template("admin/audit.html", logs=logs, mod=mod, modules=modules)
