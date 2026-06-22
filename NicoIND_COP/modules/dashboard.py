"""
NicoIND — modules/dashboard.py
Dashboard ejecutivo con KPIs en tiempo real.
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta, date
from models import (db, SalesOrder, FinancialTransaction, Product,
                    Employee, Project, MachineMetric, AuditLog)
import json

dashboard_bp = Blueprint("dashboard", __name__)


def cid():
    return current_user.company_id


@dashboard_bp.route("/")
@login_required
def index():
    cmp = cid()
    today     = date.today()
    month_ago = today - timedelta(days=30)

    # ── KPIs ─────────────────────────────────────────────
    total_sales = db.session.query(func.sum(SalesOrder.total)).filter(
        SalesOrder.company_id == cmp,
        SalesOrder.status.in_(["confirmed","delivered"])
    ).scalar() or 0

    month_sales = db.session.query(func.sum(SalesOrder.total)).filter(
        SalesOrder.company_id == cmp,
        SalesOrder.status.in_(["confirmed","delivered"]),
        SalesOrder.created_at >= datetime.combine(month_ago, datetime.min.time())
    ).scalar() or 0

    total_income = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.company_id == cmp,
        FinancialTransaction.transaction_type == "income"
    ).scalar() or 0

    total_expense = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.company_id == cmp,
        FinancialTransaction.transaction_type == "expense"
    ).scalar() or 0

    profit = total_income - total_expense

    low_stock = Product.query.filter(
        Product.company_id == cmp,
        Product.active == True,
        Product.stock <= Product.min_stock
    ).count()

    total_products = Product.query.filter_by(company_id=cmp, active=True).count()

    total_employees = Employee.query.filter_by(company_id=cmp, status="active").count()

    active_projects = Project.query.filter(
        Project.company_id == cmp,
        Project.status.in_(["active","planning"])
    ).count()

    # Inventory value
    inv_value = db.session.query(func.sum(Product.stock * Product.cost)).filter(
        Product.company_id == cmp, Product.active == True
    ).scalar() or 0

    # Average OEE last 7 days
    avg_oee = db.session.query(func.avg(MachineMetric.oee)).filter(
        MachineMetric.company_id == cmp,
        MachineMetric.record_date >= today - timedelta(days=7)
    ).scalar() or 0

    # ── Chart: Sales last 30 days ─────────────────────────
    sales_chart = []
    for i in range(29, -1, -1):
        d    = today - timedelta(days=i)
        d0   = datetime.combine(d, datetime.min.time())
        d1   = datetime.combine(d, datetime.max.time())
        amt  = db.session.query(func.sum(SalesOrder.total)).filter(
            SalesOrder.company_id == cmp,
            SalesOrder.created_at.between(d0, d1),
            SalesOrder.status.in_(["confirmed","delivered"])
        ).scalar() or 0
        exp  = db.session.query(func.sum(FinancialTransaction.amount)).filter(
            FinancialTransaction.company_id == cmp,
            FinancialTransaction.date == d,
            FinancialTransaction.transaction_type == "expense"
        ).scalar() or 0
        sales_chart.append({"date": d.strftime("%d/%m"), "sales": round(amt, 2), "expenses": round(exp, 2)})

    # ── Chart: Products by category ──────────────────────
    cat_data = db.session.query(
        Product.category, func.count(Product.id)
    ).filter_by(company_id=cmp, active=True).group_by(Product.category).all()

    # ── Recent orders ─────────────────────────────────────
    recent_orders = SalesOrder.query.filter_by(company_id=cmp).order_by(
        SalesOrder.created_at.desc()).limit(8).all()

    # ── Recent audit ─────────────────────────────────────
    recent_audit = AuditLog.query.filter_by(company_id=cmp).order_by(
        AuditLog.created_at.desc()).limit(6).all()

    # ── Projects progress ─────────────────────────────────
    active_projs = Project.query.filter(
        Project.company_id == cmp,
        Project.status.in_(["active","planning"])
    ).limit(5).all()

    return render_template("dashboard/index.html",
        # KPIs
        total_sales   = round(total_sales, 2),
        month_sales   = round(month_sales, 2),
        profit        = round(profit, 2),
        total_income  = round(total_income, 2),
        total_expense = round(total_expense, 2),
        low_stock     = low_stock,
        total_products= total_products,
        total_employees=total_employees,
        active_projects=active_projects,
        inv_value     = round(inv_value, 2),
        avg_oee       = round(avg_oee, 1),
        # Charts
        sales_chart   = json.dumps(sales_chart),
        cat_data      = json.dumps([{"label": c, "value": v} for c,v in cat_data]),
        # Tables
        recent_orders = recent_orders,
        recent_audit  = recent_audit,
        active_projs  = active_projs,
    )
