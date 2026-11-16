# Deploy DAVV College Event Portal on Render

## Before deployment
1. Make the GitHub repository private. It contains project source and the README has historically included demo credentials.
2. In the local project folder, activate the virtual environment and run `python set_admin_password.py` to replace the demo admin password. This updates only the local SQLite database.
3. Keep `data/davv_events.db` and the student Excel workbook out of GitHub. The SQLite database is needed locally for the one-time migration only.

## Create PostgreSQL on Render
1. In Render Dashboard, create a new PostgreSQL database.
2. Choose a region close to your users (e.g. Singapore if available) and a suitable plan.
3. Copy the **External Database URL** for the one-time import from your laptop. Treat it as a password; do not share it or commit it.

## Create the Web Service
1. Create a new Web Service and connect the private GitHub repository.
2. Branch: `main`
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add environment variables:
   - `DATABASE_URL`: Render PostgreSQL External Database URL
   - `SECRET_KEY`: generate a long random value with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
6. Deploy. The app creates the PostgreSQL tables on startup. Do not announce the URL to students yet; it will initially have no imported accounts.

## Import existing students and data
Run this once from your local project folder. Use the same External Database URL in the shell; do not paste it into chat or commit it:

```bash
export DATABASE_URL='PASTE_RENDER_EXTERNAL_DATABASE_URL_HERE'
source .venv/bin/activate
python migrate_sqlite_to_postgres.py
unset DATABASE_URL
```

The script copies the existing users, events, registrations, notifications, and password hashes from `data/davv_events.db` into PostgreSQL. It stops if PostgreSQL already contains users, to avoid duplicate imports. Keep the SQLite file as a private backup.

After the import, open the Render service URL and test:
- Admin login with the new admin password.
- A student login using their email ID and contact-number password.
- Create and publish a test event; register as a student; check notifications.

## Important production notes
- Never commit the SQLite database, Excel student list, `.env`, or database URL.
- Render's local filesystem is ephemeral. Event images uploaded to `static/uploads/` may disappear after deploy/restart. For production, use externally hosted image URLs or add persistent object storage.
- Use HTTPS and keep the PostgreSQL URL and `SECRET_KEY` private.
