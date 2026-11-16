# Project handover / viva notes

## Objective
A central college event portal for publishing campus events and letting students discover and register for them.

## Stack
- Python / Flask: routes, authentication and application logic.
- SQLite: student accounts, admin account, events, registrations and notifications.
- Jinja templates: server-rendered pages.
- CSS and JavaScript: responsive visual design and event image preview.

## Roles
- Student: browse/search/filter published events, view details, register, read notifications.
- Admin: dashboard, create and publish events, unpublish/delete events, view/export student directory.

## Authentication
Student login ID is the email address in the supplied spreadsheet. Initial password is the matching contact number. Passwords are salted PBKDF2-SHA256 hashes. Students can log in directly; no forced password change is required. There is no registration endpoint or sign-up page.

## Database
`users`, `events`, `registrations`, `notifications`.

## Security / deployment
Keep student personal data private. Do not push the SQLite database or source spreadsheet to a public GitHub repository. Change default admin password and Flask secret key. For production online deployment use managed PostgreSQL, HTTPS and persistent backups.
