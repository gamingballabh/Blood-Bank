"""
Blood Bank System — Flask Backend
----------------------------------
Architecture: Flask + SQLite (no ORM, beginner-friendly)
Routes:
  GET  /            → Dashboard (stats + add-donor form)
  GET  /donors      → Donor list
  GET  /inventory   → Blood inventory
  POST /add_donor   → Add a new donor
  POST /add_inventory → Add/update blood stock
  POST /delete_donor/<id> → Remove a donor
"""

import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g

# ── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "bloodbank_secret_key_2024"   # Required for flash messages
DATABASE = "bloodbank.db"


# ── Database Helpers ─────────────────────────────────────────────────────────
def get_db():
    """Return a per-request database connection (stored on Flask's 'g')."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row   # Rows behave like dicts
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Automatically close the DB connection after each request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they don't exist yet."""
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL,
            age     INTEGER NOT NULL,
            blood   TEXT    NOT NULL,
            phone   TEXT    NOT NULL,
            address TEXT,
            added_on TEXT DEFAULT (DATE('now'))
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            blood   TEXT    NOT NULL UNIQUE,
            units   INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.commit()
    db.close()


# ── Context Processor: inject nav state into all templates ───────────────────
@app.context_processor
def inject_globals():
    return dict(active_page=request.endpoint)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    db = get_db()
    donors_count  = db.execute("SELECT COUNT(*) FROM donors").fetchone()[0]
    units_count   = db.execute("SELECT SUM(units) FROM inventory").fetchone()[0] or 0
    blood_types   = db.execute("SELECT COUNT(*) FROM inventory WHERE units > 0").fetchone()[0]
    recent_donors = db.execute(
        "SELECT * FROM donors ORDER BY id DESC LIMIT 5"
    ).fetchall()
    return render_template(
        "dashboard.html",
        donors_count  = donors_count,
        units_count   = units_count,
        blood_types   = blood_types,
        recent_donors = recent_donors,
    )


@app.route("/donors")
def donors():
    db     = get_db()
    search = request.args.get("q", "").strip()
    blood_filter = request.args.get("blood", "").strip()

    query  = "SELECT * FROM donors WHERE 1=1"
    params = []

    if search:
        query  += " AND (name LIKE ? OR phone LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]

    if blood_filter:
        query  += " AND blood = ?"
        params.append(blood_filter)

    query += " ORDER BY id DESC"
    all_donors = db.execute(query, params).fetchall()

    return render_template(
        "donors.html",
        donors       = all_donors,
        search       = search,
        blood_filter = blood_filter,
    )


@app.route("/inventory")
def inventory():
    db        = get_db()
    stock     = db.execute("SELECT * FROM inventory ORDER BY blood").fetchall()
    total_units = db.execute("SELECT SUM(units) FROM inventory").fetchone()[0] or 0
    return render_template("inventory.html", stock=stock, total_units=total_units)


@app.route("/add_donor", methods=["POST"])
def add_donor():
    name    = request.form.get("name",    "").strip()
    age     = request.form.get("age",     "").strip()
    blood   = request.form.get("blood",   "").strip()
    phone   = request.form.get("phone",   "").strip()
    address = request.form.get("address", "").strip()

    # Basic server-side validation
    if not all([name, age, blood, phone]):
        flash("All fields except address are required.", "error")
        return redirect(url_for("dashboard"))

    try:
        age_int = int(age)
        if not (18 <= age_int <= 65):
            flash("Donor age must be between 18 and 65.", "error")
            return redirect(url_for("dashboard"))
    except ValueError:
        flash("Invalid age value.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute(
        "INSERT INTO donors (name, age, blood, phone, address) VALUES (?, ?, ?, ?, ?)",
        (name, age_int, blood, phone, address),
    )
    db.commit()
    flash(f"Donor '{name}' added successfully!", "success")
    return redirect(url_for("dashboard"))


@app.route("/delete_donor/<int:donor_id>", methods=["POST"])
def delete_donor(donor_id):
    db = get_db()
    donor = db.execute("SELECT name FROM donors WHERE id = ?", (donor_id,)).fetchone()
    if donor:
        db.execute("DELETE FROM donors WHERE id = ?", (donor_id,))
        db.commit()
        flash(f"Donor '{donor['name']}' removed.", "success")
    else:
        flash("Donor not found.", "error")
    return redirect(url_for("donors"))


@app.route("/add_inventory", methods=["POST"])
def add_inventory():
    blood = request.form.get("blood", "").strip()
    units = request.form.get("units", "").strip()

    if not blood or not units:
        flash("Blood group and units are required.", "error")
        return redirect(url_for("inventory"))

    try:
        units_int = int(units)
        if units_int < 1:
            raise ValueError
    except ValueError:
        flash("Units must be a positive number.", "error")
        return redirect(url_for("inventory"))

    db = get_db()
    # Insert or add to existing stock for that blood group
    db.execute("""
        INSERT INTO inventory (blood, units)
        VALUES (?, ?)
        ON CONFLICT(blood) DO UPDATE SET units = units + excluded.units
    """, (blood, units_int))
    db.commit()
    flash(f"Added {units_int} units of {blood} blood.", "success")
    return redirect(url_for("inventory"))


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()           # Create tables on first run
    app.run(debug=True)
