from datetime import datetime
from services.attendance_service import AttendanceService
from services.student_service import StudentService

def test_attendance_mark_and_duplicate_prevention():
    test_date = f"2026-11-{datetime.now().strftime('%H%M%S%f')[:6]}"
    cls = 'Grade 10'
    sec = 'A'
    subject = 'Physics Lab'
    period = 'Period 4'

    records = [
        {
            'Student_ID': 'STU-1001',
            'Student_Name': 'Alexander Smith',
            'Date': test_date,
            'Class': cls,
            'Section': sec,
            'Subject': subject,
            'Period': period,
            'Status': 'Present',
            'Remarks': 'Attended'
        },
        {
            'Student_ID': 'STU-1002',
            'Student_Name': 'Sophia Johnson',
            'Date': test_date,
            'Class': cls,
            'Section': sec,
            'Subject': subject,
            'Period': period,
            'Status': 'Late',
            'Remarks': 'Late arrival'
        }
    ]

    # 1. First save
    success, msg = AttendanceService.save_roster_attendance(records, marked_by='test_teacher', overwrite=False)
    assert success is True

    # 2. Duplicate attempt without overwrite -> should be rejected!
    dup_success, dup_msg = AttendanceService.save_roster_attendance(records, marked_by='test_teacher', overwrite=False)
    assert dup_success is False
    assert "already been marked" in dup_msg

    # 3. Overwrite attempt with overwrite=True -> should succeed!
    records[0]['Status'] = 'Absent'
    records[0]['Remarks'] = 'Correction to Absent'
    ow_success, ow_msg = AttendanceService.save_roster_attendance(records, marked_by='test_teacher', overwrite=True)
    assert ow_success is True

    # 4. Verify record in database has updated status
    has_ex, ex_rows = AttendanceService.check_existing_attendance(test_date, cls, sec, subject, period)
    assert has_ex is True
    s1 = next(r for r in ex_rows if r['Student_ID'] == 'STU-1001')
    assert s1['Status'] == 'Absent'

def test_attendance_calculation_rules():
    profile = StudentService.get_student_profile('STU-1001')
    assert profile is not None
    stats = profile['stats']
    assert 'percentage' in stats
    assert 0.0 <= stats['percentage'] <= 100.0
    assert 'total_sessions' in stats
    assert 'present_count' in stats

def test_attendance_edit_and_delete():
    # Mark a dummy record
    date_str = '2026-11-05'
    recs = [{
        'Student_ID': 'STU-1001',
        'Student_Name': 'Alexander Smith',
        'Date': date_str,
        'Class': 'Grade 10',
        'Section': 'A',
        'Subject': 'Art',
        'Period': 'Period 6',
        'Status': 'Absent',
        'Remarks': 'None'
    }]
    AttendanceService.save_roster_attendance(recs, 'admin', overwrite=True)
    _, rows = AttendanceService.check_existing_attendance(date_str, 'Grade 10', 'A', 'Art', 'Period 6')
    att_id = rows[0]['Attendance_ID']

    # Edit record
    e_success, e_msg = AttendanceService.edit_record(att_id, 'Present', 'Medical note provided', 'admin')
    assert e_success is True

    # Delete record
    d_success, d_msg = AttendanceService.delete_record(att_id)
    assert d_success is True
