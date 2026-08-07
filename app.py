"""Tijarah Mabrur website + client portal (Flask + SQLite)."""
import base64
import io
import json
import os
import re
import uuid
from datetime import datetime
from functools import wraps

def _save_base64_image(b64_str):
    if not b64_str or not b64_str.startswith("data:image"):
        return None
    try:
        header, encoded = b64_str.split(",", 1)
        ext = ".png"
        if "jpeg" in header or "jpg" in header:
            ext = ".jpg"
        elif "webp" in header:
            ext = ".webp"
        data = base64.b64decode(encoded)
        filename = f"rfq_remark_{uuid.uuid4().hex[:10]}{ext}"
        filepath = os.path.join(RFQ_IMG_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(data)
        return filename
    except Exception:
        return None

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
MACHINERY_DOC_DIR = os.path.join(UPLOAD_DIR, "machinery_docs")
RFQ_IMG_DIR = os.path.join(UPLOAD_DIR, "rfq")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOGO_DIR, exist_ok=True)
os.makedirs(MACHINERY_IMG_DIR, exist_ok=True)
os.makedirs(REPORT_PDF_DIR, exist_ok=True)
os.makedirs(MACHINERY_DOC_DIR, exist_ok=True)
os.makedirs(RFQ_IMG_DIR, exist_ok=True)

@app.route("/uploads/rfq/<filename>")
def serve_rfq_img(filename):
    from flask import send_from_directory
    return send_from_directory(RFQ_IMG_DIR, filename)

@app.route("/uploads/logos/<filename>")
@app.route("/portal/serve_logo/<filename>")
def serve_logo(filename):
    from flask import send_from_directory
    return send_from_directory(LOGO_DIR, filename)

@app.route("/uploads/machinery/<filename>")
@app.route("/portal/serve_machinery_image/<filename>")
def serve_machinery_image(filename):
    from flask import send_from_directory
    return send_from_directory(MACHINERY_IMG_DIR, filename)

@app.route("/uploads/machinery_docs/<filename>")
@app.route("/portal/serve_machinery_doc/<filename>")
def serve_machinery_doc(filename):
    from flask import send_from_directory
    return send_from_directory(MACHINERY_DOC_DIR, filename)

@app.route("/uploads/reports/<filename>")
@app.route("/portal/serve_report_pdf/<filename>")
def serve_report_pdf(filename):
    from flask import send_from_directory
    return send_from_directory(REPORT_PDF_DIR, filename)

@app.route("/favicon.ico")
def favicon():
    from flask import send_from_directory
    return send_from_directory(os.path.join(app.root_path, "static", "img"), "logo.png", mimetype="image/png")

ALLOWED_LOGO_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB uploads


def save_machinery_file(file_storage, target_dir, prefix="doc"):
    if not file_storage or not file_storage.filename:
        return ""
    ext = os.path.splitext(file_storage.filename)[1].lower()
    stored = f"{prefix}_{uuid.uuid4().hex}{ext}"
    file_storage.save(os.path.join(target_dir, stored))
    return stored


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


@app.template_filter("fmt_date")
def fmt_date_filter(d_str):
    if not d_str:
        return ""
    try:
        if "T" in str(d_str):
            dt = datetime.fromisoformat(str(d_str))
        else:
            dt = datetime.strptime(str(d_str), "%Y-%m-%d")
        return dt.strftime("%d %B %Y").lstrip("0")
    except Exception:
        return str(d_str)


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
    Admins and employees see everything; clients see their own + company-wide rows."""
    if u["role"] in ("admin", "employee"):
        return "1=1", ()
    if u["company_id"]:
        return f"({col} = ? OR m.company_id = ?)", (u["id"], u["company_id"])
    return f"{col} = ?", (u["id"],)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id") or not current_user():
            session.clear()
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


def staff_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u or u["role"] not in ("admin", "employee", "staff", "worker"):
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
    email_val = ""
    if request.method == "POST":
        email_val = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        u = q("SELECT * FROM users WHERE email = ?", (email_val,), one=True)
        if u and check_password_hash(u["password_hash"], password):
            session["user_id"] = u["id"]
            flash("Welcome back, %s!" % u["name"], "ok")
            if u["role"] in ("employee", "staff", "worker"):
                return redirect(url_for("rfq_stage_list", stage="RFQ"))
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid email or password.", "err")
        return render_template("login.html", email=email_val)
    return render_template("login.html", email=email_val)


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
    if u and u["role"] in ("employee", "staff", "worker"):
        return redirect(url_for("rfq_stage_list", stage="RFQ"))
    from datetime import date, timedelta
    cutoff = (date.today() + timedelta(days=60)).isoformat()
    if u["role"] == "admin":
        stats = {
            "machinery": q("SELECT COUNT(*) c FROM machinery", one=True)["c"],
            "clients": q("SELECT COUNT(*) c FROM users WHERE role='client'", one=True)["c"],
            "reports": q("SELECT COUNT(*) c FROM reports", one=True)["c"],
            "expiring": q("SELECT COUNT(*) c FROM machinery WHERE next_inspection != '' AND next_inspection <= ?", (cutoff,), one=True)["c"],
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
                            AND m.next_inspection != '' AND m.next_inspection <= ?""", (*params, cutoff), one=True)["c"],
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
    if u and u["role"] in ("employee", "staff", "worker"):
        return redirect(url_for("rfq_stage_list", stage="RFQ"))
    cert_type = request.args.get("type", "PMT").strip().upper()
    search = request.args.get("q", "").strip()
    page = max(request.args.get("page", 1, type=int), 1)
    scope, params = scope_clause(u)
    where = scope
    args = list(params)
    if cert_type in ("PMT", "PMA", "PMD"):
        where += " AND (m.cert_type = ? OR (m.cert_type IS NULL AND ? = 'PMT'))"
        args += [cert_type, cert_type]
    if search:
        where += " AND (m.name LIKE ? OR m.item_name LIKE ? OR m.serial_no LIKE ? OR m.cert_no LIKE ? OR m.location LIKE ?)"
        args += [f"%{search}%"] * 5
    total = q(f"SELECT COUNT(*) c FROM machinery m WHERE {where}", tuple(args), one=True)["c"]
    pages = max((total + PER_PAGE - 1) // PER_PAGE, 1)
    page = min(page, pages)
    rows = q(
        f"""SELECT m.*, u.company AS owner_company FROM machinery m
            LEFT JOIN users u ON u.id = m.owner_id
            WHERE {where} ORDER BY m.created_at DESC LIMIT ? OFFSET ?""",
        tuple(args) + (PER_PAGE, (page - 1) * PER_PAGE),
    )
    rows = [dict(r) for r in rows]
    return render_template("portal/machinery_list.html", machinery=rows, search=search,
                           cert_type=cert_type, page=page, pages=pages, total=total)


@app.route("/portal/machinery/new", methods=["GET", "POST"])
@login_required
def machinery_new():
    u = current_user()
    owners = q("SELECT id, name, company FROM users WHERE role='client' ORDER BY company") if u["role"] == "admin" else []
    if request.method == "POST":
        f = request.form
        files = request.files
        owner_id = f.get("owner_id") if u["role"] == "admin" else u["id"]
        company_id = None
        if owner_id:
            o = q("SELECT company_id FROM users WHERE id = ?", (owner_id,), one=True)
            company_id = o["company_id"] if o else None
        elif u["role"] != "admin":
            company_id = u["company_id"]

        image_filename = save_machinery_file(files.get("main_image"), MACHINERY_IMG_DIR, "m_main")
        before_image = save_machinery_file(files.get("before_image"), MACHINERY_IMG_DIR, "m_before")
        sv_image = save_machinery_file(files.get("sv_image"), MACHINERY_IMG_DIR, "m_sv")
        pg_image = save_machinery_file(files.get("pg_image"), MACHINERY_IMG_DIR, "m_pg")

        doc_design_approval = save_machinery_file(files.get("doc_design_approval"), MACHINERY_DOC_DIR, "doc_da")
        doc_design_drawing = save_machinery_file(files.get("doc_design_drawing"), MACHINERY_DOC_DIR, "doc_dd")
        doc_ht_cert = save_machinery_file(files.get("doc_ht_cert"), MACHINERY_DOC_DIR, "doc_ht")
        doc_dosh = save_machinery_file(files.get("doc_dosh"), MACHINERY_DOC_DIR, "doc_dosh")
        doc_service_report = save_machinery_file(files.get("doc_service_report"), MACHINERY_DOC_DIR, "doc_sr")
        doc_uttm_report = save_machinery_file(files.get("doc_uttm_report"), MACHINERY_DOC_DIR, "doc_ut")
        doc_sv_cert = save_machinery_file(files.get("doc_sv_cert"), MACHINERY_DOC_DIR, "doc_sv")
        doc_pg_cert = save_machinery_file(files.get("doc_pg_cert"), MACHINERY_DOC_DIR, "doc_pg")
        doc_cof = save_machinery_file(files.get("doc_cof"), MACHINERY_DOC_DIR, "doc_cof")

        execute(
            """INSERT INTO machinery (
                name, category, serial_no, cert_no, location, status, next_inspection, owner_id, company_id, notes,
                image_filename, cert_type, item_name, mawp, manufacturer, volume, year,
                before_image, medium, serviced_date, sv_image, sv_size, sv_type, sv_set_pressure, sv_calibrated_date,
                pg_image, pg_size, pg_type, pg_calibrated_date,
                doc_design_approval, doc_design_drawing, doc_ht_cert, doc_dosh, doc_service_report, doc_uttm_report, doc_sv_cert, doc_pg_cert, doc_cof,
                created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                f.get("name", "").strip(), f.get("category", "Other"), f.get("serial_no", "").strip(),
                f.get("cert_no", "").strip(), f.get("location", "").strip(), f.get("status", "Active"),
                f.get("next_inspection", ""), owner_id or None, company_id, f.get("notes", "").strip(),
                image_filename, f.get("cert_type", "PMT").strip().upper(), f.get("item_name", "").strip(),
                f.get("mawp", "").strip(), f.get("manufacturer", "").strip(), f.get("volume", "").strip(), f.get("year", "").strip(),
                before_image, f.get("medium", "").strip(), f.get("serviced_date", "").strip(),
                sv_image, f.get("sv_size", "").strip(), f.get("sv_type", "").strip(), f.get("sv_set_pressure", "").strip(), f.get("sv_calibrated_date", "").strip(),
                pg_image, f.get("pg_size", "").strip(), f.get("pg_type", "").strip(), f.get("pg_calibrated_date", "").strip(),
                doc_design_approval, doc_design_drawing, doc_ht_cert, doc_dosh, doc_service_report, doc_uttm_report, doc_sv_cert, doc_pg_cert, doc_cof,
                datetime.utcnow().isoformat()
            )
        )
        flash("Machinery added.", "ok")
        return redirect(url_for("machinery_list", type=f.get("cert_type", "PMT").strip().upper()))
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
        files = request.files
        owner_id = f.get("owner_id") if u["role"] == "admin" else m["owner_id"]
        company_id = m["company_id"]
        if u["role"] == "admin" and owner_id:
            o = q("SELECT company_id FROM users WHERE id = ?", (owner_id,), one=True)
            company_id = o["company_id"] if o else company_id

        image_filename = save_machinery_file(files.get("main_image"), MACHINERY_IMG_DIR, "m_main") or (m.get("image_filename") if m.get("image_filename") else "")
        before_image = save_machinery_file(files.get("before_image"), MACHINERY_IMG_DIR, "m_before") or (m.get("before_image") if m.get("before_image") else "")
        sv_image = save_machinery_file(files.get("sv_image"), MACHINERY_IMG_DIR, "m_sv") or (m.get("sv_image") if m.get("sv_image") else "")
        pg_image = save_machinery_file(files.get("pg_image"), MACHINERY_IMG_DIR, "m_pg") or (m.get("pg_image") if m.get("pg_image") else "")

        doc_design_approval = save_machinery_file(files.get("doc_design_approval"), MACHINERY_DOC_DIR, "doc_da") or (m.get("doc_design_approval") if m.get("doc_design_approval") else "")
        doc_design_drawing = save_machinery_file(files.get("doc_design_drawing"), MACHINERY_DOC_DIR, "doc_dd") or (m.get("doc_design_drawing") if m.get("doc_design_drawing") else "")
        doc_ht_cert = save_machinery_file(files.get("doc_ht_cert"), MACHINERY_DOC_DIR, "doc_ht") or (m.get("doc_ht_cert") if m.get("doc_ht_cert") else "")
        doc_dosh = save_machinery_file(files.get("doc_dosh"), MACHINERY_DOC_DIR, "doc_dosh") or (m.get("doc_dosh") if m.get("doc_dosh") else "")
        doc_service_report = save_machinery_file(files.get("doc_service_report"), MACHINERY_DOC_DIR, "doc_sr") or (m.get("doc_service_report") if m.get("doc_service_report") else "")
        doc_uttm_report = save_machinery_file(files.get("doc_uttm_report"), MACHINERY_DOC_DIR, "doc_ut") or (m.get("doc_uttm_report") if m.get("doc_uttm_report") else "")
        doc_sv_cert = save_machinery_file(files.get("doc_sv_cert"), MACHINERY_DOC_DIR, "doc_sv") or (m.get("doc_sv_cert") if m.get("doc_sv_cert") else "")
        doc_pg_cert = save_machinery_file(files.get("doc_pg_cert"), MACHINERY_DOC_DIR, "doc_pg") or (m.get("doc_pg_cert") if m.get("doc_pg_cert") else "")
        doc_cof = save_machinery_file(files.get("doc_cof"), MACHINERY_DOC_DIR, "doc_cof") or (m.get("doc_cof") if m.get("doc_cof") else "")

        execute(
            """UPDATE machinery SET
                name=?, category=?, serial_no=?, cert_no=?, location=?, status=?, next_inspection=?, owner_id=?, company_id=?, notes=?,
                image_filename=?, cert_type=?, item_name=?, mawp=?, manufacturer=?, volume=?, year=?,
                before_image=?, medium=?, serviced_date=?, sv_image=?, sv_size=?, sv_type=?, sv_set_pressure=?, sv_calibrated_date=?,
                pg_image=?, pg_size=?, pg_type=?, pg_calibrated_date=?,
                doc_design_approval=?, doc_design_drawing=?, doc_ht_cert=?, doc_dosh=?, doc_service_report=?, doc_uttm_report=?, doc_sv_cert=?, doc_pg_cert=?, doc_cof=?
                WHERE id=?""",
            (
                f.get("name", "").strip(), f.get("category", "Other"), f.get("serial_no", "").strip(),
                f.get("cert_no", "").strip(), f.get("location", "").strip(), f.get("status", "Active"),
                f.get("next_inspection", ""), owner_id or None, company_id, f.get("notes", "").strip(),
                image_filename, f.get("cert_type", "PMT").strip().upper(), f.get("item_name", "").strip(),
                f.get("mawp", "").strip(), f.get("manufacturer", "").strip(), f.get("volume", "").strip(), f.get("year", "").strip(),
                before_image, f.get("medium", "").strip(), f.get("serviced_date", "").strip(),
                sv_image, f.get("sv_size", "").strip(), f.get("sv_type", "").strip(), f.get("sv_set_pressure", "").strip(), f.get("sv_calibrated_date", "").strip(),
                pg_image, f.get("pg_size", "").strip(), f.get("pg_type", "").strip(), f.get("pg_calibrated_date", "").strip(),
                doc_design_approval, doc_design_drawing, doc_ht_cert, doc_dosh, doc_service_report, doc_uttm_report, doc_sv_cert, doc_pg_cert, doc_cof,
                mid
            ),
        )
        flash("Machinery updated.", "ok")
        return redirect(url_for("machinery_list", type=f.get("cert_type", "PMT").strip().upper()))
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
    return redirect(request.referrer or url_for("machinery_list"))


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
    return redirect(request.referrer or url_for("machinery_detail", mid=r["machinery_id"]))


# ---------------- sample PDF generator ----------------
@app.route("/sample-pdf/<doc_name>")
def sample_pdf(doc_name):
    clean_name = doc_name.replace("-", " ").replace("_", " ").title()
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length 220>>stream\n"
        b"BT /F1 18 Tf 50 720 Td (TIJARAH MABRUR \\(M\\) SDN BHD) Tj ET\n"
        b"BT /F1 14 Tf 50 690 Td (DOCUMENT: " + clean_name.encode("utf-8") + b") Tj ET\n"
        b"BT /F1 11 Tf 50 660 Td (Statutory DOSH Compliance & Technical Inspection Certificate) Tj ET\n"
        b"BT /F1 10 Tf 50 630 Td (Status: VERIFIED & COMPLIANT PER OSHA 1994) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \n0000000215 00000 n \n0000000284 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n540\n%%EOF"
    )
    from flask import Response
    return Response(pdf_bytes, mimetype="application/pdf", headers={"Content-Disposition": f"inline; filename={clean_name}.pdf"})


# ---------------- portal: reports list, new, edit, delete ----------------
@app.route("/portal/reports")
@login_required
def reports_list():
    u = current_user()
    if u and u["role"] in ("employee", "staff", "worker"):
        return redirect(url_for("rfq_stage_list", stage="RFQ"))
    scope, params = scope_clause(u)
    rows = q(f"""SELECT r.*, m.name AS machinery_name, m.cert_no AS machinery_cert,
                        u.name AS author_name
                 FROM reports r
                 JOIN machinery m ON m.id = r.machinery_id
                 LEFT JOIN users u ON u.id = r.created_by
                 WHERE {scope} ORDER BY r.created_at DESC""", params)
    rows = [dict(r) for r in rows]
    return render_template("portal/reports_list.html", reports=rows)


@app.route("/portal/reports/new", methods=["GET", "POST"])
@login_required
def report_new():
    u = current_user()
    if request.method == "POST":
        f = request.form
        title = f.get("title", "").strip()
        report_type = f.get("report_type", "Inspection")
        summary = f.get("summary", "").strip()
        status = f.get("status", "Draft")
        machinery_id = f.get("machinery_id", type=int)
        if not title or not machinery_id:
            flash("Title and machine are required.", "err")
            return redirect(url_for("report_new"))
        
        pdf_file = request.files.get("pdf_file")
        pdf_name = save_machinery_file(pdf_file, REPORT_PDF_DIR, "report") if (pdf_file and pdf_file.filename) else ""

        now = datetime.utcnow().isoformat()
        execute(
            "INSERT INTO reports (machinery_id, title, report_type, summary, pdf_filename, status, created_by, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (machinery_id, title, report_type, summary, pdf_name, status, u["id"], now),
        )
        flash("Report created.", "ok")
        return redirect(url_for("reports_list"))
    scope, params = scope_clause(u)
    machines = q(f"SELECT id, name FROM machinery m WHERE {scope} ORDER BY m.name", params)
    return render_template("portal/report_form.html", r=None, machines=machines,
                           report_types=REPORT_TYPES, report_statuses=REPORT_STATUSES)


@app.route("/portal/reports/<int:rid>/edit", methods=["GET", "POST"])
@login_required
def report_edit(rid):
    u = current_user()
    r = q("SELECT * FROM reports WHERE id = ?", (rid,), one=True)
    if not r:
        abort(404)
    if request.method == "POST":
        f = request.form
        title = f.get("title", "").strip()
        report_type = f.get("report_type", "Inspection")
        summary = f.get("summary", "").strip()
        status = f.get("status", "Draft")
        machinery_id = f.get("machinery_id", type=int)
        
        pdf_file = request.files.get("pdf_file")
        pdf_name = r["pdf_filename"] if _ENGINE == "pg" else r.get("pdf_filename", "")
        if pdf_file and pdf_file.filename:
            pdf_name = save_machinery_file(pdf_file, REPORT_PDF_DIR, "report")

        execute("""UPDATE reports SET machinery_id=?, title=?, report_type=?, summary=?, pdf_filename=?, status=? WHERE id=?""",
                (machinery_id, title, report_type, summary, pdf_name, status, rid))
        flash("Report updated.", "ok")
        return redirect(url_for("reports_list"))
    scope, params = scope_clause(u)
    machines = q(f"SELECT id, name FROM machinery m WHERE {scope} ORDER BY m.name", params)
    return render_template("portal/report_form.html", r=r, machines=machines,
                           report_types=REPORT_TYPES, report_statuses=REPORT_STATUSES)





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




# ---------------- employee portal (redirected) ----------------
@app.route("/portal/employee")
@login_required
def employee_portal():
    return redirect(url_for("rfq_dashboard"))


# ---------------- user management (admin) ----------------
@app.route("/portal/users/<int:uid>/change-password", methods=["POST"])
@admin_required
def user_change_password(uid):
    new_pass = request.form.get("new_password", "").strip()
    if not new_pass or len(new_pass) < 6:
        flash("Password must be at least 6 characters.", "err")
    else:
        execute("UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_pass), uid))
        flash("Password updated successfully.", "ok")
    return redirect(request.referrer or url_for("clients_list"))


@app.route("/portal/users/<int:uid>/delete", methods=["POST"])
@admin_required
def user_delete(uid):
    u = current_user()
    if u["id"] == uid:
        flash("You cannot delete your own admin account.", "err")
        return redirect(request.referrer or url_for("clients_list"))
    execute("DELETE FROM machinery WHERE owner_id = ?", (uid,))
    execute("DELETE FROM users WHERE id = ?", (uid,))
    flash("User account deleted.", "ok")
    return redirect(request.referrer or url_for("clients_list"))



# ---------------- logos & company profile ----------------



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
                   FROM users u WHERE u.role IN ('client', 'employee') ORDER BY u.created_at DESC""")
    return render_template("portal/clients_list.html", clients=clients)


@app.route("/portal/clients/new", methods=["GET", "POST"])
@admin_required
def client_new():
    companies = q("SELECT id, name FROM companies ORDER BY name")
    if request.method == "POST":
        f = request.form
        email = f.get("email", "").strip().lower()
        role = f.get("role", "client").strip()
        if role not in ("client", "employee"):
            role = "client"
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
                 role, comp_name, company_id, datetime.utcnow().isoformat()),
            )
            flash(f"User account created ({role}).", "ok")
            return redirect(url_for("clients_list"))
    return render_template("portal/client_form.html", companies=companies)


# ---------------- portal: companies (admin) ----------------
@app.route("/portal/companies")
@admin_required
def companies_list():
    rows = q("""SELECT c.*,
                    (SELECT COUNT(*) FROM users u WHERE u.company_id = c.id) AS user_count,
                    (SELECT COUNT(*) FROM machinery m WHERE m.company_id = c.id) AS machine_count,
                    (SELECT email FROM users u WHERE u.company_id = c.id ORDER BY id ASC LIMIT 1) AS client_email
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
            now = datetime.utcnow().isoformat()
            cid = execute(
                "INSERT INTO companies (name, reg_no, address, phone, logo_filename, created_at) VALUES (?,?,?,?,?,?)",
                (name, f.get("reg_no", "").strip(), f.get("address", "").strip(),
                 f.get("phone", "").strip(), "", now),
            )
            lf = request.files.get("logo")
            if lf and lf.filename:
                stored = _save_logo(lf, cid)
                if stored:
                    execute("UPDATE companies SET logo_filename=? WHERE id=?", (stored, cid))
                else:
                    flash("Logo must be PNG/JPG/WEBP/GIF — company saved without logo.", "warn")

            # Create Initial Client Account for this company so they can log in
            cemail = f.get("client_email", "").strip().lower()
            cpass = f.get("client_password", "").strip() or "client123"
            if not cemail:
                slug = re.sub(r'[^a-zA-Z0-9]', '', name.lower())[:12] or "company"
                cemail = f"client@{slug}.com"
            
            if not q("SELECT id FROM users WHERE email = ?", (cemail,), one=True):
                execute(
                    "INSERT INTO users (name, email, password_hash, role, company, company_id, created_at) VALUES (?,?,?,?,?,?,?)",
                    (f"{name} Client", cemail, generate_password_hash(cpass), "client", name, cid, now)
                )
                flash(f"Company created! Client Login: {cemail} / Password: {cpass}", "ok")
            else:
                flash(f"Company created! (Client email {cemail} already exists).", "ok")

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
    if u and u["role"] in ("employee", "staff", "worker"):
        return redirect(url_for("rfq_stage_list", stage="RFQ"))
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





# RFQ MANAGEMENT SYSTEM
# ================================================================
RFQ_STAGES = ["RFQ", "QUO", "PO", "INV", "PYMT", "KIV", "LOST"]
RFQ_STAGE_COLORS = {"RFQ": "#01a0ff", "QUO": "#f5a623", "PO": "#4caf50", "INV": "#9c27b0", "PYMT": "#e91e63", "KIV": "#ff9800", "LOST": "#f44336"}

def _next_rfq_id():
    """Generate next RFQ-YYXXX id."""
    yr = datetime.utcnow().strftime("%y")
    last = q("SELECT rfq_id FROM rfq_entries WHERE rfq_id LIKE ? ORDER BY id DESC LIMIT 1", (f"RFQ-{yr}%",), one=True)
    if last:
        try:
            num = int(last["rfq_id"].split("-")[1][2:]) + 1
        except (IndexError, ValueError):
            num = 1
    else:
        num = 1
    return f"RFQ-{yr}{num:03d}"


def _rfq_dropdown(list_type):
    rows = q("SELECT value FROM rfq_lists WHERE list_type = ? ORDER BY sort_order, id", (list_type,))
    seen = set()
    res = []
    for r in rows:
        val = r["value"].strip() if r["value"] else ""
        if val and val.lower() not in seen:
            seen.add(val.lower())
            res.append(val)
    return res


# ---- RFQ Dashboard ----
@app.route("/portal/rfq-dashboard")
@admin_required
def rfq_dashboard():
    stages_data = []
    for stage in RFQ_STAGES:
        row = q("SELECT COUNT(*) c, COALESCE(SUM(amount),0) total FROM rfq_entries WHERE stage = ?", (stage,), one=True)
        stages_data.append({"stage": stage, "count": row["c"], "total": row["total"], "color": RFQ_STAGE_COLORS.get(stage, "#888")})
    total_all = q("SELECT COUNT(*) c FROM rfq_entries", one=True)["c"]
    total_amount = q("SELECT COALESCE(SUM(amount),0) s FROM rfq_entries", one=True)["s"]

    # Open By breakdown
    open_by_rows = q("SELECT open_by, COUNT(*) c FROM rfq_entries WHERE open_by != '' GROUP BY open_by ORDER BY c DESC")

    # Pie data
    source_rows = q("SELECT source, COUNT(*) c FROM rfq_entries WHERE source != '' GROUP BY source ORDER BY c DESC")
    introducer_rows = q("SELECT introducer, COUNT(*) c FROM rfq_entries WHERE introducer != '' GROUP BY introducer ORDER BY c DESC")
    state_rows = q("SELECT state, COUNT(*) c FROM rfq_entries WHERE state != '' GROUP BY state ORDER BY c DESC")
    job_code_rows = q("SELECT job_code, COUNT(*) c FROM rfq_entries WHERE job_code != '' GROUP BY job_code ORDER BY c DESC")



    # Recent entries
    recent = q("SELECT * FROM rfq_entries ORDER BY id DESC LIMIT 8")

    # Staff performance stats (open_by)
    staff_stats = q("""SELECT open_by, COUNT(*) c, COALESCE(SUM(amount),0) total,
                    SUM(CASE WHEN stage='PYMT' THEN 1 ELSE 0 END) closed,
                    SUM(CASE WHEN stage='LOST' THEN 1 ELSE 0 END) lost
                    FROM rfq_entries WHERE open_by != '' GROUP BY open_by ORDER BY c DESC""")

    # Totals
    total_profit = q("SELECT COALESCE(SUM(net_profit),0) s FROM rfq_entries", one=True)["s"]
    total_cost = q("SELECT COALESCE(SUM(total_cost),0) s FROM rfq_entries", one=True)["s"]

    return render_template("portal/rfq_dashboard.html",
                           stages_data=stages_data, total_all=total_all, total_amount=total_amount,
                           open_by_rows=open_by_rows, source_rows=source_rows,
                           introducer_rows=introducer_rows, state_rows=state_rows, job_code_rows=job_code_rows,
                           recent=recent, staff_stats=staff_stats, total_profit=total_profit, total_cost=total_cost)


# ---- RFQ Stage List ----
@app.route("/portal/rfq/stage/<stage>")
@staff_required
def rfq_stage_list(stage):
    stage = stage.upper()
    if stage not in RFQ_STAGES:
        stage = "RFQ"
    rows = q("SELECT * FROM rfq_entries WHERE stage = ? ORDER BY id DESC", (stage,))
    stage_counts = {}
    for s in RFQ_STAGES:
        stage_counts[s] = q("SELECT COUNT(*) c FROM rfq_entries WHERE stage = ?", (s,), one=True)["c"]
    lists = {lt: _rfq_dropdown(lt) for lt in ["job_code","job_status","introducer","source","open_by","job_title","level"]}
    return render_template("portal/rfq_stage_list.html", stage=stage, rows=rows, stages=RFQ_STAGES, stage_counts=stage_counts, lists=lists)


# ---- RFQ Inline Update (from stage list) ----
@app.route("/portal/rfq/<int:eid>/inline-update", methods=["POST"])
@staff_required
def rfq_inline_update(eid):
    e = q("SELECT * FROM rfq_entries WHERE id = ?", (eid,), one=True)
    if not e:
        abort(404)
    f = request.form
    fields_map = {
        "client_name": "client_name", "job_code": "job_code", "job_title": "job_title",
        "amount": "amount", "location": "location", "state": "state", "date": "date",
        "job_status": "job_status", "level": "level", "introducer": "introducer",
        "source": "source", "open_by": "open_by", "notes": "notes"
    }
    field = f.get("field", "")
    value = f.get("value", "").strip()
    if field in fields_map:
        col = fields_map[field]
        if field == "amount":
            value = float(value or 0)
        execute(f"UPDATE rfq_entries SET {col} = ?, updated_at = ? WHERE id = ?",
                (value, datetime.utcnow().isoformat(), eid))
        flash(f"{field.replace('_',' ').title()} updated.", "ok")
    return redirect(request.referrer or url_for("rfq_stage_list", stage=e["stage"]))


# ---- RFQ New ----
@app.route("/portal/rfq/new", methods=["GET", "POST"])
@staff_required
def rfq_new():
    if request.method == "POST":
        f = request.form
        rfq_id = _next_rfq_id()
        now = datetime.utcnow().isoformat()
        
        # Handle remark image clipboard paste (base64) or file upload or URL
        b64_img = f.get("remark_image_base64", "").strip()
        rm_file = request.files.get("remark_image_file")
        if b64_img:
            saved_b64 = _save_base64_image(b64_img)
            remark_img = saved_b64 if saved_b64 else f.get("remark_image","").strip()
        elif rm_file and rm_file.filename:
            remark_img = save_machinery_file(rm_file, RFQ_IMG_DIR, "rfq_remark")
        else:
            remark_img = f.get("remark_image","").strip()

        entry_id = execute("""INSERT INTO rfq_entries (rfq_id, client_name, job_code, job_title, amount, location, state, date,
                    job_status, level, introducer, source, open_by, stage, commission, total_cost, net_profit,
                    deposit_pct, introducer_comm_pct, introducer_comm_amt, manager_comm_pct, manager_comm_amt, gross_profit,
                    contact_number, email, person_in_charge, map_link, notes,
                    machinery_pmt, machinery_pma, machinery_pmd, machinery_general, machinery_other,
                    issue_notes, progress_notes, terms_conditions, remark_text, remark_image,
                    created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (rfq_id, f.get("client_name","").strip(), f.get("job_code",""), f.get("job_title",""), float(f.get("amount",0) or 0),
                 f.get("location","").strip(), f.get("state","").strip(), f.get("date",""),
                 f.get("job_status","NEW TASK"), f.get("level",""), f.get("introducer",""), f.get("source",""), f.get("open_by",""),
                 "RFQ", float(f.get("commission",0) or 0), float(f.get("total_cost",0) or 0), float(f.get("net_profit",0) or 0),
                 float(f.get("deposit_pct",0) or 0), float(f.get("introducer_comm_pct",0) or 0), float(f.get("introducer_comm_amt",0) or 0),
                 float(f.get("manager_comm_pct",0) or 0), float(f.get("manager_comm_amt",0) or 0), float(f.get("gross_profit",0) or 0),
                 f.get("contact_number","").strip(), f.get("email","").strip(), f.get("person_in_charge","").strip(),
                 f.get("map_link","").strip(), f.get("notes","").strip(),
                 int(f.get("machinery_pmt",0) or 0), int(f.get("machinery_pma",0) or 0), int(f.get("machinery_pmd",0) or 0),
                 int(f.get("machinery_general",0) or 0), int(f.get("machinery_other",0) or 0),
                 f.get("issue_notes","").strip(), f.get("progress_notes","").strip(), f.get("terms_conditions","").strip(),
                 f.get("remark_text","").strip(), remark_img,
                 now, now))
        # Save quote items
        items_desc = request.form.getlist("item_desc[]")
        items_qty = request.form.getlist("item_qty[]")
        items_price = request.form.getlist("item_price[]")
        items_days = request.form.getlist("item_days[]")
        for i, desc in enumerate(items_desc):
            if desc.strip():
                qty = int(items_qty[i]) if i < len(items_qty) and items_qty[i] else 1
                price = float(items_price[i]) if i < len(items_price) and items_price[i] else 0
                days = int(items_days[i]) if i < len(items_days) and items_days[i] else 1
                execute("INSERT INTO rfq_items (rfq_entry_id, item_no, description, qty, unit_price, days, amount) VALUES (?,?,?,?,?,?,?)",
                        (entry_id, i+1, desc.strip(), qty, price, days, qty * price * days))
        # Save teamwork commissions
        tc_names = request.form.getlist("tc_name[]")
        tc_pcts = request.form.getlist("tc_pct[]")
        tc_amts = request.form.getlist("tc_amt[]")
        for i, name in enumerate(tc_names):
            if name.strip():
                pct = float(tc_pcts[i]) if i < len(tc_pcts) and tc_pcts[i] else 0
                amt = float(tc_amts[i]) if i < len(tc_amts) and tc_amts[i] else 0
                execute("INSERT INTO rfq_team_commissions (rfq_entry_id, person_name, percentage, amount) VALUES (?,?,?,?)",
                        (entry_id, name.strip(), pct, amt))
        flash(f"RFQ {rfq_id} created.", "ok")
        return redirect(url_for("rfq_stage_list", stage="RFQ"))

    lists = {lt: _rfq_dropdown(lt) for lt in ["job_code","job_status","introducer","source","open_by","job_title","level"]}
    open_by_people = _rfq_dropdown("open_by")
    customers = q("SELECT * FROM rfq_customers ORDER BY name")
    return render_template("portal/rfq_form.html", e=None, lists=lists, customers=customers, team_comms=[], open_by_people=open_by_people)


# ---- RFQ Edit ----
@app.route("/portal/rfq/<int:eid>/edit", methods=["GET", "POST"])
@staff_required
def rfq_edit(eid):
    e = q("SELECT * FROM rfq_entries WHERE id = ?", (eid,), one=True)
    if not e:
        abort(404)
    if request.method == "POST":
        f = request.form
        now = datetime.utcnow().isoformat()
        
        # Handle remark image clipboard paste (base64) or file upload or URL
        b64_img = f.get("remark_image_base64", "").strip()
        rm_file = request.files.get("remark_image_file")
        if b64_img:
            saved_b64 = _save_base64_image(b64_img)
            remark_img = saved_b64 if saved_b64 else e.get("remark_image", "")
        elif rm_file and rm_file.filename:
            remark_img = save_machinery_file(rm_file, RFQ_IMG_DIR, "rfq_remark")
        else:
            remark_img = f.get("remark_image", "") if f.get("remark_image", "") else e.get("remark_image", "")

        execute("""UPDATE rfq_entries SET client_name=?, job_code=?, job_title=?, amount=?, location=?, state=?, date=?,
                    job_status=?, level=?, introducer=?, source=?, open_by=?, commission=?, total_cost=?, net_profit=?,
                    deposit_pct=?, introducer_comm_pct=?, introducer_comm_amt=?, manager_comm_pct=?, manager_comm_amt=?, gross_profit=?,
                    contact_number=?, email=?, person_in_charge=?, map_link=?, notes=?,
                    machinery_pmt=?, machinery_pma=?, machinery_pmd=?, machinery_general=?, machinery_other=?,
                    issue_notes=?, progress_notes=?, terms_conditions=?, remark_text=?, remark_image=?,
                    updated_at=? WHERE id=?""",
                (f.get("client_name","").strip(), f.get("job_code",""), f.get("job_title",""), float(f.get("amount",0) or 0),
                 f.get("location","").strip(), f.get("state","").strip(), f.get("date",""),
                 f.get("job_status",""), f.get("level",""), f.get("introducer",""), f.get("source",""), f.get("open_by",""),
                 float(f.get("commission",0) or 0), float(f.get("total_cost",0) or 0), float(f.get("net_profit",0) or 0),
                 float(f.get("deposit_pct",0) or 0), float(f.get("introducer_comm_pct",0) or 0), float(f.get("introducer_comm_amt",0) or 0),
                 float(f.get("manager_comm_pct",0) or 0), float(f.get("manager_comm_amt",0) or 0), float(f.get("gross_profit",0) or 0),
                 f.get("contact_number","").strip(), f.get("email","").strip(), f.get("person_in_charge","").strip(),
                 f.get("map_link","").strip(), f.get("notes","").strip(),
                 int(f.get("machinery_pmt",0) or 0), int(f.get("machinery_pma",0) or 0), int(f.get("machinery_pmd",0) or 0),
                 int(f.get("machinery_general",0) or 0), int(f.get("machinery_other",0) or 0),
                 f.get("issue_notes","").strip(), f.get("progress_notes","").strip(), f.get("terms_conditions","").strip(),
                 f.get("remark_text","").strip(), remark_img,
                 now, eid))
        # Update quote items
        execute("DELETE FROM rfq_items WHERE rfq_entry_id = ?", (eid,))
        items_desc = request.form.getlist("item_desc[]")
        items_qty = request.form.getlist("item_qty[]")
        items_price = request.form.getlist("item_price[]")
        items_days = request.form.getlist("item_days[]")
        for i, desc in enumerate(items_desc):
            if desc.strip():
                qty = int(items_qty[i]) if i < len(items_qty) and items_qty[i] else 1
                price = float(items_price[i]) if i < len(items_price) and items_price[i] else 0
                days = int(items_days[i]) if i < len(items_days) and items_days[i] else 1
                execute("INSERT INTO rfq_items (rfq_entry_id, item_no, description, qty, unit_price, days, amount) VALUES (?,?,?,?,?,?,?)",
                        (eid, i+1, desc.strip(), qty, price, days, qty * price * days))
        # Update teamwork commissions
        execute("DELETE FROM rfq_team_commissions WHERE rfq_entry_id = ?", (eid,))
        tc_names = request.form.getlist("tc_name[]")
        tc_pcts = request.form.getlist("tc_pct[]")
        tc_amts = request.form.getlist("tc_amt[]")
        for i, name in enumerate(tc_names):
            if name.strip():
                pct = float(tc_pcts[i]) if i < len(tc_pcts) and tc_pcts[i] else 0
                amt = float(tc_amts[i]) if i < len(tc_amts) and tc_amts[i] else 0
                execute("INSERT INTO rfq_team_commissions (rfq_entry_id, person_name, percentage, amount) VALUES (?,?,?,?)",
                        (eid, name.strip(), pct, amt))
        flash(f"RFQ {e['rfq_id']} updated.", "ok")
        return redirect(url_for("rfq_stage_list", stage=e["stage"]))

    lists = {lt: _rfq_dropdown(lt) for lt in ["job_code","job_status","introducer","source","open_by","job_title","level"]}
    items = q("SELECT * FROM rfq_items WHERE rfq_entry_id = ? ORDER BY item_no", (eid,))
    team_comms = q("SELECT * FROM rfq_team_commissions WHERE rfq_entry_id = ? ORDER BY id", (eid,))
    open_by_people = _rfq_dropdown("open_by")
    customers = q("SELECT * FROM rfq_customers ORDER BY name")
    return render_template("portal/rfq_form.html", e=e, lists=lists, items=items, customers=customers, team_comms=team_comms, open_by_people=open_by_people)


# ---- RFQ Folder Explorer View ----
@app.route("/portal/rfq/<int:eid>/folder")
@staff_required
def rfq_folder(eid):
    e = q("SELECT * FROM rfq_entries WHERE id = ?", (eid,), one=True)
    if not e:
        abort(404)
    items = q("SELECT * FROM rfq_items WHERE rfq_entry_id = ? ORDER BY item_no", (eid,))
    reports = q("""SELECT r.*, m.name AS machinery_name FROM reports r
                   JOIN machinery m ON m.id = r.machinery_id
                   ORDER BY r.id DESC""")
    files_list = [
        {
            "name": f"{e['rfq_id']}_V6_RFQ_Master_Quotation.html",
            "type": "html",
            "icon": "📑",
            "category": "RFQ Summary & Quotation (V6 Sheet)",
            "size": "48 KB",
            "date": e["created_at"][:10] if e.get("created_at") else "",
            "link": url_for("rfq_detail", eid=e["id"]),
            "action": "Open V6 RFQ Sheet"
        }
    ]
    if e.get("remark_image"):
        img_src = e["remark_image"] if e["remark_image"].startswith("http") else url_for("serve_rfq_img", filename=e["remark_image"])
        files_list.append({
            "name": f"{e['rfq_id']}_Remark_SitePhoto.png",
            "type": "image",
            "icon": "📷",
            "category": "Remark Image / Site Attachment",
            "size": "240 KB",
            "date": e["updated_at"][:10] if e.get("updated_at") else "",
            "link": img_src,
            "action": "View Full Image"
        })
    for r in reports[:3]:
        files_list.append({
            "name": f"DOSH_Report_{r['id']}_{r['machinery_name']}.pdf",
            "type": "pdf",
            "icon": "📄",
            "category": f"Statutory Report ({r['report_type']})",
            "size": "1.4 MB",
            "date": r["created_at"][:10] if r.get("created_at") else "",
            "link": url_for("reports_list"),
            "action": "View Report PDF"
        })
    files_list.append({
        "name": f"{e['rfq_id']}_Official_Invoice_Form.pdf",
        "type": "pdf",
        "icon": "📝",
        "category": "Invoice & Form PDF",
        "size": "380 KB",
        "date": e["date"] if e.get("date") else "",
        "link": url_for("pdf_list"),
        "action": "Open PDF Forms"
    })
    return render_template("portal/rfq_folder.html", e=e, items=items, files_list=files_list)


# ---- RFQ Detail (Template View) ----
@app.route("/portal/rfq/<int:eid>/detail")
@staff_required
def rfq_detail(eid):
    e = q("SELECT * FROM rfq_entries WHERE id = ?", (eid,), one=True)
    if not e:
        abort(404)
    items = q("SELECT * FROM rfq_items WHERE rfq_entry_id = ? ORDER BY item_no", (eid,))
    team_comms = q("SELECT * FROM rfq_team_commissions WHERE rfq_entry_id = ? ORDER BY id", (eid,))
    total_quote = sum(float(it["amount"] or 0) for it in items)
    total_team_comm = sum(float(tc["amount"] or 0) for tc in team_comms)
    return render_template("portal/rfq_detail.html", e=e, items=items, total_quote=total_quote, team_comms=team_comms, total_team_comm=total_team_comm)


# ---- RFQ Move Stage ----
@app.route("/portal/rfq/<int:eid>/move", methods=["POST"])
@staff_required
def rfq_move(eid):
    new_stage = request.form.get("new_stage", "").upper()
    if new_stage not in RFQ_STAGES:
        flash("Invalid stage.", "err")
        return redirect(request.referrer or url_for("rfq_dashboard"))
    execute("UPDATE rfq_entries SET stage = ?, updated_at = ? WHERE id = ?",
            (new_stage, datetime.utcnow().isoformat(), eid))
    flash(f"RFQ moved to {new_stage}.", "ok")
    return redirect(request.referrer or url_for("rfq_stage_list", stage=new_stage))


# ---- RFQ Delete ----
@app.route("/portal/rfq/<int:eid>/delete", methods=["POST"])
@staff_required
def rfq_delete(eid):
    execute("DELETE FROM rfq_items WHERE rfq_entry_id = ?", (eid,))
    execute("DELETE FROM rfq_team_commissions WHERE rfq_entry_id = ?", (eid,))
    execute("DELETE FROM rfq_entries WHERE id = ?", (eid,))
    flash("RFQ deleted.", "ok")
    return redirect(request.referrer or url_for("rfq_dashboard"))


# ---- RFQ Customers ----
@app.route("/portal/rfq-customers")
@admin_required
def rfq_customers_list():
    rows = q("SELECT * FROM rfq_customers ORDER BY id DESC")
    return render_template("portal/rfq_customers.html", customers=rows)


@app.route("/portal/rfq-customers/new", methods=["GET", "POST"])
@admin_required
def rfq_customer_new():
    if request.method == "POST":
        f = request.form
        execute("INSERT INTO rfq_customers (name, mobile, email, company_name, location, state, created_at) VALUES (?,?,?,?,?,?,?)",
                (f.get("name","").strip(), f.get("mobile","").strip(), f.get("email","").strip(),
                 f.get("company_name","").strip(), f.get("location","").strip(), f.get("state","").strip(),
                 datetime.utcnow().isoformat()))
        flash("Customer added.", "ok")
        return redirect(url_for("rfq_customers_list"))
    return render_template("portal/rfq_customer_form.html", c=None)


@app.route("/portal/rfq-customers/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def rfq_customer_edit(cid):
    c = q("SELECT * FROM rfq_customers WHERE id = ?", (cid,), one=True)
    if not c:
        abort(404)
    if request.method == "POST":
        f = request.form
        execute("UPDATE rfq_customers SET name=?, mobile=?, email=?, company_name=?, location=?, state=? WHERE id=?",
                (f.get("name","").strip(), f.get("mobile","").strip(), f.get("email","").strip(),
                 f.get("company_name","").strip(), f.get("location","").strip(), f.get("state","").strip(), cid))
        flash("Customer updated.", "ok")
        return redirect(url_for("rfq_customers_list"))
    return render_template("portal/rfq_customer_form.html", c=c)


@app.route("/portal/rfq-customers/<int:cid>/delete", methods=["POST"])
@admin_required
def rfq_customer_delete(cid):
    execute("DELETE FROM rfq_customers WHERE id = ?", (cid,))
    flash("Customer deleted.", "ok")
    return redirect(url_for("rfq_customers_list"))


# ---- RFQ Lists Management ----
@app.route("/portal/rfq-lists", methods=["GET", "POST"])
@admin_required
def rfq_lists_manage():
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "add":
            lt = request.form.get("list_type", "").strip()
            val = request.form.get("value", "").strip()
            if lt and val:
                execute("INSERT INTO rfq_lists (list_type, value, sort_order) VALUES (?,?,?)", (lt, val, 999))
                flash(f"'{val}' added to {lt}.", "ok")
        elif action == "delete":
            lid = request.form.get("list_id", "")
            if lid:
                execute("DELETE FROM rfq_lists WHERE id = ?", (int(lid),))
                flash("List item deleted.", "ok")
        return redirect(url_for("rfq_lists_manage"))

    all_types = ["job_code", "job_status", "introducer", "source", "open_by", "job_title", "level"]
    lists_data = {}
    for lt in all_types:
        lists_data[lt] = q("SELECT * FROM rfq_lists WHERE list_type = ? ORDER BY sort_order, id", (lt,))
    return render_template("portal/rfq_lists_manage.html", lists_data=lists_data, all_types=all_types)


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
