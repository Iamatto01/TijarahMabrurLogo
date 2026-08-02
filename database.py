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

CREATE TABLE IF NOT EXISTS rfq_entries (
    id {_serial()},
    rfq_id TEXT NOT NULL,
    client_name TEXT DEFAULT '',
    job_code TEXT DEFAULT '',
    job_title TEXT DEFAULT '',
    amount REAL DEFAULT 0,
    location TEXT DEFAULT '',
    state TEXT DEFAULT '',
    date TEXT DEFAULT '',
    job_status TEXT DEFAULT 'NEW TASK',
    level TEXT DEFAULT '',
    introducer TEXT DEFAULT '',
    source TEXT DEFAULT '',
    open_by TEXT DEFAULT '',
    stage TEXT DEFAULT 'RFQ',
    commission REAL DEFAULT 0,
    total_cost REAL DEFAULT 0,
    net_profit REAL DEFAULT 0,
    deposit_pct REAL DEFAULT 0,
    introducer_comm_pct REAL DEFAULT 0,
    introducer_comm_amt REAL DEFAULT 0,
    manager_comm_pct REAL DEFAULT 0,
    manager_comm_amt REAL DEFAULT 0,
    gross_profit REAL DEFAULT 0,
    contact_number TEXT DEFAULT '',
    email TEXT DEFAULT '',
    person_in_charge TEXT DEFAULT '',
    map_link TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    machinery_pmt INTEGER DEFAULT 0,
    machinery_pma INTEGER DEFAULT 0,
    machinery_pmd INTEGER DEFAULT 0,
    machinery_general INTEGER DEFAULT 0,
    machinery_other INTEGER DEFAULT 0,
    issue_notes TEXT DEFAULT '',
    progress_notes TEXT DEFAULT '',
    terms_conditions TEXT DEFAULT '',
    remark_text TEXT DEFAULT '',
    remark_image TEXT DEFAULT '',
    cost_subcon_json TEXT DEFAULT '[]',
    cost_company_json TEXT DEFAULT '[]',
    owner_id INTEGER,
    company_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS rfq_items (
    id {_serial()},
    rfq_entry_id INTEGER NOT NULL,
    item_no INTEGER DEFAULT 1,
    description TEXT DEFAULT '',
    qty INTEGER DEFAULT 1,
    unit_price REAL DEFAULT 0,
    days INTEGER DEFAULT 1,
    amount REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rfq_team_commissions (
    id {_serial()},
    rfq_entry_id INTEGER NOT NULL,
    person_name TEXT NOT NULL,
    percentage REAL DEFAULT 0,
    amount REAL DEFAULT 0,
    payment_status TEXT DEFAULT '',
    payment_date TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS rfq_lists (
    id {_serial()},
    list_type TEXT NOT NULL,
    value TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rfq_customers (
    id {_serial()},
    name TEXT DEFAULT '',
    mobile TEXT DEFAULT '',
    email TEXT DEFAULT '',
    company_name TEXT DEFAULT '',
    location TEXT DEFAULT '',
    state TEXT DEFAULT '',
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
CREATE INDEX IF NOT EXISTS idx_rfq_entries_stage ON rfq_entries(stage);
CREATE INDEX IF NOT EXISTS idx_rfq_entries_owner ON rfq_entries(owner_id);
CREATE INDEX IF NOT EXISTS idx_rfq_items_entry ON rfq_items(rfq_entry_id);
CREATE INDEX IF NOT EXISTS idx_rfq_lists_type ON rfq_lists(list_type);
CREATE INDEX IF NOT EXISTS idx_rfq_team_comm ON rfq_team_commissions(rfq_entry_id);
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
            ("rfq_entries", "machinery_pmt", "ALTER TABLE rfq_entries ADD COLUMN machinery_pmt INTEGER DEFAULT 0"),
            ("rfq_entries", "machinery_pma", "ALTER TABLE rfq_entries ADD COLUMN machinery_pma INTEGER DEFAULT 0"),
            ("rfq_entries", "machinery_pmd", "ALTER TABLE rfq_entries ADD COLUMN machinery_pmd INTEGER DEFAULT 0"),
            ("rfq_entries", "machinery_general", "ALTER TABLE rfq_entries ADD COLUMN machinery_general INTEGER DEFAULT 0"),
            ("rfq_entries", "machinery_other", "ALTER TABLE rfq_entries ADD COLUMN machinery_other INTEGER DEFAULT 0"),
            ("rfq_entries", "issue_notes", "ALTER TABLE rfq_entries ADD COLUMN issue_notes TEXT DEFAULT ''"),
            ("rfq_entries", "progress_notes", "ALTER TABLE rfq_entries ADD COLUMN progress_notes TEXT DEFAULT ''"),
            ("rfq_entries", "terms_conditions", "ALTER TABLE rfq_entries ADD COLUMN terms_conditions TEXT DEFAULT ''"),
            ("rfq_entries", "remark_text", "ALTER TABLE rfq_entries ADD COLUMN remark_text TEXT DEFAULT ''"),
            ("rfq_entries", "remark_image", "ALTER TABLE rfq_entries ADD COLUMN remark_image TEXT DEFAULT ''"),
            ("rfq_entries", "cost_subcon_json", "ALTER TABLE rfq_entries ADD COLUMN cost_subcon_json TEXT DEFAULT '[]'"),
            ("rfq_entries", "cost_company_json", "ALTER TABLE rfq_entries ADD COLUMN cost_company_json TEXT DEFAULT '[]'"),
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
            ("rfq_entries", "machinery_pmt", "INTEGER DEFAULT 0"),
            ("rfq_entries", "machinery_pma", "INTEGER DEFAULT 0"),
            ("rfq_entries", "machinery_pmd", "INTEGER DEFAULT 0"),
            ("rfq_entries", "machinery_general", "INTEGER DEFAULT 0"),
            ("rfq_entries", "machinery_other", "INTEGER DEFAULT 0"),
            ("rfq_entries", "issue_notes", "TEXT DEFAULT ''"),
            ("rfq_entries", "progress_notes", "TEXT DEFAULT ''"),
            ("rfq_entries", "terms_conditions", "TEXT DEFAULT ''"),
            ("rfq_entries", "remark_text", "TEXT DEFAULT ''"),
            ("rfq_entries", "remark_image", "TEXT DEFAULT ''"),
            ("rfq_entries", "cost_subcon_json", "TEXT DEFAULT '[]'"),
            ("rfq_entries", "cost_company_json", "TEXT DEFAULT '[]'"),
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

    # ── RFQ seed data ──
    rfq_check = q("SELECT id FROM rfq_entries LIMIT 1", one=True)
    if rfq_check is None:
        now = datetime.utcnow().isoformat()
        # Seed dropdown lists
        list_seeds = [
            ("job_code", ["DOSH", "DOD1", "GSHC", "GSMC"]),
            ("job_status", ["NEW TASK", "Site Visit", "Assessment", "QUOTE", "Required more details", "PPCC", "Waiting info from client", "Ready to discuss", "Quotation sent", "Quotation received", "Quotation waiting for approval", "PO in progress", "PO ESTIMATI", "WORK PROGRESS", "Waiting for deposit", "INVOICE", "PAYMENT", "LOST"]),
            ("introducer", ["Mr. Mish", "Rico", "Shamsul JC", "A. Hafiz", "Faizt Bakhtiar"]),
            ("source", ["TMSR", "INSASR", "SPECTRO", "ADV", "SUPHIN", "3rd party"]),
            ("open_by", ["Shalhin", "Leena", "Salihah", "Shahrul", "Aiman"]),
            ("job_title", ["New Register", "Renew PMT/PMA", "Service Call", "GLOBAL INSPECTION", "Calibrate SV PG", "Design Approval"]),
            ("level", ["Low", "Medium", "High"]),
        ]
        for lt, vals in list_seeds:
            for i, v in enumerate(vals):
                execute("INSERT INTO rfq_lists (list_type, value, sort_order) VALUES (?,?,?)", (lt, v, i))

        # Seed customers
        cust_seeds = [
            ("Rosul", "012-8788955", "", "Lestro KL Sdn Bhd", "Kuchai", "Johor"),
            ("S Sanesswaran", "102432727", "sannes512@gmail.com", "Vantage MC Auto Sdn Bhd", "Telok Panglime Garang", "Selangor"),
            ("Angel", "012-670 2992", "", "Starkouch Ilo", "Klang", "Selangor"),
            ("Mr Yun", "013-8755338", "oylan-isca@emaling.com.my", "Bom Ying Glass", "Kepong", "Selangor"),
        ]
        for cs in cust_seeds:
            execute("INSERT INTO rfq_customers (name, mobile, email, company_name, location, state, created_at) VALUES (?,?,?,?,?,?,?)",
                    (*cs, now))

        # Seed sample RFQ entries
        rfq_seeds = [
            ("RFQ-26001", "Lestro KL Sdn Bhd", "DOSH", "New Register", 3000, "Rawang", "Selangor", "2026-06-01", "Site Visit", "Medium", "TMSR", "Shalhin", "RFQ"),
            ("RFQ-26002", "ABC Eng", "DOSH", "Renew PMT/PMA", 0, "Tg. Pelepas", "Johor", "2026-06-15", "NEW TASK", "High", "TMSR", "Shalhin", "RFQ"),
            ("RFQ-26003", "Vantage MC Auto Sdn Bhd", "DOD1", "Service Call", 15000, "Shah Alam", "Selangor", "2026-05-20", "Quotation sent", "Low", "ADV", "Leena", "QUO"),
            ("RFQ-26004", "IQDC Eng", "DOSH", "GLOBAL INSPECTION", 8500, "Kulim", "Kedah", "2026-04-10", "PO in progress", "", "INSASR", "Leena", "PO"),
            ("RFQ-26005", "Bom Ying Glass", "GSHC", "Calibrate SV PG", 2500, "Kepong", "Selangor", "2026-03-01", "INVOICE", "", "SPECTRO", "Shalhin", "INV"),
            ("RFQ-26006", "Top Glove Sdn Bhd", "DOD1", "New Register", 12000, "Klang", "Selangor", "2026-01-15", "PAYMENT", "", "TMSR", "Leena", "PYMT"),
        ]
        for rs in rfq_seeds:
            execute("""INSERT INTO rfq_entries (rfq_id, client_name, job_code, job_title, amount, location, state, date,
                        job_status, level, introducer, open_by, stage, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (*rs, now))

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
