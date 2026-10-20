import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'apex-attendance-secret-key-2026-v1-prod-grade')
    DATA_DIR = BASE_DIR / 'data'
    BACKUP_DIR = BASE_DIR / 'backups'
    
    # Excel File Paths
    STUDENTS_FILE = DATA_DIR / 'students.xlsx'
    ATTENDANCE_FILE = DATA_DIR / 'attendance.xlsx'
    TEACHERS_FILE = DATA_DIR / 'teachers.xlsx'
    CLASSES_FILE = DATA_DIR / 'classes.xlsx'
    USERS_FILE = DATA_DIR / 'users.xlsx'
    HOLIDAYS_FILE = DATA_DIR / 'holidays.xlsx'
    SETTINGS_FILE = DATA_DIR / 'settings.xlsx'

    # Security & Session Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True if serving over HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

    # Attendance defaults
    ATTENDANCE_STATUSES = ['Present', 'Absent', 'Late', 'Leave']
    USER_ROLES = ['Admin', 'Teacher', 'Attendance Staff']
    DEFAULT_LOW_ATTENDANCE_THRESHOLD = 75.0
    DEFAULT_ACADEMIC_YEAR = '2026-2027'
    DEFAULT_INSTITUTION_NAME = 'Apex International College'
