# Smart City Complaint Portal

A small Flask demo app for reporting city infrastructure issues, with a simple HTML form and CSS styles in `static/style.css`.

## 📁 Project structure

- `app.py` — Flask application (routes and run entrypoint)
- `templates/index.html` — Jinja2 template for the complaint form
- `static/style.css` — Styling for the site
- `requirements-dev.txt` — Python dependencies (Flask + development tools)

---

## ⚙️ Prerequisites

- Python 3.8+ (Windows instructions below)
- pip
- (Recommended) VS Code with extensions: **Live Server**, **Live Preview**, **Python**, **Prettier**, **Stylelint**, **CSS Peek**, **HTML CSS Support**

---

## 🚀 Quick start

### 1) Install dependencies

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements-dev.txt
```

(If you prefer not to use the `requirements-dev.txt`, at minimum install Flask: `pip install flask`.)

### 2) Run the Flask app (recommended)

This serves templates properly (Jinja `url_for()` will resolve static paths):

```powershell
python app.py
# then open http://127.0.0.1:5000/ in your browser
```

The app runs in debug mode by default and will flash a success message when the form is submitted.

### 3) Preview the page as static HTML (optional)

Note: `templates/index.html` uses Jinja (`{{ url_for('static', filename='style.css') }}`). Opening the file directly in a browser (or via Live Server) will not process Jinja tags, so the stylesheet link will not resolve. To preview without Flask:

- Create a simple preview file (e.g. `preview.html`) that uses a direct link to the CSS:

```html
<link rel="stylesheet" href="/static/style.css" />
```

- Then open `preview.html` with Live Server or your browser.

---

## 🧰 Developer tools & formatting

This repository includes development tools in `requirements-dev.txt`:

- `black` — code formatter
- `isort` — import sorting
- `flake8` — linting

Run them from the command line to keep the code consistent.

---

## 🔧 VS Code recommendations

Install the following extensions for a smoother experience:

- ritwickdey.LiveServer (Live Server)
- ms-vscode.live-server (Live Preview)
- ms-python.python (Python support)
- esbenp.prettier-vscode (Prettier)
- stylelint.vscode-stylelint (Stylelint)
- pranaygp.vscode-css-peek (CSS Peek)
- Zignd.html-css-class-completion (HTML/CSS class completion)

You can install extensions from VS Code's Extensions view or via CLI:

```bash
code --install-extension ritwickdey.LiveServer
code --install-extension ms-python.python
# ... and so on
```

---

## ✅ Notes & tips

- Use the Flask server when testing form submission and flash messages.
- If you want me to add a `preview.html` that links directly to `/static/style.css`, I can add it so you can use Live Server without running Flask.

---

## 🔒 Email verification (SMTP configuration)

This project sends a verification email after a complaint is submitted. Configure SMTP with environment variables before running the app.

Required environment variables (example names):

- `SMTP_HOST` (e.g. `smtp.mailtrap.io` or your provider)
- `SMTP_PORT` (e.g. `587` or `465`)
- `SMTP_USERNAME` (login)
- `SMTP_PASSWORD` (password or app-specific password)
- `SMTP_USE_TLS` (`true`/`false` — typically `true` for port 587)
- `SENDER_EMAIL` (optional, defaults to `SMTP_USERNAME`)
- `ADMIN_EMAILS` (optional, comma-separated list of admin addresses to receive notifications)

Optional:

- `TOKEN_TTL_SECONDS` — how long verification tokens are valid (default: 86400 = 24 hours)

Windows PowerShell (session-only):

```powershell
$env:SMTP_HOST = 'smtp.mailtrap.io'
$env:SMTP_PORT = '587'
$env:SMTP_USERNAME = 'your-username'
$env:SMTP_PASSWORD = 'your-password'
$env:SMTP_USE_TLS = 'true'
$env:SENDER_EMAIL = 'noreply@example.com'
```

Quick paste-ready examples

- Mailtrap (recommended for safe testing — replace placeholders):

```powershell
$env:SMTP_HOST = 'smtp.mailtrap.io'
$env:SMTP_PORT = '587'
$env:SMTP_USERNAME = 'MAILTRAP_USER'
$env:SMTP_PASSWORD = 'MAILTRAP_PASS'
$env:SMTP_USE_TLS = 'true'
$env:SENDER_EMAIL = 'abhiprincee121@gmail.com'
$env:ADMIN_EMAILS = 'admin@example.com'
python app.py
```

- Local SMTP dev server (smtp4dev or Papercut):

```powershell
# Run smtp4dev locally (default port 25) then point the app at it
$env:SMTP_HOST = 'localhost'
$env:SMTP_PORT = '25'
$env:SMTP_USERNAME = ''    # usually not needed for local SMTP
$env:SMTP_PASSWORD = ''    # usually not needed for local SMTP
$env:SENDER_EMAIL = 'abhiprincee121@gmail.com'
python app.py
```

- Quick local dev backend (no SMTP required):

```powershell
# Print emails to console
$env:DEV_EMAIL_BACKEND = 'console'
python app.py

# Or save emails to files in 'sent_emails/'
$env:DEV_EMAIL_BACKEND = 'file'
$env:EMAIL_OUTPUT_DIR = 'sent_emails'
python app.py
```

If you don't have an SMTP provider for local development, use one of these options:

- Use a local test SMTP server (smtp4dev, Papercut) and point `SMTP_HOST`/`SMTP_PORT` to it — mails will be captured locally.
- Use Mailtrap for testing (https://mailtrap.io). It's easy to set up and prevents accidentally sending real emails.

The app will still accept submissions if SMTP isn't configured, but it will show a warning flash message and the reference id on the page so you can record it manually.

---

## License

MIT — see LICENSE if you need a different license.

---

If you'd like, I can also add a `.vscode/settings.json` to wire up formatting and stylelint automatically. Would you like that? 🎯
