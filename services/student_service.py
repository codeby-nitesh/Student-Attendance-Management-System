import io
import math
from datetime import datetime
import pandas as pd
import openpyxl

from services.excel_service import ExcelService, SCHEMAS
from services.settings_service import SettingsService

class StudentService:
    @staticmethod
    def get_all_students(search=None, class_filter=None, section_filter=None, status_filter=None, page=1, per_page=15):
        df = ExcelService.read_df('students')
        
        # Filtering
        if search:
            search_str = str(search).lower().strip()
            df = df[
                df['Full_Name'].str.lower().str.contains(search_str, na=False) |
                df['Student_ID'].str.lower().str.contains(search_str, na=False) |
                df['Roll_No'].str.lower().str.contains(search_str, na=False) |
                df['Email'].str.lower().str.contains(search_str, na=False)
            ]
        
        if class_filter:
            df = df[df['Class'].str.strip().str.lower() == str(class_filter).strip().lower()]
            
        if section_filter:
            df = df[df['Section'].str.strip().str.lower() == str(section_filter).strip().lower()]

        if status_filter:
            df = df[df['Status'].str.strip().str.lower() == str(status_filter).strip().lower()]

        # Sort by Class, Section, Roll_No (numeric sort if possible)
        def sort_key(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return 999999
        
        if not df.empty:
            df['sort_roll'] = df['Roll_No'].apply(sort_key)
            df = df.sort_values(by=['Class', 'Section', 'sort_roll', 'Full_Name']).drop(columns=['sort_roll'])

        total_count = len(df)
        total_pages = max(1, math.ceil(total_count / per_page))
        current_page = max(1, min(page, total_pages))
        
        start_idx = (current_page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_df = df.iloc[start_idx:end_idx]

        students = paginated_df.to_dict(orient='records')
        return students, total_count, total_pages, current_page

    @staticmethod
    def get_student_by_id(student_id):
        df = ExcelService.read_df('students')
        matched = df[df['Student_ID'].astype(str) == str(student_id).strip()]
        if not matched.empty:
            return matched.iloc[0].to_dict()
        return None

    @staticmethod
    def add_student(data):
        df = ExcelService.read_df('students')
        
        full_name = str(data.get('Full_Name', '')).strip()
        roll_no = str(data.get('Roll_No', '')).strip()
        cls = str(data.get('Class', '')).strip()
        sec = str(data.get('Section', '')).strip()

        if not full_name or not roll_no or not cls or not sec:
            return False, "Full Name, Roll Number, Class, and Section are required."

        # Check duplicate roll number in same class & section
        dup_roll = df[
            (df['Class'].str.lower() == cls.lower()) &
            (df['Section'].str.lower() == sec.lower()) &
            (df['Roll_No'].str.lower() == roll_no.lower())
        ]
        if not dup_roll.empty:
            return False, f"Roll No. '{roll_no}' already exists in {cls} Section {sec}."

        # Custom Student_ID or auto-generated
        student_id = str(data.get('Student_ID', '')).strip()
        if not student_id:
            student_id = ExcelService.generate_id('STU', df['Student_ID'].tolist())
        else:
            if (df['Student_ID'].str.lower() == student_id.lower()).any():
                return False, f"Student ID '{student_id}' already exists."

        admission_date = str(data.get('Admission_Date', '')).strip() or datetime.now().strftime('%Y-%m-%d')
        status = str(data.get('Status', 'Active')).strip() or 'Active'

        new_student = {
            'Student_ID': student_id,
            'Roll_No': roll_no,
            'Full_Name': full_name,
            'Email': str(data.get('Email', '')).strip(),
            'Phone': str(data.get('Phone', '')).strip(),
            'Class': cls,
            'Section': sec,
            'Course': str(data.get('Course', '')).strip(),
            'Admission_Date': admission_date,
            'Status': status
        }
        df = pd.concat([df, pd.DataFrame([new_student])], ignore_index=True)
        ExcelService.save_df('students', df)
        return True, student_id

    @staticmethod
    def update_student(student_id, data):
        df = ExcelService.read_df('students')
        matched_idx = df[df['Student_ID'].astype(str) == str(student_id).strip()].index
        if matched_idx.empty:
            return False, "Student not found."

        idx = matched_idx[0]
        roll_no = str(data.get('Roll_No', df.at[idx, 'Roll_No'])).strip()
        cls = str(data.get('Class', df.at[idx, 'Class'])).strip()
        sec = str(data.get('Section', df.at[idx, 'Section'])).strip()

        # Check duplicate roll number for other students
        dup_roll = df[
            (df.index != idx) &
            (df['Class'].str.lower() == cls.lower()) &
            (df['Section'].str.lower() == sec.lower()) &
            (df['Roll_No'].str.lower() == roll_no.lower())
        ]
        if not dup_roll.empty:
            return False, f"Roll No. '{roll_no}' already exists in {cls} Section {sec} for another student."

        df.at[idx, 'Roll_No'] = roll_no
        df.at[idx, 'Full_Name'] = str(data.get('Full_Name', df.at[idx, 'Full_Name'])).strip()
        df.at[idx, 'Email'] = str(data.get('Email', df.at[idx, 'Email'])).strip()
        df.at[idx, 'Phone'] = str(data.get('Phone', df.at[idx, 'Phone'])).strip()
        df.at[idx, 'Class'] = cls
        df.at[idx, 'Section'] = sec
        df.at[idx, 'Course'] = str(data.get('Course', df.at[idx, 'Course'])).strip()
        df.at[idx, 'Admission_Date'] = str(data.get('Admission_Date', df.at[idx, 'Admission_Date'])).strip()
        df.at[idx, 'Status'] = str(data.get('Status', df.at[idx, 'Status'])).strip()

        ExcelService.save_df('students', df)
        return True, "Student updated successfully."

    @staticmethod
    def delete_student(student_id):
        df = ExcelService.read_df('students')
        matched = df[df['Student_ID'].astype(str) == str(student_id).strip()]
        if matched.empty:
            return False, "Student not found."

        df = df[df['Student_ID'].astype(str) != str(student_id).strip()]
        ExcelService.save_df('students', df)
        return True, "Student deleted successfully."

    @staticmethod
    def get_students_for_class_section(cls, sec):
        df = ExcelService.read_df('students')
        df = df[
            (df['Class'].str.strip().str.lower() == str(cls).strip().lower()) &
            (df['Section'].str.strip().str.lower() == str(sec).strip().lower()) &
            (df['Status'].str.strip().str.lower() == 'active')
        ]
        def sort_key(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return 999999
        if not df.empty:
            df['sort_roll'] = df['Roll_No'].apply(sort_key)
            df = df.sort_values(by=['sort_roll', 'Full_Name']).drop(columns=['sort_roll'])
        return df.to_dict(orient='records')

    @staticmethod
    def import_students_from_excel(file_storage):
        """
        Parses an uploaded Excel file, validates headers and rows, and imports records.
        Returns (success, imported_count, errors_list, preview_list).
        """
        try:
            import_df = pd.read_excel(file_storage, dtype=str, engine='openpyxl').fillna('')
        except Exception as e:
            return False, 0, [f"Failed to read Excel file: {str(e)}"], []

        required_cols = ['Roll_No', 'Full_Name', 'Class', 'Section']
        for col in required_cols:
            if col not in import_df.columns:
                return False, 0, [f"Missing required column header: '{col}'. Please use the template."], []

        current_df = ExcelService.read_df('students')
        errors = []
        valid_rows = []
        existing_ids = set(current_df['Student_ID'].str.lower().tolist())
        
        # Track roll numbers per class/section combination
        class_sec_rolls = set()
        for _, row in current_df.iterrows():
            key = f"{row.get('Class','').strip().lower()}_{row.get('Section','').strip().lower()}_{row.get('Roll_No','').strip().lower()}"
            class_sec_rolls.add(key)

        for idx, row in import_df.iterrows():
            row_num = idx + 2
            full_name = str(row.get('Full_Name', '')).strip()
            roll_no = str(row.get('Roll_No', '')).strip()
            cls = str(row.get('Class', '')).strip()
            sec = str(row.get('Section', '')).strip()

            if not full_name or not roll_no or not cls or not sec:
                errors.append(f"Row {row_num}: Missing required value (Full Name, Roll No, Class, or Section).")
                continue

            cs_key = f"{cls.lower()}_{sec.lower()}_{roll_no.lower()}"
            if cs_key in class_sec_rolls:
                errors.append(f"Row {row_num}: Duplicate Roll No '{roll_no}' in {cls} {sec}.")
                continue
            class_sec_rolls.add(cs_key)

            student_id = str(row.get('Student_ID', '')).strip()
            if student_id:
                if student_id.lower() in existing_ids:
                    errors.append(f"Row {row_num}: Student ID '{student_id}' already exists.")
                    continue
                existing_ids.add(student_id.lower())
            else:
                student_id = ExcelService.generate_id('STU', list(existing_ids))
                existing_ids.add(student_id.lower())

            valid_rows.append({
                'Student_ID': student_id,
                'Roll_No': roll_no,
                'Full_Name': full_name,
                'Email': str(row.get('Email', '')).strip(),
                'Phone': str(row.get('Phone', '')).strip(),
                'Class': cls,
                'Section': sec,
                'Course': str(row.get('Course', '')).strip(),
                'Admission_Date': str(row.get('Admission_Date', '')).strip() or datetime.now().strftime('%Y-%m-%d'),
                'Status': str(row.get('Status', 'Active')).strip() or 'Active'
            })

        if valid_rows:
            combined_df = pd.concat([current_df, pd.DataFrame(valid_rows)], ignore_index=True)
            ExcelService.save_df('students', combined_df)

        return True, len(valid_rows), errors, valid_rows

    @staticmethod
    def generate_import_template():
        """Generates an in-memory sample Excel template for importing students."""
        sample_data = [
            {
                'Student_ID': 'STU-1050',
                'Roll_No': '101',
                'Full_Name': 'John Doe',
                'Email': 'john.doe@example.com',
                'Phone': '+1-555-0100',
                'Class': 'Grade 10',
                'Section': 'A',
                'Course': 'General Science',
                'Admission_Date': '2026-08-01',
                'Status': 'Active'
            },
            {
                'Student_ID': '',
                'Roll_No': '102',
                'Full_Name': 'Jane Smith',
                'Email': 'jane.smith@example.com',
                'Phone': '+1-555-0101',
                'Class': 'Grade 10',
                'Section': 'A',
                'Course': 'General Science',
                'Admission_Date': '2026-08-01',
                'Status': 'Active'
            }
        ]
        df = pd.DataFrame(sample_data, columns=SCHEMAS['students'])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='StudentsTemplate')
        output.seek(0)
        return output

    @staticmethod
    def export_students_excel(search=None, class_filter=None, section_filter=None, status_filter=None):
        """Exports filtered student data as an Excel file in-memory."""
        students, _, _, _ = StudentService.get_all_students(
            search=search, class_filter=class_filter,
            section_filter=section_filter, status_filter=status_filter,
            page=1, per_page=100000
        )
        df = pd.DataFrame(students, columns=SCHEMAS['students'])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')
        output.seek(0)
        return output

    @staticmethod
    def get_student_profile(student_id):
        student = StudentService.get_student_by_id(student_id)
        if not student:
            return None

        att_df = ExcelService.read_df('attendance')
        student_att = att_df[att_df['Student_ID'].astype(str) == str(student_id).strip()]

        total_sessions = len(student_att)
        present_count = len(student_att[student_att['Status'].str.lower() == 'present'])
        absent_count = len(student_att[student_att['Status'].str.lower() == 'absent'])
        late_count = len(student_att[student_att['Status'].str.lower() == 'late'])
        leave_count = len(student_att[student_att['Status'].str.lower() == 'leave'])

        # Percentage calculation according to configured rules
        late_weight = SettingsService.get_late_weight()
        leave_in_total = SettingsService.is_leave_counted_in_total()

        if leave_in_total:
            applicable_sessions = total_sessions
        else:
            applicable_sessions = total_sessions - leave_count

        if applicable_sessions > 0:
            effective_present = present_count + (late_count * late_weight)
            percentage = round((effective_present / applicable_sessions) * 100, 1)
        else:
            percentage = 100.0 if total_sessions == 0 else 0.0

        # Sort attendance history by Date descending, Period descending
        history = student_att.sort_values(by=['Date', 'Period'], ascending=[False, False]).to_dict(orient='records')

        # Monthly summary for the current month
        current_year_month = datetime.now().strftime('%Y-%m')
        curr_month_df = student_att[student_att['Date'].str.startswith(current_year_month)]
        
        calendar_events = {}
        for _, row in curr_month_df.iterrows():
            date_str = str(row.get('Date', '')).strip()
            status = str(row.get('Status', '')).strip()
            calendar_events[date_str] = status

        return {
            'student': student,
            'stats': {
                'total_sessions': total_sessions,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'leave_count': leave_count,
                'percentage': percentage,
                'threshold': SettingsService.get_attendance_threshold(),
                'is_low_attendance': percentage < SettingsService.get_attendance_threshold()
            },
            'history': history,
            'calendar_events': calendar_events
        }
