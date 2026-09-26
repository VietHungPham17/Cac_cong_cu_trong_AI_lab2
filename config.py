"""
Cấu hình hệ thống Student Management System.
"""

import os

# Database
DATABASE_PATH = os.environ.get("SMS_DB_PATH", "sms.db")
DATABASE_BACKUP_DIR = os.environ.get("SMS_BACKUP_DIR", "backups")

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Validation
STUDENT_ID_PATTERN = r"^[A-Z]{2}\d{6,8}$"
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
PHONE_PATTERN = r"^\+?[\d\s-]{9,15}$"

# Grade
GRADE_SCALE = {
    "A+": 4.0, "A": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0,
    "F": 0.0
}

MIN_GPA = 0.0
MAX_GPA = 4.0

# Report
REPORT_OUTPUT_DIR = os.environ.get("SMS_REPORT_DIR", "reports")
REPORT_FORMATS = ["csv", "json", "txt"]

# Logging
LOG_LEVEL = os.environ.get("SMS_LOG_LEVEL", "INFO")
LOG_FILE = os.environ.get("SMS_LOG_FILE", "sms.log")

# Application
APP_NAME = "Student Management System"
APP_VERSION = "1.0.0"
MAX_LOGIN_ATTEMPTS = 5
SESSION_TIMEOUT = 3600  # seconds
