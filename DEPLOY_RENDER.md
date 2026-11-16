# Deploy SDSF Events on Render

## Before deployment

1. Keep the GitHub repository private.
2. Ensure the latest application code and `static/images/sdsf-logo.jpg` are committed.
3. Never commit `.env`, student spreadsheets, SQLite databases, PostgreSQL URLs, Brevo API keys or Flask secret keys.
4. The student database is already imported into managed PostgreSQL; this deployment ZIP intentionally does not contain the local SQLite database.

## Render Web Service

Connect the private GitHub repository and use:

- Branch: `main`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Region: same region as the Render PostgreSQL database

## Environment variables

Configure these under the Render Web Service → Environment:

| Key | Value |
|---|---|
| `DATABASE_URL` | PostgreSQL Internal Database URL |
| `SECRET_KEY` | A newly generated random secret |
| `BREVO_API_KEY` | Private Brevo API key |
| `BREVO_SENDER_EMAIL` | Sender email verified in Brevo |
| `BREVO_SENDER_NAME` | `SDSF Events` |

Save changes and deploy.

## Post-deployment test

1. Sign in as administrator.
2. Create and publish a test event.
3. Sign in using a test student account.
4. Register for the event.
5. Verify the in-portal registration and confirmation email.
6. Check Render application logs if any operation fails.

## Important

- The sender email must be verified in Brevo. Verifying a phone number is not sufficient.
- Do not paste secrets into chat or commit them to GitHub.
- Event images uploaded to the Render service filesystem may disappear after redeploys. Use externally hosted image URLs or persistent object storage for important event images.
