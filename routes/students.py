from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from services.auth_service import login_required, role_required
from services.student_service import StudentService
from services.class_service import ClassService

students_bp = Blueprint('students', __name__)

@students_bp.route('/students')
@login_required
def index():
    search = request.args.get('search', '').strip()
    class_filter = request.args.get('class', '').strip()
    section_filter = request.args.get('section', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = int(request.args.get('page', 1))

    students, total_count, total_pages, current_page = StudentService.get_all_students(
        search=search, class_filter=class_filter,
        section_filter=section_filter, status_filter=status_filter,
        page=page, per_page=15
    )

    class_options = ClassService.get_dropdown_options()

    return render_template(
        'students/index.html',
        students=students,
        total_count=total_count,
        total_pages=total_pages,
        current_page=current_page,
        search=search,
        class_filter=class_filter,
        section_filter=section_filter,
        status_filter=status_filter,
        class_options=class_options
    )

@students_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Teacher', 'Attendance Staff'])
def add():
    class_options = ClassService.get_dropdown_options()
    if request.method == 'POST':
        success, res = StudentService.add_student(request.form)
        if success:
            flash(f"Student successfully added with ID: {res}", 'success')
            return redirect(url_for('students.index'))
        else:
            flash(res, 'danger')
            return render_template('students/form.html', student=request.form, is_edit=False, class_options=class_options)

    return render_template('students/form.html', student={}, is_edit=False, class_options=class_options)

@students_bp.route('/students/edit/<student_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Teacher', 'Attendance Staff'])
def edit(student_id):
    student = StudentService.get_student_by_id(student_id)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('students.index'))

    class_options = ClassService.get_dropdown_options()

    if request.method == 'POST':
        success, msg = StudentService.update_student(student_id, request.form)
        if success:
            flash(msg, 'success')
            return redirect(url_for('students.index'))
        else:
            flash(msg, 'danger')
            return render_template('students/form.html', student=request.form, is_edit=True, student_id=student_id, class_options=class_options)

    return render_template('students/form.html', student=student, is_edit=True, student_id=student_id, class_options=class_options)

@students_bp.route('/students/delete/<student_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def delete(student_id):
    success, msg = StudentService.delete_student(student_id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('students.index'))

@students_bp.route('/students/export')
@login_required
def export_excel():
    search = request.args.get('search', '').strip()
    class_filter = request.args.get('class', '').strip()
    section_filter = request.args.get('section', '').strip()
    status_filter = request.args.get('status', '').strip()

    file_stream = StudentService.export_students_excel(
        search=search, class_filter=class_filter,
        section_filter=section_filter, status_filter=status_filter
    )
    return send_file(
        file_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='students_export.xlsx'
    )

@students_bp.route('/students/template')
@login_required
def download_template():
    file_stream = StudentService.generate_import_template()
    return send_file(
        file_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='student_import_template.xlsx'
    )

@students_bp.route('/students/import', methods=['POST'])
@login_required
@role_required(['Admin', 'Teacher'])
def import_excel():
    if 'file' not in request.files:
        flash('No file selected.', 'warning')
        return redirect(url_for('students.index'))

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('Invalid file format. Please upload an Excel file (.xlsx).', 'danger')
        return redirect(url_for('students.index'))

    success, count, errors, _ = StudentService.import_students_from_excel(file)
    if success:
        if count > 0:
            flash(f"Successfully imported {count} student records!", 'success')
        if errors:
            flash(f"Import completed with {len(errors)} warnings/skipped rows: " + "; ".join(errors[:3]), 'warning')
    else:
        flash(f"Import failed: " + "; ".join(errors), 'danger')

    return redirect(url_for('students.index'))
