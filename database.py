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
    rfq_check = q("SELECT id FROM rfq_entries LIMIT 1", one=True)
    if rfq_check is None:
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

        # Seed 30+ RFQ Entries across all 7 stages matching Google Sheet amounts & categories
        rfq_data_list = [
            # Stage: RFQ
            ("RFQ-26001", "Petronas Chemicals Group Berhad", "EPCC", "New Register", 45000, "Kerteh", "Terengganu", "2026-06-01", "Site Visit", "High", "Doc", "TMSB", "Shalhin", "RFQ", 22000, 23000, 18500, 10, 5, 1150, 3, 690),
            ("RFQ-26002", "Top Glove Corporation Bhd", "DOSH", "Renew PMT/PMA", 18500, "Klang", "Selangor", "2026-06-05", "NEW TASK", "Medium", "Syukri", "TMSR", "Shalhin", "RFQ", 8000, 10500, 8500, 20, 5, 525, 2, 210),
            ("RFQ-26003", "Lestro KL Sdn Bhd", "DOSH", "New Register", 12000, "Kuchai", "Kuala Lumpur", "2026-06-08", "Assessment", "Low", "A. Hafiz", "SPECTRO", "Leena", "RFQ", 5000, 7000, 5800, 10, 5, 350, 2, 140),
            ("RFQ-26004", "Westports Malaysia Sdn. Bhd.", "DOD1", "GLOBAL INSPECTION", 28000, "Port Klang", "Selangor", "2026-06-12", "Required more details", "High", "Zed", "ADV", "Salihah", "RFQ", 12000, 16000, 13000, 15, 5, 800, 3, 480),
            ("RFQ-26005", "MMC Corporation Berhad", "Assessment", "Service Call", 15000, "Kuala Lumpur", "Kuala Lumpur", "2026-06-14", "Site Visit", "Medium", "Doc", "TMSB", "Shahrul", "RFQ", 6500, 8500, 7000, 10, 5, 425, 2, 170),
            
            # Stage: QUO
            ("RFQ-26006", "Nestlé Products Sdn. Bhd.", "DOSH", "Renew PMT/PMA", 125000, "Shah Alam", "Selangor", "2026-05-10", "Quotation sent", "High", "Doc", "TMSB", "Shalhin", "QUO", 60000, 65000, 52000, 30, 5, 3250, 3, 1950),
            ("RFQ-26007", "Shell Malaysia Trading Sdn. Bhd.", "EPCC", "Design Approval", 480000, "Port Dickson", "N. Sembilan", "2026-05-15", "Quotation waiting for approval", "High", "Syukri", "TMSB", "Leena", "QUO", 260000, 220000, 180000, 50, 5, 11000, 3, 6600),
            ("RFQ-26008", "Dialog Group Berhad", "DOSH", "GLOBAL INSPECTION", 95000, "Pengerang", "Johor", "2026-05-18", "Quotation received", "Medium", "A. Hafiz", "SPECTRO", "Salihah", "QUO", 45000, 50000, 41000, 20, 5, 2500, 2, 1000),
            ("RFQ-26009", "Tenaga Nasional Berhad (TNB)", "Training", "Service Call", 65000, "Kuala Lumpur", "Kuala Lumpur", "2026-05-22", "Ready to discuss", "Low", "Sharifah", "ADV", "Shahrul", "QUO", 28000, 37000, 31000, 10, 5, 1850, 2, 740),
            ("RFQ-26010", "Lotte Chemical Titan (M) Sdn. Bhd.", "DOSH", "Calibrate SV PG", 42000, "Pasir Gudang", "Johor", "2026-05-25", "Quotation sent", "Medium", "Doc", "TMSR", "Aiman", "QUO", 18000, 24000, 19500, 10, 5, 1200, 3, 720),

            # Stage: PO
            ("RFQ-26011", "Sime Darby Industrial Sdn. Bhd.", "DOD1", "Renew PMT/PMA", 45000, "Puchong", "Selangor", "2026-04-05", "PO in progress", "High", "Doc", "TMSB", "Shalhin", "PO", 20000, 25000, 20000, 20, 5, 1250, 3, 750),
            ("RFQ-26012", "Sapura Energy Berhad", "EPCC", "GLOBAL INSPECTION", 95000, "Seri Kembangan", "Selangor", "2026-04-12", "WORK PROGRESS", "High", "Syukri", "TMSB", "Leena", "PO", 48000, 47000, 38000, 30, 5, 2350, 3, 1410),
            ("RFQ-26013", "Gas Malaysia Berhad", "GSHC", "Calibrate SV PG", 18500, "Shah Alam", "Selangor", "2026-04-18", "PO ESTIMATI", "Medium", "Captain", "ADV", "Salihah", "PO", 8500, 10000, 8000, 10, 5, 500, 2, 200),
            ("RFQ-26014", "Boustead Heavy Industries Corp", "DOSH", "New Register", 35000, "Lumut", "Perak", "2026-04-22", "WORK PROGRESS", "Medium", "Doc", "INSASR", "Aiman", "PO", 16000, 19000, 15500, 20, 5, 950, 2, 380),

            # Stage: INV
            ("RFQ-26015", "Vantage MC Auto Sdn Bhd", "DOD1", "Service Call", 38000, "Shah Alam", "Selangor", "2026-03-05", "INVOICE", "Medium", "Doc", "TMSB", "Shalhin", "INV", 16000, 22000, 18000, 50, 5, 1100, 3, 660),
            ("RFQ-26016", "Starkouch Ilo", "Asset (PKNS)", "Renew PMT/PMA", 24000, "Klang", "Selangor", "2026-03-12", "Waiting for deposit", "Low", "A. Hafiz", "SPECTRO", "Leena", "INV", 10000, 14000, 11500, 50, 5, 700, 2, 280),
            ("RFQ-26017", "Bom Ying Glass", "GSMC", "Calibrate SV PG", 16500, "Kepong", "Selangor", "2026-03-18", "INVOICE", "Low", "Zed", "SAFEAIR", "Salihah", "INV", 7000, 9500, 7800, 30, 5, 475, 2, 190),
            ("RFQ-26018", "MISC Berhad", "OSHC", "GLOBAL INSPECTION", 42000, "Kuala Lumpur", "Kuala Lumpur", "2026-03-25", "INVOICE", "High", "Doc", "TMSB", "Shahrul", "INV", 18000, 24000, 19800, 50, 5, 1200, 2, 480),

            # Stage: PYMT
            ("RFQ-26019", "Petronas Chemicals Group Berhad", "DOSH", "New Register", 250000, "Kerteh", "Terengganu", "2026-01-10", "PAYMENT", "High", "Doc", "TMSB", "Shalhin", "PYMT", 120000, 130000, 105000, 100, 5, 6500, 3, 3900),
            ("RFQ-26020", "Top Glove Corporation Bhd", "DOD1", "Renew PMT/PMA", 180000, "Klang", "Selangor", "2026-01-18", "PAYMENT", "High", "Syukri", "TMSB", "Leena", "PYMT", 85000, 95000, 78000, 100, 5, 4750, 3, 2850),
            ("RFQ-26021", "Nestlé Products Sdn. Bhd.", "EPCC", "Design Approval", 165000, "Shah Alam", "Selangor", "2026-01-25", "PAYMENT", "High", "Doc", "TMSB", "Salihah", "PYMT", 75000, 90000, 73000, 100, 5, 4500, 3, 2700),
            ("RFQ-26022", "Shell Malaysia Trading Sdn. Bhd.", "DOSH", "Renew PMT/PMA", 92000, "Port Dickson", "N. Sembilan", "2026-02-05", "PAYMENT", "Medium", "A. Hafiz", "TMSR", "Aiman", "PYMT", 42000, 50000, 41000, 100, 5, 2500, 2, 1000),

            # Stage: KIV
            ("RFQ-26023", "Westports Malaysia Sdn. Bhd.", "PPEai", "GLOBAL INSPECTION", 85000, "Port Klang", "Selangor", "2026-02-15", "Waiting info from client", "Low", "Doc", "TMSB", "Shalhin", "KIV", 40000, 45000, 37000, 0, 5, 2250, 2, 900),
            ("RFQ-26024", "MMC Corporation Berhad", "Asset (PKNS)", "New Register", 62000, "Kuala Lumpur", "Kuala Lumpur", "2026-02-20", "PPCC", "Low", "Syukri", "TMSR", "Leena", "KIV", 28000, 34000, 28000, 0, 5, 1700, 2, 680),
            ("RFQ-26025", "Lestro KL Sdn Bhd", "DOSH", "Renew PMT/PMA", 38000, "Kuchai", "Kuala Lumpur", "2026-02-24", "Required more details", "Low", "Zed", "SPECTRO", "Shahrul", "KIV", 17000, 21000, 17000, 0, 5, 1050, 2, 420),

            # Stage: LOST
            ("RFQ-26026", "ABC Eng", "DOSH", "New Register", 18500, "Tg. Pelepas", "Johor", "2026-02-28", "LOST", "High", "Sharifah", "3rd party", "Aiman", "LOST", 10000, 8500, 0, 0, 0, 0, 0, 0),
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
