# 🏭 NicoIND — Nicolás Industrial Intelligence Dashboard

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%20|%203.12%20|%203.13%20|%203.14-blue?style=flat-square&logo=python"/>
  <img src="https://img.shields.io/badge/Flask-3.0%2B-green?style=flat-square&logo=flask"/>
  <img src="https://img.shields.io/badge/scikit--learn-1.5%2B-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/PostgreSQL-Ready-336791?style=flat-square&logo=postgresql"/>
  <img src="https://img.shields.io/badge/Render-Deploy-46E3B7?style=flat-square"/>
</p>

> Plataforma ERP empresarial con IA para gestión industrial.
> Desarrollado por **Nicolás Rodríguez** — Portafolio profesional.

---

## 🚀 Instalación (Python 3.11 – 3.14)

```bash
# 1. Clonar
git clone https://github.com/tu-usuario/NicoIND.git
cd NicoIND

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias (sin Build Tools, sin compilación)
pip install -r requirements.txt

# 4. Ejecutar
python app.py
# → http://localhost:5000
```

> ✅ **Python 3.14 compatible.** Todos los paquetes usan wheels pre-compilados.
> No se requiere Visual Studio Build Tools ni compilador C.

---

## 👤 Usuarios demo

| Usuario | Contraseña | Rol |
|---|---|---|
| `superadmin` | `12345` | Super Admin |
| `admin` | `12345` | Administrador |
| `analista` | `12345` | Analista |

---

## ✨ Módulos

| Módulo | Descripción |
|---|---|
| 📊 **Dashboard Ejecutivo** | KPIs, ventas, OEE, proyectos |
| 📦 **Inventario** | CRUD completo, alertas de stock, movimientos |
| 💰 **Finanzas** | P&L, flujo de caja, análisis por categoría |
| 👥 **Recursos Humanos** | Empleados, departamentos, nómina |
| 📋 **Proyectos** | Kanban board, tareas, progreso |
| ⚙️ **Ingeniería Industrial** | OEE (Disp. × Rend. × Cal.) |
| 📈 **Business Intelligence** | Analytics cruzados 12 meses |
| 🤖 **IA Empresarial** | Predicción ventas, anomalías, EOQ |
| 📄 **Reportes** | PDF (ReportLab) + Excel (OpenPyXL) |
| 🔐 **Seguridad** | RBAC, auditoría completa |

---

## 🗄️ Base de datos

**Desarrollo (SQLite — automático):**
```
nicond.db  ←  se crea solo al iniciar
```

**Producción (PostgreSQL):**
```env
DATABASE_URL=postgresql://user:password@host:5432/nicond
```

---

## ☁️ Deploy en Render

1. Subir a GitHub
2. Nuevo **Web Service** en [render.com](https://render.com)
3. **Build:** `pip install -r requirements.txt`
4. **Start:** `gunicorn app:app --workers 2 --timeout 120`
5. Variables: `SECRET_KEY` + `DATABASE_URL` (PostgreSQL de Render)

---

## 📦 Dependencias (sin compilación)

```
Flask>=3.0.3          # pure Python
Flask-SQLAlchemy>=3.1.1  # pure Python
Flask-Login>=0.6.3    # pure Python
Flask-Bcrypt>=1.0.1   # binary wheel disponible
SQLAlchemy>=2.0.30    # pure Python
reportlab>=4.1.0      # wheel Python 3.14
openpyxl>=3.1.2       # pure Python
numpy>=2.0.0          # wheel Python 3.14
scikit-learn>=1.5.0   # wheel Python 3.14
psycopg2-binary>=2.9.9  # pre-compiled binary
gunicorn>=22.0.0      # pure Python
python-dotenv>=1.0.1  # pure Python
```

---

## 🏗️ Arquitectura

```
NicoIND/
├── app.py          ← python app.py
├── config.py
├── models.py       ← 14 modelos + datos demo
├── modules/        ← 11 blueprints Flask
├── static/         ← CSS dark theme + JS
├── templates/      ← 22 plantillas Jinja2
├── requirements.txt
├── runtime.txt     ← python-3.14.5
└── Procfile
```

---

**Nicolás Rodríguez** · Desarrollador & Ingeniero Industrial
