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

    admin_email = "tmsb@tijarahmabrur.com"
    # Update existing admin account email if present
    execute("UPDATE users SET email = ? WHERE role = 'admin' OR email = 'muhammadsaifudinmj@gmail.com'", (admin_email,))
    
    row = q("SELECT id FROM users WHERE email = ?", (admin_email,), one=True)
    if row is None:
        execute(
            "INSERT INTO users (name, email, password_hash, role, company, created_at) VALUES (?,?,?,?,?,?)",
            ("TMSB Admin", admin_email, generate_password_hash("admin"),
             "admin", "Tijarah Mabrur (M) Sdn. Bhd.", datetime.utcnow().isoformat()),
        )

    # ── Seed Dozens of Companies & Clients for Demo ──
    companies_seed = [
        ("Petronas Chemicals Group Berhad", "199801003700", "Complex Kerteh, 24300 Kerteh, Terengganu", "+609-826 8000", "petronas@tijarahmabrur.com"),
        ("Top Glove Corporation Bhd", "199901004000", "Lot 4969, Jalan Tepi Sungai, 41100 Klang, Selangor", "+603-3392 1992", "topglove@tijarahmabrur.com"),
        ("Nestlé Products Sdn. Bhd.", "197901005000", "Batu Tiga Industrial Estate, 40000 Shah Alam, Selangor", "+603-5510 6888", "nestle@tijarahmabrur.com"),
        ("Shell Malaysia Trading Sdn. Bhd.", "196501001000", "Refinery Complex, 71000 Port Dickson, N.Sembilan", "+606-647 1311", "shell@tijarahmabrur.com"),
        ("Sime Darby Industrial Sdn. Bhd.", "198201002000", "1, Jalan Puchong, 47100 Puchong, Selangor", "+603-8060 8000", "simedarby@tijarahmabrur.com"),
        ("Tenaga Nasional Berhad (TNB)", "199001009000", "129, Jalan Bangsar, 59200 Kuala Lumpur", "+603-2296 5566", "tnb@tijarahmabrur.com"),
        ("Dialog Group Berhad", "198901008000", "Pengerang Deepwater Terminal, 81600 Pengerang, Johor", "+607-817 1000", "dialog@tijarahmabrur.com"),
        ("Sapura Energy Berhad", "201101007000", "Mines Resort City, 43300 Seri Kembangan, Selangor", "+603-8659 8888", "sapura@tijarahmabrur.com"),
        ("Gas Malaysia Berhad", "199201006000", "Seksyen 13, 40100 Shah Alam, Selangor", "+603-5518 0100", "gas@tijarahmabrur.com"),
        ("MISC Berhad", "196801000500", "Menara Dayabumi, 50050 Kuala Lumpur", "+603-2273 8088", "misc@tijarahmabrur.com"),
        ("Lotte Chemical Titan (M) Sdn. Bhd.", "199101003000", "PLO 312, 81700 Pasir Gudang, Johor", "+607-251 2111", "lotte@tijarahmabrur.com"),
        ("Boustead Heavy Industries Corp", "197101000800", "Pengkalan TLDM, 32100 Lumut, Perak", "+605-683 2111", "boustead@tijarahmabrur.com"),
        ("Westports Malaysia Sdn. Bhd.", "199301002200", "Pulau Indah, 42009 Port Klang, Selangor", "+603-3169 4000", "westports@tijarahmabrur.com"),
        ("MMC Corporation Berhad", "197601001100", "Jalan Sultan Ismail, 50250 Kuala Lumpur", "+603-2171 6000", "mmc@tijarahmabrur.com"),
        ("Lestro KL Sdn Bhd", "202101009900", "Kuchai Entrepreneurs Park, 58200 Kuala Lumpur", "+603-7980 1122", "lestro@tijarahmabrur.com"),
    ]

    now = datetime.utcnow().isoformat()
    machinery_templates = [
        ("Air Receiver Tank", "Pressure Vessel", "PMT"),
        ("Overhead Traveling Crane", "Lifting Device", "PMA"),
        ("Water Tube Steam Boiler", "Boiler", "PMD"),
        ("Screw Air Compressor", "Compressor", "PMT"),
        ("Heat Exchanger Vessel", "Pressure Vessel", "PMT"),
        ("Hydraulic Goods Hoist", "Lifting Device", "PMA"),
        ("Thermal Oil Heater", "Boiler", "PMD"),
        ("High Pressure Storage Tank", "Pressure Vessel", "PMT"),
    ]

    for i, (cname, reg, addr, phone, cemail) in enumerate(companies_seed):
        crow = q("SELECT id FROM companies WHERE name = ?", (cname,), one=True)
        if crow is None:
            cid = execute(
                "INSERT INTO companies (name, reg_no, address, phone, email, logo_filename, created_at) VALUES (?,?,?,?,?,?,?)",
                (cname, reg, addr, phone, cemail, "", now),
            )
        else:
            cid = crow["id"] if _ENGINE == "pg" else crow[0]

        # Seed Client Account for this Company if not existing
        urow = q("SELECT id FROM users WHERE email = ?", (cemail,), one=True)
        if urow is None:
            uid = execute(
                "INSERT INTO users (name, email, password_hash, role, company, company_id, created_at) VALUES (?,?,?,?,?,?,?)",
                (f"{cname} (PIC)", cemail, generate_password_hash("client123"), "client", cname, cid, now),
            )
        else:
            uid = urow["id"] if _ENGINE == "pg" else urow[0]

        # Seed Machinery items for this Company (2-3 machines per company)
        m_count = q("SELECT COUNT(*) c FROM machinery WHERE company_id = ?", (cid,), one=True)["c"]
        if m_count == 0:
            for j in range(2 + (i % 2)):
                m_name, m_cat, m_type = machinery_templates[(i + j) % len(machinery_templates)]
                sn = f"SN-{m_type}-{1000 + i*10 + j}"
                cert = f"{m_type}-DOSH-2024-{2000 + i*10 + j}"
                loc = addr.split(",")[-1].strip() if "," in addr else "Site Yard"
                status = "Active" if j == 0 else ("Under Maintenance" if j == 1 and i % 3 == 0 else "Active")
                next_insp = f"2026-{(10 + j) % 12 + 1:02d}-15"
                execute(
                    """INSERT INTO machinery (name, category, cert_type, serial_no, cert_no, location, status, next_inspection, owner_id, company_id, notes, created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (f"{m_name} #{j+1}", m_cat, m_type, sn, cert, loc, status, next_insp, uid, cid, "Statutory inspection verified per OSHA 1994", now)
                )

    # ── RFQ seed data ──
    rfq_count_row = q("SELECT COUNT(*) c FROM rfq_entries", one=True)
    rfq_count = rfq_count_row["c"] if rfq_count_row else 0
    if rfq_count < 100:
        execute("DELETE FROM rfq_items")
        execute("DELETE FROM rfq_entries")
        now = datetime.utcnow().isoformat()
        # Seed dropdown lists matching Master DB
        list_seeds = [
            ("job_code", ["DOSH", "DOD1", "EPCC", "Asset (PKNS)", "Assessment", "Training", "OSHC", "PPEai", "GSHC", "GSMC"]),
            ("job_status", ["NEW TASK", "Site Visit", "Assessment", "QUOTE", "Required more details", "PPCC", "Waiting info from client", "Ready to discuss", "Quotation sent", "Quotation received", "Quotation waiting for approval", "PO in progress", "PO ESTIMATI", "WORK PROGRESS", "Waiting for deposit", "INVOICE", "PAYMENT", "LOST"]),
            ("introducer", ["Doc", "Syukri", "A. Hafiz", "Zed", "Sharifah", "Captain", "Mr. Mish", "Rico", "Shamsul JC", "Faizt Bakhtiar"]),
            ("source", ["TMSB", "TMSR", "SPECTRO", "ADV", "INSASR", "SAFEAIR", "SUPHIN", "3rd party"]),
            ("open_by", ["Shalhin", "Leena", "Salihah", "Shahrul", "Aiman", "Rico", "Mish"]),
            ("job_title", ["New Register", "Renew PMT/PMA", "Service Call", "GLOBAL INSPECTION", "Calibrate SV PG", "Design Approval", "Hydrostatic Test", "UTTM Report"]),
            ("level", ["Low", "Medium", "High"]),
        ]
        for lt, vals in list_seeds:
            for i, v in enumerate(vals):
                execute("INSERT INTO rfq_lists (list_type, value, sort_order) VALUES (?,?,?)", (lt, v, i))

        # Seed Customers matching Master DB
        cust_seeds = [
            ("Petronas PIC", "012-8268000", "petronas@tijarahmabrur.com", "Petronas Chemicals Group Berhad", "Kerteh", "Terengganu"),
            ("Top Glove PIC", "013-3921992", "topglove@tijarahmabrur.com", "Top Glove Corporation Bhd", "Klang", "Selangor"),
            ("Nestlé PIC", "012-5510688", "nestle@tijarahmabrur.com", "Nestlé Products Sdn. Bhd.", "Shah Alam", "Selangor"),
            ("Shell PIC", "016-6471311", "shell@tijarahmabrur.com", "Shell Malaysia Trading Sdn. Bhd.", "Port Dickson", "N. Sembilan"),
            ("Sime Darby PIC", "013-8060800", "simedarby@tijarahmabrur.com", "Sime Darby Industrial Sdn. Bhd.", "Puchong", "Selangor"),
            ("TNB PIC", "012-2296556", "tnb@tijarahmabrur.com", "Tenaga Nasional Berhad (TNB)", "Jalan Bangsar", "Kuala Lumpur"),
            ("Dialog PIC", "017-8171000", "dialog@tijarahmabrur.com", "Dialog Group Berhad", "Pengerang", "Johor"),
            ("Sapura PIC", "013-8659888", "sapura@tijarahmabrur.com", "Sapura Energy Berhad", "Seri Kembangan", "Selangor"),
            ("Gas Malaysia PIC", "012-5518010", "gas@tijarahmabrur.com", "Gas Malaysia Berhad", "Shah Alam", "Selangor"),
            ("MISC PIC", "012-2273808", "misc@tijarahmabrur.com", "MISC Berhad", "Kuala Lumpur", "Kuala Lumpur"),
            ("Rosul", "012-8788955", "rosul@lestro.com", "Lestro KL Sdn Bhd", "Kuchai", "Kuala Lumpur"),
            ("S Sanesswaran", "010-2432727", "sannes512@gmail.com", "Vantage MC Auto Sdn Bhd", "Telok Panglime Garang", "Selangor"),
            ("Angel", "012-6702992", "angel@starkouch.com", "Starkouch Ilo", "Klang", "Selangor"),
            ("Mr Yun", "013-8755338", "oylan-isca@emaling.com.my", "Bom Ying Glass", "Kepong", "Selangor"),
        ]
        for cs in cust_seeds:
            execute("INSERT INTO rfq_customers (name, mobile, email, company_name, location, state, created_at) VALUES (?,?,?,?,?,?,?)",
                    (*cs, now))

        # Seed all 119 RFQ Entries from Tijarah Mabrur Master DB Google Sheet
        rfq_data_list = [
            ('RFQ-26194', 'Cgu Wong', 'DOSH', 'New Register', 0, 'Rawang', 'Selangor', '2026-06-16', 'BOSS to call!', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26197', 'MMC Prai', 'PPEai', 'PPE ai', 0, 'Prai', 'P. Pinang', '2026-05-19', 'Presentation', 'Medium', 'Doc', 'TMSB', 'Shalihin', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26247', 'SRN Utama Enterprise', 'Asset (PKNS)', 'Tangki Air', 0, 'Shah Alam', 'Selangor', '2026-06-29', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26204', 'Kedah', 'DOSH', 'Renewal PMT PMA', 0, 'Kedah', 'Kedah', '2026-06-19', 'Waiting info from client', 'Low', 'Doc', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26261', 'SRN Utama Enterprise', 'Asset (PKNS)', 'Bumbung Sek 20 Blok 15', 17999.87, 'Shah Alam', 'Selangor', '2026-07-06', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 18100, -100.13, -100.13, 0, 0, 0, 0, 0),
            ('RFQ-26268', 'XSD Paper International Sdn Bhd', 'DOSH', 'Service PMA', 11900, 'Padang Serai', 'Kedah', '2026-07-08', 'NEW TASK', 'Low', 'Doc', 'TMSB', 'Leena', 'RFQ', 9350, 2550, 2550, 0, 0, 0, 0, 0),
            ('RFQ-26264', 'Spectroscience Laboratories Sdn Bhd', 'DOSH', 'UTTM', 0, 'Petaling', 'Selangor', '2026-07-07', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26200', 'Ken Ying Glass Sdn Bhd', 'DOSH', 'New Register', 0, 'Kepong', 'Selangor', '2026-06-19', 'Waiting info from client', 'Low', 'Zed', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26265', 'Spectroscience Laboratories Sdn Bhd', 'DOSH', 'Load', 6500, 'Petaling', 'Selangor', '2026-07-07', 'Ready to discuss', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 4175, 2325, 2325, 0, 0, 0, 0, 0),
            ('RFQ-26178', 'Pineng', 'DOSH', 'Inspection', 0, 'George Town', 'P. Pinang', '2026-06-01', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26270', 'Menate', 'Training', 'OSHC', 0, 'Setapak', 'Kuala Lumpur', '2026-07-10', 'Waiting info from client', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26252', 'mamat Kat johor', 'DOSH', 'Verify 3rd party', 0, 'Johor Bahru', 'Johor', '2026-07-01', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26269', 'Darrien', 'DOSH', 'NR', 0, 'Cyberjaya', 'Selangor', '2026-07-09', 'Waiting info from client', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26284', 'OSHC PUBLIC', 'OSHC', 'OSHC', 2597, 'Cheras', 'Kuala Lumpur', '2026-07-23', 'Work done!', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 696.5, 1900.5, 1900.5, 0, 0, 0, 0, 0),
            ('RFQ-26285', 'MK', 'Assessment', 'EIA', 0, 'Johor Bahru', 'Johor', '2026-07-24', 'Waiting info from client', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26289', 'SJE Eng', 'DOSH', 'Inspection', 0, 'Puncak Alam', 'Selangor', '2026-07-27', 'Waiting info from client', 'Low', 'Sharifah', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26291', 'OGPC SDN BHD', 'EPCC', 'Coolant', 0, 'Shah Alam', 'Selangor', '2026-07-27', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26297', 'Airflux Malaysia Sdn Bhd', 'DOSH', 'Design Approval', 12000, 'Klang', 'Selangor', '2026-07-30', 'Required more details', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 0, 12000, 12000, 0, 0, 0, 0, 0),
            ('RFQ-26298', 'Jg Container (Malaysia) Sdn Bhd', 'DOSH', 'Pemula', 2860, 'Klang', 'Selangor', '2026-07-31', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'RFQ', 300, 2560, 2560, 0, 0, 0, 0, 0),
            ('RFQ-26147', 'Ayamas Food Corporation Sdn Bhd', 'DOSH', 'Renewal', 192925, 'Klang', 'Selangor', '2026-05-19', 'Quotation sent', 'High', '-', 'TMSB', 'Leena', 'QUO', 76751, 116174, 116174, 0, 0, 0, 0, 0),
            ('RFQ-26223', 'Ayamas Food Corporation Sdn Bhd', 'Assessment', 'Assessment', 312321, 'Klang', 'Selangor', '2026-05-20', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'QUO', 0, 312321, 312321, 0, 0, 0, 0, 0),
            ('RFQ-26202', 'Jg Container (Malaysia) Sdn Bhd', 'DOSH', 'Service Tank', 15000, 'Klang', 'Selangor', '2026-06-19', 'Quotation sent', 'Low', '-', 'SPECTRO', 'Leena', 'QUO', 5000, 10000, 10000, 0, 0, 0, 0, 0),
            ('RFQ-26159', 'Vantage Chery Auto Sdn Bhd', 'DOSH', 'New Register', 0, 'Klang', 'Selangor', '2026-05-20', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26253', 'Aida Manufacturing ( Asia) Sdn Bhd', 'DOSH', 'New Tank 0.24m3', 291400, 'Pasir Gudang', 'Johor', '2026-07-02', 'Quotation sent', 'High', '-', 'TMSB', 'Leena', 'QUO', 128000, 163400, 163400, 0, 0, 0, 0, 0),
            ('RFQ-26254', 'Aida Manufacturing ( Asia) Sdn Bhd', 'DOSH', 'New Tank 0.24m3', 223700, 'Pasir Gudang', 'Johor', '2026-07-02', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 86000, 137700, 137700, 0, 0, 0, 0, 0),
            ('RFQ-26179', 'Jg Container (Malaysia) Sdn Bhd', 'DOSH', 'Renewal PMA', 18600, 'Klang', 'Selangor', '2026-06-12', 'Quotation sent', 'Low', '-', 'SPECTRO', 'Leena', 'QUO', 12200, 6400, 6400, 0, 0, 0, 0, 0),
            ('RFQ-26255', 'Aida Manufacturing ( Asia) Sdn Bhd', 'DOSH', 'New Tank 0.269 m3', 110800, 'Pasir Gudang', 'Johor', '2026-07-02', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 51600, 59200, 59200, 0, 0, 0, 0, 0),
            ('RFQ-26251', 'TAYO INDUSTRIES SDN BHD', 'DOSH', 'service and calibration', 6250, 'Rawang', 'Selangor', '2026-07-01', 'Ready to discuss', 'Low', '-', 'TMSB', 'Leena', 'QUO', 0, 6250, 6250, 0, 0, 0, 0, 0),
            ('RFQ-26256', 'Aida Manufacturing ( Asia) Sdn Bhd', 'DOSH', 'New Tank 0.303m3', 30300, 'Pasir Gudang', 'Johor', '2026-07-03', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 14400, 15900, 15900, 0, 0, 0, 0, 0),
            ('RFQ-26262', 'SRN Utama Enterprise', 'Asset (PKNS)', 'Bumbung Sek 20 Blok 13', 24000.2, 'Shah Alam', 'Selangor', '2026-07-06', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 10360, 13640.2, 13640.2, 0, 0, 0, 0, 0),
            ('RFQ-26257', 'Aida Manufacturing ( Asia) Sdn Bhd', 'DOSH', 'New Tank 0.147 m3', 59400, 'Pasir Gudang', 'Johor', '2026-07-03', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 28300, 31100, 31100, 0, 0, 0, 0, 0),
            ('RFQ-26280', 'ETC Cleaning', 'DOSH', 'Cleaning Water Tank', 17800, 'Cyberjaya', 'Kuala Lumpur', '2026-07-17', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 14400, 3400, 3400, 0, 0, 0, 0, 0),
            ('RFQ-26275', 'TAYO INDUSTRIES SDN BHD', 'DOSH', 'Servive UT Calibrate', 5900, 'Port Dickson', 'N. Sembilan', '2026-07-16', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 0, 5900, 5900, 0, 0, 0, 0, 0),
            ('RFQ-26281', 'RAF Synergy', 'DOSH', 'Calibration SV PG', 6800, 'Tanah Merah', 'Kelantan', '2026-07-21', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 380, 6420, 6420, 0, 0, 0, 0, 0),
            ('RFQ-26282', 'TAYO INDUSTRIES SDN BHD', 'DOSH', 'HT', 4100, 'Jeram', 'Selangor', '2026-07-22', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 1071.4, 3028.6, 3028.6, 0, 0, 0, 0, 0),
            ('RFQ-26283', 'SNA Construction', 'DOSH', 'Renewal PMA', 1800, 'Sungai Besar', 'Selangor', '2026-07-22', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 750, 1050, 1050, 0, 0, 0, 0, 0),
            ('RFQ-26276', 'TAYO INDUSTRIES SDN BHD', 'DOSH', 'Service UT Calibrate', 6100, 'Jeram', 'Selangor', '2026-07-16', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 0, 6100, 6100, 0, 0, 0, 0, 0),
            ('RFQ-26259', 'Ingress Technologies Sdn Bhd', 'DOSH', 'Kitchen', 15100, 'Bukit Beruntung', 'Selangor', '2026-07-06', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 8500, 6600, 6600, 0, 0, 0, 0, 0),
            ('RFQ-26286', 'Vigor Jaya Sdn Bhd', 'DOSH', 'UTTM', 18500, 'Port Dickson', 'N. Sembilan', '2026-07-24', 'Quotation received', 'Low', '-', 'TMSB', 'Leena', 'QUO', 11452, 7048, 7048, 0, 0, 0, 0, 0),
            ('RFQ-26293', 'NACM', 'DOSH', 'Calibration', 1700, 'Kuala Lumpur', 'Kuala Lumpur', '2026-07-28', 'Quotation received', 'Low', '-', 'TMSB', 'Leena', 'QUO', 0, 1700, 1700, 0, 0, 0, 0, 0),
            ('RFQ-26292', 'RAF Synergy', 'DOSH', 'On Site Calibration SV PG', 1410, 'UPSI', 'Selangor', '2026-07-28', 'Quotation received', 'Low', '-', 'TMSB', 'Leena', 'QUO', 0, 1410, 1410, 0, 0, 0, 0, 0),
            ('RFQ-26248', 'TAYO INDUSTRIES SDN BHD', 'DOSH', 'HT', 2000, 'Pasir Gudang', 'Johor', '2026-06-29', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 670, 1330, 1330, 0, 0, 0, 0, 0),
            ('RFQ-26258', 'SRN Utama Enterprise', 'Asset (PKNS)', 'Motor Repair', 8800, 'Shah Alam', 'Selangor', '2026-07-06', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'QUO', 14851, -6051, -6051, 0, 0, 0, 0, 0),
            ('RFQ-26296', 'Atlantic Steam Engineering Sdn Bhd', 'DOSH', 'UT', 900, 'Kapar', 'Selangor', '2026-07-30', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'QUO', 0, 900, 900, 0, 0, 0, 0, 0),
            ('RFQ-26227', 'Medi-Life (M) Sdn Bhd', 'DOSH', 'New Register', 2600, 'Shah Alam', 'Selangor', '2026-06-26', 'Work on arrangement', 'Low', '-', 'TMSB', 'Leena', 'PO', 0, 2600, 2600, 0, 0, 0, 0, 0),
            ('RFQ-26230', 'SME Aerospace Sdn. Bhd.', 'DOSH', 'Calibrate SV PG', 9400, 'Sungai Buloh', 'Selangor', '2026-06-26', 'Work on arrangement', 'Low', '-', 'TMSB', 'Leena', 'PO', 918, 8482, 8482, 0, 0, 0, 0, 0),
            ('RFQ-26213', 'Ayamas Food Corporation Sdn Bhd', 'DOSH', 'Repair Boiler', 13400, 'Klang', 'Selangor', '2026-06-23', 'Work on arrangement', 'Low', '-', 'TMSB', 'Leena', 'PO', 19980, -6580, -6580, 0, 0, 0, 0, 0),
            ('RFQ-26240', 'Ladang Rakyat Trengganu Sdn Bhd', 'EPCC', 'Genset JPE', 28500, 'Kemaman', 'Terengganu', '2026-06-26', 'Work on arrangement', 'Low', '-', 'TMSB', 'Leena', 'PO', 13445, 15055, 15055, 0, 0, 0, 0, 0),
            ('RFQ-26241', 'Avery Dennison Materials Sdn Bhd', 'DOSH', 'Cleaning M3', 29182.8, 'Bangi', 'Selangor', '2026-06-26', 'Work on arrangement', 'Low', '-', 'TMSB', 'Leena', 'PO', 21200, 7982.8, 7982.8, 0, 0, 0, 0, 0),
            ('RFQ-26174', 'DELLOYD INDUSTRIES (M) SDN BHD', 'Training', 'Training Reach Truck', 17750, 'Klang', 'Selangor', '2026-06-03', 'Work on arrangement', 'Low', '-', 'TMSB', 'Leena', 'PO', 6250, 11500, 11500, 0, 0, 0, 0, 0),
            ('RFQ-26287', 'Nu Tech Combustion Engineering Sdn Bhd', 'DOSH', 'Witness HT', 1700, 'Pasir Gudang', 'Johor', '2026-07-24', 'Work on arrangement', 'Low', '-', 'TMSB', 'Leena', 'PO', 900, 800, 800, 0, 0, 0, 0, 0),
            ('RFQ-26294', 'PK Agro-Industrial Products (M) Sdn Bhd', 'DOSH', 'UTTM', 6000, 'Seremban', 'N. Sembilan', '2026-07-29', 'Work on arrangement', 'Low', '-', 'SPECTRO', 'Leena', 'PO', 0, 6000, 6000, 0, 0, 0, 0, 0),
            ('RFQ-26224', 'Jg Container (Malaysia) Sdn Bhd', 'DOSH', 'UT', 3750, 'Klang', 'Selangor', '2026-06-25', 'Work done!', 'Low', '-', 'SPECTRO', 'Leena', 'PO', 0, 3750, 3750, 0, 0, 0, 0, 0),
            ('RFQ-26295', 'Jg Container (Malaysia) Sdn Bhd', 'DOSH', 'Service PMT', 21500, 'Klang', 'Selangor', '2026-07-29', 'Work on arrangement', 'Low', '-', 'SPECTRO', 'Leena', 'PO', 0, 21500, 21500, 0, 0, 0, 0, 0),
            ('RFQ-26182', 'Atlas Copco', 'DOSH', 'New Register', 6500, 'Banting', 'Selangor', '2026-06-05', 'Work on arrangement', 'High', '-', 'TMSB', 'Leena', 'PO', 800, 5700, 5700, 0, 0, 0, 0, 0),
            ('RFQ-26137', 'DELLOYD INDUSTRIES (M) SDN BHD', 'DOSH', 'Service Inspection', 1800, 'Klang', 'Selangor', '2026-05-18', 'Invoice sent', 'High', '-', 'TMSB', 'Leena', 'INV', 0, 1800, 1800, 0, 0, 0, 0, 0),
            ('RFQ-26231', 'Nu Tech Combustion Engineering Sdn Bhd', 'DOSH', 'Witness HT', 1800, 'Telok Panglima Garang', 'Selangor', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 751.7, 1048.3, 1048.3, 0, 0, 0, 0, 0),
            ('RFQ-26232', 'Nu Tech Combustion Engineering Sdn Bhd', 'DOSH', 'Design Approval', 12500, 'Shah Alam', 'Selangor', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 12500, 12500, 0, 0, 0, 0, 0),
            ('RFQ-26234', 'TG Porcelain Sdn Bhd (Factory 13P)', 'DOSH', 'Service', 2500, 'Klang', 'Selangor', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 2500, 2500, 0, 0, 0, 0, 0),
            ('RFQ-26235', 'TG Porcelain Sdn Bhd (Factory 13P)', 'DOSH', 'Supply PG', 300, 'Klang', 'Selangor', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 60, 240, 240, 0, 0, 0, 0, 0),
            ('RFQ-26236', 'TG Porcelain Sdn Bhd (Factory 13P)', 'DOSH', 'Service PMA', 1300, 'Klang', 'Selangor', '2026-06-04', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 350, 950, 950, 0, 0, 0, 0, 0),
            ('RFQ-26237', 'TOP QUALITY GLOVE SDN BHD (F31)', 'DOSH', 'UTTM', 1500, 'Klang', 'Selangor', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 1500, 1500, 0, 0, 0, 0, 0),
            ('RFQ-26238', 'TOP QUALITY GLOVE SDN BHD (F31)', 'DOSH', 'New register', 5400, 'Klang', 'Selangor', '2026-06-26', 'Work on arrangement', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 5400, 5400, 0, 0, 0, 0, 0),
            ('RFQ-26244', 'Xpert Engineering Solutions Sdn Bhd', 'DOSH', 'Register PMA', 8500, 'Ampang', 'Selangor', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 8500, 8500, 0, 0, 0, 0, 0),
            ('RFQ-26198', 'NPC Metalform (M) Sdn  Bhd', 'DOSH', 'UT', 1700, 'Gelang Patah', 'Johor', '2026-06-15', 'Invoice sent', 'High', 'Doc', 'ADV', 'Shalihin', 'INV', 590, 949.05, 949.05, 160.95, 0, 160.95, 0, 0),
            ('RFQ-26190', 'TAYO INDUSTRIES SDN BHD', 'DOSH', 'Service & UT', 2500, 'Port Dickson', 'N. Sembilan', '2026-06-12', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 2500, 2500, 0, 0, 0, 0, 0),
            ('RFQ-26175', 'DELLOYD INDUSTRIES (M) SDN BHD', 'DOSH', 'UT', 3500, 'Klang', 'Selangor', '2026-06-03', 'Waiting for report...', 'Low', '-', 'TMSB', 'Leena', 'INV', 200, 3300, 3300, 0, 0, 0, 0, 0),
            ('RFQ-26167', 'NISSHA PRECISION TECHNOLOGIES MALAYSIA SDN BHD', 'DOSH', 'UTTM', 8350, 'Bangi', 'Selangor', '2026-05-21', 'Waiting for report...', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 8350, 8350, 0, 0, 0, 0, 0),
            ('RFQ-26192', 'DELLOYD INDUSTRIES (M) SDN BHD', 'DOSH', 'UTTM', 3500, 'Klang', 'Selangor', '2026-06-16', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 200, 3300, 3300, 0, 0, 0, 0, 0),
            ('RFQ-26229', 'Top Glove Sdn Bhd (F10)', 'DOSH', 'Name Plate', 680, 'Klang', 'Selangor', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 290, 390, 390, 0, 0, 0, 0, 0),
            ('RFQ-26228', 'Nu Tech Combustion Engineering Sdn Bhd', 'DOSH', 'Witness HT', 900, 'Johor Bahru', 'Selangor', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 900, 900, 0, 0, 0, 0, 0),
            ('RFQ-26272', 'Hicom-Yamaha Manufacturing (M) Sdn Bhd', 'DOSH', 'Calibrate', 2000, 'Shah Alam', 'Selangor', '2026-07-13', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 200, 1800, 1800, 0, 0, 0, 0, 0),
            ('RFQ-26180', 'SME Aerospace Sdn. Bhd.', 'DOSH', 'New Sv & Pg', 2080, 'Rawang', 'Selangor', '2026-06-05', 'Work on arrangement', 'Low', '-', 'TMSB', 'Leena', 'INV', 980, 1100, 1100, 0, 0, 0, 0, 0),
            ('RFQ-26263', 'TAYO INDUSTRIES SDN BHD', 'DOSH', 'Cal SV PG', 650, 'Bangi', 'Selangor', '2026-07-07', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 650, 650, 0, 0, 0, 0, 0),
            ('RFQ-26288', 'SRN Utama Enterprise', 'Asset (PKNS)', 'invoice bulan 6', 6496.2, 'Shah Alam', 'Selangor', '2026-07-15', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 6496.2, 6496.2, 0, 0, 0, 0, 0),
            ('RFQ-26170', 'Pejabat Kesihatan Pergigian Daerah Langkawi', 'DOSH', 'Service, Cal SV PG', 3650, 'Kuah, Langkawi', 'Kedah', '2026-05-22', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 860, 2790, 2790, 0, 0, 0, 0, 0),
            ('RFQ-26233', 'Pejabat Kesihatan Pergigian Daerah Langkawi', 'DOSH', 'Service', 1400, 'Kuah, Langkawi', 'Kedah', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 0, 1400, 1400, 0, 0, 0, 0, 0),
            ('RFQ-26191', 'Ais Indah', 'DOSH', 'new register', 60000, 'Kuantan', 'Pahang', '2026-06-12', 'Invoice sent', 'Low', '-', 'ADV', 'Leena', 'INV', 0, 60000, 60000, 0, 0, 0, 0, 0),
            ('RFQ-26239', 'Ladang Rakyat Trengganu Sdn Bhd', 'EPCC', 'Genset', 21000, 'Kemaman', 'Terengganu', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'INV', 15000, 6000, 6000, 0, 0, 0, 0, 0),
            ('RFQ-26141', 'Pejabat Kesihatan Pergigian Daerah Langkawi', 'DOSH', 'Service', 2000, 'Langkawi', 'Kedah', '2026-05-18', 'Invoice sent', 'Low', 'Doc', 'TMSB', 'Leena', 'INV', 650, 1350, 1350, 0, 0, 0, 0, 0),
            ('RFQ-26148', 'OGPC SDN BHD', 'EPCC', 'Skid', 177000, 'Shah Alam', 'Selangor', '2026-05-19', 'Payment received', 'Urgent', 'Syukri', 'TMSB', 'Leena', 'PYMT', 153647.85, 23352.15, 23352.15, 0, 0, 0, 0, 0),
            ('RFQ-26162', 'Public Training', 'Training', 'OSHC', 4894, 'Shah Alam', 'Selangor', '2026-05-20', 'Payment received', 'Low', '-', 'TMSB', 'Leena', 'PYMT', 393.9, 4500.1, 4500.1, 0, 0, 0, 0, 0),
            ('RFQ-26176', 'Camoor', 'Assessment', 'Assessment', 33599.95, 'Petaling', 'Selangor', '2026-06-03', 'Payment received', 'Low', '-', 'TMSB', 'Leena', 'PYMT', 20599.94, 13000.01, 13000.01, 0, 0, 0, 0, 0),
            ('RFQ-26177', 'PEJABAT KESIHATAN PERGIGIAN DAERAH KULIM', 'DOSH', 'Inspection', 25600, 'Kulim', 'Kedah', '2026-06-03', 'Payment received', 'Low', '-', 'TMSB', 'Leena', 'PYMT', 981.76, 24618.24, 24618.24, 0, 0, 0, 0, 0),
            ('RFQ-26181', 'Chemkimia Sdn Bhd', 'Assessment', 'Hirarc', 8000, 'Bukit Beruntung', 'Selangor', '2026-06-05', 'New task', 'Low', 'A. Hafiz', 'TMSB', 'Leena', 'PYMT', 0, 1600, 1600, 3200, 0, 3200, 0, 0),
            ('RFQ-26163', 'Advance HSE', 'DOSH', 'Part replacement', 62144, 'George Town', 'P. Pinang', '2026-05-20', 'Payment received', 'Low', '-', 'TMSB', 'Leena', 'PYMT', 49084.4, 13059.6, 13059.6, 0, 0, 0, 0, 0),
            ('RFQ-26165', 'Advance HSE', 'DOSH', 'Perform Load Test', 42900, 'George Town', 'P. Pinang', '2026-05-20', 'Payment received', 'Low', '-', 'TMSB', 'Leena', 'PYMT', 3615.44, 39284.56, 39284.56, 0, 0, 0, 0, 0),
            ('RFQ-26164', 'Advance HSE', 'DOSH', 'Load', 5800, 'George Town', 'P. Pinang', '2026-05-20', 'Payment received', 'Low', '-', 'TMSB', 'Leena', 'PYMT', 3500, 2300, 2300, 0, 0, 0, 0, 0),
            ('RFQ-26185', 'Advance HSE', 'DOSH', 'service pma', 15935, 'George Town', 'P. Pinang', '2026-06-08', 'Payment received', 'Low', '-', 'TMSB', 'Leena', 'PYMT', 12000, 3935, 3935, 0, 0, 0, 0, 0),
            ('RFQ-26168', 'OGPC', 'EPCC', 'VO skid', 53046, 'Kemaman', 'Terengganu', '2026-05-21', 'Payment received', 'Urgent', 'Syukri', 'TMSB', 'Leena', 'PYMT', 24349.81, 28696.19, 28696.19, 0, 0, 0, 0, 0),
            ('RFQ-26189', 'OGPC SDN BHD', 'EPCC', 'Skid Assembly', 8300, 'Shah Alam', 'Selangor', '2026-06-12', 'Payment received', 'Urgent', 'Syukri', 'TMSB', 'Leena', 'PYMT', 2062.44, 6237.56, 6237.56, 0, 0, 0, 0, 0),
            ('RFQ-26245', 'OGPC SDN BHD', 'EPCC', 'Fuel gas scrubber', 18000, 'Shah Alam', 'Selangor', '2026-06-26', 'Payment received', 'Urgent', 'Syukri', 'TMSB', 'Leena', 'PYMT', 989.2, 17010.8, 17010.8, 0, 0, 0, 0, 0),
            ('RFQ-26203', 'JKKP KL', 'OSHC', 'OSHC', 35116.8, 'KL', 'Kuala Lumpur', '2026-06-19', 'Payment received', 'Low', '-', 'TMSB', 'Leena', 'PYMT', 27235, 7881.8, 7881.8, 0, 0, 0, 0, 0),
            ('RFQ-26250', 'Bluescope Kapar', 'DOSH', 'Piping', 800, 'Kapar', 'Selangor', '2026-06-30', 'Arrangement set!', 'Low', '-', 'SAFEAIR', 'Leena', 'PYMT', 0, 800, 800, 0, 0, 0, 0, 0),
            ('RFQ-26226', 'Chemkimia Sdn Bhd', 'DOSH', 'New Register', 7100, 'Bukit Beruntung', 'Selangor', '2026-06-26', 'Invoice sent', 'Low', '-', 'TMSB', 'Leena', 'PYMT', 600, 6500, 6500, 0, 0, 0, 0, 0),
            ('RFQ-26279', 'OGPC SDN BHD', 'EPCC', 'Spreader bar', 248954, 'Shah Alam', 'Selangor', '2025-11-12', 'Payment received', 'Urgent', 'Syukri', 'TMSB', 'Shalihin', 'PYMT', 158935, 90019, 90019, 0, 0, 0, 0, 0),
            ('RFQ-26184', 'Atlas Copco', 'DOSH', 'Registration', 0, 'Johor Bahru', 'Johor', '2026-06-08', 'New task', 'Low', '-', 'TMSB', 'Leena', 'LOST', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26187', 'Starfeedmills', 'DOSH', 'new register', 0, 'Klang', 'Selangor', '2026-06-11', 'Waiting info from client', 'Low', '-', 'TMSB', 'Leena', 'LOST', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26225', 'JinJing', 'Training', 'HIrarc/JHA', 5800, 'Kulim', 'Kedah', '2026-06-26', 'Waiting info from client', 'Low', 'Doc', 'TMSB', 'Leena', 'LOST', 2500, 2800, 2800, 500, 0, 500, 0, 0),
            ('RFQ-26188', 'TOP QUALITY GLOVE SDN BHD (F31)', 'DOSH', 'New Register', 53500, 'Klang', 'Selangor', '2026-06-11', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'LOST', 0, 53500, 53500, 0, 0, 0, 0, 0),
            ('RFQ-26193', 'Ais Indah', 'DOSH', 'Renewal', 8200, 'Kuantan', 'Pahang', '2026-06-16', 'Waiting info from client', 'High', 'Doc', 'ADV', 'Leena', 'LOST', 2060, 4316.42, 4316.42, 1823.58, 0, 1823.58, 0, 0),
            ('RFQ-26214', 'Hajris group (Q-Bistro)', 'OSHC', 'Oshc inhouse', 7650, 'Putrajaya', 'Selangor', '2026-05-19', 'Waiting info from client', 'High', 'A. Hafiz', 'TMSB', 'Shalihin', 'LOST', 100, 6224.98, 6224.98, 1325.03, 0, 1325.03, 0, 0),
            ('RFQ-26243', 'Kuala Lumpur Fried Chicken (Malaysia) Sdn Bhd', 'DOSH', 'Renewal PMA', 0, 'Sungai Buloh', 'Selangor', '2026-06-26', 'NEW TASK', 'Low', 'Doc', 'TMSB', 'Leena', 'LOST', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26149', 'OGPC SDN BHD', 'EPCC', 'Inspection', 18000, 'Shah Alam', 'Selangor', '2026-05-19', 'Invoice sent', 'Urgent', 'Syukri', 'TMSB', 'Leena', 'LOST', 7.5, 17992.5, 17992.5, 0, 0, 0, 0, 0),
            ('RFQ-26216', 'Veriwise Sdn. Bhd', 'DOSH', 'Service Ut Cal', 9700, 'Bandar Baru Uda', 'Johor', '2026-06-23', 'Unsuccessfull', 'Low', '-', 'TMSB', 'Leena', 'LOST', 1460, 8240, 8240, 0, 0, 0, 0, 0),
            ('RFQ-26249', 'Imprexis Solutions & Engineering (M) Sdn Bhd', 'DOSH', 'NR', 14120, 'Johor Bahru', 'Johor', '2026-07-14', 'Unsuccessfull', 'Low', '-', 'TMSB', 'Leena', 'LOST', 1310, 12810, 12810, 0, 0, 0, 0, 0),
            ('RFQ-26201', 'Percetakan Rina Sdn Bhd', 'DOSH', 'New Register', 12490, 'Cheras', 'Selangor', '2026-06-19', 'Quotation sent', 'Low', 'Zed', 'TMSB', 'Leena', 'LOST', 1050, 11096.8, 11096.8, 343.2, 0, 343.2, 0, 0),
            ('RFQ-26215', 'Atlantic Steam Engineering Sdn Bhd', 'DOSH', 'UTTM', 1800, 'Shah Alam', 'Selangor', '2026-06-03', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'LOST', 50, 1750, 1750, 0, 0, 0, 0, 0),
            ('RFQ-26274', 'TG Porcelain Sdn Bhd (Factory 13P)', 'DOSH', 'General Service', 1300, 'Klang', 'Selangor', '2026-07-15', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'LOST', 300, 1000, 1000, 0, 0, 0, 0, 0),
            ('RFQ-26211', 'ETC Cleaning Services Sdn Bhd', 'DOSH', 'Rental', 650, 'Cheras', 'Kuala Lumpur', '2026-06-23', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'LOST', 300, 350, 350, 0, 0, 0, 0, 0),
            ('RFQ-26290', 'NACM', 'DOSH', 'Calibrate SV PG', 0, 'Cheras', 'Kuala Lumpur', '2026-07-27', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'LOST', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26160', 'Vantage MG Auto Sdn Bhd', 'DOSH', 'New Register', 0, 'Telok Panglima Garang', 'Selangor', '2026-05-20', 'Pending issue', 'Low', 'Captain', 'TMSB', 'Leena', 'LOST', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26161', 'Micron', 'DOSH', 'Renewal', 3200, 'Muar', 'Johor', '2026-05-20', 'Waiting info from client', 'Low', '-', 'TMSB', 'Leena', 'LOST', 0, 3200, 3200, 0, 0, 0, 0, 0),
            ('RFQ-26246', 'TAYO INDUSTRIES SDN BHD', 'DOSH', 'HT', 0, 'Rawang', 'Selangor', '2026-06-29', 'NEW TASK', 'Low', '-', 'TMSB', 'Leena', 'LOST', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26183', 'PTTEP', 'DOSH', 'Inspection', 0, 'Miri', 'Sarawak', '2026-06-08', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'LOST', 0, 0, 0, 0, 0, 0, 0, 0),
            ('RFQ-26271', 'Safeair Asia Sdn Bhd', 'DOSH', 'Install Tank', 4850, 'Puchong', 'Selangor', '2026-07-13', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'LOST', 2100, 2750, 2750, 0, 0, 0, 0, 0),
            ('RFQ-26266', 'PAIP', 'DOSH', 'service PMA', 220480, 'Kuantan', 'Pahang', '2026-07-06', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'LOST', 10800, 209680, 209680, 0, 0, 0, 0, 0),
            ('RFQ-26260', 'SRN Utama Enterprise', 'Asset (PKNS)', 'Pagar Ss 6', 22015, 'Shah Alam', 'Selangor', '2026-07-06', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'LOST', 14300, 7715, 7715, 0, 0, 0, 0, 0),
            ('RFQ-26267', 'ETC Cleaning Services', 'DOSH', 'Rental', 900, 'Cheras', 'Kuala Lumpur', '2026-07-08', 'Quotation sent', 'Low', '-', 'TMSB', 'Leena', 'LOST', 500, 400, 400, 0, 0, 0, 0, 0),
        ]

        for (rfq_id, client_name, job_code, job_title, amount, location, state, date, job_status, level, introducer, source, open_by, stage, total_cost, gross_profit, net_profit, dep_pct, intro_pct, intro_amt, mgr_pct, mgr_amt) in rfq_data_list:
            total_comm = intro_amt + mgr_amt
            entry_id = execute("""INSERT INTO rfq_entries (rfq_id, client_name, job_code, job_title, amount, location, state, date,
                        job_status, level, introducer, source, open_by, stage, commission, total_cost, net_profit,
                        deposit_pct, introducer_comm_pct, introducer_comm_amt, manager_comm_pct, manager_comm_amt, gross_profit,
                        notes, created_at, updated_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (rfq_id, client_name, job_code, job_title, amount, location, state, date,
                     job_status, level, introducer, source, open_by, stage, total_comm, total_cost, net_profit,
                     dep_pct, intro_pct, intro_amt, mgr_pct, mgr_amt, gross_profit,
                     f"Statutory compliance project for {client_name}", now, now))

            # Add 2 Quote items per RFQ entry
            execute("INSERT INTO rfq_items (rfq_entry_id, item_no, description, qty, unit_price, days, amount) VALUES (?,?,?,?,?,?,?)",
                    (entry_id, 1, f"Engineering Assessment & {job_title} for {client_name}", 1, amount * 0.7, 1, amount * 0.7))
            execute("INSERT INTO rfq_items (rfq_entry_id, item_no, description, qty, unit_price, days, amount) VALUES (?,?,?,?,?,?,?)",
                    (entry_id, 2, f"DOSH Documentation, Endorsement & Hydrostatic Test", 1, amount * 0.3, 1, amount * 0.3))

    # ── Seed Reports for Demo ──
    rep_check = q("SELECT id FROM reports LIMIT 1", one=True)
    if rep_check is None:
        now = datetime.utcnow().isoformat()
        admin = q("SELECT id FROM users WHERE role = 'admin' LIMIT 1", one=True)
        admin_id = admin["id"] if admin else 1
        machines = q("SELECT id, name, cert_no FROM machinery LIMIT 15")
        
        report_seeds = [
            ("Annual Statutory DOSH Inspection", "Inspection", "Approved", "Vessel inspected thoroughly per OSHA 1994 & Factory Machinery Act. Safety valve set pressure verified at 10.5 Bar. No structural defects found."),
            ("UTTM Thickness Testing Report", "Inspection", "Approved", "Ultrasonic Thickness Testing conducted on shell plates. Minimum wall thickness measured at 8.2mm (above minimum required 6.0mm)."),
            ("Hydrostatic Pressure Test Verification", "Inspection", "Approved", "Hydrostatic test applied at 1.5x MAWP (15.75 Bar) for 30 minutes. Zero pressure drop recorded."),
            ("Safety Valve & Pressure Gauge Calibration", "Calibration", "Approved", "Safety Valve POP test verified. Pressure Gauge calibrated against master digital gauge. Deviation within +/- 0.5%."),
            ("Boiler Burner & Combustion Maintenance", "Maintenance", "Submitted", "Burner nozzle replaced, fuel pump strainers cleaned, flue gas analyzer test completed. Efficiency improved to 88.5%."),
            ("Overhead Crane Proof Load Test", "Inspection", "Approved", "Proof load test applied at 125% rated capacity (12.5 Ton). Brake holding test and limit switches verified fully functional."),
            ("NDT Magnetic Particle Inspection", "NDT", "Approved", "MPI examination conducted on longitudinal and circumferential welds. Zero surface cracks or linear indications detected."),
            ("Service Call & System Diagnostics", "Maintenance", "Draft", "Compressor air filter & oil separator element replaced. Running pressure stable at 7.5 Bar."),
        ]

        for idx, m in enumerate(machines):
            title_tpl, rtype, rstat, rsum = report_seeds[idx % len(report_seeds)]
            full_title = f"{title_tpl} — {m['name']}"
            execute(
                "INSERT INTO reports (machinery_id, title, report_type, summary, pdf_filename, status, created_by, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (m["id"], full_title, rtype, rsum, "", rstat, admin_id, now)
            )

    if _ENGINE == "pg":
        conn.commit()
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
