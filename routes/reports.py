from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, send_file
from services.auth_service import login_required
from services.report_service import ReportService
from services.class_service import ClassService
from services.settings_service import SettingsService

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def index():
    report_type = request.args.get('type', 'student_summary')
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    class_filter = request.args.get('class_name', '').strip()
    section_filter = request.args.get('section', '').strip()

    class_options = ClassService.get_dropdown_options()
    threshold = SettingsService.get_attendance_threshold()

    data = []
    if report_type == 'student_summary':
        data = ReportService.get_aggregated_student_report(
            date_from=date_from, date_to=date_to,
            class_filter=class_filter, section_filter=section_filter,
            low_only=False
        )
    elif report_type == 'low_attendance':
        data = ReportService.get_aggregated_student_report(
            date_from=date_from, date_to=date_to,
            class_filter=class_filter, section_filter=section_filter,
            low_only=True
        )
    elif report_type == 'class_wise':
        data = ReportService.get_class_wise_report(date_from=date_from, date_to=date_to)
    elif report_type == 'subject_wise':
        data = ReportService.get_subject_wise_report(date_from=date_from, date_to=date_to)

    # Summary metrics for quick visual insight
    total_items = len(data)
    avg_percentage = 0.0
    if total_items > 0:
        avg_percentage = round(sum(d.get('percentage', 0.0) for d in data) / total_items, 1)

    return render_template(
        'reports/index.html',
        report_type=report_type,
        date_from=date_from,
        date_to=date_to,
        class_filter=class_filter,
        section_filter=section_filter,
        class_options=class_options,
        threshold=threshold,
        data=data,
        total_items=total_items,
        avg_percentage=avg_percentage
    )

@reports_bp.route('/reports/export/excel')
@login_required
def export_excel():
    report_type = request.args.get('type', 'student_summary')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    class_filter = request.args.get('class_name', '').strip()
    section_filter = request.args.get('section', '').strip()

    if report_type == 'student_summary':
        data = ReportService.get_aggregated_student_report(date_from, date_to, class_filter, section_filter, low_only=False)
    elif report_type == 'low_attendance':
        data = ReportService.get_aggregated_student_report(date_from, date_to, class_filter, section_filter, low_only=True)
    elif report_type == 'class_wise':
        data = ReportService.get_class_wise_report(date_from, date_to)
    elif report_type == 'subject_wise':
        data = ReportService.get_subject_wise_report(date_from, date_to)
    else:
        data = []

    file_stream = ReportService.export_report_to_excel(report_type, data)
    return send_file(
        file_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"{report_type}_report.xlsx"
    )

@reports_bp.route('/reports/export/pdf')
@login_required
def export_pdf():
    report_type = request.args.get('type', 'student_summary')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    class_filter = request.args.get('class_name', '').strip()
    section_filter = request.args.get('section', '').strip()

    subtitle = f"Period: {date_from or 'Beginning'} to {date_to or 'Present'}"
    if class_filter:
        subtitle += f" | Filter: Class {class_filter} {section_filter}"

    if report_type in ('student_summary', 'low_attendance'):
        is_low = (report_type == 'low_attendance')
        data = ReportService.get_aggregated_student_report(date_from, date_to, class_filter, section_filter, low_only=is_low)
        title = "Student Low Attendance Report" if is_low else "Student Attendance Summary Report"
        headers = ['Roll No', 'Student Name', 'Class', 'Sec', 'Total', 'Present', 'Absent', 'Late', 'Leave', 'Att %']
        rows = []
        for d in data:
            rows.append([
                str(d['roll_no']),
                str(d['full_name'])[:25],
                str(d['class']),
                str(d['section']),
                str(d['total_sessions']),
                str(d['present']),
                str(d['absent']),
                str(d['late']),
                str(d['leave']),
                f"{d['percentage']}%"
            ])
    elif report_type == 'class_wise':
        data = ReportService.get_class_wise_report(date_from, date_to)
        title = "Class-Wise Attendance Report"
        headers = ['Class Name', 'Section', 'Class Teacher', 'Total Sessions', 'Present', 'Absent', 'Late', 'Leave', 'Avg %']
        rows = []
        for d in data:
            rows.append([
                str(d['class_name']),
                str(d['section']),
                str(d['class_teacher'])[:20],
                str(d['total_records']),
                str(d['present']),
                str(d['absent']),
                str(d['late']),
                str(d['leave']),
                f"{d['percentage']}%"
            ])
    else:  # subject_wise
        data = ReportService.get_subject_wise_report(date_from, date_to)
        title = "Subject-Wise Attendance Report"
        headers = ['Subject', 'Total Sessions', 'Present', 'Absent', 'Late', 'Leave', 'Attendance %']
        rows = []
        for d in data:
            rows.append([
                str(d['subject']),
                str(d['total_records']),
                str(d['present']),
                str(d['absent']),
                str(d['late']),
                str(d['leave']),
                f"{d['percentage']}%"
            ])

    pdf_stream = ReportService.export_report_to_pdf(title, subtitle, headers, rows)
    return send_file(
        pdf_stream,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{report_type}_report.pdf"
    )
