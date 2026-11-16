"""One-time import of the existing local SQLite data into DATABASE_URL PostgreSQL.
Run from the project directory after setting DATABASE_URL in the shell.
The script copies hashed passwords; it never exports plaintext passwords.
"""
import os
import sqlite3
from db_backend import db, init_postgres_schema, DB_PATH

TABLES = ("users", "events", "registrations", "notifications")


def main():
    if not os.environ.get("DATABASE_URL"):
        raise SystemExit("Set DATABASE_URL to your Render PostgreSQL External Database URL first.")
    if not DB_PATH.exists():
        raise SystemExit(f"Local SQLite database not found: {DB_PATH}")

    source = sqlite3.connect(DB_PATH)
    source.row_factory = sqlite3.Row
    init_postgres_schema()

    with db() as target:
        # Avoid duplicate imports if this script is accidentally run twice.
        existing = target.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing:
            raise SystemExit("The PostgreSQL database already contains users. Import stopped to prevent duplicates.")

        for table in TABLES:
            rows = source.execute(f"SELECT * FROM {table}").fetchall()
            if not rows:
                print(f"{table}: 0 rows")
                continue
            columns = rows[0].keys()
            col_sql = ", ".join(columns)
            placeholders = ", ".join(["?"] * len(columns))
            target.executemany(
                f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})",
                [tuple(row[col] for col in columns) for row in rows],
            )
            print(f"{table}: imported {len(rows)} rows")

        # Advance generated IDs so future inserts do not collide with imported IDs.
        for table in TABLES:
            target.execute(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1), "
                f"EXISTS(SELECT 1 FROM {table}))"
            )

    source.close()
    print("Import complete. Verify the counts in Render PostgreSQL before opening the site.")


if __name__ == "__main__":
    main()
