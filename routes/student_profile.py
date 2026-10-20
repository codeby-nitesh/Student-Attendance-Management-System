from datetime import datetime
from flask import Blueprint, render_template, abort, send_file
from services.auth_service import login_required
from services.student_service import StudentService
from services.report_service import ReportService

student_profile_bp = Blueprint('student_profile', __name__)

@student_profile_bp.route('/students/profile/<student_id>')
@login_required
def profile(student_id):
    data = StudentService.get_student_profile(student_id)
    if not data:
        abort(404)

    # Generate current month calendar matrix
    now = datetime.now()
    year = now.year
    month = now.month
    month_name = now.strftime('%B %Y')

    import calendar
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    month_days = cal.monthdayscalendar(year, month)

    return render_template(
        'students/profile.html',
        student=data['student'],
        stats=data['stats'],
        history=data['history'],
        calendar_events=data['calendar_events'],
        month_days=month_days,
        month_name=month_name,
        current_year=year,
        current_month=month
    )

@student_profile_bp.route('/students/profile/<student_id>/export-pdf')
@login_required
def export_pdf(student_id):
    data = StudentService.get_student_profile(student_id)
    if not data:
        abort(404)

    student = data['student']
    stats = data['stats']
    title = f"Attendance Report - {student['Full_Name']} (Roll: {student['Roll_No']})"
    subtitle = f"Class: {student['Class']} {student['Section']} | Overall Attendance: {stats['percentage']}% | Sessions: {stats['total_sessions']} | Present: {stats['present_count']} | Absent: {stats['absent_count']} | Late: {stats['late_count']} | Leave: {stats['leave_count']}"

    headers = ['Date', 'Period', 'Subject', 'Status', 'Remarks', 'Recorded By']
    rows = []
    for h in data['history'][:100]:  # Up to 100 recent sessions
        rows.append([
            str(h.get('Date', '')),
            str(h.get('Period', '')),
            str(h.get('Subject', '')),
            str(h.get('Status', '')),
            str(h.get('Remarks', ''))[:30],
            str(h.get('Marked_By', ''))[:20]
        ])

    pdf_stream = ReportService.export_report_to_pdf(title, subtitle, headers, rows)
    return send_file(
        pdf_stream,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"attendance_{student['Student_ID']}.pdf"
    )
