"""Database layer for Tijarah Mabrur portal (PostgreSQL + SQLite fallback)."""
import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "tijarah.db")
DATABASE_URL = os.getenv("DATABASE_URL")

_ENGINE = None
_PLACEHOLDER = "?"


def _detect_engine():
    if DATABASE_URL:
        try:
            import psycopg2  # noqa: F401
            return "pg"
        except ImportError:
            pass
    return "sqlite"


_ENGINE = _detect_engine()
_PLACEHOLDER = "%s" if _ENGINE == "pg" else "?"
_pg_conn = None


def _pg_connect():
    global _pg_conn
    if _pg_conn is None or _pg_conn.closed:
        import psycopg2
        _pg_conn = psycopg2.connect(DATABASE_URL)
        _pg_conn.autocommit = False
    return _pg_conn


def _serial():
    return "SERIAL" if _ENGINE == "pg" else "INTEGER PRIMARY KEY AUTOINCREMENT"


SCHEMA = f"""
CREATE TABLE IF NOT EXISTS companies (
    id {_serial()},
    name TEXT NOT NULL UNIQUE,
    reg_no TEXT DEFAULT '',
    address TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    logo_filename TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id {_serial()},
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'client',
    company TEXT DEFAULT '',
    company_id INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS machinery (
    id {_serial()},
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    serial_no TEXT DEFAULT '',
    cert_no TEXT DEFAULT '',
    location TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Active',
    next_inspection TEXT DEFAULT '',
    owner_id INTEGER,
    company_id INTEGER,
    notes TEXT DEFAULT '',
    image_filename TEXT DEFAULT '',
    cert_type TEXT DEFAULT 'PMT',
    item_name TEXT DEFAULT '',
    mawp TEXT DEFAULT '',
    manufacturer TEXT DEFAULT '',
    volume TEXT DEFAULT '',
    year TEXT DEFAULT '',
    before_image TEXT DEFAULT '',
    medium TEXT DEFAULT '',
    serviced_date TEXT DEFAULT '',
    sv_image TEXT DEFAULT '',
    sv_size TEXT DEFAULT '',
    sv_type TEXT DEFAULT '',
    sv_set_pressure TEXT DEFAULT '',
    sv_calibrated_date TEXT DEFAULT '',
    pg_image TEXT DEFAULT '',
    pg_size TEXT DEFAULT '',
    pg_type TEXT DEFAULT '',
    pg_calibrated_date TEXT DEFAULT '',
    doc_design_approval TEXT DEFAULT '',
    doc_design_drawing TEXT DEFAULT '',
    doc_ht_cert TEXT DEFAULT '',
    doc_dosh TEXT DEFAULT '',
    doc_service_report TEXT DEFAULT '',
    doc_uttm_report TEXT DEFAULT '',
    doc_sv_cert TEXT DEFAULT '' ,
    doc_pg_cert TEXT DEFAULT '',
    doc_cof TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS machinery_images (
    id {_serial()},
    machinery_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    caption TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id {_serial()},
    machinery_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    report_type TEXT NOT NULL DEFAULT 'Inspection',
    summary TEXT DEFAULT '',
    pdf_filename TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Draft',
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pdf_templates (
    id {_serial()},
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    filename TEXT NOT NULL,
    fields_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pdf_submissions (
    id {_serial()},
    template_id INTEGER NOT NULL,
    machinery_id INTEGER,
    data_json TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expiry_reminders (
    id {_serial()},
    machinery_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    reminder_date TEXT NOT NULL,
    days_before INTEGER NOT NULL DEFAULT 30,
    sent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_machinery_owner ON machinery(owner_id);
CREATE INDEX IF NOT EXISTS idx_machinery_company ON machinery(company_id);
CREATE INDEX IF NOT EXISTS idx_reports_machinery ON reports(machinery_id);
CREATE INDEX IF NOT EXISTS idx_submissions_template ON pdf_submissions(template_id);
CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_machinery_images_mid ON machinery_images(machinery_id);
CREATE INDEX IF NOT EXISTS idx_expiry_reminders_mid ON expiry_reminders(machinery_id);
CREATE INDEX IF NOT EXISTS idx_expiry_reminders_sent ON expiry_reminders(sent);
"""


def _migrate(conn):
    machinery_cols = [
        ("cert_type", "TEXT DEFAULT 'PMT'"),
        ("item_name", "TEXT DEFAULT ''"),
        ("mawp", "TEXT DEFAULT ''"),
        ("manufacturer", "TEXT DEFAULT ''"),
        ("volume", "TEXT DEFAULT ''"),
        ("year", "TEXT DEFAULT ''"),
        ("before_image", "TEXT DEFAULT ''"),
        ("medium", "TEXT DEFAULT ''"),
        ("serviced_date", "TEXT DEFAULT ''"),
        ("sv_image", "TEXT DEFAULT ''"),
        ("sv_size", "TEXT DEFAULT ''"),
        ("sv_type", "TEXT DEFAULT ''"),
        ("sv_set_pressure", "TEXT DEFAULT ''"),
        ("sv_calibrated_date", "TEXT DEFAULT ''"),
        ("pg_image", "TEXT DEFAULT ''"),
        ("pg_size", "TEXT DEFAULT ''"),
        ("pg_type", "TEXT DEFAULT ''"),
        ("pg_calibrated_date", "TEXT DEFAULT ''"),
        ("doc_design_approval", "TEXT DEFAULT ''"),
        ("doc_design_drawing", "TEXT DEFAULT ''"),
        ("doc_ht_cert", "TEXT DEFAULT ''"),
        ("doc_dosh", "TEXT DEFAULT ''"),
        ("doc_service_report", "TEXT DEFAULT ''"),
        ("doc_uttm_report", "TEXT DEFAULT ''"),
        ("doc_sv_cert", "TEXT DEFAULT ''"),
        ("doc_pg_cert", "TEXT DEFAULT ''"),
        ("doc_cof", "TEXT DEFAULT ''"),
    ]
    if _ENGINE == "sqlite":
        for table, col, ddl in [
            ("users", "company_id", "ALTER TABLE users ADD COLUMN company_id INTEGER"),
            ("machinery", "company_id", "ALTER TABLE machinery ADD COLUMN company_id INTEGER"),
            ("machinery", "image_filename", "ALTER TABLE machinery ADD COLUMN image_filename TEXT DEFAULT ''"),
            ("companies", "email", "ALTER TABLE companies ADD COLUMN email TEXT DEFAULT ''"),
            ("reports", "pdf_filename", "ALTER TABLE reports ADD COLUMN pdf_filename TEXT DEFAULT ''"),
        ] + [("machinery", col, f"ALTER TABLE machinery ADD COLUMN {col} {col_type}") for col, col_type in machinery_cols]:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
            if col not in cols:
                conn.execute(ddl)
        for table_ddl in [
            """CREATE TABLE IF NOT EXISTS machinery_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machinery_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                caption TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS expiry_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machinery_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                reminder_date TEXT NOT NULL,
                days_before INTEGER NOT NULL DEFAULT 30,
                sent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )""",
        ]:
            conn.execute(table_ddl)
        conn.commit()
    else:
        cur = conn.cursor()
        for table, col, col_type in [
            ("users", "company_id", "INTEGER"),
            ("machinery", "company_id", "INTEGER"),
            ("machinery", "image_filename", "TEXT DEFAULT ''"),
            ("companies", "email", "TEXT DEFAULT ''"),
            ("reports", "pdf_filename", "TEXT DEFAULT ''"),
        ] + [("machinery", col, col_type) for col, col_type in machinery_cols]:
            try:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except Exception:
                conn.rollback()
            else:
                conn.commit()
        for table_ddl in [
            """CREATE TABLE IF NOT EXISTS machinery_images (
                id SERIAL PRIMARY KEY,
                machinery_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                caption TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS expiry_reminders (
                id SERIAL PRIMARY KEY,
                machinery_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                reminder_date TEXT NOT NULL,
                days_before INTEGER NOT NULL DEFAULT 30,
                sent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )""",
        ]:
            try:
                cur.execute(table_ddl)
            except Exception:
                conn.rollback()
            else:
                conn.commit()


def get_db():
    if _ENGINE == "pg":
        return _pg_connect()
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def init_db():
    if _ENGINE == "pg":
        conn = _pg_connect()
        cur = conn.cursor()
        for stmt in SCHEMA.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    cur.execute(stmt)
                except Exception:
                    conn.rollback()
        conn.commit()
        _migrate(conn)
        for stmt in INDEXES.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    cur.execute(stmt)
                except Exception:
                    conn.rollback()
        conn.commit()
    else:
        conn = get_db()
        conn.executescript(SCHEMA)
        conn.commit()
        _migrate(conn)
        conn.executescript(INDEXES)
        conn.commit()

    admin_email = "muhammadsaifudinmj@gmail.com"
    row = q("SELECT id FROM users WHERE email = ?", (admin_email,), one=True)
    if row is None:
        execute(
            "INSERT INTO users (name, email, password_hash, role, company, created_at) VALUES (?,?,?,?,?,?)",
            ("Muhammad Saifudin", admin_email, generate_password_hash("admin"),
             "admin", "Tijarah Mabrur (M) Sdn. Bhd.", datetime.utcnow().isoformat()),
        )

    row = q("SELECT id FROM companies WHERE name = ?", ("Demo Industries Sdn. Bhd.",), one=True)
    if row is None:
        cid = execute(
            "INSERT INTO companies (name, reg_no, address, phone, email, logo_filename, created_at) VALUES (?,?,?,?,?,?,?)",
            ("Demo Industries Sdn. Bhd.", "202001000000 (0000000-X)",
             "No. 1, Jalan Industri, 40000 Shah Alam, Selangor.", "+603 5000 0000",
             "demo@demo.com", "", datetime.utcnow().isoformat()),
        )
        demo_company_id = cid
    else:
        demo_company_id = row["id"] if _ENGINE == "pg" else row[0]

    client_email = "client@demo.com"
    row = q("SELECT id FROM users WHERE email = ?", (client_email,), one=True)
    if row is None:
        cid2 = execute(
            "INSERT INTO users (name, email, password_hash, role, company, company_id, created_at) VALUES (?,?,?,?,?,?,?)",
            ("Demo Client", client_email, generate_password_hash("client"),
             "client", "Demo Industries Sdn. Bhd.", demo_company_id,
             datetime.utcnow().isoformat()),
        )
        client_id = cid2
        
        # Default Employee user
        execute(
            "INSERT INTO users (name, email, password_hash, role, company, company_id, created_at) VALUES (?,?,?,?,?,?,?)",
            ("Demo Employee", "employee@demo.com", generate_password_hash("employee"),
             "employee", "Demo Industries Sdn. Bhd.", demo_company_id,
             datetime.utcnow().isoformat()),
        )

        now = datetime.utcnow().isoformat()
        for m_data in [
            ("Air Receiver Tank A-101", "Pressure Vessel", "SN-AR-1001", "PMA-SEL-2024-0001", "Semenyih Yard", "Active", "2026-11-20", client_id, demo_company_id, "Annual DOSH inspection due", now),
            ("Overhead Crane OH-02", "Lifting Device", "SN-OC-2200", "PMA-SEL-2024-0142", "Semenyih Yard", "Active", "2026-09-05", client_id, demo_company_id, "", now),
            ("Steam Boiler B-7", "Boiler", "SN-BL-7770", "PMA-JHR-2023-0910", "Bandar Penawar", "Under Maintenance", "2026-08-01", client_id, demo_company_id, "Burner service in progress", now),
            ("Puma Compressor PU-550", "Compressor", "SN-PU-5550", "-", "HQ Setapak", "Active", "2027-01-15", None, None, "Company demo unit", now),
        ]:
            execute(
                "INSERT INTO machinery (name, category, serial_no, cert_no, location, status, next_inspection, owner_id, company_id, notes, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                m_data,
            )
        admin = q("SELECT id FROM users WHERE email = ?", (admin_email,), one=True)
        admin_id = admin["id"] if _ENGINE == "pg" else admin[0]
        for r_data in [
            (1, "Annual Statutory Inspection - A-101", "Inspection", "Vessel inspected per OSHA 1994. No defects found.", "Approved", admin_id, now),
            (3, "Boiler Burner Maintenance", "Maintenance", "Burner nozzle replaced, combustion test passed.", "Submitted", admin_id, now),
        ]:
            execute(
                "INSERT INTO reports (machinery_id, title, report_type, summary, status, created_by, created_at) VALUES (?,?,?,?,?,?,?)",
                r_data,
            )

    if _ENGINE == "pg":
        conn.close()


def _fetch_rows(cur, rows):
    if _ENGINE == "pg":
        cols = [desc[0] for desc in cur.description]
        return [dict(zip(cols, row)) for row in rows]
    return rows


def _fetch_one(cur, row):
    if row is None:
        return None
    if _ENGINE == "pg":
        cols = [desc[0] for desc in cur.description]
        return dict(zip(cols, row))
    return row


def q(sql, args=(), one=False):
    if _ENGINE == "pg":
        sql = sql.replace("?", "%s")
    if _ENGINE == "pg":
        conn = _pg_connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, args)
            rows = cur.fetchall()
            return _fetch_one(cur, rows[0] if rows else None) if one else _fetch_rows(cur, rows)
        finally:
            conn.close()
    else:
        conn = get_db()
        try:
            cur = conn.execute(sql, args)
            rows = cur.fetchall()
            return (rows[0] if rows else None) if one else rows
        finally:
            conn.close()


def execute(sql, args=()):
    if _ENGINE == "pg":
        sql = sql.replace("?", "%s")
    if _ENGINE == "pg":
        conn = _pg_connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, args)
            if "RETURNING id" in sql.upper():
                row = cur.fetchone()
                conn.commit()
                return row[0] if row else None
            conn.commit()
            return cur.lastrowid if hasattr(cur, 'lastrowid') and cur.lastrowid else None
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = get_db()
        try:
            cur = conn.execute(sql, args)
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
