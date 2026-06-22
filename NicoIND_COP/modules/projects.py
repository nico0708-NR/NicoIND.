"""
NicoIND — modules/projects.py
Gestión de proyectos con tareas estilo Kanban.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date
from models import db, Project, ProjectTask, AuditLog

projects_bp = Blueprint("projects", __name__)

def cid(): return current_user.company_id

def audit(action, desc):
    db.session.add(AuditLog(company_id=cid(), user_id=current_user.id,
                            action=action, module="projects",
                            description=desc, ip_address=request.remote_addr))


@projects_bp.route("/projects")
@login_required
def index():
    status = request.args.get("status","all")
    q = Project.query.filter_by(company_id=cid())
    if status != "all": q = q.filter_by(status=status)
    projs = q.order_by(Project.created_at.desc()).all()

    summary = {"active":0,"planning":0,"completed":0,"on_hold":0}
    for p in Project.query.filter_by(company_id=cid()).all():
        if p.status in summary: summary[p.status] += 1

    return render_template("projects/index.html", projs=projs, summary=summary, status=status)


@projects_bp.route("/projects/add", methods=["GET","POST"])
@login_required
def add():
    if request.method == "POST":
        sd = request.form.get("start_date","")
        ed = request.form.get("end_date","")
        p = Project(
            company_id  = cid(),
            name        = request.form.get("name","").strip(),
            description = request.form.get("description","").strip(),
            status      = request.form.get("status","planning"),
            priority    = request.form.get("priority","medium"),
            start_date  = date.fromisoformat(sd) if sd else date.today(),
            end_date    = date.fromisoformat(ed) if ed else None,
            budget      = float(request.form.get("budget",0) or 0),
            progress    = int(request.form.get("progress",0) or 0),
            manager_id  = current_user.id)
        db.session.add(p)
        audit("CREATE", f"Proyecto creado: {p.name}")
        db.session.commit()
        flash(f"Proyecto '{p.name}' creado.", "success")
        return redirect(url_for("projects.index"))
    return render_template("projects/form.html", proj=None)


@projects_bp.route("/projects/<int:pid>", methods=["GET","POST"])
@login_required
def detail(pid):
    proj = Project.query.filter_by(id=pid, company_id=cid()).first_or_404()
    if request.method == "POST":
        # Update progress / status
        proj.progress = int(request.form.get("progress", proj.progress) or proj.progress)
        proj.status   = request.form.get("status", proj.status)
        db.session.commit()
        flash("Proyecto actualizado.", "success")
        return redirect(url_for("projects.detail", pid=pid))

    tasks_by_status = {
        "todo":        [t for t in proj.tasks if t.status == "todo"],
        "in_progress": [t for t in proj.tasks if t.status == "in_progress"],
        "review":      [t for t in proj.tasks if t.status == "review"],
        "done":        [t for t in proj.tasks if t.status == "done"],
    }
    return render_template("projects/detail.html", proj=proj, tasks=tasks_by_status)


@projects_bp.route("/projects/<int:pid>/task/add", methods=["POST"])
@login_required
def add_task(pid):
    proj = Project.query.filter_by(id=pid, company_id=cid()).first_or_404()
    dd   = request.form.get("due_date","")
    t = ProjectTask(
        project_id  = pid,
        title       = request.form.get("title","").strip(),
        description = request.form.get("description","").strip(),
        status      = request.form.get("status","todo"),
        priority    = request.form.get("priority","medium"),
        assigned_to = request.form.get("assigned_to","").strip(),
        due_date    = date.fromisoformat(dd) if dd else None)
    db.session.add(t)
    # Recalc progress
    all_tasks  = ProjectTask.query.filter_by(project_id=pid).count() + 1
    done_tasks = ProjectTask.query.filter_by(project_id=pid, status="done").count()
    proj.progress = int(done_tasks / all_tasks * 100) if all_tasks else 0
    audit("CREATE", f"Tarea agregada: {t.title} → {proj.name}")
    db.session.commit()
    flash("Tarea agregada.", "success")
    return redirect(url_for("projects.detail", pid=pid))


@projects_bp.route("/projects/task/update/<int:tid>", methods=["POST"])
@login_required
def update_task(tid):
    t = ProjectTask.query.get_or_404(tid)
    t.status = request.form.get("status", t.status)
    proj = Project.query.filter_by(id=t.project_id, company_id=cid()).first_or_404()
    all_tasks  = ProjectTask.query.filter_by(project_id=proj.id).count()
    done_tasks = ProjectTask.query.filter_by(project_id=proj.id, status="done").count()
    proj.progress = int(done_tasks / all_tasks * 100) if all_tasks else 0
    db.session.commit()
    return jsonify({"ok": True, "progress": proj.progress})
