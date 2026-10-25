from flask import Flask, send_from_directory, request, jsonify, redirect, url_for, session, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import secrets
import re
from datetime import datetime

from data_analyzer import analyze_dataset
from data_cleaner import clean_dataset
from segmentation_engine import segment_customers
from business_analytics import build_business_analytics

import os


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

STATIC_DIR = os.path.join(
    FRONTEND_DIR,
    "static"
)

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "data",
    "uploads"
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

REPORTS_DIR = os.path.join(
    BASE_DIR,
    "data",
    "reports"
)

POWERBI_DIR = os.path.join(
    BASE_DIR,
    "powerbi"
)


# ============================================================
# CREATE REQUIRED FOLDERS
# ============================================================

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(POWERBI_DIR, exist_ok=True)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    static_url_path="/static",
    template_folder=os.path.join(FRONTEND_DIR, "templates")
)

CORS(app)

# Authentication and SQLite configuration
DATABASE_PATH = os.path.join(BASE_DIR, "data", "app_database.sqlite3")
USERS_DATA_DIR = os.path.join(BASE_DIR, "data", "users")
os.makedirs(USERS_DATA_DIR, exist_ok=True)
_secret_path = os.path.join(BASE_DIR, ".flask_secret_key")
if os.path.exists(_secret_path):
    with open(_secret_path, "r", encoding="utf-8") as _secret_file:
        _secret_key = _secret_file.read().strip()
else:
    _secret_key = secrets.token_hex(32)
    with open(_secret_path, "w", encoding="utf-8") as _secret_file:
        _secret_file.write(_secret_key)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", _secret_key)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", MAX_CONTENT_LENGTH=100 * 1024 * 1024)

def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def init_database():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS activity_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_history_user_date ON activity_history(user_id, created_at DESC)")

def record_activity(event_type, title, details=""):
    user_id = session.get("user_id")
    if not user_id:
        return
    with get_db() as db:
        db.execute("INSERT INTO activity_history(user_id, event_type, title, details, created_at) VALUES (?, ?, ?, ?, ?)",
                   (user_id, event_type, title, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def user_directories():
    user_id = session.get("user_id")
    if not user_id:
        return {"uploads": UPLOAD_DIR, "processed": PROCESSED_DIR, "reports": REPORTS_DIR}
    base = os.path.join(USERS_DATA_DIR, str(user_id))
    paths = {"uploads": os.path.join(base, "uploads"), "processed": os.path.join(base, "processed"), "reports": os.path.join(base, "reports")}
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    return paths

@app.before_request
def require_login_for_app():
    public_endpoints = {"home", "login_page", "register_user", "login_user", "logout_user", "current_user", "health_check", "static"}
    if request.endpoint in public_endpoints or request.endpoint is None:
        return None
    if not session.get("user_id"):
        if request.path.startswith("/static/"):
            return None
        return jsonify({"success": False, "error": "Please log in to continue.", "login_required": True}), 401
    return None

init_database()


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/", methods=["GET"])
def home():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/login", methods=["GET"])
def login_page():
    if session.get("user_id"):
        return redirect(url_for("home"))
    return send_from_directory(FRONTEND_DIR, "login.html")

@app.route("/register", methods=["POST"])
def register_user():
    data = request.get_json(silent=True) or request.form
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if len(name) < 2:
        return jsonify({"success": False, "error": "Please enter your name (at least 2 characters)."}), 400
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return jsonify({"success": False, "error": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "error": "Password must contain at least 8 characters."}), 400
    try:
        with get_db() as db:
            cursor = db.execute("INSERT INTO users(name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                                (name, email, generate_password_hash(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            session.clear()
            session["user_id"] = cursor.lastrowid
            session["user_name"] = name
            session["user_email"] = email
        user_directories()
        return jsonify({"success": True, "message": "Account created successfully.", "redirect": "/"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "An account with this email already exists. Please log in."}), 409

@app.route("/login", methods=["POST"])
def login_user():
    data = request.get_json(silent=True) or request.form
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    with get_db() as db:
        user = db.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"success": False, "error": "Incorrect email or password."}), 401
    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    user_directories()
    return jsonify({"success": True, "message": "Login successful.", "redirect": "/"})

@app.route("/logout", methods=["POST"])
def logout_user():
    session.clear()
    return jsonify({"success": True, "redirect": "/login"})

@app.route("/api/me", methods=["GET"])
def current_user():
    if not session.get("user_id"):
        return jsonify({"success": False, "authenticated": False}), 401
    return jsonify({"success": True, "authenticated": True, "name": session.get("user_name"), "email": session.get("user_email")})

@app.route("/history", methods=["GET"])
def history_page():
    return send_from_directory(FRONTEND_DIR, "history.html")

@app.route("/api/history", methods=["GET"])
def get_history():
    with get_db() as db:
        rows = db.execute("SELECT event_type, title, details, created_at FROM activity_history WHERE user_id = ? ORDER BY id DESC LIMIT 100", (session["user_id"],)).fetchall()
    return jsonify({"success": True, "items": [dict(row) for row in rows]})


# ============================================================
# GET LATEST UPLOADED DATASET
# ============================================================

def get_latest_dataset(directory=None):

    directory = directory or user_directories()["uploads"]
    files = [
        file
        for file in os.listdir(directory)
        if file.lower().endswith(
            (".csv", ".xlsx", ".xls", ".xlsm", ".ods", ".tsv", ".txt", ".json", ".jsonl", ".ndjson")
        )
    ]

    if not files:
        return None

    latest_file = max(
        files,
        key=lambda file: os.path.getmtime(
            os.path.join(
                directory,
                file
            )
        )
    )

    return latest_file


# ============================================================
# UPLOAD DATASET
# ============================================================

@app.route("/upload", methods=["POST"])
def upload_dataset():

    try:

        if "dataset" not in request.files:

            return jsonify({
                "success": False,
                "error": "No dataset was selected."
            }), 400

        file = request.files["dataset"]

        if file.filename == "":

            return jsonify({
                "success": False,
                "error": "No file was selected."
            }), 400

        allowed_extensions = {
            ".csv",
            ".xlsx",
            ".xls", ".xlsm", ".ods", ".tsv", ".txt", ".json", ".jsonl", ".ndjson"
        }

        extension = os.path.splitext(
            file.filename
        )[1].lower()

        if extension not in allowed_extensions:

            return jsonify({
                "success": False,
                "error": (
                    "Supported formats: CSV, Excel, TSV/TXT and JSON/JSONL."
                )
            }), 400

        # Save uploaded dataset
        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            return jsonify({
                "success": False,
                "error": "The uploaded filename is not valid."
            }), 400
        upload_dir = user_directories()["uploads"]
        file_path = os.path.join(upload_dir, safe_filename)
        file.save(file_path)
        with get_db() as db:
            db.execute("INSERT INTO datasets(user_id, filename, stored_path, uploaded_at) VALUES (?, ?, ?, ?)",
                       (session["user_id"], safe_filename, os.path.relpath(file_path, BASE_DIR), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        record_activity("Upload", safe_filename, "Dataset uploaded successfully")

        return jsonify({
            "success": True,
            "message": "Dataset uploaded successfully!",
            "filename": safe_filename
        })

    except Exception as error:

        print("UPLOAD ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# BEFORE-CLEANING ANALYSIS
# ============================================================

@app.route("/analyze", methods=["GET"])
def analyze_uploaded_dataset():

    try:

        paths = user_directories()
        latest_file = get_latest_dataset(paths["uploads"])

        if latest_file is None:

            return jsonify({
                "success": False,
                "error": (
                    "No dataset found. "
                    "Please upload a dataset first."
                )
            }), 404

        file_path = os.path.join(
            paths["uploads"],
            latest_file
        )

        result = analyze_dataset(
            file_path
        )

        return jsonify({
            "success": True,
            "filename": latest_file,
            "analysis": result
        })

    except Exception as error:

        print("ANALYSIS ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# AI DATA CLEANING
# ============================================================

@app.route("/clean", methods=["POST"])
def clean_uploaded_dataset():

    try:

        paths = user_directories()
        latest_file = get_latest_dataset(paths["uploads"])

        if latest_file is None:

            return jsonify({
                "success": False,
                "error": (
                    "No dataset found. "
                    "Please upload a dataset first."
                )
            }), 404

        input_file = os.path.join(
            paths["uploads"],
            latest_file
        )

        output_file = os.path.join(
            paths["processed"],
            "cleaned_customers.csv"
        )

        report_file = os.path.join(
            paths["reports"],
            "cleaning_report.json"
        )

        report = clean_dataset(
            input_file,
            output_file,
            report_file
        )
        record_activity("Cleaning", latest_file, "AI data cleaning completed")

        return jsonify({
            "success": True,
            "message": (
                "AI data cleaning completed successfully."
            ),
            "original_file": latest_file,
            "cleaned_file": "cleaned_customers.csv",
            "report_file": "cleaning_report.json",
            "report": report
        })

    except Exception as error:

        print("CLEANING ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# AFTER-CLEANING ANALYSIS
# ============================================================

@app.route("/analyze-cleaned", methods=["GET"])
def analyze_cleaned_dataset():

    try:

        paths = user_directories()
        cleaned_file = os.path.join(
            paths["processed"],
            "cleaned_customers.csv"
        )

        if not os.path.exists(cleaned_file):

            return jsonify({
                "success": False,
                "error": (
                    "Cleaned dataset not found. "
                    "Please run AI data cleaning first."
                )
            }), 404

        result = analyze_dataset(
            cleaned_file
        )

        return jsonify({
            "success": True,
            "filename": "cleaned_customers.csv",
            "analysis": result
        })

    except Exception as error:

        print(
            "CLEANED ANALYSIS ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# AI CUSTOMER SEGMENTATION
# ============================================================

@app.route("/segment", methods=["POST"])
def segment_cleaned_dataset():

    try:

        paths = user_directories()
        cleaned_file = os.path.join(
            paths["processed"],
            "cleaned_customers.csv"
        )

        if not os.path.exists(cleaned_file):

            return jsonify({
                "success": False,
                "error": (
                    "Cleaned dataset not found. "
                    "Please run AI data cleaning first."
                )
            }), 404

        # Output segmented dataset
        segmented_file = os.path.join(
            paths["processed"],
            "segmented_customers.csv"
        )

        # Segmentation report
        segmentation_report = os.path.join(
            paths["reports"],
            "segmentation_report.json"
        )

        # Run segmentation
        result = segment_customers(
            cleaned_file,
            segmented_file,
            segmentation_report
        )
        record_activity("Segmentation", "Customer segmentation", "Segmentation completed successfully")

        return jsonify({
            "success": True,
            "message": (
                "AI customer segmentation "
                "completed successfully."
            ),
            "segmented_file": (
                "segmented_customers.csv"
            ),
            "report_file": (
                "segmentation_report.json"
            ),
            "segmentation": result
        })

    except Exception as error:

        print(
            "SEGMENTATION ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# SHOP OWNER BUSINESS ANALYTICS
# ============================================================

@app.route("/business-analytics", methods=["GET"])
def business_analytics():

    try:

        paths = user_directories()
        latest_file = get_latest_dataset(paths["uploads"])

        if latest_file is None:

            return jsonify({
                "success": False,
                "error": (
                    "No dataset found. "
                    "Please upload a dataset first."
                )
            }), 404

        # Always analyze the latest upload. Using a leftover cleaned file
        # from a previous upload caused stale customer/gender counts.
        input_file = os.path.join(paths["uploads"], latest_file)

        result = build_business_analytics(input_file)

        return jsonify({
            "success": True,
            "filename": os.path.basename(input_file),
            "business_analytics": result
        })

    except Exception as error:

        print("BUSINESS ANALYTICS ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# POWER BI DATA CHECK
# ============================================================

@app.route("/powerbi-data", methods=["GET"])
def powerbi_data():

    try:

        paths = user_directories()
        segmented_file = os.path.join(
            paths["processed"],
            "segmented_customers.csv"
        )

        if not os.path.exists(segmented_file):

            return jsonify({
                "success": False,
                "error": (
                    "Segmented dataset not found. "
                    "Please run AI segmentation first."
                )
            }), 404

        return jsonify({
            "success": True,
            "message": (
                "Segmented customer data is ready "
                "for Power BI."
            ),
            "file": "segmented_customers.csv"
        })

    except Exception as error:

        print(
            "POWER BI DATA ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# DOWNLOAD SEGMENTED DATASET
# ============================================================

@app.route(
    "/download-segmented",
    methods=["GET"]
)
def download_segmented():

    segmented_file = "segmented_customers.csv"

    processed_dir = user_directories()["processed"]
    file_path = os.path.join(
        processed_dir,
        segmented_file
    )

    if not os.path.exists(file_path):

        return jsonify({
            "success": False,
            "error": (
                "Segmented dataset not found. "
                "Please run AI segmentation first."
            )
        }), 404

    return send_from_directory(
        processed_dir,
        segmented_file,
        as_attachment=True
    )


# ============================================================
# POWER BI DASHBOARD IMAGE
# ============================================================

@app.route(
    "/dashboard",
    methods=["GET"]
)
def dashboard():

    dashboard_image = os.path.join(
        STATIC_DIR,
        "dashboard.png"
    )

    if not os.path.exists(dashboard_image):

        return jsonify({
            "success": False,
            "error": (
                "Power BI dashboard image not found."
            )
        }), 404

    return send_from_directory(
        STATIC_DIR,
        "dashboard.png"
    )


# ============================================================
# POWER BI DASHBOARD PAGE
# ============================================================

@app.route(
    "/powerbi",
    methods=["GET"]
)
def powerbi_dashboard():

    dashboard_image = os.path.join(
        STATIC_DIR,
        "dashboard.png"
    )

    if not os.path.exists(dashboard_image):

        return jsonify({
            "success": False,
            "error": (
                "Dashboard image not found."
            )
        }), 404

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            AI Customer Segmentation Dashboard
        </title>

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <style>

            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background: #f5f7fb;
            }}

            .dashboard-container {{
                width: 100%;
                min-height: 100vh;
                padding: 20px;
            }}

            .dashboard-title {{
                text-align: center;
                margin-bottom: 20px;
            }}

            .dashboard-title h1 {{
                margin: 0;
                font-size: 28px;
            }}

            .dashboard-wrapper {{
                width: 100%;
                overflow-x: auto;
                background: white;
                padding: 15px;
                border-radius: 12px;
                box-shadow:
                    0 4px 15px rgba(0,0,0,0.08);
            }}

            .dashboard-wrapper img {{
                display: block;
                width: 100%;
                max-width: 1600px;
                height: auto;
                margin: auto;
            }}

        </style>

    </head>

    <body>

        <div class="dashboard-container">

            <div class="dashboard-title">

                <h1>
                    AI Customer Segmentation Dashboard
                </h1>

            </div>

            <div class="dashboard-wrapper">

                <img
                    src="/static/dashboard.png"
                    alt="Power BI Dashboard"
                >

            </div>

        </div>

    </body>

    </html>
    """


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health_check():

    return jsonify({
        "status": "running",
        "project": (
            "AI Customer Segmentation Platform"
        )
    })


# ============================================================
# API 404 HANDLER
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({
        "success": False,
        "error": "API endpoint not found."
    }), 404


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":

    print()

    print("=" * 60)

    print(
        "AI CUSTOMER SEGMENTATION PLATFORM"
    )

    print("=" * 60)

    print()

    print(
        "Website        : "
        "http://127.0.0.1:5000/"
    )

    print(
        "Health         : "
        "http://127.0.0.1:5000/health"
    )

    print(
        "Analysis       : "
        "GET /analyze"
    )

    print(
        "Cleaning       : "
        "POST /clean"
    )

    print(
        "Cleaned        : "
        "GET /analyze-cleaned"
    )

    print(
        "Segmentation   : "
        "POST /segment"
    )

    print(
        "Power BI Data  : "
        "GET /powerbi-data"
    )

    print(
        "Dashboard      : "
        "http://127.0.0.1:5000/powerbi"
    )

    print(
        "Download CSV   : "
        "http://127.0.0.1:5000/download-segmented"
    )

    print()

    print("=" * 60)

    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )