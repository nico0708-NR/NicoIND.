"""
NicoIND — modules/finance.py
Gestión financiera: ingresos, gastos, P&L, flujo de caja.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta, date
from models import db, FinancialTransaction, AuditLog
import json

finance_bp = Blueprint("finance", __name__)


def cid(): return current_user.company_id


def audit(action, desc):
    db.session.add(AuditLog(company_id=cid(), user_id=current_user.id,
                            action=action, module="finance",
                            description=desc, ip_address=request.remote_addr))


@finance_bp.route("/finance")
@login_required
def index():
    period = request.args.get("period", "30")
    ttype  = request.args.get("type",   "all")
    days   = int(period) if period.isdigit() else 30
    since  = date.today() - timedelta(days=days)

    q = FinancialTransaction.query.filter(
        FinancialTransaction.company_id == cid(),
        FinancialTransaction.date >= since)
    if ttype != "all": q = q.filter_by(transaction_type=ttype)
    transactions = q.order_by(FinancialTransaction.date.desc()).all()

    total_income  = sum(t.amount for t in transactions if t.transaction_type == "income")
    total_expense = sum(t.amount for t in transactions if t.transaction_type == "expense")
    profit        = total_income - total_expense
    margin        = round(profit / total_income * 100, 1) if total_income else 0

    # By category
    inc_by_cat  = {}
    exp_by_cat  = {}
    for t in transactions:
        if t.transaction_type == "income":
            inc_by_cat[t.category] = inc_by_cat.get(t.category, 0) + t.amount
        else:
            exp_by_cat[t.category] = exp_by_cat.get(t.category, 0) + t.amount

    # Daily flow for chart
    daily = {}
    for t in transactions:
        ds = t.date.strftime("%d/%m")
        if ds not in daily: daily[ds] = {"date": ds, "income": 0, "expense": 0}
        if t.transaction_type == "income":  daily[ds]["income"] += t.amount
        else:                               daily[ds]["expense"] += t.amount
    chart_data = sorted(daily.values(), key=lambda x: x["date"])

    return render_template("finance/index.html",
        transactions  = transactions[:50],
        total_income  = round(total_income, 2),
        total_expense = round(total_expense, 2),
        profit        = round(profit, 2),
        margin        = margin,
        inc_by_cat    = inc_by_cat,
        exp_by_cat    = exp_by_cat,
        chart_data    = json.dumps(chart_data),
        period=period, ttype=ttype)


@finance_bp.route("/finance/add", methods=["GET","POST"])
@login_required
def add():
    if request.method == "POST":
        t = FinancialTransaction(
            company_id       = cid(),
            transaction_type = request.form.get("transaction_type","income"),
            category         = request.form.get("category","").strip(),
            description      = request.form.get("description","").strip(),
            amount           = float(request.form.get("amount",0) or 0),
            date             = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date(),
            reference        = request.form.get("reference",""),
            user_id          = current_user.id)
        db.session.add(t)
        audit("CREATE", f"Transacción {t.transaction_type}: ${t.amount:.2f} - {t.description}")
        db.session.commit()
        flash("Transacción registrada correctamente.", "success")
        return redirect(url_for("finance.index"))

    return render_template("finance/form.html", tx=None, today=date.today().isoformat())


@finance_bp.route("/finance/delete/<int:tid>", methods=["POST"])
@login_required
def delete(tid):
    t = FinancialTransaction.query.filter_by(id=tid, company_id=cid()).first_or_404()
    audit("DELETE", f"Transacción eliminada: {t.description} ${t.amount:.2f}")
    db.session.delete(t)
    db.session.commit()
    flash("Transacción eliminada.", "warning")
    return redirect(url_for("finance.index"))


@finance_bp.route("/finance/api/chart")
@login_required
def api_chart():
    days  = int(request.args.get("days", 30))
    since = date.today() - timedelta(days=days)
    txs   = FinancialTransaction.query.filter(
        FinancialTransaction.company_id == cid(),
        FinancialTransaction.date >= since).all()
    daily = {}
    for t in txs:
        ds = t.date.strftime("%Y-%m-%d")
        if ds not in daily: daily[ds] = {"date": ds, "income": 0, "expense": 0}
        if t.transaction_type == "income": daily[ds]["income"] += t.amount
        else:                              daily[ds]["expense"] += t.amount
    return jsonify(sorted(daily.values(), key=lambda x: x["date"]))
