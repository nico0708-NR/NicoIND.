"""
NicoIND — modules/ai_engine.py
Motor de Inteligencia Artificial con modelos reales.
Usa scikit-learn y numpy para predicciones empresariales.
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta, date
from models import db, SalesOrder, FinancialTransaction, Product, MachineMetric, AIPrediction
import json, math

# ── Imports de IA ──────────────────────────────────────────────
try:
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import r2_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

ai_bp = Blueprint("ai", __name__)

def cid(): return current_user.company_id


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE IA
# ══════════════════════════════════════════════════════════════

def predict_sales_30(company_id):
    """Predicción de ventas próximos 30 días con Regresión Lineal."""
    if not ML_AVAILABLE:
        return None

    # Obtener ventas diarias últimos 90 días
    since = date.today() - timedelta(days=90)
    orders = SalesOrder.query.filter(
        SalesOrder.company_id == company_id,
        SalesOrder.status.in_(["confirmed","delivered"]),
        SalesOrder.created_at >= datetime.combine(since, datetime.min.time())
    ).all()

    if len(orders) < 10:
        return {"error": "Datos insuficientes (mínimo 10 ventas)"}

    # Agrupar por día
    daily = {}
    for o in orders:
        d = o.created_at.date().isoformat()
        daily[d] = daily.get(d, 0) + o.total

    if len(daily) < 7:
        return {"error": "Se necesitan al menos 7 días de datos"}

    dates = sorted(daily.keys())
    amounts = [daily[d] for d in dates]

    X = np.arange(len(amounts)).reshape(-1, 1)
    y = np.array(amounts)

    model = LinearRegression()
    model.fit(X, y)
    r2 = round(r2_score(y, model.predict(X)), 3)

    # Predecir próximos 30 días
    future_X = np.arange(len(amounts), len(amounts) + 30).reshape(-1, 1)
    preds     = model.predict(future_X)
    preds     = np.maximum(preds, 0)  # No negativos

    future_dates = [(date.today() + timedelta(days=i+1)).strftime("%d/%m") for i in range(30)]

    # Estadísticas
    trend    = float(model.coef_[0])
    avg_pred = float(np.mean(preds))
    total_pred = float(np.sum(preds))

    return {
        "type": "sales_prediction",
        "r2": r2,
        "confidence": min(95, max(50, int(r2 * 100))),
        "trend_daily": round(trend, 2),
        "avg_daily_pred": round(avg_pred, 2),
        "total_30d_pred": round(total_pred, 2),
        "historical_labels": [d[-5:] for d in dates[-30:]],  # últimos 30 días
        "historical_values": [round(daily[d], 2) for d in dates[-30:]],
        "future_labels": future_dates,
        "future_values": [round(v, 2) for v in preds.tolist()],
        "trend_text": "alcista 📈" if trend > 0 else "bajista 📉",
    }


def detect_financial_anomalies(company_id):
    """Detección de anomalías en transacciones con Isolation Forest."""
    if not ML_AVAILABLE:
        return None

    txs = FinancialTransaction.query.filter(
        FinancialTransaction.company_id == company_id
    ).order_by(FinancialTransaction.date.desc()).limit(200).all()

    if len(txs) < 15:
        return {"error": "Se necesitan al menos 15 transacciones"}

    amounts = np.array([[t.amount] for t in txs])
    scaler  = StandardScaler()
    scaled  = scaler.fit_transform(amounts)

    clf = IsolationForest(contamination=0.08, random_state=42)
    predictions = clf.fit_predict(scaled)

    anomalies = []
    for t, pred in zip(txs, predictions):
        if pred == -1:
            anomalies.append({
                "id": t.id,
                "date": t.date.isoformat(),
                "type": t.transaction_type,
                "category": t.category,
                "description": t.description,
                "amount": t.amount,
            })

    # Stats
    avg_amount = float(np.mean([t.amount for t in txs]))
    std_amount = float(np.std([t.amount for t in txs]))

    return {
        "type": "anomaly_detection",
        "total_analyzed": len(txs),
        "anomalies_found": len(anomalies),
        "anomaly_rate": round(len(anomalies) / len(txs) * 100, 1),
        "avg_amount": round(avg_amount, 2),
        "std_amount": round(std_amount, 2),
        "anomalies": anomalies[:10],  # máximo 10 en detalle
        "confidence": 85,
    }


def forecast_demand(company_id):
    """Pronóstico de demanda por categoría de producto."""
    if not ML_AVAILABLE:
        return None

    # Ventas por categoría en últimos 60 días
    from models import SaleItem
    since = datetime.now() - timedelta(days=60)

    sales = db.session.query(
        Product.category,
        func.sum(SaleItem.quantity),
        func.sum(SaleItem.subtotal)
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(SalesOrder, SalesOrder.id == SaleItem.order_id)\
     .filter(Product.company_id == company_id,
             SalesOrder.created_at >= since)\
     .group_by(Product.category).all()

    if not sales:
        return {"error": "Sin datos de ventas por categoría"}

    forecast = []
    for cat, qty, rev in sales:
        daily_qty = float(qty or 0) / 60
        daily_rev = float(rev or 0) / 60
        forecast.append({
            "category":        cat,
            "daily_qty":       round(daily_qty, 1),
            "forecast_30d_qty":round(daily_qty * 30, 0),
            "daily_rev":       round(daily_rev, 2),
            "forecast_30d_rev":round(daily_rev * 30, 2),
        })

    forecast.sort(key=lambda x: x["forecast_30d_rev"], reverse=True)

    return {
        "type": "demand_forecast",
        "period_days": 30,
        "forecast": forecast,
        "confidence": 75,
        "note": "Basado en promedio móvil de 60 días"
    }


def inventory_optimization(company_id):
    """Optimización de inventario: EOQ y puntos de reorden."""
    products = Product.query.filter_by(company_id=company_id, active=True).all()
    if not products:
        return {"error": "Sin productos"}

    results = []
    for p in products:
        # EOQ simplificado: sqrt(2 * D * S / H)
        # D = demanda anual estimada (stock actual * 12 turnover factor)
        D = max(p.stock * 4, 10)        # Demanda anual estimada
        S = p.cost * 0.05               # Costo de ordenar (5% del costo)
        H = p.cost * 0.20               # Costo de mantener (20% del valor)
        eoq = math.sqrt(2 * D * S / H) if H > 0 else p.min_stock

        # Punto de reorden
        lead_time_days = 7
        daily_demand   = D / 365
        reorder_point  = daily_demand * lead_time_days + p.min_stock

        status = p.stock_status
        recommendation = "OK"
        if status == "out":   recommendation = "⚠️ REORDENAR URGENTE"
        elif status == "low": recommendation = "🔄 Reabastecer pronto"
        elif status == "over":recommendation = "📦 Stock excesivo"

        results.append({
            "product": p.name,
            "category": p.category,
            "stock": p.stock,
            "min_stock": p.min_stock,
            "eoq": round(eoq, 0),
            "reorder_point": round(reorder_point, 0),
            "status": status,
            "recommendation": recommendation,
            "stock_value": p.stock_value,
        })

    # Resumen
    urgent = sum(1 for r in results if "URGENTE" in r["recommendation"])
    reorder = sum(1 for r in results if "Reabastecer" in r["recommendation"])

    return {
        "type": "inventory_optimization",
        "total_products": len(results),
        "urgent": urgent,
        "to_reorder": reorder,
        "results": results[:20],  # top 20
        "confidence": 80,
    }


def oee_prediction(company_id):
    """Tendencia y predicción del OEE."""
    if not ML_AVAILABLE:
        return None

    since = date.today() - timedelta(days=30)
    metrics = MachineMetric.query.filter(
        MachineMetric.company_id == company_id,
        MachineMetric.record_date >= since
    ).order_by(MachineMetric.record_date).all()

    if len(metrics) < 10:
        return {"error": "Se necesitan al menos 10 registros OEE"}

    # Por máquina
    machines = list(set(m.machine_name for m in metrics))
    machine_trends = {}

    for mach in machines:
        data = [m for m in metrics if m.machine_name == mach]
        if len(data) < 5: continue
        X  = np.arange(len(data)).reshape(-1, 1)
        y  = np.array([m.oee for m in data])
        lr = LinearRegression().fit(X, y)
        trend = float(lr.coef_[0])
        current_oee = float(y[-1])
        predicted_oee = float(lr.predict([[len(data) + 7]])[0])  # 7 días futuro

        machine_trends[mach] = {
            "current_oee":   round(current_oee, 1),
            "predicted_oee": round(max(0, min(100, predicted_oee)), 1),
            "trend":         round(trend, 3),
            "trend_text":    "Mejorando ↑" if trend > 0 else "Decline ↓",
            "status":        "good" if current_oee >= 85 else ("medium" if current_oee >= 70 else "poor"),
        }

    avg_oee = round(sum(m.oee for m in metrics) / len(metrics), 1)

    return {
        "type": "oee_prediction",
        "avg_oee": avg_oee,
        "machine_trends": machine_trends,
        "world_class_oee": 85.0,
        "gap": round(85.0 - avg_oee, 1),
        "confidence": 78,
    }


# ══════════════════════════════════════════════════════════════
# RUTAS
# ══════════════════════════════════════════════════════════════

@ai_bp.route("/ai")
@login_required
def index():
    company_id = cid()
    results    = {}

    results["sales"]     = predict_sales_30(company_id)
    results["anomalies"] = detect_financial_anomalies(company_id)
    results["demand"]    = forecast_demand(company_id)
    results["inventory"] = inventory_optimization(company_id)
    results["oee"]       = oee_prediction(company_id)

    # Save prediction record
    pred = AIPrediction(
        company_id      = company_id,
        prediction_type = "full_analysis",
        input_summary   = f"Análisis completo - {date.today().isoformat()}",
        output_json     = json.dumps({"modules": list(results.keys())}),
        confidence      = 80
    )
    db.session.add(pred)
    try: db.session.commit()
    except: db.session.rollback()

    return render_template("ai/index.html",
                           results=results,
                           ml_available=ML_AVAILABLE,
                           results_json=json.dumps(results, default=str))


@ai_bp.route("/ai/api/sales")
@login_required
def api_sales():
    r = predict_sales_30(cid())
    return jsonify(r or {"error": "Sin datos"})


@ai_bp.route("/ai/api/anomalies")
@login_required
def api_anomalies():
    r = detect_financial_anomalies(cid())
    return jsonify(r or {"error": "Sin datos"})
