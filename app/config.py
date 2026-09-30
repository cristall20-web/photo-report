# app/config.py
import os

# На Render DATA_DIR=/app/data (постоянный диск)
# Локально — текущая папка
DATA_DIR = os.environ.get("DATA_DIR", ".")

DB_PATH = os.path.join(DATA_DIR, "photo_report.db")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")