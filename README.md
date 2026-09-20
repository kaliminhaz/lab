# hackosquad · Day 3 Lab — The Lie That Breaks Websites

A tiny, self-contained, **intentionally vulnerable** login form for practicing
classic SQL Injection. Bright themed to match the Cyber Week lesson page.

⚠️ **This app is deliberately insecure.** It exists to be broken. Never deploy
it on a public network, never reuse `app.py`'s login query anywhere real.

## Run it

```bash
docker compose up --build
```

Then open **http://localhost:5000**

To stop and wipe the database:

```bash
docker compose down
```

(There's no volume mount, so every fresh `up` starts with a clean DB —
nobody can leave the box in a broken state for the next person.)

## What's inside

- `app.py` — Flask app. The login route builds its SQL query with plain
  string concatenation (`"... WHERE username = '" + username + "' ..."`),
  which is the entire vulnerability. Everything else (sessions, the flag
  reveal, the "live query" display) is just scaffolding around that one bug.
- SQLite database, seeded on first boot with:
  - `admin` — a real, randomly-strong password nobody is meant to guess
  - `alex` / `Secret123` — a normal account, to prove the login works honestly
- The **flag only appears on the dashboard when you're logged in as `admin`.**
  You can't get there with the real password (you don't have it) — you have
  to make the database say "yes" through logic instead.

## The intended solve

On the login page, username field:

```
' OR 1=1 --
```

Password field: anything.

That closes the quoted string early, adds a condition that's always true,
and comments out the rest of the original query (including the password
check). The database hands back the first matching row — which is `admin`,
row #1 — and the app logs you in as them.

## Customizing before you share it

Edit `docker-compose.yml`:
- `FLAG` — the flag string shown on success
- `ADMIN_PASSWORD` — irrelevant to the intended solve, but change it anyway
- `SECRET_KEY` — Flask session signing key

## Optional hardening exercise (round 2)

Once someone solves it, a good follow-up is having them **fix** `app.py`
themselves: swap the concatenated query for a parameterized one —

```python
cur.execute(
    "SELECT * FROM users WHERE username = ? AND password = ?",
    (username, password),
)
```

— rebuild, and confirm the same payload no longer works. Seeing the exact
one-line fix land is often more memorable than the exploit itself.
