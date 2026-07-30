"""SQLite database layer for Tijarah Mabrur portal."""
import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "tijarah.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    reg_no TEXT DEFAULT '',                      -- SSM / ROC number
    address TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    logo_filename TEXT DEFAULT '',               -- stored under uploads/logos/
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'client',        -- 'admin' | 'client'
    company TEXT DEFAULT '',
    company_id INTEGER,                          -- tenant link (NULL for admins)
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS machinery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,                      -- Pressure Vessel | Lifting Device | Boiler | Compressor | Other
    serial_no TEXT DEFAULT '',
    cert_no TEXT DEFAULT '',                     -- PMA / PMT / PMD cert number
    location TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Active',       -- Active | Under Maintenance | Expired
    next_inspection TEXT DEFAULT '',             -- ISO date
    owner_id INTEGER,                            -- client user id (NULL = company owned)
    company_id INTEGER,                          -- tenant company
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machinery_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    report_type TEXT NOT NULL DEFAULT 'Inspection',  -- Inspection | Calibration | Maintenance | NDT
    summary TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Draft',        -- Draft | Submitted | Approved
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (machinery_id) REFERENCES machinery(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS pdf_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    filename TEXT NOT NULL,
    fields_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pdf_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    machinery_id INTEGER,
    data_json TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (template_id) REFERENCES pdf_templates(id),
    FOREIGN KEY (machinery_id) REFERENCES machinery(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_machinery_owner ON machinery(owner_id);
CREATE INDEX IF NOT EXISTS idx_reports_machinery ON reports(machinery_id);
CREATE INDEX IF NOT EXISTS idx_submissions_template ON pdf_submissions(template_id);
"""

# Indexes on columns added by migration must be created AFTER _migrate()
INDEXES_AFTER_MIGRATION = """
CREATE INDEX IF NOT EXISTS idx_machinery_company ON machinery(company_id);
CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id);
"""


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL mode + tuned pragmas: safe for many concurrent readers (SaaS-scale on SQLite)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _migrate(conn):
    """Add new columns to existing databases (idempotent)."""
    for table, col, ddl in [
        ("users", "company_id", "ALTER TABLE users ADD COLUMN company_id INTEGER"),
        ("machinery", "company_id", "ALTER TABLE machinery ADD COLUMN company_id INTEGER"),
    ]:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
        if col not in cols:
            conn.execute(ddl)
    conn.commit()


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    _migrate(conn)
    conn.executescript(INDEXES_AFTER_MIGRATION)
    conn.commit()

    # Seed admin account
    admin_email = "muhammadsaifudinmj@gmail.com"
    row = conn.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, company, created_at) VALUES (?,?,?,?,?,?)",
            ("Muhammad Saifudin", admin_email, generate_password_hash("admin"),
             "admin", "Tijarah Mabrur (M) Sdn. Bhd.", datetime.utcnow().isoformat()),
        )
        conn.commit()

    # Seed a sample client company + user + machinery for demo
    row = conn.execute("SELECT id FROM companies WHERE name = ?", ("Demo Industries Sdn. Bhd.",)).fetchone()
    if row is None:
        cur = conn.execute(
            "INSERT INTO companies (name, reg_no, address, phone, logo_filename, created_at) VALUES (?,?,?,?,?,?)",
            ("Demo Industries Sdn. Bhd.", "202001000000 (0000000-X)",
             "No. 1, Jalan Industri, 40000 Shah Alam, Selangor.", "+603 5000 0000",
             "", datetime.utcnow().isoformat()),
        )
        conn.commit()
        demo_company_id = cur.lastrowid
    else:
        demo_company_id = row[0]

    client_email = "client@demo.com"
    row = conn.execute("SELECT id FROM users WHERE email = ?", (client_email,)).fetchone()
    if row is None:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, role, company, company_id, created_at) VALUES (?,?,?,?,?,?,?)",
            ("Demo Client", client_email, generate_password_hash("client"),
             "client", "Demo Industries Sdn. Bhd.", demo_company_id,
             datetime.utcnow().isoformat()),
        )
        conn.commit()
        client_id = cur.lastrowid
        now = datetime.utcnow().isoformat()
        conn.executemany(
            """INSERT INTO machinery (name, category, serial_no, cert_no, location, status, next_inspection, owner_id, company_id, notes, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            [
                ("Air Receiver Tank A-101", "Pressure Vessel", "SN-AR-1001", "PMA-SEL-2024-0001", "Semenyih Yard", "Active", "2026-11-20", client_id, demo_company_id, "Annual DOSH inspection due", now),
                ("Overhead Crane OH-02", "Lifting Device", "SN-OC-2200", "PMA-SEL-2024-0142", "Semenyih Yard", "Active", "2026-09-05", client_id, demo_company_id, "", now),
                ("Steam Boiler B-7", "Boiler", "SN-BL-7770", "PMA-JHR-2023-0910", "Bandar Penawar", "Under Maintenance", "2026-08-01", client_id, demo_company_id, "Burner service in progress", now),
                ("Puma Compressor PU-550", "Compressor", "SN-PU-5550", "-", "HQ Setapak", "Active", "2027-01-15", None, None, "Company demo unit", now),
            ],
        )
        conn.commit()
        admin = conn.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
        conn.executemany(
            """INSERT INTO reports (machinery_id, title, report_type, summary, status, created_by, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            [
                (1, "Annual Statutory Inspection - A-101", "Inspection", "Vessel inspected per OSHA 1994 & Factory and Machinery Act. No defects found.", "Approved", admin["id"], now),
                (3, "Boiler Burner Maintenance", "Maintenance", "Burner nozzle replaced, combustion test passed.", "Submitted", admin["id"], now),
            ],
        )
        conn.commit()
    conn.close()


# ---------- helpers ----------
def q(sql, args=(), one=False):
    conn = get_db()
    try:
        cur = conn.execute(sql, args)
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def execute(sql, args=()):
    conn = get_db()
    try:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
