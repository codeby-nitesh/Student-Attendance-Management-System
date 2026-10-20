from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.auth_service import AuthService, login_required, role_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
@role_required(['Admin'])
def index():
    users_list = AuthService.get_all_users()
    return render_template('users/index.html', users=users_list)

@users_bp.route('/users/add', methods=['POST'])
@login_required
@role_required(['Admin'])
def add():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', 'Attendance Staff')
    status = request.form.get('status', 'Active')

    success, msg = AuthService.create_user(username, password, full_name, email, role, status)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('users.index'))

@users_bp.route('/users/edit/<user_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def edit(user_id):
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', 'Attendance Staff')
    status = request.form.get('status', 'Active')

    success, msg = AuthService.update_user(user_id, full_name, email, role, status)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('users.index'))

@users_bp.route('/users/reset-password/<user_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def reset_password(user_id):
    new_password = request.form.get('new_password', '')
    success, msg = AuthService.reset_password(user_id, new_password)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('users.index'))
