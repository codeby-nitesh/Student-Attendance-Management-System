from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from services.auth_service import login_required, role_required
from services.teacher_service import TeacherService

teachers_bp = Blueprint('teachers', __name__)

@teachers_bp.route('/teachers')
@login_required
def index():
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', '').strip()
    status = request.args.get('status', '').strip()

    teachers = TeacherService.get_all_teachers(search=search, department=dept, status=status)
    return render_template('teachers/index.html', teachers=teachers, search=search, department=dept, status=status)

@teachers_bp.route('/teachers/add', methods=['POST'])
@login_required
@role_required(['Admin'])
def add():
    success, msg = TeacherService.add_teacher(request.form)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('teachers.index'))

@teachers_bp.route('/teachers/edit/<teacher_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def edit(teacher_id):
    success, msg = TeacherService.update_teacher(teacher_id, request.form)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('teachers.index'))

@teachers_bp.route('/teachers/delete/<teacher_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def delete(teacher_id):
    success, msg = TeacherService.delete_teacher(teacher_id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('teachers.index'))

@teachers_bp.route('/teachers/export')
@login_required
def export_excel():
    file_stream = TeacherService.export_teachers_excel()
    return send_file(
        file_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='teachers_export.xlsx'
    )
