import pytest
import shutil
from pathlib import Path
from app import create_app
from config import Config
from services.excel_service import ExcelService

@pytest.fixture(scope='session')
def test_dirs(tmp_path_factory):
    base_tmp = tmp_path_factory.mktemp('attendance_test_data')
    data_dir = base_tmp / 'data'
    backup_dir = base_tmp / 'backups'
    data_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Override Config paths
    old_data = Config.DATA_DIR
    old_backup = Config.BACKUP_DIR
    Config.DATA_DIR = data_dir
    Config.BACKUP_DIR = backup_dir

    # Initialize isolated Excel files
    ExcelService.init_all_files(custom_data_dir=data_dir)

    yield data_dir, backup_dir

    # Restore
    Config.DATA_DIR = old_data
    Config.BACKUP_DIR = old_backup

@pytest.fixture
def app(test_dirs):
    data_dir, backup_dir = test_dirs
    flask_app = create_app()
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key-12345',
        'WTF_CSRF_ENABLED': False
    })
    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Client authenticated as Admin"""
    with client.session_transaction() as sess:
        sess['user_id'] = 'USR-1001'
        sess['username'] = 'admin'
        sess['full_name'] = 'System Administrator'
        sess['role'] = 'Admin'
        sess['email'] = 'admin@apexcollege.edu'
    return client

@pytest.fixture
def teacher_client(client):
    """Client authenticated as Teacher"""
    with client.session_transaction() as sess:
        sess['user_id'] = 'USR-1002'
        sess['username'] = 'teacher'
        sess['full_name'] = 'Prof. Robert Miller'
        sess['role'] = 'Teacher'
        sess['email'] = 'teacher@apexcollege.edu'
    return client

@pytest.fixture
def staff_client(client):
    """Client authenticated as Attendance Staff"""
    with client.session_transaction() as sess:
        sess['user_id'] = 'USR-1003'
        sess['username'] = 'staff'
        sess['full_name'] = 'Sarah Jenkins'
        sess['role'] = 'Attendance Staff'
        sess['email'] = 'staff@apexcollege.edu'
    return client
