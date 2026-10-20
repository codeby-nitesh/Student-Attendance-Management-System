from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import AuthService, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user, error = AuthService.authenticate(username, password)
        if error:
            flash(error, 'danger')
            return render_template('login.html', username=username)

        # Store in session
        session.clear()
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user['role']
        session['email'] = user['email']

        flash(f"Welcome back, {user['full_name']}! Signed in as {user['role']}.", 'success')
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = AuthService.get_user_by_id(session['user_id'])
    if not user:
        flash('User account not found.', 'danger')
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            if full_name:
                AuthService.update_user(user['user_id'], full_name, email, user['role'], user['status'])
                session['full_name'] = full_name
                session['email'] = email
                flash('Profile updated successfully.', 'success')
            else:
                flash('Full Name is required.', 'warning')
        elif action == 'change_password':
            old_pass = request.form.get('current_password', '')
            new_pass = request.form.get('new_password', '')
            confirm_pass = request.form.get('confirm_password', '')

            _, err = AuthService.authenticate(user['username'], old_pass)
            if err:
                flash('Current password is incorrect.', 'danger')
            elif len(new_pass) < 6:
                flash('New password must be at least 6 characters long.', 'warning')
            elif new_pass != confirm_pass:
                flash('New password and confirmation do not match.', 'warning')
            else:
                AuthService.reset_password(user['user_id'], new_pass)
                flash('Password changed successfully!', 'success')

        return redirect(url_for('auth.profile'))

    return render_template('profile.html', user=user)
