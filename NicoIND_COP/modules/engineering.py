"""
NicoIND — modules/engineering.py
Ingeniería Industrial: OEE, métricas de máquinas, productividad.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date, timedelta
from models import db, MachineMetric, AuditLog
import json

engineering_bp = Blueprint("engineering", __name__)

def cid(): return current_user.company_id


@engineering_bp.route("/engineering")
@login_required
def index():
    days  = int(request.args.get("days", 30))
    mach  = request.args.get("machine","all")
    since = date.today() - timedelta(days=days)

    q = MachineMetric.query.filter(
        MachineMetric.company_id == cid(),
        MachineMetric.record_date >= since)
    if mach != "all": q = q.filter_by(machine_name=mach)
    metrics = q.order_by(MachineMetric.record_date.desc()).all()

    machines = [r[0] for r in db.session.query(MachineMetric.machine_name).filter_by(
        company_id=cid()).distinct().all()]

    # Averages per machine
    machine_stats = {}
    for m in machines:
        subset = [x for x in metrics if x.machine_name == m]
        if subset:
            machine_stats[m] = {
                "oee":       round(sum(x.oee for x in subset) / len(subset), 1),
                "avail":     round(sum(x.availability for x in subset) / len(subset), 1),
                "perf":      round(sum(x.performance for x in subset) / len(subset), 1),
                "qual":      round(sum(x.quality for x in subset) / len(subset), 1),
                "prod":      sum(x.production_units for x in subset),
                "defects":   sum(x.defect_units for x in subset),
                "downtime":  sum(x.downtime_minutes for x in subset),
            }

    # Chart: OEE trend
    chart_data = {}
    for x in metrics:
        ds = x.record_date.strftime("%d/%m")
        if ds not in chart_data: chart_data[ds] = {}
        chart_data[ds][x.machine_name] = x.oee
    chart_list = [{"date": k, **v} for k, v in sorted(chart_data.items())]

    overall_oee = round(sum(x.oee for x in metrics) / len(metrics), 1) if metrics else 0

    return render_template("engineering/index.html",
        metrics=metrics[:50], machine_stats=machine_stats,
        machines=machines, overall_oee=overall_oee,
        chart_data=json.dumps(chart_list),
        days=days, mach=mach)


@engineering_bp.route("/engineering/add", methods=["POST"])
@login_required
def add_metric():
    avail = float(request.form.get("availability",0) or 0)
    perf  = float(request.form.get("performance",0)  or 0)
    qual  = float(request.form.get("quality",0)      or 0)
    oee   = round(avail * perf * qual / 10000, 2)
    rd    = request.form.get("record_date","")

    mm = MachineMetric(
        company_id      = cid(),
        machine_name    = request.form.get("machine_name","").strip(),
        record_date     = date.fromisoformat(rd) if rd else date.today(),
        availability    = avail, performance=perf, quality=qual, oee=oee,
        production_units= int(request.form.get("production_units",0) or 0),
        defect_units    = int(request.form.get("defect_units",0)     or 0),
        downtime_minutes= int(request.form.get("downtime_minutes",0) or 0),
        shift           = request.form.get("shift","day"),
        notes           = request.form.get("notes",""))
    db.session.add(mm)
    db.session.add(AuditLog(company_id=cid(), user_id=current_user.id,
                             action="CREATE", module="engineering",
                             description=f"Métrica OEE: {mm.machine_name} OEE={oee}%",
                             ip_address=request.remote_addr))
    db.session.commit()
    flash(f"Métrica OEE registrada. OEE calculado: {oee}%", "success")
    return redirect(url_for("engineering.index"))
