from functools import wraps
from datetime import datetime
from flask import session, redirect, url_for, flash, abort, request
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

from services.excel_service import ExcelService

class AuthService:
    @staticmethod
    def get_all_users():
        df = ExcelService.read_df('users')
        users = []
        for _, row in df.iterrows():
            users.append({
                'user_id': str(row.get('User_ID', '')),
                'username': str(row.get('Username', '')),
                'full_name': str(row.get('Full_Name', '')),
                'email': str(row.get('Email', '')),
                'role': str(row.get('Role', 'Attendance Staff')),
                'status': str(row.get('Status', 'Active')),
                'created_at': str(row.get('Created_At', '')),
                'last_login': str(row.get('Last_Login', ''))
            })
        return users

    @staticmethod
    def get_user_by_username(username):
        df = ExcelService.read_df('users')
        matched = df[df['Username'].str.lower() == str(username).lower()]
        if not matched.empty:
            row = matched.iloc[0]
            return {
                'user_id': str(row.get('User_ID', '')),
                'username': str(row.get('Username', '')),
                'password_hash': str(row.get('Password_Hash', '')),
                'full_name': str(row.get('Full_Name', '')),
                'email': str(row.get('Email', '')),
                'role': str(row.get('Role', '')),
                'status': str(row.get('Status', 'Active')),
                'created_at': str(row.get('Created_At', '')),
                'last_login': str(row.get('Last_Login', ''))
            }
        return None

    @staticmethod
    def get_user_by_id(user_id):
        df = ExcelService.read_df('users')
        matched = df[df['User_ID'] == str(user_id)]
        if not matched.empty:
            row = matched.iloc[0]
            return {
                'user_id': str(row.get('User_ID', '')),
                'username': str(row.get('Username', '')),
                'password_hash': str(row.get('Password_Hash', '')),
                'full_name': str(row.get('Full_Name', '')),
                'email': str(row.get('Email', '')),
                'role': str(row.get('Role', '')),
                'status': str(row.get('Status', 'Active')),
                'created_at': str(row.get('Created_At', '')),
                'last_login': str(row.get('Last_Login', ''))
            }
        return None

    @staticmethod
    def authenticate(username, password):
        user = AuthService.get_user_by_username(username)
        if not user:
            return None, "Invalid username or password."
        if user['status'] != 'Active':
            return None, "This account is inactive. Please contact an administrator."
        if not check_password_hash(user['password_hash'], password):
            return None, "Invalid username or password."
        
        # Update last login
        AuthService.update_last_login(user['user_id'])
        return user, None

    @staticmethod
    def update_last_login(user_id):
        df = ExcelService.read_df('users')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if (df['User_ID'] == user_id).any():
            df.loc[df['User_ID'] == user_id, 'Last_Login'] = now_str
            ExcelService.save_df('users', df, create_backup=False)

    @staticmethod
    def create_user(username, password, full_name, email, role, status='Active'):
        username = username.strip()
        if not username or not password:
            return False, "Username and password are required."
        
        df = ExcelService.read_df('users')
        if (df['Username'].str.lower() == username.lower()).any():
            return False, f"Username '{username}' already exists."

        user_id = ExcelService.generate_id('USR', df['User_ID'].tolist())
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        new_row = {
            'User_ID': user_id,
            'Username': username,
            'Password_Hash': generate_password_hash(password),
            'Full_Name': full_name.strip(),
            'Email': email.strip(),
            'Role': role,
            'Status': status,
            'Created_At': now_str,
            'Last_Login': ''
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        ExcelService.save_df('users', df)
        return True, "User created successfully."

    @staticmethod
    def update_user(user_id, full_name, email, role, status):
        df = ExcelService.read_df('users')
        if not (df['User_ID'] == user_id).any():
            return False, "User not found."

        df.loc[df['User_ID'] == user_id, 'Full_Name'] = full_name.strip()
        df.loc[df['User_ID'] == user_id, 'Email'] = email.strip()
        df.loc[df['User_ID'] == user_id, 'Role'] = role
        df.loc[df['User_ID'] == user_id, 'Status'] = status
        ExcelService.save_df('users', df)
        return True, "User updated successfully."

    @staticmethod
    def reset_password(user_id, new_password):
        if not new_password or len(new_password) < 6:
            return False, "Password must be at least 6 characters long."
        df = ExcelService.read_df('users')
        if not (df['User_ID'] == user_id).any():
            return False, "User not found."
        df.loc[df['User_ID'] == user_id, 'Password_Hash'] = generate_password_hash(new_password)
        ExcelService.save_df('users', df)
        return True, "Password reset successfully."

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash('You do not have permission to access that resource.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
