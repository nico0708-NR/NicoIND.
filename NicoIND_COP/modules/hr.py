"""
NicoIND — modules/hr.py
Recursos Humanos: empleados, departamentos, nómina.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date
from models import db, Employee, Department, AuditLog

hr_bp = Blueprint("hr", __name__)

def cid(): return current_user.company_id

def audit(action, desc):
    db.session.add(AuditLog(company_id=cid(), user_id=current_user.id,
                            action=action, module="hr",
                            description=desc, ip_address=request.remote_addr))


@hr_bp.route("/hr")
@login_required
def index():
    search = request.args.get("q","")
    dept   = request.args.get("dept","all")
    status = request.args.get("status","active")

    q = Employee.query.filter_by(company_id=cid())
    if status != "all":  q = q.filter_by(status=status)
    if dept   != "all":
        dep = Department.query.filter_by(company_id=cid(), id=int(dept)).first()
        if dep: q = q.filter_by(department_id=dep.id)
    if search: q = q.filter(Employee.full_name.ilike(f"%{search}%"))
    employees = q.order_by(Employee.full_name).all()

    depts = Department.query.filter_by(company_id=cid()).all()
    total_salary = sum(e.salary for e in employees)
    active_count = sum(1 for e in employees if e.status == "active")

    dept_summary = db.session.query(
        Department.name,
        func.count(Employee.id),
        func.sum(Employee.salary)
    ).join(Employee, Employee.department_id == Department.id, isouter=True).filter(
        Department.company_id == cid()
    ).group_by(Department.id, Department.name).all()

    return render_template("hr/index.html",
        employees    = employees,
        depts        = depts,
        total_salary = round(total_salary, 2),
        active_count = active_count,
        dept_summary = dept_summary,
        search=search, dept=dept, status=status)


@hr_bp.route("/hr/add", methods=["GET","POST"])
@login_required
def add():
    if request.method == "POST":
        hd = request.form.get("hire_date","")
        emp = Employee(
            company_id    = cid(),
            department_id = int(request.form.get("department_id") or 0) or None,
            code          = request.form.get("code","").strip(),
            full_name     = request.form.get("full_name","").strip(),
            position      = request.form.get("position","").strip(),
            salary        = float(request.form.get("salary",0) or 0),
            hire_date     = date.fromisoformat(hd) if hd else date.today(),
            status        = request.form.get("status","active"),
            email         = request.form.get("email","").strip(),
            phone         = request.form.get("phone","").strip())
        db.session.add(emp)
        audit("CREATE", f"Empleado creado: {emp.full_name}")
        db.session.commit()
        flash(f"Empleado '{emp.full_name}' registrado.", "success")
        return redirect(url_for("hr.index"))

    depts = Department.query.filter_by(company_id=cid()).all()
    return render_template("hr/form.html", emp=None, depts=depts, action="add")


@hr_bp.route("/hr/edit/<int:eid>", methods=["GET","POST"])
@login_required
def edit(eid):
    emp = Employee.query.filter_by(id=eid, company_id=cid()).first_or_404()
    if request.method == "POST":
        hd = request.form.get("hire_date","")
        emp.department_id = int(request.form.get("department_id") or 0) or emp.department_id
        emp.code          = request.form.get("code", emp.code)
        emp.full_name     = request.form.get("full_name", emp.full_name)
        emp.position      = request.form.get("position", emp.position)
        emp.salary        = float(request.form.get("salary", emp.salary) or emp.salary)
        emp.hire_date     = date.fromisoformat(hd) if hd else emp.hire_date
        emp.status        = request.form.get("status", emp.status)
        emp.email         = request.form.get("email", emp.email)
        emp.phone         = request.form.get("phone", emp.phone)
        audit("UPDATE", f"Empleado actualizado: {emp.full_name}")
        db.session.commit()
        flash("Empleado actualizado.", "success")
        return redirect(url_for("hr.index"))

    depts = Department.query.filter_by(company_id=cid()).all()
    return render_template("hr/form.html", emp=emp, depts=depts, action="edit")


@hr_bp.route("/hr/delete/<int:eid>", methods=["POST"])
@login_required
def delete(eid):
    emp = Employee.query.filter_by(id=eid, company_id=cid()).first_or_404()
    emp.status = "inactive"
    audit("DELETE", f"Empleado desactivado: {emp.full_name}")
    db.session.commit()
    flash(f"Empleado '{emp.full_name}' desactivado.", "warning")
    return redirect(url_for("hr.index"))
