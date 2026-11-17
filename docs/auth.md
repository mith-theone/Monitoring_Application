# Auth notes (demo)

- The demo admin password is **hashed** with Werkzeug (`generate_password_hash`) at app startup.
- Sign-in compares the submitted password to the stored hash via `check_password_hash` (constant-time library check).
- Plaintext passwords are never stored for verification and must not be logged.
- Change the demo password with `ADMIN_PASSWORD` (and optionally `ADMIN_USERNAME`, `SECRET_KEY`) in the environment before starting the app.
