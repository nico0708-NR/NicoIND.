"""
NicoIND — modules/inventory.py
Gestión de inventario: CRUD, movimientos, alertas.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime
from models import db, Product, StockMovement, AuditLog
import json

inventory_bp = Blueprint("inventory", __name__)


def cid(): return current_user.company_id


def audit(action, desc):
    db.session.add(AuditLog(company_id=cid(), user_id=current_user.id,
                            action=action, module="inventory",
                            description=desc, ip_address=request.remote_addr))


@inventory_bp.route("/inventory")
@login_required
def index():
    cat    = request.args.get("cat", "all")
    search = request.args.get("q", "")
    status = request.args.get("status", "all")

    q = Product.query.filter_by(company_id=cid(), active=True)
    if cat != "all":    q = q.filter_by(category=cat)
    if search:          q = q.filter(Product.name.ilike(f"%{search}%"))

    products = q.order_by(Product.name).all()

    if status == "low":  products = [p for p in products if p.stock_status == "low"]
    elif status == "out": products = [p for p in products if p.stock_status == "out"]

    categories = [r[0] for r in db.session.query(Product.category).filter_by(
        company_id=cid(), active=True).distinct().all()]

    total_val = sum(p.stock_value for p in products)
    low_count = sum(1 for p in products if p.stock_status in ("low","out"))

    return render_template("inventory/index.html",
                           products=products, categories=categories,
                           total_val=total_val, low_count=low_count,
                           cat=cat, search=search, status=status)


@inventory_bp.route("/inventory/add", methods=["GET","POST"])
@login_required
def add():
    if request.method == "POST":
        p = Product(
            company_id = cid(),
            code       = request.form.get("code","").strip(),
            name       = request.form.get("name","").strip(),
            category   = request.form.get("category","").strip(),
            unit       = request.form.get("unit","unidad"),
            stock      = float(request.form.get("stock",0) or 0),
            min_stock  = float(request.form.get("min_stock",10) or 10),
            max_stock  = float(request.form.get("max_stock",500) or 500),
            cost       = float(request.form.get("cost",0) or 0),
            price      = float(request.form.get("price",0) or 0),
            supplier   = request.form.get("supplier",""),
            location   = request.form.get("location",""),
        )
        db.session.add(p)
        db.session.flush()
        if p.stock > 0:
            mv = StockMovement(product_id=p.id, company_id=cid(),
                               movement_type="in", quantity=p.stock,
                               unit_cost=p.cost, reference="Stock inicial",
                               user_id=current_user.id)
            db.session.add(mv)
        audit("CREATE", f"Producto creado: {p.name}")
        db.session.commit()
        flash(f"Producto '{p.name}' creado correctamente.", "success")
        return redirect(url_for("inventory.index"))

    categories = [r[0] for r in db.session.query(Product.category).filter_by(
        company_id=cid(), active=True).distinct().all()]
    return render_template("inventory/form.html", product=None, categories=categories, action="add")


@inventory_bp.route("/inventory/edit/<int:pid>", methods=["GET","POST"])
@login_required
def edit(pid):
    p = Product.query.filter_by(id=pid, company_id=cid()).first_or_404()
    if request.method == "POST":
        old_name = p.name
        p.code     = request.form.get("code", p.code)
        p.name     = request.form.get("name", p.name)
        p.category = request.form.get("category", p.category)
        p.unit     = request.form.get("unit", p.unit)
        p.min_stock= float(request.form.get("min_stock", p.min_stock) or p.min_stock)
        p.max_stock= float(request.form.get("max_stock", p.max_stock) or p.max_stock)
        p.cost     = float(request.form.get("cost", p.cost) or p.cost)
        p.price    = float(request.form.get("price", p.price) or p.price)
        p.supplier = request.form.get("supplier", p.supplier)
        p.location = request.form.get("location", p.location)
        audit("UPDATE", f"Producto actualizado: {old_name}")
        db.session.commit()
        flash("Producto actualizado.", "success")
        return redirect(url_for("inventory.index"))

    categories = [r[0] for r in db.session.query(Product.category).filter_by(
        company_id=cid(), active=True).distinct().all()]
    return render_template("inventory/form.html", product=p, categories=categories, action="edit")


@inventory_bp.route("/inventory/delete/<int:pid>", methods=["POST"])
@login_required
def delete(pid):
    p = Product.query.filter_by(id=pid, company_id=cid()).first_or_404()
    p.active = False
    audit("DELETE", f"Producto desactivado: {p.name}")
    db.session.commit()
    flash(f"Producto '{p.name}' eliminado.", "warning")
    return redirect(url_for("inventory.index"))


@inventory_bp.route("/inventory/movement/<int:pid>", methods=["POST"])
@login_required
def movement(pid):
    p    = Product.query.filter_by(id=pid, company_id=cid()).first_or_404()
    mtype= request.form.get("movement_type","in")
    qty  = float(request.form.get("quantity",0) or 0)
    ref  = request.form.get("reference","")
    if qty <= 0:
        flash("La cantidad debe ser mayor que 0.", "danger")
        return redirect(url_for("inventory.index"))
    if mtype == "out" and p.stock < qty:
        flash("Stock insuficiente para esta salida.", "danger")
        return redirect(url_for("inventory.index"))
    mv = StockMovement(product_id=p.id, company_id=cid(),
                       movement_type=mtype, quantity=qty,
                       unit_cost=p.cost, reference=ref,
                       user_id=current_user.id)
    db.session.add(mv)
    if mtype == "in":        p.stock += qty
    elif mtype == "out":     p.stock -= qty
    elif mtype == "adjustment": p.stock = qty
    audit("UPDATE", f"Movimiento {mtype} {qty} u. de {p.name}")
    db.session.commit()
    flash(f"Movimiento registrado correctamente.", "success")
    return redirect(url_for("inventory.index"))


@inventory_bp.route("/inventory/api/chart")
@login_required
def api_chart():
    cat_data = db.session.query(Product.category, func.count(Product.id),
                                func.sum(Product.stock * Product.cost)).filter_by(
        company_id=cid(), active=True).group_by(Product.category).all()
    return jsonify([{"category": c, "count": n, "value": round(v or 0, 2)}
                    for c, n, v in cat_data])
