"""Tijarah Mabrur website + client portal (Flask + SQLite)."""
import io
import json
import os
import re
import uuid
from datetime import datetime
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   send_file, session, url_for)
from pypdf import PdfReader
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from database import execute, get_db, init_db, q
from pdf_utils import extract_acroform_fields, fill_pdf, validate_fields_json

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me-in-production-tijarah-2026")

UPLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads")
LOGO_DIR = os.path.join(UPLOAD_DIR, "logos")
MACHINERY_IMG_DIR = os.path.join(UPLOAD_DIR, "machinery")
REPORT_PDF_DIR = os.path.join(UPLOAD_DIR, "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOGO_DIR, exist_ok=True)
os.makedirs(MACHINERY_IMG_DIR, exist_ok=True)
os.makedirs(REPORT_PDF_DIR, exist_ok=True)

ALLOWED_LOGO_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB uploads

# SMTP config for email reminders (set via env vars)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@tijarahmabrur.com")


@app.template_filter("fromjson")
def fromjson_filter(s):
    try:
        return json.loads(s)
    except Exception:
        return []


CATEGORIES = ["Pressure Vessel", "Lifting Device", "Boiler", "Compressor", "Other"]
STATUSES = ["Active", "Under Maintenance", "Expired"]
REPORT_TYPES = ["Inspection", "Calibration", "Maintenance", "NDT"]
REPORT_STATUSES = ["Draft", "Submitted", "Approved"]
PER_PAGE = 25  # pagination size for large tenant datasets


# ---------------- auth helpers ----------------
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return q("SELECT * FROM users WHERE id = ?", (uid,), one=True)


@app.context_processor
def inject_globals():
    u = current_user()
    company = None
    if u and u["company_id"]:
        company = q("SELECT * FROM companies WHERE id = ?", (u["company_id"],), one=True)
    return {"user": u, "tenant_company": company}


def scope_clause(u, col="m.owner_id"):
    """Return (sql_fragment, params) limiting rows to what this user may see.
    Admins see everything; clients see their own + company-wide rows."""
    if u["role"] == "admin":
        return "1=1", ()
    if u["company_id"]:
        return f"({col} = ? OR m.company_id = ?)", (u["id"], u["company_id"])
    return f"{col} = ?", (u["id"],)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "warn")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u or u["role"] != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapper


# ---------------- public website ----------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------- auth ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        u = q("SELECT * FROM users WHERE email = ?", (email,), one=True)
        if u and check_password_hash(u["password_hash"], password):
            session["user_id"] = u["id"]
            flash("Welcome back, %s!" % u["name"], "ok")
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid email or password.", "err")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        company_name = request.form.get("company_name", "").strip()

        # Validation
        errors = []
        if not name:
            errors.append("Full name is required.")
        if not email:
            errors.append("Email is required.")
        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if not company_name:
            errors.append("Company name is required.")

        # Check if email already exists
        if email and q("SELECT id FROM users WHERE email = ?", (email,), one=True):
            errors.append("An account with this email already exists.")

        if errors:
            for e in errors:
                flash(e, "err")
            return render_template("register.html",
                                   name=name, email=email, company_name=company_name)

        # Create company
        now = datetime.utcnow().isoformat()
        execute("INSERT INTO companies (name, created_at) VALUES (?, ?)", (company_name, now))
        company = q("SELECT id FROM companies WHERE name = ?", (company_name,), one=True)
        company_id = company["id"]

        # Create user (client role)
        execute(
            "INSERT INTO users (name, email, password_hash, role, company, company_id, created_at) VALUES (?, ?, ?, 'client', ?, ?, ?)",
            (name, email, generate_password_hash(password), company_name, company_id, now),
        )

        flash("Account created! Please log in.", "ok")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "ok")
    return redirect(url_for("home"))


# ---------------- portal: dashboard ----------------
@app.route("/portal")
@login_required
def dashboard():
    u = current_user()
    if u["role"] == "admin":
        stats = {
            "machinery": q("SELECT COUNT(*) c FROM machinery", one=True)["c"],
            "clients": q("SELECT COUNT(*) c FROM users WHERE role='client'", one=True)["c"],
            "reports": q("SELECT COUNT(*) c FROM reports", one=True)["c"],
            "expiring": q("""SELECT COUNT(*) c FROM machinery
                            WHERE next_inspection != '' AND next_inspection <= date('now','+60 day')""", one=True)["c"],
        }
        recent_machinery = q("""SELECT m.*, u.company AS owner_company FROM machinery m
                                LEFT JOIN users u ON u.id = m.owner_id
                                ORDER BY m.created_at DESC LIMIT 5""")
        recent_reports = q("""SELECT r.*, m.name AS machinery_name FROM reports r
                              JOIN machinery m ON m.id = r.machinery_id
                              ORDER BY r.created_at DESC LIMIT 5""")
        upcoming = q("""SELECT m.*, u.company AS owner_company FROM machinery m
                        LEFT JOIN users u ON u.id = m.owner_id
                        WHERE m.next_inspection != '' ORDER BY m.next_inspection ASC LIMIT 5""")
    else:
        scope, params = scope_clause(u)
        stats = {
            "machinery": q(f"SELECT COUNT(*) c FROM machinery m WHERE {scope}", params, one=True)["c"],
            "reports": q(f"""SELECT COUNT(*) c FROM reports r JOIN machinery m ON m.id=r.machinery_id
                            WHERE {scope}""", params, one=True)["c"],
            "expiring": q(f"""SELECT COUNT(*) c FROM machinery m WHERE {scope}
                            AND m.next_inspection != '' AND m.next_inspection <= date('now','+60 day')""", params, one=True)["c"],
        }
        recent_machinery = q(f"""SELECT m.*, '' AS owner_company FROM machinery m
                                WHERE {scope} ORDER BY m.created_at DESC LIMIT 5""", params)
        recent_reports = q(f"""SELECT r.*, m.name AS machinery_name FROM reports r
                              JOIN machinery m ON m.id = r.machinery_id
                              WHERE {scope} ORDER BY r.created_at DESC LIMIT 5""", params)
        upcoming = q(f"""SELECT m.*, '' AS owner_company FROM machinery m
                        WHERE {scope} AND m.next_inspection != ''
                        ORDER BY m.next_inspection ASC LIMIT 5""", params)
    return render_template("portal/dashboard.html", stats=stats,
                           recent_machinery=recent_machinery,
                           recent_reports=recent_reports, upcoming=upcoming)


# ---------------- portal: machinery ----------------
@app.route("/portal/machinery")
@login_required
def machinery_list():
    u = current_user()
    search = request.args.get("q", "").strip()
    page = max(request.args.get("page", 1, type=int), 1)
    scope, params = scope_clause(u)
    where = scope
    args = list(params)
    if search:
        where += " AND (m.name LIKE ? OR m.serial_no LIKE ? OR m.cert_no LIKE ? OR m.location LIKE ?)"
        args += [f"%{search}%"] * 4
    total = q(f"SELECT COUNT(*) c FROM machinery m WHERE {where}", tuple(args), one=True)["c"]
    pages = max((total + PER_PAGE - 1) // PER_PAGE, 1)
    page = min(page, pages)
    rows = q(
        f"""SELECT m.*, u.company AS owner_company FROM machinery m
            LEFT JOIN users u ON u.id = m.owner_id
            WHERE {where} ORDER BY m.created_at DESC LIMIT ? OFFSET ?""",
        tuple(args) + (PER_PAGE, (page - 1) * PER_PAGE),
    )
    return render_template("portal/machinery_list.html", machinery=rows, search=search,
                           page=page, pages=pages, total=total)


@app.route("/portal/machinery/new", methods=["GET", "POST"])
@login_required
def machinery_new():
    u = current_user()
    owners = q("SELECT id, name, company FROM users WHERE role='client' ORDER BY company") if u["role"] == "admin" else []
    if request.method == "POST":
        f = request.form
        owner_id = f.get("owner_id") if u["role"] == "admin" else u["id"]
        company_id = None
        if owner_id:
            o = q("SELECT company_id FROM users WHERE id = ?", (owner_id,), one=True)
            company_id = o["company_id"] if o else None
        elif u["role"] != "admin":
            company_id = u["company_id"]
        execute(
            """INSERT INTO machinery (name, category, serial_no, cert_no, location, status, next_inspection, owner_id, company_id, notes, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (f.get("name", "").strip(), f.get("category", "Other"), f.get("serial_no", "").strip(),
             f.get("cert_no", "").strip(), f.get("location", "").strip(), f.get("status", "Active"),
             f.get("next_inspection", ""), owner_id or None, company_id,
             f.get("notes", "").strip(), datetime.utcnow().isoformat()),
        )
        flash("Machinery added.", "ok")
        return redirect(url_for("machinery_list"))
    return render_template("portal/machinery_form.html", m=None, categories=CATEGORIES,
                           statuses=STATUSES, owners=owners)


@app.route("/portal/machinery/<int:mid>/edit", methods=["GET", "POST"])
@login_required
def machinery_edit(mid):
    u = current_user()
    m = q("SELECT * FROM machinery WHERE id = ?", (mid,), one=True)
    if not m or (u["role"] != "admin" and m["owner_id"] != u["id"]):
        abort(404)
    owners = q("SELECT id, name, company FROM users WHERE role='client' ORDER BY company") if u["role"] == "admin" else []
    if request.method == "POST":
        f = request.form
        owner_id = f.get("owner_id") if u["role"] == "admin" else m["owner_id"]
        company_id = m["company_id"]
        if u["role"] == "admin" and owner_id:
            o = q("SELECT company_id FROM users WHERE id = ?", (owner_id,), one=True)
            company_id = o["company_id"] if o else company_id
        execute(
            """UPDATE machinery SET name=?, category=?, serial_no=?, cert_no=?, location=?,
               status=?, next_inspection=?, owner_id=?, company_id=?, notes=? WHERE id=?""",
            (f.get("name", "").strip(), f.get("category", "Other"), f.get("serial_no", "").strip(),
             f.get("cert_no", "").strip(), f.get("location", "").strip(), f.get("status", "Active"),
             f.get("next_inspection", ""), owner_id or None, company_id,
             f.get("notes", "").strip(), mid),
        )
        flash("Machinery updated.", "ok")
        return redirect(url_for("machinery_list"))
    return render_template("portal/machinery_form.html", m=m, categories=CATEGORIES,
                           statuses=STATUSES, owners=owners)


@app.route("/portal/machinery/<int:mid>/delete", methods=["POST"])
@login_required
def machinery_delete(mid):
    u = current_user()
    m = q("SELECT * FROM machinery WHERE id = ?", (mid,), one=True)
    if not m or (u["role"] != "admin" and m["owner_id"] != u["id"]):
        abort(404)
    for img in q("SELECT * FROM machinery_images WHERE machinery_id = ?", (mid,)):
        try:
            os.remove(os.path.join(MACHINERY_IMG_DIR, img["filename"]))
        except OSError:
            pass
    execute("DELETE FROM machinery_images WHERE machinery_id = ?", (mid,))
    execute("DELETE FROM reports WHERE machinery_id = ?", (mid,))
    execute("DELETE FROM expiry_reminders WHERE machinery_id = ?", (mid,))
    execute("DELETE FROM machinery WHERE id = ?", (mid,))
    flash("Machinery deleted.", "ok")
    return redirect(url_for("machinery_list"))


# ---------------- machinery detail page ----------------
@app.route("/portal/machinery/<int:mid>")
@login_required
def machinery_detail(mid):
    u = current_user()
    m = q("SELECT * FROM machinery WHERE id = ?", (mid,), one=True)
    if not m or (u["role"] != "admin" and m["owner_id"] != u["id"] and m["company_id"] != u["company_id"]):
        abort(404)
    owner = q("SELECT name, company, email FROM users WHERE id = ?", (m["owner_id"],), one=True) if m["owner_id"] else None
    company = q("SELECT * FROM companies WHERE id = ?", (m["company_id"],), one=True) if m["company_id"] else None
    images = q("SELECT * FROM machinery_images WHERE machinery_id = ? ORDER BY sort_order", (mid,))
    reports = q("""SELECT r.*, usr.name AS author FROM reports r
                   JOIN users usr ON usr.id = r.created_by
                   WHERE r.machinery_id = ? ORDER BY r.created_at DESC""", (mid,))
    reminders = q("SELECT * FROM expiry_reminders WHERE machinery_id = ? ORDER BY reminder_date", (mid,))
    from datetime import date, timedelta
    return render_template("portal/machinery_detail.html", m=m, owner=owner, company=company,
                           images=images, reports=reports, reminders=reminders,
                           report_types=REPORT_TYPES, report_statuses=REPORT_STATUSES,
                           today=date.today().isoformat(),
                           today_plus_60=(date.today() + timedelta(days=60)).isoformat())

@app.route("/portal/machinery/<int:mid>/upload-image", methods=["POST"])
@login_required
def machinery_upload_image(mid):
    u = current_user()
    m = q("SELECT * FROM machinery WHERE id = ?", (mid,), one=True)
    if not m or (u["role"] != "admin" and m["owner_id"] != u["id"]):
        abort(404)
    f = request.files.get("image")
    if f and f.filename:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            flash("Invalid image format.", "err")
            return redirect(url_for("machinery_detail", mid=mid))
        stored = f"m{mid}_{uuid.uuid4().hex}{ext}"
        f.save(os.path.join(MACHINERY_IMG_DIR, stored))
        sort = request.form.get("sort_order", 0, type=int)
        caption = request.form.get("caption", "").strip()
        execute(
            "INSERT INTO machinery_images (machinery_id, filename, caption, sort_order, created_at) VALUES (?,?,?,?,?)",
            (mid, stored, caption, sort, datetime.utcnow().isoformat()),
        )
        if not m.get("image_filename"):
            execute("UPDATE machinery SET image_filename = ? WHERE id = ?", (stored, mid))
        flash("Image uploaded.", "ok")
    return redirect(url_for("machinery_detail", mid=mid))

@app.route("/portal/machinery/<int:mid>/delete-image/<int:iid>", methods=["POST"])
@login_required
def machinery_delete_image(mid, iid):
    u = current_user()
    m = q("SELECT * FROM machinery WHERE id = ?", (mid,), one=True)
    if not m or (u["role"] != "admin" and m["owner_id"] != u["id"]):
        abort(404)
    img = q("SELECT * FROM machinery_images WHERE id = ? AND machinery_id = ?", (iid, mid), one=True)
    if img:
        try:
            os.remove(os.path.join(MACHINERY_IMG_DIR, img["filename"]))
        except OSError:
            pass
        if m.get("image_filename") == img["filename"]:
            execute("UPDATE machinery SET image_filename = '' WHERE id = ?", (mid,))
        execute("DELETE FROM machinery_images WHERE id = ?", (iid,))
        flash("Image removed.", "ok")
    return redirect(url_for("machinery_detail", mid=mid))


# ---------------- machinery report upload (PDF) ----------------
@app.route("/portal/machinery/<int:mid>/report/new", methods=["POST"])
@login_required
def machinery_report_new(mid):
    u = current_user()
    m = q("SELECT * FROM machinery WHERE id = ?", (mid,), one=True)
    if not m or (u["role"] != "admin" and m["owner_id"] != u["id"] and m["company_id"] != u["company_id"]):
        abort(404)
    title = request.form.get("title", "").strip()
    report_type = request.form.get("report_type", "Inspection")
    summary = request.form.get("summary", "").strip()
    status = request.form.get("status", "Draft")
    pdf_file = request.files.get("pdf_file")
    pdf_filename = ""
    if pdf_file and pdf_file.filename and pdf_file.filename.lower().endswith(".pdf"):
        pdf_filename = f"r_{mid}_{uuid.uuid4().hex}.pdf"
        pdf_file.save(os.path.join(REPORT_PDF_DIR, pdf_filename))
    if not title:
        flash("Report title is required.", "err")
        return redirect(url_for("machinery_detail", mid=mid))
    execute(
        """INSERT INTO reports (machinery_id, title, report_type, summary, pdf_filename, status, created_by, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (mid, title, report_type, summary, pdf_filename, status, u["id"], datetime.utcnow().isoformat()),
    )
    flash("Report added.", "ok")
    return redirect(url_for("machinery_detail", mid=mid))

@app.route("/portal/reports/<int:rid>/download-pdf")
@login_required
def report_download_pdf(rid):
    u = current_user()
    r = q("SELECT r.*, m.owner_id, m.company_id FROM reports r JOIN machinery m ON m.id = r.machinery_id WHERE r.id = ?", (rid,), one=True)
    if not r or (u["role"] != "admin" and r["owner_id"] != u["id"] and r["company_id"] != u["company_id"]):
        abort(404)
    if not r.get("pdf_filename"):
        abort(404)
    path = os.path.join(REPORT_PDF_DIR, r["pdf_filename"])
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype="application/pdf", as_attachment=True,
                     download_name=f"report_{rid}.pdf")

@app.route("/portal/reports/<int:rid>/delete", methods=["POST"])
@login_required
def report_delete(rid):
    u = current_user()
    r = q("SELECT r.*, m.owner_id, m.company_id FROM reports r JOIN machinery m ON m.id = r.machinery_id WHERE r.id = ?", (rid,), one=True)
    if not r or (u["role"] != "admin" and r["owner_id"] != u["id"] and r["company_id"] != u["company_id"]):
        abort(404)
    if r.get("pdf_filename"):
        path = os.path.join(REPORT_PDF_DIR, r["pdf_filename"])
        if os.path.exists(path): os.remove(path)
    execute("DELETE FROM reports WHERE id = ?", (rid,))
    flash("Report deleted.", "ok")
    return redirect(url_for("machinery_detail", mid=r["machinery_id"]))

# ---------------- expiry reminders ----------------


# ---------------- expiry reminders ----------------
@app.route("/portal/machinery/<int:mid>/reminder/new", methods=["POST"])
@login_required
def expiry_reminder_new(mid):
    u = current_user()
    m = q("SELECT * FROM machinery WHERE id = ?", (mid,), one=True)
    if not m or (u["role"] != "admin" and m["owner_id"] != u["id"]):
        abort(404)
    email = request.form.get("email", "").strip().lower()
    reminder_date = request.form.get("reminder_date", "").strip()
    days_before = request.form.get("days_before", 30, type=int)
    if not email or not reminder_date:
        flash("Email and reminder date are required.", "err")
        return redirect(url_for("machinery_detail", mid=mid))
    execute(
        "INSERT INTO expiry_reminders (machinery_id, user_id, email, reminder_date, days_before, sent, created_at) VALUES (?,?,?,?,?,0,?)",
        (mid, u["id"], email, reminder_date, days_before, datetime.utcnow().isoformat()),
    )
    flash("Reminder set. Email will be sent when due.", "ok")
    return redirect(url_for("machinery_detail", mid=mid))

@app.route("/portal/machinery/<int:mid>/reminder/<int:rid>/delete", methods=["POST"])
@login_required
def expiry_reminder_delete(mid, rid):
    u = current_user()
    r = q("SELECT * FROM expiry_reminders WHERE id = ? AND machinery_id = ?", (rid, mid), one=True)
    if not r or (u["role"] != "admin" and r["user_id"] != u["id"]):
        abort(404)
    execute("DELETE FROM expiry_reminders WHERE id = ?", (rid,))
    flash("Reminder removed.", "ok")
    return redirect(url_for("machinery_detail", mid=mid))

@app.route("/uploads/machinery/<path:filename>")
@login_required
def serve_machinery_image(filename):
    return send_file(os.path.join(MACHINERY_IMG_DIR, filename))


# ---------------- employee portal (Google Sheets embed) ----------------
EMPLOYEE_SHEET_URL = os.getenv("EMPLOYEE_SHEET_URL", "")

@app.route("/portal/employee")
@login_required
def employee_portal():
    u = current_user()
    if not EMPLOYEE_SHEET_URL:
        flash("Employee portal not configured (set EMPLOYEE_SHEET_URL env var).", "warn")
        return redirect(url_for("dashboard"))
    return render_template("portal/employee_portal.html", sheet_url=EMPLOYEE_SHEET_URL)


# ---------------- logos & company profile ----------------
@app.route("/uploads/logos/<path:filename>")
@login_required
def serve_logo(filename):
    return send_file(os.path.join(LOGO_DIR, filename))


def _save_logo(file_storage, company_id):
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_LOGO_EXT:
        return None
    stored = f"c{company_id}_{uuid.uuid4().hex}{ext}"
    file_storage.save(os.path.join(LOGO_DIR, stored))
    return stored


@app.route("/portal/company", methods=["GET", "POST"])
@login_required
def company_profile():
    u = current_user()
    if not u["company_id"]:
        flash("Your account is not linked to a company.", "warn")
        return redirect(url_for("dashboard"))
    c = q("SELECT * FROM companies WHERE id = ?", (u["company_id"],), one=True)
    if request.method == "POST":
        f = request.form
        logo = c["logo_filename"]
        lf = request.files.get("logo")
        if lf and lf.filename:
            new_logo = _save_logo(lf, c["id"])
            if new_logo:
                if logo:
                    try:
                        os.remove(os.path.join(LOGO_DIR, logo))
                    except OSError:
                        pass
                logo = new_logo
            else:
                flash("Logo must be PNG/JPG/WEBP/GIF.", "err")
        execute("UPDATE companies SET name=?, reg_no=?, address=?, phone=?, logo_filename=? WHERE id=?",
                (f.get("name", c["name"]).strip(), f.get("reg_no", "").strip(),
                 f.get("address", "").strip(), f.get("phone", "").strip(), logo, c["id"]))
        flash("Company profile updated.", "ok")
        return redirect(url_for("company_profile"))
    return render_template("portal/company_profile.html", c=c)


# ---------------- portal: clients (admin) ----------------
@app.route("/portal/clients")
@admin_required
def clients_list():
    clients = q("""SELECT u.*, (SELECT COUNT(*) FROM machinery m WHERE m.owner_id = u.id) AS machine_count
                   FROM users u WHERE u.role = 'client' ORDER BY u.created_at DESC""")
    return render_template("portal/clients_list.html", clients=clients)


@app.route("/portal/clients/new", methods=["GET", "POST"])
@admin_required
def client_new():
    companies = q("SELECT id, name FROM companies ORDER BY name")
    if request.method == "POST":
        f = request.form
        email = f.get("email", "").strip().lower()
        if q("SELECT id FROM users WHERE email = ?", (email,), one=True):
            flash("Email already exists.", "err")
        else:
            company_id = f.get("company_id") or None
            comp_name = f.get("company", "").strip()
            if company_id:
                crow = q("SELECT name FROM companies WHERE id = ?", (company_id,), one=True)
                if crow:
                    comp_name = crow["name"]
            execute(
                "INSERT INTO users (name, email, password_hash, role, company, company_id, created_at) VALUES (?,?,?,?,?,?,?)",
                (f.get("name", "").strip(), email,
                 generate_password_hash(f.get("password", "changeme")),
                 "client", comp_name, company_id, datetime.utcnow().isoformat()),
            )
            flash("Client account created.", "ok")
            return redirect(url_for("clients_list"))
    return render_template("portal/client_form.html", companies=companies)


# ---------------- portal: companies (admin) ----------------
@app.route("/portal/companies")
@admin_required
def companies_list():
    rows = q("""SELECT c.*,
                    (SELECT COUNT(*) FROM users u WHERE u.company_id = c.id) AS user_count,
                    (SELECT COUNT(*) FROM machinery m WHERE m.company_id = c.id) AS machine_count
                FROM companies c ORDER BY c.created_at DESC""")
    return render_template("portal/companies_list.html", companies=rows)


@app.route("/portal/companies/new", methods=["GET", "POST"])
@admin_required
def company_new():
    if request.method == "POST":
        f = request.form
        name = f.get("name", "").strip()
        if not name:
            flash("Company name is required.", "err")
        elif q("SELECT id FROM companies WHERE name = ?", (name,), one=True):
            flash("A company with that name already exists.", "err")
        else:
            cid = execute(
                "INSERT INTO companies (name, reg_no, address, phone, logo_filename, created_at) VALUES (?,?,?,?,?,?)",
                (name, f.get("reg_no", "").strip(), f.get("address", "").strip(),
                 f.get("phone", "").strip(), "", datetime.utcnow().isoformat()),
            )
            lf = request.files.get("logo")
            if lf and lf.filename:
                stored = _save_logo(lf, cid)
                if stored:
                    execute("UPDATE companies SET logo_filename=? WHERE id=?", (stored, cid))
                else:
                    flash("Logo must be PNG/JPG/WEBP/GIF — company saved without logo.", "warn")
            flash("Company created.", "ok")
            return redirect(url_for("companies_list"))
    return render_template("portal/company_form.html", c=None)


@app.route("/portal/companies/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def company_edit(cid):
    c = q("SELECT * FROM companies WHERE id = ?", (cid,), one=True)
    if not c:
        abort(404)
    if request.method == "POST":
        f = request.form
        logo = c["logo_filename"]
        lf = request.files.get("logo")
        if lf and lf.filename:
            new_logo = _save_logo(lf, cid)
            if new_logo:
                if logo:
                    try:
                        os.remove(os.path.join(LOGO_DIR, logo))
                    except OSError:
                        pass
                logo = new_logo
            else:
                flash("Logo must be PNG/JPG/WEBP/GIF.", "err")
        execute("UPDATE companies SET name=?, reg_no=?, address=?, phone=?, logo_filename=? WHERE id=?",
                (f.get("name", c["name"]).strip(), f.get("reg_no", "").strip(),
                 f.get("address", "").strip(), f.get("phone", "").strip(), logo, cid))
        flash("Company updated.", "ok")
        return redirect(url_for("companies_list"))
    return render_template("portal/company_form.html", c=c)


@app.route("/portal/companies/<int:cid>/delete", methods=["POST"])
@admin_required
def company_delete(cid):
    c = q("SELECT * FROM companies WHERE id = ?", (cid,), one=True)
    if not c:
        abort(404)
    execute("UPDATE users SET company_id = NULL WHERE company_id = ?", (cid,))
    execute("UPDATE machinery SET company_id = NULL WHERE company_id = ?", (cid,))
    execute("DELETE FROM companies WHERE id = ?", (cid,))
    if c["logo_filename"]:
        try:
            os.remove(os.path.join(LOGO_DIR, c["logo_filename"]))
        except OSError:
            pass
    flash("Company deleted (linked users/machines kept, unlinked).", "ok")
    return redirect(url_for("companies_list"))


# ---------------- portal: database viewer (admin) ----------------
@app.route("/portal/database")
@admin_required
def db_viewer():
    table = request.args.get("table", "users")
    if table not in ("users", "machinery", "reports"):
        table = "users"
    if table == "users":
        rows = q("SELECT id, name, email, role, company, created_at FROM users ORDER BY id")
        cols = ["id", "name", "email", "role", "company", "created_at"]
    elif table == "machinery":
        rows = q("SELECT * FROM machinery ORDER BY id")
        cols = ["id", "name", "category", "serial_no", "cert_no", "location", "status", "next_inspection", "owner_id", "notes", "created_at"]
    else:
        rows = q("SELECT * FROM reports ORDER BY id")
        cols = ["id", "machinery_id", "title", "report_type", "summary", "status", "created_by", "created_at"]
    return render_template("portal/db_viewer.html", table=table, rows=rows, cols=cols)


# ---------------- portal: PDF forms ----------------
def _template_path(t):
    return os.path.join(UPLOAD_DIR, t["filename"])


def _machinery_options(u):
    if u["role"] == "admin":
        return q("SELECT id, name FROM machinery ORDER BY name")
    scope, params = scope_clause(u)
    return q(f"SELECT id, name FROM machinery m WHERE {scope} ORDER BY name", params)


@app.route("/portal/pdf")
@login_required
def pdf_list():
    u = current_user()
    templates = q("""SELECT t.*,
                        (SELECT COUNT(*) FROM pdf_submissions s WHERE s.template_id = t.id) AS sub_count
                     FROM pdf_templates t ORDER BY t.created_at DESC""")
    return render_template("portal/pdf_list.html", templates=templates)


@app.route("/portal/pdf/upload", methods=["GET", "POST"])
@admin_required
def pdf_upload():
    if request.method == "POST":
        f = request.files.get("pdf")
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "").strip()
        if not f or not f.filename.lower().endswith(".pdf"):
            flash("Please choose a PDF file.", "err")
            return redirect(url_for("pdf_upload"))
        if not name:
            name = os.path.splitext(f.filename)[0]
        stored = f"{uuid.uuid4().hex}.pdf"
        path = os.path.join(UPLOAD_DIR, stored)
        f.save(path)
        fields = extract_acroform_fields(path)
        tid = execute(
            "INSERT INTO pdf_templates (name, description, filename, fields_json, created_at) VALUES (?,?,?,?,?)",
            (name, desc, stored, json.dumps(fields), datetime.utcnow().isoformat()),
        )
        if fields:
            flash(f"Template uploaded — auto-detected {len(fields)} fillable field(s).", "ok")
        else:
            flash("Template uploaded. No fillable fields detected — define them in the Fields JSON editor.", "warn")
        return redirect(url_for("pdf_edit_fields", tid=tid))
    return render_template("portal/pdf_upload.html")


@app.route("/portal/pdf/<int:tid>/fields", methods=["GET", "POST"])
@admin_required
def pdf_edit_fields(tid):
    t = q("SELECT * FROM pdf_templates WHERE id = ?", (tid,), one=True)
    if not t:
        abort(404)
    if request.method == "POST":
        fields, err = validate_fields_json(request.form.get("fields_json", "[]"))
        if err:
            flash(err, "err")
            return render_template("portal/pdf_fields.html", t=t,
                                   fields_json=request.form.get("fields_json", "[]"))
        execute("UPDATE pdf_templates SET name = ?, description = ?, fields_json = ? WHERE id = ?",
                (request.form.get("name", t["name"]).strip(),
                 request.form.get("description", "").strip(),
                 json.dumps(fields), tid))
        flash(f"Saved {len(fields)} field(s).", "ok")
        return redirect(url_for("pdf_list"))
    pretty = json.dumps(json.loads(t["fields_json"] or "[]"), indent=2)
    return render_template("portal/pdf_fields.html", t=t, fields_json=pretty)


@app.route("/portal/pdf/<int:tid>/delete", methods=["POST"])
@admin_required
def pdf_delete_template(tid):
    t = q("SELECT * FROM pdf_templates WHERE id = ?", (tid,), one=True)
    if not t:
        abort(404)
    execute("DELETE FROM pdf_submissions WHERE template_id = ?", (tid,))
    execute("DELETE FROM pdf_templates WHERE id = ?", (tid,))
    try:
        os.remove(_template_path(t))
    except OSError:
        pass
    flash("Template deleted.", "ok")
    return redirect(url_for("pdf_list"))


@app.route("/portal/pdf/<int:tid>/fill", methods=["GET", "POST"])
@login_required
def pdf_fill(tid):
    u = current_user()
    t = q("SELECT * FROM pdf_templates WHERE id = ?", (tid,), one=True)
    if not t:
        abort(404)
    fields = json.loads(t["fields_json"] or "[]")
    machines = _machinery_options(u)
    if request.method == "POST":
        data = {f["name"]: request.form.get(f["name"], "") for f in fields}
        machinery_id = request.form.get("machinery_id") or None
        if machinery_id:
            m = q("SELECT * FROM machinery WHERE id = ?", (machinery_id,), one=True)
            if not m or (u["role"] != "admin" and m["owner_id"] != u["id"]
                         and m["company_id"] != u["company_id"]):
                abort(403)
        execute(
            "INSERT INTO pdf_submissions (template_id, machinery_id, data_json, created_by, created_at) VALUES (?,?,?,?,?)",
            (tid, machinery_id, json.dumps(data), u["id"], datetime.utcnow().isoformat()),
        )
        try:
            pdf_bytes = fill_pdf(_template_path(t), fields, data)
        except Exception as e:
            flash(f"Saved, but failed to render PDF: {e}", "err")
            return redirect(url_for("pdf_list"))
        fname = re.sub(r"[^A-Za-z0-9_-]+", "_", t["name"]).strip("_") or "report"
        return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                         as_attachment=True, download_name=f"{fname}_filled.pdf")
    return render_template("portal/pdf_fill.html", t=t, fields=fields, machines=machines)


@app.route("/portal/pdf/<int:tid>/submissions")
@login_required
def pdf_submissions(tid):
    u = current_user()
    t = q("SELECT * FROM pdf_templates WHERE id = ?", (tid,), one=True)
    if not t:
        abort(404)
    if u["role"] == "admin":
        subs = q("""SELECT s.*, u.name AS author, m.name AS machinery_name FROM pdf_submissions s
                    JOIN users u ON u.id = s.created_by
                    LEFT JOIN machinery m ON m.id = s.machinery_id
                    WHERE s.template_id = ? ORDER BY s.created_at DESC""", (tid,))
    else:
        subs = q("""SELECT s.*, u.name AS author, m.name AS machinery_name FROM pdf_submissions s
                    JOIN users u ON u.id = s.created_by
                    LEFT JOIN machinery m ON m.id = s.machinery_id
                    WHERE s.template_id = ? AND s.created_by = ? ORDER BY s.created_at DESC""",
                 (tid, u["id"]))
    return render_template("portal/pdf_submissions.html", t=t, subs=subs)


@app.route("/portal/pdf/submission/<int:sid>/export")
@login_required
def pdf_export_submission(sid):
    u = current_user()
    s = q("SELECT * FROM pdf_submissions WHERE id = ?", (sid,), one=True)
    if not s or (u["role"] != "admin" and s["created_by"] != u["id"]):
        abort(404)
    t = q("SELECT * FROM pdf_templates WHERE id = ?", (s["template_id"],), one=True)
    if not t:
        abort(404)
    fields = json.loads(t["fields_json"] or "[]")
    data = json.loads(s["data_json"])
    pdf_bytes = fill_pdf(_template_path(t), fields, data)
    fname = re.sub(r"[^A-Za-z0-9_-]+", "_", t["name"]).strip("_") or "report"
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True, download_name=f"{fname}_{sid}.pdf")


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="You don't have permission to view this page."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found."), 404


# ---------------- email + expiry reminder scheduler ----------------
def send_email(to, subject, body):
    """Send an email via SMTP. Returns True on success. Gracefully skips if not configured."""
    if not SMTP_HOST:
        app.logger.warning("SMTP not configured — skipping email to %s", to)
        return False
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    msg = MIMEMultipart()
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        app.logger.info("Email sent to %s — %s", to, subject)
        return True
    except Exception as e:
        app.logger.error("Email failed to %s: %s", to, e)
        return False


def check_and_send_reminders():
    """Scheduled job: find unsent reminders where we're within the notification window, send email, mark sent."""
    from datetime import date, timedelta
    today = date.today().isoformat()
    rows = q("""
        SELECT r.*, m.name AS machine_name, m.next_inspection
        FROM expiry_reminders r
        JOIN machinery m ON m.id = r.machinery_id
        WHERE r.sent = 0
          AND r.reminder_date <= ?
    """, (today,))
    sent_count = 0
    for r in rows:
        subject = f"[Tijarah Mabrur] Inspection Reminder — {r['machine_name']}"
        body = (
            f"Dear Client,\n\n"
            f"This is an automated reminder from Tijarah Mabrur (M) Sdn. Bhd.\n\n"
            f"Machine: {r['machine_name']}\n"
            f"Inspection due: {r['next_inspection'] or r['reminder_date']}\n"
            f"Reminder set for: {r['reminder_date']} ({r['days_before']} days before)\n\n"
            f"Please contact us to schedule the inspection if not already arranged.\n\n"
            f"— Tijarah Mabrur (M) Sdn. Bhd."
        )
        if send_email(r["email"], subject, body):
            execute("UPDATE expiry_reminders SET sent = 1 WHERE id = ?", (r["id"],))
            sent_count += 1
    if sent_count:
        app.logger.info("Expiry reminders: sent %d email(s)", sent_count)


def _setup_scheduler():
    """Start APScheduler background scheduler for expiry reminders."""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(
        check_and_send_reminders,
        trigger=IntervalTrigger(hours=6),
        id="expiry_reminder_job",
        name="Expiry reminder checker",
        replace_existing=True,
    )
    sched.start()
    app.logger.info("Scheduler started — checking expiry reminders every 6 hours")

# Run DB init + scheduler at module level (works for both `python app.py` and `gunicorn`)
_init_done = False
def _bootstrap():
    global _init_done
    if _init_done:
        return
    _init_done = True
    init_db()
    _setup_scheduler()

_bootstrap()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
