"""
NicoIND — modules/bi.py
Business Intelligence: análisis cruzado de datos empresariales.
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta, date
from models import (db, SalesOrder, SaleItem, Product, FinancialTransaction,
                    Employee, Project, MachineMetric)
import json

bi_bp = Blueprint("bi", __name__)

def cid(): return current_user.company_id


@bi_bp.route("/bi")
@login_required
def index():
    company_id = cid()
    today      = date.today()
    year_ago   = today - timedelta(days=365)

    # ── Ventas mensuales (12 meses) ──────────────────────
    monthly_sales = []
    for i in range(11, -1, -1):
        mo    = today.replace(day=1) - timedelta(days=i * 30)
        month_str = mo.strftime("%b %Y")
        mo_start  = datetime(mo.year, mo.month, 1)
        if mo.month == 12:
            mo_end = datetime(mo.year + 1, 1, 1)
        else:
            mo_end = datetime(mo.year, mo.month + 1, 1)
        amt = db.session.query(func.sum(SalesOrder.total)).filter(
            SalesOrder.company_id == company_id,
            SalesOrder.created_at >= mo_start,
            SalesOrder.created_at < mo_end,
            SalesOrder.status.in_(["confirmed","delivered"])
        ).scalar() or 0
        exp = db.session.query(func.sum(FinancialTransaction.amount)).filter(
            FinancialTransaction.company_id == company_id,
            FinancialTransaction.date >= mo_start.date(),
            FinancialTransaction.date < mo_end.date(),
            FinancialTransaction.transaction_type == "expense"
        ).scalar() or 0
        monthly_sales.append({"month": month_str, "sales": round(amt,2), "expenses": round(exp,2)})

    # ── Top productos más vendidos ─────────────────────────
    top_products = db.session.query(
        Product.name,
        func.sum(SaleItem.quantity).label("total_qty"),
        func.sum(SaleItem.subtotal).label("total_rev")
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(SalesOrder, SalesOrder.id == SaleItem.order_id)\
     .filter(Product.company_id == company_id,
             SalesOrder.created_at >= datetime.combine(year_ago, datetime.min.time()))\
     .group_by(Product.id, Product.name)\
     .order_by(func.sum(SaleItem.subtotal).desc())\
     .limit(10).all()

    # ── Categorías ────────────────────────────────────────
    cat_sales = db.session.query(
        Product.category,
        func.sum(SaleItem.subtotal).label("rev")
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(SalesOrder, SalesOrder.id == SaleItem.order_id)\
     .filter(Product.company_id == company_id)\
     .group_by(Product.category)\
     .order_by(func.sum(SaleItem.subtotal).desc()).all()

    # ── Resumen financiero anual ──────────────────────────
    total_inc = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.company_id == company_id,
        FinancialTransaction.transaction_type == "income",
        FinancialTransaction.date >= year_ago).scalar() or 0
    total_exp = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.company_id == company_id,
        FinancialTransaction.transaction_type == "expense",
        FinancialTransaction.date >= year_ago).scalar() or 0

    # ── OEE promedio por máquina ──────────────────────────
    oee_by_machine = db.session.query(
        MachineMetric.machine_name,
        func.avg(MachineMetric.oee)
    ).filter(MachineMetric.company_id == company_id)\
     .group_by(MachineMetric.machine_name).all()

    # ── Proyectos por estado ──────────────────────────────
    proj_by_status = db.session.query(
        Project.status, func.count(Project.id)
    ).filter_by(company_id=company_id).group_by(Project.status).all()

    # ── Salary by department ─────────────────────────────
    sal_by_dept = db.session.query(
        func.coalesce(Employee.department_id, 0),
        func.count(Employee.id),
        func.sum(Employee.salary)
    ).filter_by(company_id=company_id, status="active")\
     .group_by(Employee.department_id).all()

    return render_template("bi/index.html",
        monthly_sales   = json.dumps(monthly_sales),
        top_products    = top_products,
        cat_sales       = cat_sales,
        total_inc       = round(total_inc, 2),
        total_exp       = round(total_exp, 2),
        profit_annual   = round(total_inc - total_exp, 2),
        oee_by_machine  = oee_by_machine,
        proj_by_status  = proj_by_status,
        sal_by_dept     = sal_by_dept,
    )
