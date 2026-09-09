"""
QR-Based Cow Digital Passport
------------------------------
A demo module of a Smart Farm Management System.

Lets a farmer register a cow, generates a unique QR code that points to
that cow's public profile ("digital passport"), and lets anyone who scans
the QR code view the cow's information from a phone browser.

Run with: python app.py
"""

import os
import sqlite3
import uuid

import qrcode
import mysql.connector
from mysql.connector import Error as MySQLError

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    abort,
)

# ------------------------------------------------------------------
# App configuration
# ------------------------------------------------------------------

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "cow-passport-demo-secret"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

QR_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "qr_codes"
)

ALLOWED_IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg"
}

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    QR_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = (
    5 * 1024 * 1024
)

# ------------------------------------------------------------------
# Public URL used inside QR codes
# ------------------------------------------------------------------

SITE_BASE_URL = os.environ.get(
    "SITE_BASE_URL",
    "https://192.168.100.2:5000"
)

PORT = int(
    os.environ.get(
        "PORT",
        "5000"
    )
)

# ------------------------------------------------------------------
# Database configuration
# ------------------------------------------------------------------

DB_CONFIG = {
    "host": os.environ.get(
        "DB_HOST",
        "localhost"
    ),

    "user": os.environ.get(
        "DB_USER",
        "root"
    ),

    "password": os.environ.get(
        "DB_PASSWORD",
        ""
    ),

    "database": os.environ.get(
        "DB_NAME",
        "cow_qr_demo"
    ),
}

# SQLite database path
DB_PATH = os.path.join(
    BASE_DIR,
    "cow_qr_demo.sqlite3"
)

# mysql by default
DB_TYPE = os.environ.get(
    "DB_TYPE",
    "mysql"
).lower()


# ------------------------------------------------------------------
# SQLite Cursor Wrapper
# ------------------------------------------------------------------

class SQLiteCursor:
    """
    Wrap sqlite3 cursor so the app can use the same
    MySQL-style %s placeholders.
    """

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=()):
        if params:
            query = query.replace(
                "%s",
                "?"
            )

        return self._cursor.execute(
            query,
            tuple(params)
        )

    def executemany(
        self,
        query,
        seq_of_params
    ):
        if seq_of_params:
            query = query.replace(
                "%s",
                "?"
            )

        return self._cursor.executemany(
            query,
            seq_of_params
        )

    def fetchall(self):
        rows = self._cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def fetchone(self):
        row = self._cursor.fetchone()

        if row is not None:
            return dict(row)

        return None

    def close(self):
        return self._cursor.close()

    def __getattr__(self, name):
        return getattr(
            self._cursor,
            name
        )


# ------------------------------------------------------------------
# SQLite Connection Wrapper
# ------------------------------------------------------------------

class SQLiteConnection:
    """
    Provide the subset of the DB API
    expected by the Flask routes.
    """

    def __init__(self, connection):

        self._conn = connection

        self._conn.row_factory = sqlite3.Row

        self._conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        ensure_sqlite_schema(
            self._conn
        )

    def cursor(self, dictionary=False):

        return SQLiteCursor(
            self._conn.cursor()
        )

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(
            self._conn,
            name
        )


# ------------------------------------------------------------------
# SQLite Database Schema
# ------------------------------------------------------------------

def ensure_sqlite_schema(conn):

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL UNIQUE,
            cow_name TEXT NOT NULL,
            breed TEXT,
            cow_type TEXT,
            gender TEXT,
            age INTEGER,
            date_of_birth TEXT,
            color TEXT,
            registered_location TEXT,
            owner_name TEXT,
            owner_contact TEXT,
            health_status TEXT,
            health_score INTEGER,
            vaccination_status TEXT,
            last_vaccination_date TEXT,
            last_health_check TEXT,
            disease_history TEXT,
            milk_production REAL,
            notes TEXT,
            image_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS found_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL,
            finder_name TEXT NOT NULL,
            finder_contact TEXT NOT NULL,
            current_area TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cow_id)
                REFERENCES cows(cow_id)
                ON DELETE CASCADE
        )
        """
    )

    conn.commit()

    # --------------------------------------------------------------
    # Add sample cows only if database is empty
    # --------------------------------------------------------------

    cow_count = conn.execute(
        "SELECT COUNT(*) AS total FROM cows"
    ).fetchone()[0]

    if cow_count == 0:

        sample_cows = [

            (
                "COW001",
                "Ganga",
                "Gir",
                "Dairy",
                "Female",
                4,
                "2022-03-14",
                "Reddish Brown",
                "Shivapur Dairy Farm, Pune",
                "Ramesh Patil",
                "9876543210",
                "Healthy",
                92,
                "Up to date",
                "2026-05-10",
                "2026-08-20",
                "None reported",
                12.50,
                "Calm temperament, good milk yield through the year.",
                None,
            ),

            (
                "COW002",
                "Lakshmi",
                "Sahiwal",
                "Dairy",
                "Female",
                5,
                "2021-07-02",
                "Light Brown",
                "Shivapur Dairy Farm, Pune",
                "Ramesh Patil",
                "9876543210",
                "Healthy",
                88,
                "Up to date",
                "2026-04-22",
                "2026-08-15",
                "Minor mastitis (treated, 2024)",
                10.80,
                "Requires slightly warmer shelter in winter.",
                None,
            ),

            (
                "COW003",
                "Radha",
                "Red Sindhi",
                "Dairy",
                "Female",
                3,
                "2023-01-19",
                "Deep Red",
                "Shivapur Dairy Farm, Pune",
                "Sunita Patil",
                "9876501234",
                "Under Observation",
                75,
                "Pending",
                "2025-11-05",
                "2026-08-25",
                "Recovering from foot infection",
                8.20,
                "Vaccination booster due next month.",
                None,
            ),
        ]

        conn.executemany(
            """
            INSERT INTO cows
            (
                cow_id,
                cow_name,
                breed,
                cow_type,
                gender,
                age,
                date_of_birth,
                color,
                registered_location,
                owner_name,
                owner_contact,
                health_status,
                health_score,
                vaccination_status,
                last_vaccination_date,
                last_health_check,
                disease_history,
                milk_production,
                notes,
                image_path
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            sample_cows
        )

        conn.commit()


# ------------------------------------------------------------------
# SQLite Connection
# ------------------------------------------------------------------

def get_sqlite_connection():

    return SQLiteConnection(
        sqlite3.connect(
            DB_PATH
        )
    )


# ------------------------------------------------------------------
# Database Connection
# ------------------------------------------------------------------

def get_db_connection():

    global DB_TYPE

    # --------------------------------------------------------------
    # Explicit SQLite mode
    # --------------------------------------------------------------

    if DB_TYPE == "sqlite":

        return get_sqlite_connection()

    # --------------------------------------------------------------
    # Try MySQL
    # --------------------------------------------------------------

    try:

        connection = mysql.connector.connect(
            **DB_CONFIG
        )

        return connection

    except MySQLError as err:

        app.logger.warning(
            "MySQL unavailable at %s. "
            "Using SQLite fallback instead. "
            "Details: %s",
            DB_CONFIG.get("host"),
            err
        )

        DB_TYPE = "sqlite"

        return get_sqlite_connection()


# ------------------------------------------------------------------
# Image Validation
# ------------------------------------------------------------------

def allowed_image(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_IMAGE_EXTENSIONS
    )


# ------------------------------------------------------------------
# Save Cow Image
# ------------------------------------------------------------------

def save_cow_image(file_storage):

    """
    Validate and save uploaded cow photo.

    Returns:
        filename if valid image uploaded
        None if no image uploaded
    """

    if (
        not file_storage
        or
        file_storage.filename == ""
    ):
        return None

    if not allowed_image(
        file_storage.filename
    ):
        raise ValueError(
            "Only PNG, JPG or JPEG images are allowed."
        )

    ext = file_storage.filename.rsplit(
        ".",
        1
    )[1].lower()

    unique_name = (
        f"{uuid.uuid4().hex}.{ext}"
    )

    file_storage.save(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            unique_name
        )
    )

    return unique_name


# ------------------------------------------------------------------
# Generate QR Code
# ------------------------------------------------------------------

def generate_qr_for_cow(cow_id):

    """
    Create QR code for a cow.

    QR contains only the public profile URL.
    """

    profile_url = (
        f"{SITE_BASE_URL}/cow/{cow_id}"
    )

    qr_img = qrcode.make(
        profile_url
    )

    qr_path = os.path.join(
        QR_FOLDER,
        f"{cow_id}.png"
    )

    qr_img.save(
        qr_path
    )

    return f"{cow_id}.png"


# ==================================================================
# ROUTES
# ==================================================================


# ------------------------------------------------------------------
# Home
# ------------------------------------------------------------------

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ------------------------------------------------------------------
# Uploaded Images
# ------------------------------------------------------------------

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():

    search = request.args.get(
        "q",
        ""
    ).strip()

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        if search:

            like = f"%{search}%"

            cursor.execute(
                """
                SELECT *
                FROM cows
                WHERE cow_id LIKE %s
                   OR cow_name LIKE %s
                ORDER BY created_at DESC
                """,
                (
                    like,
                    like
                )
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM cows
                ORDER BY created_at DESC
                """
            )

        cows = cursor.fetchall()

        cursor.execute(
            "SELECT COUNT(*) AS total FROM cows"
        )

        total = cursor.fetchone()[
            "total"
        ]

    finally:

        cursor.close()
        conn.close()

    return render_template(
        "dashboard.html",
        cows=cows,
        total=total,
        search=search
    )


# ------------------------------------------------------------------
# Delete Cow
# ------------------------------------------------------------------

@app.route(
    "/delete/<cow_id>",
    methods=["POST"]
)
def delete_cow(cow_id):

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    row = None

    try:

        cursor.execute(
            """
            SELECT image_path
            FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        row = cursor.fetchone()

        cursor.execute(
            """
            DELETE FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        conn.commit()

    finally:

        cursor.close()
        conn.close()

    # --------------------------------------------------------------
    # Delete stored image
    # --------------------------------------------------------------

    if row and row.get(
        "image_path"
    ):

        img_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            row["image_path"]
        )

        if os.path.exists(
            img_path
        ):

            os.remove(
                img_path
            )

    # --------------------------------------------------------------
    # Delete QR image
    # --------------------------------------------------------------

    qr_path = os.path.join(
        QR_FOLDER,
        f"{cow_id}.png"
    )

    if os.path.exists(
        qr_path
    ):

        os.remove(
            qr_path
        )

    flash(
        f"Cow {cow_id} was removed from the registry.",
        "success"
    )

    return redirect(
        url_for("dashboard")
    )


# ==================================================================
# REGISTER COW
# ==================================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register_cow():

    # --------------------------------------------------------------
    # Display form
    # --------------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "register_cow.html"
        )

    form = request.form

    # --------------------------------------------------------------
    # Required fields
    # --------------------------------------------------------------

    required_fields = [
        "cow_id",
        "cow_name",
        "breed",
        "cow_type",
        "gender",
        "owner_name",
        "owner_contact",
    ]

    missing = [
        field
        for field in required_fields
        if not form.get(
            field,
            ""
        ).strip()
    ]

    if missing:

        flash(
            "Please fill in required field(s): "
            + ", ".join(missing),
            "error"
        )

        return render_template(
            "register_cow.html",
            form=form
        )

    # --------------------------------------------------------------
    # Get Cow ID
    # --------------------------------------------------------------

    cow_id = form.get(
        "cow_id",
        ""
    ).strip()

    cow_name = form.get(
        "cow_name",
        ""
    ).strip()

    # --------------------------------------------------------------
    # Save image
    # --------------------------------------------------------------

    try:

        image_filename = save_cow_image(
            request.files.get(
                "cow_image"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return render_template(
            "register_cow.html",
            form=form
        )

    # --------------------------------------------------------------
    # Convert blank values to None
    # --------------------------------------------------------------

    def none_if_blank(value):

        if value in (
            None,
            ""
        ):
            return None

        return value

    # --------------------------------------------------------------
    # Prepare data
    # --------------------------------------------------------------

    data = (

        cow_id,

        cow_name,

        form.get(
            "breed",
            ""
        ).strip(),

        form.get(
            "cow_type",
            ""
        ).strip(),

        form.get(
            "gender",
            ""
        ).strip(),

        none_if_blank(
            form.get("age")
        ),

        none_if_blank(
            form.get("date_of_birth")
        ),

        none_if_blank(
            form.get("color")
        ),

        none_if_blank(
            form.get("registered_location")
        ),

        form.get(
            "owner_name",
            ""
        ).strip(),

        form.get(
            "owner_contact",
            ""
        ).strip(),

        none_if_blank(
            form.get("health_status")
        ),

        none_if_blank(
            form.get("health_score")
        ),

        none_if_blank(
            form.get("vaccination_status")
        ),

        none_if_blank(
            form.get("last_vaccination_date")
        ),

        none_if_blank(
            form.get("last_health_check")
        ),

        none_if_blank(
            form.get("disease_history")
        ),

        none_if_blank(
            form.get("milk_production")
        ),

        none_if_blank(
            form.get("notes")
        ),

        image_filename,
    )

    # --------------------------------------------------------------
    # Connect to database
    # --------------------------------------------------------------

    conn = get_db_connection()

    cursor = conn.cursor()

    try:

        # ----------------------------------------------------------
        # Check duplicate Cow ID BEFORE INSERT
        # ----------------------------------------------------------

        cursor.execute(
            """
            SELECT cow_id
            FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        existing_cow = cursor.fetchone()

        if existing_cow:

            flash(
                f"Cow ID '{cow_id}' is already registered. "
                "Please choose a different Cow ID.",
                "error"
            )

            return render_template(
                "register_cow.html",
                form=form
            )

        # ----------------------------------------------------------
        # Insert Cow
        # ----------------------------------------------------------

        cursor.execute(
            """
            INSERT INTO cows
            (
                cow_id,
                cow_name,
                breed,
                cow_type,
                gender,
                age,
                date_of_birth,
                color,
                registered_location,
                owner_name,
                owner_contact,
                health_status,
                health_score,
                vaccination_status,
                last_vaccination_date,
                last_health_check,
                disease_history,
                milk_production,
                notes,
                image_path
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            data
        )

        # ----------------------------------------------------------
        # Save database changes
        # ----------------------------------------------------------

        conn.commit()

    except (
        MySQLError,
        sqlite3.IntegrityError
    ) as error:

        conn.rollback()

        # ----------------------------------------------------------
        # Duplicate Cow ID
        # ----------------------------------------------------------

        if (
            isinstance(
                error,
                sqlite3.IntegrityError
            )
            or
            getattr(
                error,
                "errno",
                None
            ) == 1062
        ):

            flash(
                f"Cow ID '{cow_id}' is already registered. "
                "Please choose a different Cow ID.",
                "error"
            )

        else:

            app.logger.exception(
                "Error while registering cow"
            )

            flash(
                "Could not save the cow. "
                "Please check the database and try again.",
                "error"
            )

        return render_template(
            "register_cow.html",
            form=form
        )

    finally:

        cursor.close()

        conn.close()

    # --------------------------------------------------------------
    # Generate QR AFTER successful registration
    # --------------------------------------------------------------

    generate_qr_for_cow(
        cow_id
    )

    # --------------------------------------------------------------
    # Success message
    # --------------------------------------------------------------

    flash(
        f"{cow_name} ({cow_id}) was registered successfully.",
        "success"
    )

    # --------------------------------------------------------------
    # Show QR page
    # --------------------------------------------------------------

    return redirect(
        url_for(
            "show_qr",
            cow_id=cow_id
        )
    )


# ==================================================================
# QR CODE
# ==================================================================

@app.route(
    "/qr/<cow_id>"
)
def show_qr(cow_id):

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT cow_id, cow_name
            FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        cow = cursor.fetchone()

    finally:

        cursor.close()
        conn.close()

    if not cow:

        abort(404)

    qr_filename = (
        f"{cow_id}.png"
    )

    qr_path = os.path.join(
        QR_FOLDER,
        qr_filename
    )

    if not os.path.exists(
        qr_path
    ):

        generate_qr_for_cow(
            cow_id
        )

    profile_url = (
        f"{SITE_BASE_URL}/cow/{cow_id}"
    )

    return render_template(
        "qr.html",
        cow=cow,
        qr_filename=qr_filename,
        profile_url=profile_url
    )


# ==================================================================
# QR SCANNER
# ==================================================================

@app.route("/scan")
def scan():

    return render_template(
        "scan.html"
    )


# ==================================================================
# COW DIGITAL PASSPORT
# ==================================================================

@app.route(
    "/cow/<cow_id>"
)
def cow_profile(cow_id):

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT *
            FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        cow = cursor.fetchone()

    finally:

        cursor.close()
        conn.close()

    if not cow:

        abort(404)

    return render_template(
        "cow_profile.html",
        cow=cow
    )


# ==================================================================
# REPORT FOUND COW
# ==================================================================

@app.route(
    "/report_found/<cow_id>",
    methods=["GET", "POST"]
)
def report_found(cow_id):

    # --------------------------------------------------------------
    # Find cow
    # --------------------------------------------------------------

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                cow_id,
                cow_name,
                registered_location
            FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        cow = cursor.fetchone()

    finally:

        cursor.close()
        conn.close()

    if not cow:

        abort(404)

    # --------------------------------------------------------------
    # Display report form
    # --------------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "report_found.html",
            cow=cow
        )

    # --------------------------------------------------------------
    # Process report
    # --------------------------------------------------------------

    form = request.form

    required_fields = [
        "finder_name",
        "finder_contact"
    ]

    missing = [
        field
        for field in required_fields
        if not form.get(
            field,
            ""
        ).strip()
    ]

    if missing:

        flash(
            "Please fill in required field(s): "
            + ", ".join(missing),
            "error"
        )

        return render_template(
            "report_found.html",
            cow=cow,
            form=form
        )

    # --------------------------------------------------------------
    # Save found report
    # --------------------------------------------------------------

    conn = get_db_connection()

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO found_reports
            (
                cow_id,
                finder_name,
                finder_contact,
                current_area,
                message
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                cow_id,

                form.get(
                    "finder_name",
                    ""
                ).strip(),

                form.get(
                    "finder_contact",
                    ""
                ).strip(),

                form.get(
                    "current_area",
                    ""
                ).strip() or None,

                form.get(
                    "message",
                    ""
                ).strip() or None,
            )
        )

        conn.commit()

    except (
        MySQLError,
        sqlite3.IntegrityError
    ):

        conn.rollback()

        flash(
            "Could not submit the found-cow report. "
            "Please try again.",
            "error"
        )

        return render_template(
            "report_found.html",
            cow=cow,
            form=form
        )

    finally:

        cursor.close()
        conn.close()

    flash(
        "The owner has been notified about the found cow.",
        "success"
    )

    return redirect(
        url_for(
            "cow_profile",
            cow_id=cow_id
        )
    )


# ==================================================================
# ERROR HANDLER
# ==================================================================

@app.errorhandler(404)
def not_found(_error):

    return render_template(
        "404.html"
    ), 404


# ==================================================================
# START APPLICATION
# ==================================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=PORT,
        ssl_context="adhoc"
    )