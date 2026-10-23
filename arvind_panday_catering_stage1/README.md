# Arvind Panday Food and Catering Services

Flask + SQLite starter project with public pages, a protected admin dashboard, enquiry management, catalogue management, and PythonAnywhere deployment notes.

## Requirements
- Python 3.10+ (select a version supported by your PythonAnywhere account)
- pip

## Local setup (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set a strong `SECRET_KEY` in `.env`. For local development, you can set:
```powershell
$env:SECRET_KEY = "use-a-long-random-secret-here"
$env:FLASK_DEBUG = "1"
python app.py
```
Open `http://127.0.0.1:5000`.

## Create the first admin account
The application intentionally does not ship with a public default admin password. After installing dependencies, run:
```bash
python create_admin.py
```
Follow the prompts to create the first administrator. Do not expose this setup script publicly.

## PythonAnywhere deployment
1. Upload or clone this project into your PythonAnywhere home directory.
2. Create a virtual environment using a Python version supported by your account:
   `mkvirtualenv --python=/usr/bin/python3.11 arvind-catering`
   (Adjust the version to one actually available in your account.)
3. Install dependencies:
   `pip install -r ~/arvind_panday_catering/requirements.txt`
4. Create a persistent data directory outside the code folder:
   `mkdir -p ~/arvind_panday_data/uploads`
5. Run `python create_admin.py` in the virtualenv after setting the same database and instance paths you plan to use in WSGI.
6. In the PythonAnywhere Web tab, create a Flask/WSGI application and point its WSGI file to this project's `wsgi.py`, or copy the relevant import/configuration from it into the generated WSGI file.
7. Set `SECRET_KEY`, `INSTANCE_DIR`, `UPLOAD_DIR`, and `DATABASE_URL` in the WSGI file before importing `app`. Use a long random secret. Example database URL:
   `sqlite:////home/YOURUSERNAME/arvind_panday_data/catering.db`
8. Set the virtualenv path in the Web tab and add static mapping for `/static/` to this project's `static/` directory.
9. Reload the web app and test public pages, login, enquiry submission, and persistent data.
10. For HTTPS production, set `COOKIE_SECURE=1` after HTTPS is active.

### Important deployment notes
- Paths in WSGI and the admin-creation command must point to the same persistent database.
- Back up the SQLite database and uploads before deployment changes.
- Do not delete or overwrite the database during normal releases.
- `wsgi.py` calls `init_db()` to create missing tables and seed basic demo entries. It does not create an admin account.
- Do not put private certification documents in the public static folder.
- Email, WhatsApp messaging, maps, and other external integrations require valid configuration and may depend on account plan/network restrictions.
- Review PythonAnywhere's current account, storage, outbound network, and web-app limits before production launch.

## Included admin areas
- Overview
- Enquiries and status updates
- Services, branches, team, certifications, testimonials CRUD
- Website contact/social settings
- Administrator password change

## Known starter limitations
This is a foundation to customize, not a fully audited production system. Before launch, add dedicated upload workflows for gallery/certifications, richer audit logging, pagination for large datasets, database migrations, backups, and comprehensive automated tests. Do not publish fabricated business or certification details.
