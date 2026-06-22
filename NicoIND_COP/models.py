"""
NicoIND — models.py
Todos los modelos de base de datos y función de sembrado de datos demo.
Autor: Nicolás Rodríguez
"""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from datetime import datetime, date, timedelta
import random, json, math

db      = SQLAlchemy()
bcrypt  = Bcrypt()

# ══════════════════════════════════════════════════════════════
# MODELOS
# ══════════════════════════════════════════════════════════════

class Company(db.Model):
    """Empresa (multi-tenant)."""
    __tablename__ = "companies"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), nullable=False)
    ruc        = db.Column(db.String(30))
    address    = db.Column(db.String(250))
    phone      = db.Column(db.String(30))
    email      = db.Column(db.String(120))
    industry   = db.Column(db.String(100))
    active     = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users      = db.relationship("User",       backref="company", lazy="dynamic")
    products   = db.relationship("Product",    backref="company", lazy="dynamic")


class User(db.Model, UserMixin):
    """Usuario del sistema con RBAC."""
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    company_id    = db.Column(db.Integer, db.ForeignKey("companies.id"))
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name     = db.Column(db.String(150))
    role          = db.Column(db.String(30), default="analyst")
    is_active     = db.Column(db.Boolean, default=True)
    avatar        = db.Column(db.String(200))
    last_login    = db.Column(db.DateTime)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    # role: superadmin | admin | manager | analyst | operator | viewer

    def set_password(self, pwd):  self.password_hash = bcrypt.generate_password_hash(pwd).decode()
    def check_password(self, pwd): return bcrypt.check_password_hash(self.password_hash, pwd)

    @property
    def initials(self):
        parts = (self.full_name or self.username).split()
        return "".join(p[0].upper() for p in parts[:2])


class Product(db.Model):
    """Producto / artículo de inventario."""
    __tablename__ = "products"
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey("companies.id"))
    code        = db.Column(db.String(50))
    name        = db.Column(db.String(200), nullable=False)
    category    = db.Column(db.String(100))
    unit        = db.Column(db.String(30), default="unidad")
    stock       = db.Column(db.Float, default=0)
    min_stock   = db.Column(db.Float, default=10)
    max_stock   = db.Column(db.Float, default=500)
    cost        = db.Column(db.Float, default=0)
    price       = db.Column(db.Float, default=0)
    supplier    = db.Column(db.String(150))
    location    = db.Column(db.String(100))
    active      = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    movements   = db.relationship("StockMovement", backref="product", lazy="dynamic")
    sale_items  = db.relationship("SaleItem",       backref="product", lazy="dynamic")

    @property
    def stock_value(self): return round(self.stock * self.cost, 2)
    @property
    def stock_status(self):
        if self.stock <= 0:         return "out"
        if self.stock <= self.min_stock: return "low"
        if self.stock >= self.max_stock: return "over"
        return "ok"
    @property
    def margin(self):
        if self.cost > 0: return round((self.price - self.cost) / self.cost * 100, 1)
        return 0


class StockMovement(db.Model):
    """Entrada / salida de inventario."""
    __tablename__ = "stock_movements"
    id             = db.Column(db.Integer, primary_key=True)
    product_id     = db.Column(db.Integer, db.ForeignKey("products.id"))
    company_id     = db.Column(db.Integer, db.ForeignKey("companies.id"))
    movement_type  = db.Column(db.String(20))   # in | out | adjustment
    quantity       = db.Column(db.Float, default=0)
    unit_cost      = db.Column(db.Float, default=0)
    reference      = db.Column(db.String(100))
    notes          = db.Column(db.Text)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


class SalesOrder(db.Model):
    """Pedido / venta."""
    __tablename__ = "sales_orders"
    id           = db.Column(db.Integer, primary_key=True)
    company_id   = db.Column(db.Integer, db.ForeignKey("companies.id"))
    order_number = db.Column(db.String(30))
    customer     = db.Column(db.String(150))
    total        = db.Column(db.Float, default=0)
    status       = db.Column(db.String(20), default="confirmed")
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    items        = db.relationship("SaleItem", backref="order", lazy="dynamic")


class SaleItem(db.Model):
    """Línea de pedido."""
    __tablename__ = "sale_items"
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey("sales_orders.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    quantity   = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, default=0)
    subtotal   = db.Column(db.Float, default=0)


class FinancialTransaction(db.Model):
    """Transacción financiera (ingresos y gastos)."""
    __tablename__ = "financial_transactions"
    id               = db.Column(db.Integer, primary_key=True)
    company_id       = db.Column(db.Integer, db.ForeignKey("companies.id"))
    transaction_type = db.Column(db.String(20))   # income | expense
    category         = db.Column(db.String(100))
    description      = db.Column(db.String(300))
    amount           = db.Column(db.Float, default=0)
    date             = db.Column(db.Date, default=date.today)
    reference        = db.Column(db.String(100))
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)


class Department(db.Model):
    """Departamento organizacional."""
    __tablename__ = "departments"
    id            = db.Column(db.Integer, primary_key=True)
    company_id    = db.Column(db.Integer, db.ForeignKey("companies.id"))
    name          = db.Column(db.String(100), nullable=False)
    manager_name  = db.Column(db.String(150))
    budget        = db.Column(db.Float, default=0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    employees     = db.relationship("Employee", backref="department", lazy="dynamic")


class Employee(db.Model):
    """Empleado (RRHH)."""
    __tablename__ = "employees"
    id            = db.Column(db.Integer, primary_key=True)
    company_id    = db.Column(db.Integer, db.ForeignKey("companies.id"))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    code          = db.Column(db.String(30))
    full_name     = db.Column(db.String(150), nullable=False)
    position      = db.Column(db.String(100))
    salary        = db.Column(db.Float, default=0)
    hire_date     = db.Column(db.Date)
    status        = db.Column(db.String(20), default="active")   # active | inactive | leave
    email         = db.Column(db.String(120))
    phone         = db.Column(db.String(30))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


class Project(db.Model):
    """Proyecto."""
    __tablename__ = "projects"
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey("companies.id"))
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status      = db.Column(db.String(20), default="planning")
    priority    = db.Column(db.String(20), default="medium")
    start_date  = db.Column(db.Date)
    end_date    = db.Column(db.Date)
    budget      = db.Column(db.Float, default=0)
    progress    = db.Column(db.Integer, default=0)
    manager_id  = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    tasks       = db.relationship("ProjectTask", backref="project", lazy="dynamic")


class ProjectTask(db.Model):
    """Tarea dentro de un proyecto."""
    __tablename__ = "project_tasks"
    id          = db.Column(db.Integer, primary_key=True)
    project_id  = db.Column(db.Integer, db.ForeignKey("projects.id"))
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status      = db.Column(db.String(20), default="todo")   # todo | in_progress | review | done
    priority    = db.Column(db.String(20), default="medium")
    assigned_to = db.Column(db.String(100))
    due_date    = db.Column(db.Date)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class MachineMetric(db.Model):
    """Métricas OEE de máquinas (Ingeniería Industrial)."""
    __tablename__ = "machine_metrics"
    id                 = db.Column(db.Integer, primary_key=True)
    company_id         = db.Column(db.Integer, db.ForeignKey("companies.id"))
    machine_name       = db.Column(db.String(100))
    record_date        = db.Column(db.Date, default=date.today)
    availability       = db.Column(db.Float, default=0)   # 0-100 %
    performance        = db.Column(db.Float, default=0)
    quality            = db.Column(db.Float, default=0)
    oee                = db.Column(db.Float, default=0)
    production_units   = db.Column(db.Integer, default=0)
    defect_units       = db.Column(db.Integer, default=0)
    downtime_minutes   = db.Column(db.Integer, default=0)
    shift              = db.Column(db.String(20), default="day")
    notes              = db.Column(db.Text)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    """Registro de auditoría."""
    __tablename__ = "audit_logs"
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey("companies.id"))
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    action      = db.Column(db.String(50))   # CREATE | UPDATE | DELETE | LOGIN | LOGOUT
    module      = db.Column(db.String(50))
    description = db.Column(db.String(400))
    ip_address  = db.Column(db.String(50))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user        = db.relationship("User", foreign_keys=[user_id])


class AIPrediction(db.Model):
    """Resultado de predicción de IA."""
    __tablename__ = "ai_predictions"
    id              = db.Column(db.Integer, primary_key=True)
    company_id      = db.Column(db.Integer, db.ForeignKey("companies.id"))
    prediction_type = db.Column(db.String(50))
    input_summary   = db.Column(db.Text)
    output_json     = db.Column(db.Text)
    confidence      = db.Column(db.Float, default=0)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def output(self):
        try:   return json.loads(self.output_json) if self.output_json else {}
        except: return {}


# ══════════════════════════════════════════════════════════════
# SIEMBRA DE DATOS DEMO
# ══════════════════════════════════════════════════════════════

PRODUCT_DATA = [
    ("Motor Eléctrico 5HP",   "Maquinaria",    "unidad",  850, 1200, "ElecMotors SA"),
    ("Rodamiento 6205",       "Componentes",   "unidad",   12,   25, "SKF Perú"),
    ("Cable AWG 12 (m)",      "Materiales",    "metro",     3,    8, "Indeco"),
    ("Contactor 40A",         "Eléctrico",     "unidad",   95,  155, "Siemens"),
    ("Sensor de proximidad",  "Automatización","unidad",   75,  130, "Pepperl+Fuchs"),
    ("Compresor 50L",         "Neumática",     "unidad",  420,  650, "Atlas Copco"),
    ("Válvula solenoide 1/2\"","Neumática",    "unidad",   55,   90, "Festo"),
    ("Tornillo M10x50 (100u)","Fijaciones",    "caja",     18,   32, "Fastenall"),
    ("Aceite hidráulico 20L", "Lubricantes",   "galón",    65,   95, "Shell"),
    ("Filtro de aire 2\"",    "Neumática",     "unidad",   28,   48, "Parker"),
    ("PLC Siemens S7-1200",   "Automatización","unidad", 1800, 2600, "Siemens"),
    ("Variador de frecuencia 5HP","Eléctrico", "unidad",  750, 1100, "ABB"),
    ("Cinta transportadora 2m","Maquinaria",   "unidad",  320,  490, "Intralox"),
    ("Interruptor termo 32A", "Eléctrico",     "unidad",   45,   80, "Schneider"),
    ("Manguera neumática 8mm","Neumática",     "metro",     5,   10, "Festo"),
    ("Grasa industrial 1kg",  "Lubricantes",   "unidad",   22,   38, "Mobil"),
    ("Encoder 1000ppr",       "Automatización","unidad",  210,  320, "Sick"),
    ("Correa trapezoidal A48","Transmisión",   "unidad",   35,   58, "Gates"),
    ("Panel eléctrico 60x80", "Eléctrico",     "unidad",  180,  280, "Rittal"),
    ("Martillo neumático",    "Herramientas",  "unidad",  140,  220, "Atlas Copco"),
    ("Soldadora MIG 250A",    "Herramientas",  "unidad",  890, 1250, "Lincoln Electric"),
    ("Esmeril angular 4.5\"", "Herramientas",  "unidad",  120,  185, "Bosch"),
    ("Taladro percutor 800W", "Herramientas",  "unidad",  210,  320, "DeWalt"),
    ("Calibrador digital 150mm","Medición",    "unidad",   55,   88, "Mitutoyo"),
    ("Micrómetro 0-25mm",     "Medición",      "unidad",   95,  150, "Mitutoyo"),
    ("Nivel de precisión",    "Medición",      "unidad",   75,  120, "Stanley"),
    ("Resina epoxi 1kg",      "Adhesivos",     "unidad",   48,   80, "Loctite"),
    ("Pintura anticorrosión", "Recubrimientos","litro",    35,   58, "Tekno"),
    ("Disco de corte 4.5\"",  "Consumibles",   "unidad",    8,   14, "Norton"),
    ("Broca HSS 10mm",        "Consumibles",   "unidad",   12,   20, "Sandvik"),
]

CUSTOMERS = ["Industrias Alfa SA","Metalúrgica Beta","Constructora Gamma","Minera Delta",
             "Textil Epsilon","Agroindustrial Zeta","Farmacéutica Eta","Automotriz Theta",
             "Electrónica Iota","Plásticos Kappa","Calzados Lambda","Químicos Mu"]

EMPLOYEES_DATA = [
    ("Gerencia",         "Director General",      9500),
    ("Gerencia",         "Gerente de Operaciones", 7200),
    ("Producción",       "Jefe de Producción",    5500),
    ("Producción",       "Técnico de Mantenimiento",3200),
    ("Producción",       "Operario CNC",          2800),
    ("Producción",       "Operario de Ensamble",  2600),
    ("Producción",       "Control de Calidad",    3000),
    ("Logística",        "Jefe de Almacén",       4200),
    ("Logística",        "Asistente Logístico",   2400),
    ("Finanzas",         "Contador General",      5800),
    ("Finanzas",         "Analista Financiero",   3800),
    ("RRHH",             "Jefe de RRHH",          4800),
    ("RRHH",             "Asistente RRHH",        2500),
    ("Ventas",           "Gerente Comercial",     6200),
    ("Ventas",           "Ejecutivo de Ventas",   3500),
    ("Ventas",           "Asistente Ventas",      2400),
    ("TI",               "Analista de Sistemas",  4500),
    ("TI",               "Soporte Técnico",       2800),
    ("Ingeniería",       "Ingeniero de Proyectos",5200),
    ("Ingeniería",       "Dibujante CAD",         3000),
]

NAMES = ["Carlos Mendoza","Ana García","Luis Torres","María López","Jorge Ramírez",
         "Patricia Silva","Roberto Castro","Claudia Vargas","Fernando Díaz","Sonia Herrera",
         "Eduardo Morales","Valentina Ruiz","Ricardo Peña","Natalia Flores","Miguel Ángel Soto",
         "Daniela Ortiz","Andrés Jiménez","Fernanda Romero","Sebastián Cruz","Alejandra Reyes"]


def seed_demo_data():
    """Crea datos demo completos si la base de datos está vacía."""
    if Company.query.count() > 0:
        return

    rng = random.Random(42)

    # ── Empresas ──────────────────────────────────────────
    c1 = Company(name="Demo Corp S.A.", ruc="20512345678",
                 address="Av. Industrial 1234, Lima", phone="01-234-5678",
                 email="info@democorp.pe", industry="Manufactura")
    c2 = Company(name="Tech Industrial SRL", ruc="20587654321",
                 address="Jr. Tecnología 567, Lima", phone="01-987-6543",
                 email="info@techind.pe", industry="Automatización")
    db.session.add_all([c1, c2])
    db.session.flush()

    # ── Usuarios ──────────────────────────────────────────
    def make_user(username, email, name, role, company, pwd="12345"):
        u = User(company_id=company.id, username=username, email=email,
                 full_name=name, role=role)
        u.set_password(pwd)
        return u

    users = [
        make_user("superadmin", "super@nicond.io",       "Nicolás Rodríguez", "superadmin", c1),
        make_user("admin",      "admin@democorp.pe",     "Carlos Mendoza",    "admin",      c1),
        make_user("manager",    "manager@democorp.pe",   "Ana García",        "manager",    c1),
        make_user("analista",   "analista@democorp.pe",  "Luis Torres",       "analyst",    c1),
        make_user("admin2",     "admin@techind.pe",      "María López",       "admin",      c2),
    ]
    db.session.add_all(users)
    db.session.flush()
    adm1 = users[1]

    # ── Departamentos ─────────────────────────────────────
    dept_names = ["Gerencia","Producción","Logística","Finanzas","RRHH","Ventas","TI","Ingeniería"]
    depts = {}
    for i, dname in enumerate(dept_names):
        d = Department(company_id=c1.id, name=dname,
                       manager_name=NAMES[i % len(NAMES)],
                       budget=rng.uniform(50000, 200000))
        db.session.add(d)
        db.session.flush()
        depts[dname] = d

    # ── Empleados ─────────────────────────────────────────
    for i, (dept, pos, sal) in enumerate(EMPLOYEES_DATA):
        emp = Employee(
            company_id   = c1.id,
            department_id= depts[dept].id,
            code         = f"EMP{i+1:04d}",
            full_name    = NAMES[i % len(NAMES)],
            position     = pos,
            salary       = sal + rng.uniform(-200, 200),
            hire_date    = date.today() - timedelta(days=rng.randint(30, 2000)),
            status       = "active",
            email        = f"emp{i+1}@democorp.pe",
            phone        = f"9{rng.randint(10000000,99999999)}"
        )
        db.session.add(emp)

    # ── Productos ─────────────────────────────────────────
    products = []
    for i, (name, cat, unit, cost, price, supp) in enumerate(PRODUCT_DATA):
        stk = rng.uniform(5, 300)
        p = Product(
            company_id = c1.id,
            code       = f"PRD{i+1:04d}",
            name       = name, category=cat, unit=unit,
            stock      = round(stk, 1),
            min_stock  = 10, max_stock=500,
            cost       = cost + rng.uniform(-10, 10),
            price      = price + rng.uniform(-15, 15),
            supplier   = supp,
            location   = f"A{rng.randint(1,5)}-{rng.randint(1,20):02d}"
        )
        db.session.add(p)
        products.append(p)
    db.session.flush()

    # ── Ventas (90 días) ──────────────────────────────────
    base_date = datetime.utcnow()
    order_num = 1
    for days_ago in range(90, 0, -1):
        n_orders = rng.randint(1, 4)
        order_date = base_date - timedelta(days=days_ago)
        for _ in range(n_orders):
            n_items = rng.randint(1, 4)
            order = SalesOrder(
                company_id   = c1.id,
                order_number = f"OC-{order_num:05d}",
                customer     = rng.choice(CUSTOMERS),
                status       = rng.choices(["confirmed","delivered","pending"],
                                           weights=[0.5,0.4,0.1])[0],
                user_id      = adm1.id,
                created_at   = order_date,
                total        = 0
            )
            db.session.add(order)
            db.session.flush()
            total = 0
            for _ in range(n_items):
                prod = rng.choice(products)
                qty  = rng.randint(1, 10)
                item = SaleItem(order_id=order.id, product_id=prod.id,
                                quantity=qty, unit_price=prod.price,
                                subtotal=qty * prod.price)
                total += item.subtotal
                db.session.add(item)
            order.total = round(total, 2)
            order_num += 1

    # ── Transacciones Financieras (90 días) ───────────────
    income_cats  = ["Ventas Producto","Servicios","Comisiones","Otros Ingresos"]
    expense_cats = ["Sueldos","Servicios Básicos","Alquiler","Materiales",
                    "Marketing","Transporte","Mantenimiento","Impuestos","Otros"]
    for days_ago in range(90, 0, -1):
        tx_date = (base_date - timedelta(days=days_ago)).date()
        # Income
        for _ in range(rng.randint(1, 3)):
            ft = FinancialTransaction(
                company_id=c1.id, transaction_type="income",
                category=rng.choice(income_cats),
                description=f"Ingreso {rng.choice(CUSTOMERS)}",
                amount=round(rng.uniform(500, 8000), 2),
                date=tx_date, user_id=adm1.id)
            db.session.add(ft)
        # Expense
        for _ in range(rng.randint(1, 2)):
            ft = FinancialTransaction(
                company_id=c1.id, transaction_type="expense",
                category=rng.choice(expense_cats),
                description=f"Gasto operacional",
                amount=round(rng.uniform(100, 3500), 2),
                date=tx_date, user_id=adm1.id)
            db.session.add(ft)

    # ── Proyectos ─────────────────────────────────────────
    proj_data = [
        ("Automatización Línea 1", "active",   "high",   75, 85000),
        ("Implementación ERP",     "active",   "high",   40, 120000),
        ("Certificación ISO 9001", "active",   "medium", 60, 35000),
        ("Modernización Almacén",  "planning", "medium", 10, 55000),
        ("Proyecto Solar 50kW",    "planning", "low",     5, 95000),
        ("Mejora Layout Planta",   "completed","medium",100, 28000),
        ("Sistema CCTV",           "completed","low",    100, 18000),
        ("Mantenimiento Predictivo","on_hold",  "high",   25, 42000),
    ]
    proj_prios = ["high","high","medium","medium","low"]
    projs = []
    for i, (name, status, prio, prog, bud) in enumerate(proj_data):
        sd = date.today() - timedelta(days=rng.randint(10, 180))
        p = Project(
            company_id=c1.id, name=name, description=f"Descripción del proyecto: {name}",
            status=status, priority=prio, start_date=sd,
            end_date=sd + timedelta(days=rng.randint(60,365)),
            budget=bud, progress=prog, manager_id=adm1.id)
        db.session.add(p)
        projs.append(p)
    db.session.flush()

    task_titles = ["Análisis de requerimientos","Diseño técnico","Adquisición de equipos",
                   "Instalación","Pruebas y comisionado","Capacitación personal",
                   "Documentación","Cierre del proyecto"]
    task_statuses = ["todo","in_progress","review","done"]
    for proj in projs:
        for i, tt in enumerate(rng.sample(task_titles, rng.randint(4,7))):
            t = ProjectTask(
                project_id=proj.id, title=tt,
                status=rng.choice(task_statuses),
                priority=rng.choice(["low","medium","high"]),
                assigned_to=rng.choice(NAMES),
                due_date=date.today() + timedelta(days=rng.randint(-10, 60)))
            db.session.add(t)

    # ── Métricas OEE (30 días, 3 máquinas) ───────────────
    machines = ["Torno CNC-01","Fresadora CNC-02","Prensa Hidráulica-03"]
    for days_ago in range(30, 0, -1):
        mdate = (base_date - timedelta(days=days_ago)).date()
        for mach in machines:
            avail = rng.uniform(78, 98)
            perf  = rng.uniform(72, 95)
            qual  = rng.uniform(90, 99)
            oee   = round(avail * perf * qual / 10000, 2)
            mm = MachineMetric(
                company_id=c1.id, machine_name=mach, record_date=mdate,
                availability=round(avail,2), performance=round(perf,2),
                quality=round(qual,2), oee=oee,
                production_units=rng.randint(200,600),
                defect_units=rng.randint(0,15),
                downtime_minutes=rng.randint(0,90))
            db.session.add(mm)

    db.session.commit()
    print("✅ Datos demo creados. Usuarios: superadmin/12345, admin/12345, analista/12345")
