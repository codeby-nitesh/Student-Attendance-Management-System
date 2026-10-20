import io
import math
from datetime import datetime, timedelta
import pandas as pd

from services.excel_service import ExcelService, SCHEMAS
from services.settings_service import SettingsService

class AttendanceService:
    @staticmethod
    def check_existing_attendance(date_str, cls, sec, subject, period):
        df = ExcelService.read_df('attendance')
        matched = df[
            (df['Date'] == date_str) &
            (df['Class'].str.lower() == cls.lower()) &
            (df['Section'].str.lower() == sec.lower()) &
            (df['Subject'].str.lower() == subject.lower()) &
            (df['Period'].str.lower() == period.lower())
        ]
        return not matched.empty, matched.to_dict(orient='records')

    @staticmethod
    def save_roster_attendance(records, marked_by, overwrite=False):
        """
        Saves a batch of attendance records for a class roster.
        Validates duplicate entries and handles overwrite if requested.
        """
        if not records:
            return False, "No attendance entries to record."

        df = ExcelService.read_df('attendance')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check duplicates
        date_str = records[0]['Date']
        cls = records[0]['Class']
        sec = records[0]['Section']
        subject = records[0]['Subject']
        period = records[0]['Period']

        has_existing, existing_rows = AttendanceService.check_existing_attendance(date_str, cls, sec, subject, period)
        if has_existing and not overwrite:
            return False, f"Attendance has already been marked for {cls} {sec} - {subject} ({period}) on {date_str}. Please confirm overwrite if you wish to update."

        # If overwrite, remove existing rows for this slot
        if has_existing and overwrite:
            df = df[~(
                (df['Date'] == date_str) &
                (df['Class'].str.lower() == cls.lower()) &
                (df['Section'].str.lower() == sec.lower()) &
                (df['Subject'].str.lower() == subject.lower()) &
                (df['Period'].str.lower() == period.lower())
            )]

        existing_ids = df['Attendance_ID'].tolist()
        new_rows = []
        for rec in records:
            att_id = ExcelService.generate_id('ATT', existing_ids)
            existing_ids.append(att_id)
            new_rows.append({
                'Attendance_ID': att_id,
                'Student_ID': str(rec.get('Student_ID', '')).strip(),
                'Student_Name': str(rec.get('Student_Name', '')).strip(),
                'Date': date_str,
                'Class': cls,
                'Section': sec,
                'Subject': subject,
                'Period': period,
                'Status': str(rec.get('Status', 'Present')).strip(),
                'Marked_By': marked_by,
                'Remarks': str(rec.get('Remarks', '')).strip(),
                'Timestamp': now_str
            })

        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        ExcelService.save_df('attendance', df)
        return True, f"Successfully recorded attendance for {len(new_rows)} students."

    @staticmethod
    def get_attendance_records(date_from=None, date_to=None, class_filter=None, section_filter=None,
                               student_search=None, subject_filter=None, status_filter=None,
                               page=1, per_page=20):
        df = ExcelService.read_df('attendance')
        
        if date_from:
            df = df[df['Date'] >= date_from]
        if date_to:
            df = df[df['Date'] <= date_to]
        if class_filter:
            df = df[df['Class'].str.lower() == class_filter.lower()]
        if section_filter:
            df = df[df['Section'].str.lower() == section_filter.lower()]
        if subject_filter:
            df = df[df['Subject'].str.lower() == subject_filter.lower()]
        if status_filter:
            df = df[df['Status'].str.lower() == status_filter.lower()]
        if student_search:
            s = student_search.lower()
            df = df[
                df['Student_Name'].str.lower().str.contains(s, na=False) |
                df['Student_ID'].str.lower().str.contains(s, na=False)
            ]

        # Sort by Date descending, Period descending, Student_Name ascending
        if not df.empty:
            df = df.sort_values(by=['Date', 'Period', 'Student_Name'], ascending=[False, False, True])

        total_count = len(df)
        total_pages = max(1, math.ceil(total_count / per_page))
        current_page = max(1, min(page, total_pages))

        start_idx = (current_page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_df = df.iloc[start_idx:end_idx]

        records = paginated_df.to_dict(orient='records')
        return records, total_count, total_pages, current_page

    @staticmethod
    def edit_record(attendance_id, status, remarks, user_name):
        df = ExcelService.read_df('attendance')
        matched_idx = df[df['Attendance_ID'] == attendance_id].index
        if matched_idx.empty:
            return False, "Attendance record not found."

        idx = matched_idx[0]
        df.at[idx, 'Status'] = status
        df.at[idx, 'Remarks'] = remarks
        df.at[idx, 'Marked_By'] = f"{df.at[idx, 'Marked_By']} (edited by {user_name})"
        df.at[idx, 'Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        ExcelService.save_df('attendance', df)
        return True, "Attendance record updated successfully."

    @staticmethod
    def delete_record(attendance_id):
        df = ExcelService.read_df('attendance')
        matched = df[df['Attendance_ID'] == attendance_id]
        if matched.empty:
            return False, "Attendance record not found."
        df = df[df['Attendance_ID'] != attendance_id]
        ExcelService.save_df('attendance', df)
        return True, "Record deleted successfully."

    @staticmethod
    def export_records_excel(date_from=None, date_to=None, class_filter=None, section_filter=None,
                             student_search=None, subject_filter=None, status_filter=None):
        records, _, _, _ = AttendanceService.get_attendance_records(
            date_from=date_from, date_to=date_to, class_filter=class_filter,
            section_filter=section_filter, student_search=student_search,
            subject_filter=subject_filter, status_filter=status_filter,
            page=1, per_page=100000
        )
        df = pd.DataFrame(records, columns=SCHEMAS['attendance'])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='AttendanceRecords')
        output.seek(0)
        return output

    @staticmethod
    def get_dashboard_metrics(target_date=None):
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')

        students_df = ExcelService.read_df('students')
        att_df = ExcelService.read_df('attendance')

        # Total active students
        total_students = len(students_df[students_df['Status'].str.lower() == 'active'])
        if total_students == 0:
            total_students = len(students_df)

        # Filter attendance for the chosen date
        today_att = att_df[att_df['Date'] == target_date]

        present_count = len(today_att[today_att['Status'].str.lower() == 'present'])
        absent_count = len(today_att[today_att['Status'].str.lower() == 'absent'])
        late_count = len(today_att[today_att['Status'].str.lower() == 'late'])
        leave_count = len(today_att[today_att['Status'].str.lower() == 'leave'])
        total_marked = len(today_att)

        late_weight = SettingsService.get_late_weight()
        leave_in_total = SettingsService.is_leave_counted_in_total()

        if leave_in_total:
            applicable_total = total_marked
        else:
            applicable_total = total_marked - leave_count

        if applicable_total > 0:
            effective_present = present_count + (late_count * late_weight)
            attendance_pct = round((effective_present / applicable_total) * 100, 1)
        else:
            attendance_pct = 0.0

        # 7-day trend
        try:
            curr_dt = datetime.strptime(target_date, '%Y-%m-%d')
        except ValueError:
            curr_dt = datetime.now()

        trend_dates = []
        trend_present = []
        trend_absent = []
        trend_late = []
        trend_leave = []

        for i in range(6, -1, -1):
            d = (curr_dt - timedelta(days=i)).strftime('%Y-%m-%d')
            trend_dates.append(d)
            day_df = att_df[att_df['Date'] == d]
            trend_present.append(int(len(day_df[day_df['Status'].str.lower() == 'present'])))
            trend_absent.append(int(len(day_df[day_df['Status'].str.lower() == 'absent'])))
            trend_late.append(int(len(day_df[day_df['Status'].str.lower() == 'late'])))
            trend_leave.append(int(len(day_df[day_df['Status'].str.lower() == 'leave'])))

        # Class-wise attendance for target date
        class_stats = []
        classes_df = ExcelService.read_df('classes')
        for _, c_row in classes_df.iterrows():
            c_name = str(c_row.get('Class_Name', '')).strip()
            c_sec = str(c_row.get('Section', '')).strip()
            label = f"{c_name}-{c_sec}"
            
            c_att = today_att[
                (today_att['Class'].str.lower() == c_name.lower()) &
                (today_att['Section'].str.lower() == c_sec.lower())
            ]
            c_marked = len(c_att)
            if c_marked > 0:
                c_p = len(c_att[c_att['Status'].str.lower() == 'present'])
                c_l = len(c_att[c_att['Status'].str.lower() == 'late'])
                c_pct = round(((c_p + c_l * late_weight) / c_marked) * 100, 1)
            else:
                c_pct = 0.0
            
            class_stats.append({
                'label': label,
                'marked': c_marked,
                'percentage': c_pct
            })

        # Recent attendance activity (latest 8 records)
        recent_activity = []
        if not att_df.empty:
            recent_sorted = att_df.sort_values(by=['Date', 'Timestamp'], ascending=[False, False]).head(8)
            recent_activity = recent_sorted.to_dict(orient='records')

        return {
            'target_date': target_date,
            'total_students': total_students,
            'total_marked': total_marked,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'leave_count': leave_count,
            'attendance_pct': attendance_pct,
            'trend': {
                'dates': trend_dates,
                'present': trend_present,
                'absent': trend_absent,
                'late': trend_late,
                'leave': trend_leave
            },
            'class_stats': class_stats,
            'recent_activity': recent_activity
        }
