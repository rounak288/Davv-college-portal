"""Set a new admin password in the local SQLite database before cloud import."""
import base64, getpass, hashlib, secrets, sqlite3
from db_backend import DB_PATH


def make_hash(password):
    rounds = 600_000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
    enc = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    return f"pbkdf2_sha256${rounds}${enc(salt)}${enc(digest)}"


def main():
    email = input("Admin email [admin@davv.edu.in]: ").strip() or "admin@davv.edu.in"
    password = getpass.getpass("New admin password (12+ characters): ")
    confirm = getpass.getpass("Confirm new password: ")
    if len(password) < 12 or password != confirm:
        raise SystemExit("Passwords must match and be at least 12 characters.")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("UPDATE users SET password_hash=? WHERE email=? COLLATE NOCASE AND role='admin'", (make_hash(password), email))
    conn.commit()
    conn.close()
    if cur.rowcount != 1:
        raise SystemExit("Admin account not found; no password was changed.")
    print("Admin password updated in the local database.")


if __name__ == "__main__":
    main()
