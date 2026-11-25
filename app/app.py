"""Northvale University - Information & Announcements Portal.

A small Flask application backed by PostgreSQL. The same code runs in:
  * Environment 1: Docker containers inside an Ubuntu VirtualBox VM (IaaS-style)
  * Environment 2: Render web service + Render PostgreSQL (PaaS)

All configuration comes from environment variables (12-factor style):
  DATABASE_URL    postgresql://user:password@host:5432/dbname   (required)
  SECRET_KEY      random string used to sign the session cookie
  ADMIN_USERNAME  administrator login
  ADMIN_PASSWORD  administrator password
  APP_ENV         label shown in the footer (e.g. "Docker on Ubuntu VM", "Render")
"""
import hmac
import os
import socket
import time
from functools import wraps
from pathlib import Path

import psycopg
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from psycopg.rows import dict_row

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or "admin123"  # demo default
APP_ENV = os.environ.get("APP_ENV", "local")
SCHEMA_FILE = Path(__file__).with_name("schema.sql")


# --------------------------------------------------------------------------- #
# Database helpers
# --------------------------------------------------------------------------- #
def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db(retries: int = 30, delay: float = 2.0) -> None:
    """Create tables and sample data. Retries while the DB container starts."""
    for attempt in range(1, retries + 1):
        try:
            with get_conn() as conn:
                conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
            print(f"[init_db] schema ready (attempt {attempt})", flush=True)
            return
        except psycopg.OperationalError as exc:
            print(f"[init_db] database not ready ({exc.__class__.__name__}), "
                  f"retry {attempt}/{retries}", flush=True)
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database")


def query(sql, params=None, one=False):
    with get_conn() as conn:
        cur = conn.execute(sql, params or ())
        rows = cur.fetchall() if cur.description else None
    if rows is None:
        return None
    return rows[0] if (one and rows) else (None if one else rows)


# --------------------------------------------------------------------------- #
# Authentication (basic session-based login for the administrator)
# --------------------------------------------------------------------------- #
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please log in as administrator.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {
        "app_env": APP_ENV,
        "server_host": socket.gethostname(),
        "is_admin": session.get("is_admin", False),
    }


# --------------------------------------------------------------------------- #
# Public pages
# --------------------------------------------------------------------------- #
@app.route("/")
def home():
    recent = query("""
        SELECT a.id, a.title, a.body, a.published_at, d.name AS department
        FROM announcements a LEFT JOIN departments d ON d.id = a.department_id
        ORDER BY a.published_at DESC LIMIT 3""")
    stats = query("""SELECT (SELECT COUNT(*) FROM departments)   AS departments,
                            (SELECT COUNT(*) FROM announcements) AS announcements""",
                  one=True)
    return render_template("home.html", recent=recent, stats=stats)


@app.route("/departments")
def departments():
    rows = query("""
        SELECT d.*, COUNT(a.id) AS announcement_count
        FROM departments d LEFT JOIN announcements a ON a.department_id = d.id
        GROUP BY d.id ORDER BY d.name""")
    return render_template("departments.html", departments=rows)


@app.route("/announcements")
def announcements():
    rows = query("""
        SELECT a.id, a.title, a.body, a.published_at, a.updated_at,
               d.name AS department
        FROM announcements a LEFT JOIN departments d ON d.id = a.department_id
        ORDER BY a.published_at DESC""")
    return render_template("announcements.html", announcements=rows)


@app.route("/health")
def health():
    """Health check used by Docker and Render: verifies the DB is reachable."""
    try:
        query("SELECT 1")
        return {"status": "ok", "database": "reachable", "env": APP_ENV}, 200
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "database": str(exc.__class__.__name__)}, 503


# --------------------------------------------------------------------------- #
# Login / logout
# --------------------------------------------------------------------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and not ADMIN_PASSWORD:
        flash("Administration is disabled: ADMIN_PASSWORD is not configured.", "error")
    elif request.method == "POST":
        user_ok = hmac.compare_digest(request.form.get("username", ""), ADMIN_USERNAME)
        pass_ok = hmac.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD)
        if user_ok and pass_ok:
            session.clear()
            session["is_admin"] = True
            flash("Logged in as administrator.", "success")
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/admin") else url_for("admin"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("home"))


# --------------------------------------------------------------------------- #
# Administration (protected CRUD on announcements)
# --------------------------------------------------------------------------- #
def _form_values():
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    dept = request.form.get("department_id") or None
    return title, body, (int(dept) if dept else None)


@app.route("/admin")
@login_required
def admin():
    rows = query("""
        SELECT a.id, a.title, a.published_at, a.updated_at, d.name AS department
        FROM announcements a LEFT JOIN departments d ON d.id = a.department_id
        ORDER BY a.published_at DESC""")
    return render_template("admin.html", announcements=rows)


@app.route("/admin/new", methods=["GET", "POST"])
@login_required
def admin_new():
    if request.method == "POST":
        title, body, dept = _form_values()
        if not title or not body:
            flash("Title and content are required.", "error")
        else:
            query("INSERT INTO announcements (title, body, department_id) "
                  "VALUES (%s, %s, %s)", (title, body, dept))
            flash(f'Announcement "{title}" created.', "success")
            return redirect(url_for("admin"))
    depts = query("SELECT id, name FROM departments ORDER BY name")
    return render_template("announcement_form.html", item=None, departments=depts)


@app.route("/admin/<int:ann_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit(ann_id):
    item = query("SELECT * FROM announcements WHERE id = %s", (ann_id,), one=True)
    if item is None:
        abort(404)
    if request.method == "POST":
        title, body, dept = _form_values()
        if not title or not body:
            flash("Title and content are required.", "error")
        else:
            query("UPDATE announcements SET title=%s, body=%s, department_id=%s, "
                  "updated_at=NOW() WHERE id=%s", (title, body, dept, ann_id))
            flash(f'Announcement #{ann_id} updated.', "success")
            return redirect(url_for("admin"))
    depts = query("SELECT id, name FROM departments ORDER BY name")
    return render_template("announcement_form.html", item=item, departments=depts)


@app.route("/admin/<int:ann_id>/delete", methods=["POST"])
@login_required
def admin_delete(ann_id):
    query("DELETE FROM announcements WHERE id = %s", (ann_id,))
    flash(f"Announcement #{ann_id} deleted.", "success")
    return redirect(url_for("admin"))


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


# Create tables / sample data when the module is loaded (gunicorn --preload
# runs this once in the master process before the workers are forked).
if os.environ.get("SKIP_DB_INIT") != "1":
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
