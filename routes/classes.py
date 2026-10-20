from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from services.auth_service import login_required, role_required
from services.class_service import ClassService
from services.teacher_service import TeacherService

classes_bp = Blueprint('classes', __name__)

@classes_bp.route('/classes')
@login_required
def index():
    classes_list = ClassService.get_all_classes()
    teachers = TeacherService.get_all_teachers(status='Active')
    return render_template('classes/index.html', classes=classes_list, teachers=teachers)

@classes_bp.route('/classes/add', methods=['POST'])
@login_required
@role_required(['Admin', 'Teacher'])
def add():
    success, msg = ClassService.add_class(request.form)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('classes.index'))

@classes_bp.route('/classes/edit/<class_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'Teacher'])
def edit(class_id):
    success, msg = ClassService.update_class(class_id, request.form)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('classes.index'))

@classes_bp.route('/classes/delete/<class_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def delete(class_id):
    success, msg = ClassService.delete_class(class_id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('classes.index'))

@classes_bp.route('/classes/export')
@login_required
def export_excel():
    file_stream = ClassService.export_classes_excel()
    return send_file(
        file_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='classes_export.xlsx'
    )
