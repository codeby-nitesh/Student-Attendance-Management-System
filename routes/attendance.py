from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from services.auth_service import login_required, role_required
from services.attendance_service import AttendanceService
from services.student_service import StudentService
from services.class_service import ClassService
from services.settings_service import SettingsService

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance/mark', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Teacher', 'Attendance Staff'])
def mark():
    class_options = ClassService.get_dropdown_options()
    default_cls = SettingsService.get('default_class', 'Grade 10')
    default_sec = SettingsService.get('default_section', 'A')

    if request.method == 'POST':
        date_str = request.form.get('date', datetime.now().strftime('%Y-%m-%d')).strip()
        cls = request.form.get('class', '').strip()
        sec = request.form.get('section', '').strip()
        subject = request.form.get('subject', 'General').strip()
        period = request.form.get('period', 'Period 1').strip()
        overwrite = request.form.get('overwrite') == '1'

        student_ids = request.form.getlist('student_ids[]')
        student_names = request.form.getlist('student_names[]')

        records = []
        for sid, sname in zip(student_ids, student_names):
            status = request.form.get(f"status_{sid}", 'Present')
            remarks = request.form.get(f"remarks_{sid}", '').strip()
            records.append({
                'Student_ID': sid,
                'Student_Name': sname,
                'Date': date_str,
                'Class': cls,
                'Section': sec,
                'Subject': subject,
                'Period': period,
                'Status': status,
                'Remarks': remarks
            })

        marked_by = session.get('username', 'system')
        success, msg = AttendanceService.save_roster_attendance(records, marked_by, overwrite=overwrite)

        if success:
            flash(msg, 'success')
            return redirect(url_for('attendance.records', date_from=date_str, date_to=date_str, class_name=cls, section=sec))
        else:
            flash(msg, 'warning')
            # Redirect back with query params to show overwrite option
            return redirect(url_for('attendance.mark', date=date_str, class_name=cls, section=sec, subject=subject, period=period, needs_confirm=1))

    # GET request
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_class = request.args.get('class_name', default_cls)
    selected_section = request.args.get('section', default_sec)
    selected_subject = request.args.get('subject', 'Mathematics')
    selected_period = request.args.get('period', 'Period 1')
    needs_confirm = request.args.get('needs_confirm') == '1'

    # Get students for this class/section
    students = StudentService.get_students_for_class_section(selected_class, selected_section)

    # Check if attendance exists
    has_existing, existing_records = AttendanceService.check_existing_attendance(
        selected_date, selected_class, selected_section, selected_subject, selected_period
    )

    # Build status map if already marked
    existing_status_map = {}
    existing_remarks_map = {}
    if has_existing:
        for r in existing_records:
            existing_status_map[str(r['Student_ID'])] = r.get('Status', 'Present')
            existing_remarks_map[str(r['Student_ID'])] = r.get('Remarks', '')

    periods = ['Period 1', 'Period 2', 'Period 3', 'Period 4', 'Period 5', 'Period 6', 'Period 7', 'Period 8']

    return render_template(
        'attendance/mark.html',
        class_options=class_options,
        selected_date=selected_date,
        selected_class=selected_class,
        selected_section=selected_section,
        selected_subject=selected_subject,
        selected_period=selected_period,
        periods=periods,
        students=students,
        has_existing=has_existing,
        needs_confirm=needs_confirm,
        existing_status_map=existing_status_map,
        existing_remarks_map=existing_remarks_map
    )

@attendance_bp.route('/attendance/records')
@login_required
def records():
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    class_filter = request.args.get('class_name', '').strip()
    section_filter = request.args.get('section', '').strip()
    student_search = request.args.get('student', '').strip()
    subject_filter = request.args.get('subject', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = int(request.args.get('page', 1))

    rec_list, total_count, total_pages, current_page = AttendanceService.get_attendance_records(
        date_from=date_from, date_to=date_to, class_filter=class_filter,
        section_filter=section_filter, student_search=student_search,
        subject_filter=subject_filter, status_filter=status_filter,
        page=page, per_page=20
    )

    class_options = ClassService.get_dropdown_options()

    return render_template(
        'attendance/records.html',
        records=rec_list,
        total_count=total_count,
        total_pages=total_pages,
        current_page=current_page,
        date_from=date_from,
        date_to=date_to,
        class_filter=class_filter,
        section_filter=section_filter,
        student_search=student_search,
        subject_filter=subject_filter,
        status_filter=status_filter,
        class_options=class_options
    )

@attendance_bp.route('/attendance/records/edit/<attendance_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'Teacher'])
def edit_record(attendance_id):
    status = request.form.get('status', 'Present').strip()
    remarks = request.form.get('remarks', '').strip()
    user_name = session.get('username', 'user')

    success, msg = AttendanceService.edit_record(attendance_id, status, remarks, user_name)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')

    return redirect(request.referrer or url_for('attendance.records'))

@attendance_bp.route('/attendance/records/delete/<attendance_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def delete_record(attendance_id):
    success, msg = AttendanceService.delete_record(attendance_id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(request.referrer or url_for('attendance.records'))

@attendance_bp.route('/attendance/records/export')
@login_required
def export_excel():
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    class_filter = request.args.get('class_name', '').strip()
    section_filter = request.args.get('section', '').strip()
    student_search = request.args.get('student', '').strip()
    subject_filter = request.args.get('subject', '').strip()
    status_filter = request.args.get('status', '').strip()

    file_stream = AttendanceService.export_records_excel(
        date_from=date_from, date_to=date_to, class_filter=class_filter,
        section_filter=section_filter, student_search=student_search,
        subject_filter=subject_filter, status_filter=status_filter
    )
    return send_file(
        file_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='attendance_records_export.xlsx'
    )
