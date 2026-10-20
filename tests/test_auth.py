from werkzeug.security import check_password_hash
from services.auth_service import AuthService

def test_login_success(client):
    res = client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Executive Dashboard" in res.data or b"Signed in as Admin" in res.data

def test_login_invalid_password(client):
    res = client.post('/login', data={'username': 'admin', 'password': 'WrongPassword'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Invalid username or password" in res.data

def test_login_nonexistent_user(client):
    res = client.post('/login', data={'username': 'ghost_user', 'password': 'Password123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Invalid username or password" in res.data

def test_logout(auth_client):
    res = auth_client.get('/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b"successfully logged out" in res.data

def test_role_authorization_staff_restricted(staff_client):
    # Attendance staff trying to access admin-only Excel center
    res = staff_client.get('/excel-center', follow_redirects=True)
    assert res.status_code == 200
    assert b"do not have permission" in res.data

def test_password_hashing():
    user = AuthService.get_user_by_username('admin')
    assert user is not None
    assert user['password_hash'] != 'Admin@123'
    assert check_password_hash(user['password_hash'], 'Admin@123')
