"""
hackosquad :: Day 3 Lab — "The Lie That Breaks Websites"
A deliberately vulnerable login form for practicing classic SQL Injection.

⚠️  INTENTIONALLY INSECURE. Do not deploy this anywhere public.
    The whole point is the login query below is built with raw string
    concatenation instead of parameterized queries.
"""

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "not-a-real-secret-for-a-ctf-box")

DB_PATH = "/app/data/lab.db"
FLAG = os.environ.get("FLAG", "hackosquad{qu0t3s_ar3_n0t_c0nsent}")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs("/app/data", exist_ok=True)
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Only seed once
    existing = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if existing == 0:
        # id=1 on purpose — the classic "' OR 1=1 --" bypass grabs the
        # first row the query matches, which is exactly why admin
        # accounts being row #1 is a real-world footgun too.
        conn.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
            ("admin", os.environ.get("ADMIN_PASSWORD", "Tr0ub4dor&9xk2"), 1),
        )
        conn.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
            ("alex", "Secret123", 0),
        )
    conn.commit()
    conn.close()


@app.route("/", methods=["GET"])
def index():
    session.clear()
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    conn = get_db()
    cur = conn.cursor()

    # --- THIS is the vulnerability -------------------------------------
    # Raw f-string concatenation straight into the SQL text. Nothing here
    # escapes quotes, so a single ' in the username field lets an
    # attacker rewrite the logical structure of the WHERE clause.
    query = (
        "SELECT * FROM users WHERE username = '"
        + username
        + "' AND password = '"
        + password
        + "'"
    )
    # ---------------------------------------------------------------------

    try:
        cur.execute(query)
        row = cur.fetchone()
        error = None
    except sqlite3.OperationalError as e:
        row = None
        error = f"Database error: {e}"

    conn.close()

    if row:
        session["user"] = row["username"]
        session["is_admin"] = bool(row["is_admin"])
        session["via_injection"] = username != row["username"] or "'" in username
        return redirect(url_for("dashboard"))

    return render_template(
        "index.html",
        error=error or "Login failed. Username or password incorrect.",
        last_query=query,
        last_username=username,
    )


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    return render_template(
        "dashboard.html",
        user=session["user"],
        is_admin=session.get("is_admin", False),
        flag=FLAG if session.get("is_admin") else None,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/hint")
def hint():
    return render_template("hint.html")


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)