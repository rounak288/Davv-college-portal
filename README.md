# SDSF Events

A Flask-based campus event management portal for the **School of Data Science and Forecasting (SDSF), Devi Ahilya Vishwavidyalaya, Indore**. It uses SQLite for local development and managed PostgreSQL in production.

## Features

- Login-only access; no public sign-up.
- Student accounts are provisioned by the administration.
- Student login ID: college email address; initial password: matching contact number.
- Passwords stored as salted PBKDF2-SHA256 hashes.
- Separate admin dashboard, event creation, publishing, unpublishing and deletion.
- Event cover image upload or external image URL.
- Student event discovery, category filtering, search, event details and registration.
- In-portal notifications for event announcements and registration confirmations.
- Brevo transactional email confirmation after successful event registration.
- SDSF identity and supplied institutional logo throughout the interface.

## Local setup (Ubuntu)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Local setup (Windows CMD)

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

Open http://127.0.0.1:5000.

## Production deployment

See [DEPLOY_RENDER.md](DEPLOY_RENDER.md). For registration email configuration, see [EMAIL_SETUP.md](EMAIL_SETUP.md).

## Required production environment variables

- `DATABASE_URL`: Render PostgreSQL Internal Database URL.
- `SECRET_KEY`: long random Flask session secret.
- `BREVO_API_KEY`: private Brevo API key.
- `BREVO_SENDER_EMAIL`: email sender verified in Brevo.
- `BREVO_SENDER_NAME`: `SDSF Events`.

Never commit `.env`, database URLs, API keys, secret keys, student spreadsheets or SQLite databases to GitHub. The ZIP intentionally excludes the local student database. The production PostgreSQL database was imported separately.

## Security and operations

- Keep the GitHub repository private.
- Use HTTPS and a strong, private `SECRET_KEY`.
- Rotate any credentials that have been exposed.
- Render's ordinary filesystem is ephemeral. Uploaded event images in `static/uploads/` may not persist across redeploys; use externally hosted image URLs or persistent object storage for production.
