import os
from pathlib import Path

# PythonAnywhere WSGI configuration example.
# Set these environment variables in the PythonAnywhere WSGI file before importing app.
os.environ.setdefault("SECRET_KEY", "REPLACE_WITH_A_LONG_RANDOM_SECRET")
os.environ.setdefault("INSTANCE_DIR", str(Path.home() / "arvind_panday_data"))
os.environ.setdefault("UPLOAD_DIR", str(Path.home() / "arvind_panday_data" / "uploads"))
os.environ.setdefault("DATABASE_URL", "sqlite:///" + str(Path.home() / "arvind_panday_data" / "catering.db"))

from app import app, init_db
init_db()
application = app
