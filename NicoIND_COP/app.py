"""
╔══════════════════════════════════════════════════════════════╗
║   NicoIND — Nicolás Industrial Intelligence Dashboard        ║
║   Desarrollado por: Nicolás Rodríguez                        ║
║   Versión: 1.0.0                                             ║
║   Ejecutar: python app.py                                    ║
╚══════════════════════════════════════════════════════════════╝
"""
import os
from flask import Flask, render_template
from flask_login import LoginManager

from config   import Config
from models   import db, bcrypt, User, seed_demo_data

from modules.auth        import auth_bp
from modules.dashboard   import dashboard_bp
from modules.inventory   import inventory_bp
from modules.finance     import finance_bp
from modules.hr          import hr_bp
from modules.projects    import projects_bp
from modules.engineering import engineering_bp
from modules.bi          import bi_bp
from modules.reports     import reports_bp
from modules.ai_engine   import ai_bp
from modules.admin       import admin_bp


# ══════════════════════════════════════════════════════════════
# APP FACTORY
# ══════════════════════════════════════════════════════════════

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Extensiones ──────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)

    lm = LoginManager(app)
    lm.login_view         = "auth.login"
    lm.login_message      = "🔐 Inicia sesión para acceder a NicoIND."
    lm.login_message_category = "warning"

    @lm.user_loader
    def load_user(uid):
        return User.query.get(int(uid))

    # ── Blueprints ───────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(engineering_bp)
    app.register_blueprint(bi_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)

    # ── Error handlers ───────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/404.html", is_500=True), 500

    # ── DB + Datos demo ──────────────────────────────────────
    with app.app_context():
        db.create_all()
        seed_demo_data()

    return app


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════
app = create_app()

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") != "production"

    print("\n" + "═" * 54)
    print("  🏭  NicoIND — Industrial Intelligence Dashboard")
    print(f"  🌐  http://localhost:{port}")
    print("  ─" * 27)
    print("  👤  superadmin / 12345   (Super Administrador)")
    print("  👤  admin      / 12345   (Administrador)")
    print("  👤  analista   / 12345   (Analista)")
    print("═" * 54 + "\n")

    app.run(debug=debug, host="0.0.0.0", port=port)
