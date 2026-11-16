# DAVV College Event Portal

Flask event management portal for DAVV, Indore. Uses SQLite for local development and managed PostgreSQL for production.

## Included
- Login-only access; no public sign-up.
- 67 student accounts imported from the supplied Excel workbook.
- Student username: email ID; initial password: corresponding contact number.
- Passwords stored as salted PBKDF2-SHA256 hashes (not plaintext).
- No forced password change; students sign in directly with their email ID and matching contact number.
- Separate admin dashboard, event creation, publishing, unpublishing and deletion.
- Event cover photo upload or external image URL.
- Student event discovery, category filtering, search, event details and registration.
- In-portal notifications for new published events and registration confirmations.
- Responsive, image-rich campus event interface.

## Default admin credentials
- Login ID: `admin@davv.edu.in`
- Initial password: `Admin@123`
- Admin password remains `Admin@123` for the local demo.

## Run on Windows CMD
```bat
cd DAVV_College_Event_Portal
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```
Open http://127.0.0.1:5000

## Run on Ubuntu
```bash
cd DAVV_College_Event_Portal
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Student login
Use the email address as the login ID and the matching contact number as the password. No password update is required. The admin demo login remains `admin@davv.edu.in` / `Admin@123`.

## Production deployment
See [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for PostgreSQL migration and Render deployment steps.

## Deployment warning
The included SQLite database is pre-populated and works for a local demonstration. Many cloud hosting services use ephemeral filesystems, so SQLite data can be lost on redeploy/restart and may not be shared reliably across multiple instances. For a real online multi-user deployment, migrate the database to managed PostgreSQL before launch. Do not commit the database or spreadsheet to a public GitHub repository: they contain personal student information. Keep the DB in a private/local demo copy or provide it securely as a deployment secret/seed process.

Set a strong `SECRET_KEY` environment variable in production. Use HTTPS. Change the default admin password. Use only images you have permission to publish.
