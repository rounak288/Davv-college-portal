# SDSF Events — Brevo registration emails

SDSF Events sends a transactional confirmation email after a student's event registration has been committed to PostgreSQL. The email includes the event title, category, date, time, venue and description.

The integration uses Brevo's HTTPS API (`https://api.brevo.com/v3/smtp/email`), not SMTP. This avoids SMTP ports that may be blocked by free cloud hosting.

## 1. Prepare your Brevo sender

1. Sign in to Brevo.
2. Verify the sender email address you want SDSF Events to send from. Phone-number verification alone does not verify an email sender.
3. Generate a Brevo API key from **Settings → SMTP & API → API Keys**.
4. Keep the API key private. Do not put it in source code, GitHub, screenshots or this ZIP.

## 2. Add Render environment variables

In Render, open the SDSF Events Web Service → **Environment** and add:

| Key | Value |
|---|---|
| `BREVO_API_KEY` | Your private Brevo API key |
| `BREVO_SENDER_EMAIL` | The email address verified in Brevo |
| `BREVO_SENDER_NAME` | `SDSF Events` |
| `SECRET_KEY` | A long random Flask session secret |
| `DATABASE_URL` | Render PostgreSQL Internal Database URL |

Save the changes and redeploy.

## 3. Test

1. Sign in with a student account whose inbox you can access.
2. Register for one published test event.
3. Confirm the registration is visible in the portal.
4. Check the student's inbox and spam folder.
5. If email delivery fails, check Render application logs. The registration remains saved; the application does not roll back a valid registration because an email provider is temporarily unavailable.

## Notes

- Brevo must accept the sender address before it can send from it.
- Never share or commit `BREVO_API_KEY`, `DATABASE_URL` or `SECRET_KEY`.
- Do not paste secrets into this chat.
