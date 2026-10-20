import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
import pandas as pd
import openpyxl
from werkzeug.security import generate_password_hash

from config import Config

# Global re-entrant lock for file synchronization
_FILE_LOCK = threading.RLock()

# Schemas for all required workbooks
SCHEMAS = {
    'students': [
        'Student_ID', 'Roll_No', 'Full_Name', 'Email', 'Phone',
        'Class', 'Section', 'Course', 'Admission_Date', 'Status'
    ],
    'attendance': [
        'Attendance_ID', 'Student_ID', 'Student_Name', 'Date', 'Class',
        'Section', 'Subject', 'Period', 'Status', 'Marked_By', 'Remarks', 'Timestamp'
    ],
    'teachers': [
        'Teacher_ID', 'Full_Name', 'Email', 'Phone', 'Department',
        'Designation', 'Assigned_Classes', 'Assigned_Subjects', 'Status'
    ],
    'classes': [
        'Class_ID', 'Class_Name', 'Section', 'Stream_or_Course', 'Room_No',
        'Class_Teacher', 'Status'
    ],
    'users': [
        'User_ID', 'Username', 'Password_Hash', 'Full_Name', 'Email',
        'Role', 'Status', 'Created_At', 'Last_Login'
    ],
    'holidays': [
        'Holiday_ID', 'Holiday_Name', 'Start_Date', 'End_Date', 'Type', 'Description'
    ],
    'settings': [
        'Key', 'Value', 'Category', 'Description', 'Updated_At'
    ]
}

def sanitize_cell_value(val):
    """
    Prevents Excel Formula Injection (CSV/XLSX Formula Injection).
    Prepends a single quote if the string begins with =, +, -, @, tab, or newline.
    """
    if isinstance(val, str) and len(val) > 0:
        if val[0] in ('=', '+', '-', '@', '\t', '\r', '\n'):
            return "'" + val
    return val

def sanitize_dataframe(df):
    """Sanitizes all string elements in a DataFrame before writing to Excel."""
    return df.map(sanitize_cell_value)

class ExcelService:
    @staticmethod
    def get_file_path(name, custom_data_dir=None):
        data_dir = Path(custom_data_dir) if custom_data_dir else Config.DATA_DIR
        return data_dir / f"{name}.xlsx"

    @staticmethod
    def read_df(name_or_path, custom_data_dir=None):
        """
        Thread-safely reads an Excel file into a pandas DataFrame.
        Ensures all expected columns exist. If file is missing or corrupt, returns empty DataFrame with schema.
        """
        with _FILE_LOCK:
            if isinstance(name_or_path, (str, Path)) and not str(name_or_path).endswith('.xlsx'):
                path = ExcelService.get_file_path(name_or_path, custom_data_dir)
                schema_name = str(name_or_path)
            else:
                path = Path(name_or_path)
                schema_name = path.stem

            if not path.exists():
                columns = SCHEMAS.get(schema_name, [])
                return pd.DataFrame(columns=columns)

            try:
                # Read all columns as string/object to preserve leading zeros in roll nos, phones, etc.
                df = pd.read_excel(path, dtype=str, engine='openpyxl')
                df = df.fillna('')
                
                # Check if all schema columns are present
                expected_cols = SCHEMAS.get(schema_name, [])
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = ''
                        
                return df
            except Exception as e:
                print(f"Warning: Error reading {path}: {e}. Returning empty DataFrame.")
                columns = SCHEMAS.get(schema_name, [])
                return pd.DataFrame(columns=columns)

    @staticmethod
    def save_df(name_or_path, df, custom_data_dir=None, create_backup=True):
        """
        Thread-safely and atomically writes a DataFrame to an Excel file.
        Uses write-to-temp-then-replace to eliminate file corruption risk.
        Creates an automatic backup before overwriting.
        """
        with _FILE_LOCK:
            if isinstance(name_or_path, (str, Path)) and not str(name_or_path).endswith('.xlsx'):
                path = ExcelService.get_file_path(name_or_path, custom_data_dir)
                schema_name = str(name_or_path)
            else:
                path = Path(name_or_path)
                schema_name = path.stem

            path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if file already exists
            if create_backup and path.exists() and path.stat().st_size > 0:
                ExcelService.create_backup(path)

            # Ensure DataFrame has all columns in consistent order if defined in schema
            expected_cols = SCHEMAS.get(schema_name, None)
            if expected_cols:
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = ''
                # Reorder so schema columns come first
                other_cols = [c for c in df.columns if c not in expected_cols]
                df = df[expected_cols + other_cols]

            # Sanitize for formula injection
            clean_df = sanitize_dataframe(df.copy().fillna(''))

            # Atomic write via temporary file
            temp_path = path.parent / f"{path.stem}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.tmp.xlsx"
            try:
                # Use openpyxl writer with styled headers
                with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
                    clean_df.to_excel(writer, index=False, sheet_name='Sheet1')
                    
                    # Auto-adjust column widths in openpyxl sheet
                    worksheet = writer.sheets['Sheet1']
                    for col in worksheet.columns:
                        max_len = 0
                        col_letter = col[0].column_letter
                        for cell in col:
                            val_str = str(cell.value or '')
                            if len(val_str) > max_len:
                                max_len = len(val_str)
                        worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

                # Atomically replace destination file
                if os.name == 'nt' and path.exists():
                    os.replace(temp_path, path)
                else:
                    os.replace(temp_path, path)
                return True
            except Exception as e:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass
                raise RuntimeError(f"Failed to save Excel workbook {path.name}: {e}")

    @staticmethod
    def lock():
        """Returns the re-entrant synchronization lock for transactional blocks."""
        return _FILE_LOCK

    @staticmethod
    def transactional_update(name_or_path, update_func, custom_data_dir=None, create_backup=True):
        """
        Executes a read-modify-write operation atomically under the global file lock.
        update_func takes current DataFrame and returns modified DataFrame.
        """
        with _FILE_LOCK:
            df = ExcelService.read_df(name_or_path, custom_data_dir)
            new_df = update_func(df)
            ExcelService.save_df(name_or_path, new_df, custom_data_dir, create_backup)
            return new_df

    @staticmethod
    def create_backup(file_path):
        """Creates a timestamped backup copy in Config.BACKUP_DIR."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            backup_dir = Config.BACKUP_DIR
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]
            backup_name = f"{file_path.stem}_{timestamp}.xlsx"
            backup_path = backup_dir / backup_name
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Warning: Could not create backup for {file_path}: {e}")
            return None

    @staticmethod
    def generate_id(prefix, current_ids):
        """Generates sequential ID like STU-1001, ATT-10001, etc."""
        nums = []
        for cid in current_ids:
            if isinstance(cid, str) and cid.startswith(prefix + '-'):
                try:
                    num = int(cid.split('-')[1])
                    nums.append(num)
                except ValueError:
                    pass
        next_num = max(nums) + 1 if nums else 1001
        return f"{prefix}-{next_num}"

    @classmethod
    def init_all_files(cls, custom_data_dir=None):
        """
        Initializes all required Excel workbooks with schemas and initial seed data if they do not exist.
        """
        with _FILE_LOCK:
            data_dir = Path(custom_data_dir) if custom_data_dir else Config.DATA_DIR
            data_dir.mkdir(parents=True, exist_ok=True)
            Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

            # 1. Users Workbook
            users_path = cls.get_file_path('users', data_dir)
            if not users_path.exists():
                initial_users = [
                    {
                        'User_ID': 'USR-1001',
                        'Username': 'admin',
                        'Password_Hash': generate_password_hash('Admin@123'),
                        'Full_Name': 'System Administrator',
                        'Email': 'admin@apexcollege.edu',
                        'Role': 'Admin',
                        'Status': 'Active',
                        'Created_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Last_Login': ''
                    },
                    {
                        'User_ID': 'USR-1002',
                        'Username': 'teacher',
                        'Password_Hash': generate_password_hash('Teacher@123'),
                        'Full_Name': 'Prof. Robert Miller',
                        'Email': 'robert.miller@apexcollege.edu',
                        'Role': 'Teacher',
                        'Status': 'Active',
                        'Created_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Last_Login': ''
                    },
                    {
                        'User_ID': 'USR-1003',
                        'Username': 'staff',
                        'Password_Hash': generate_password_hash('Staff@123'),
                        'Full_Name': 'Sarah Jenkins',
                        'Email': 'sarah.j@apexcollege.edu',
                        'Role': 'Attendance Staff',
                        'Status': 'Active',
                        'Created_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Last_Login': ''
                    }
                ]
                cls.save_df('users', pd.DataFrame(initial_users), custom_data_dir=data_dir, create_backup=False)

            # 2. Classes Workbook
            classes_path = cls.get_file_path('classes', data_dir)
            if not classes_path.exists():
                initial_classes = [
                    {'Class_ID': 'CLS-101', 'Class_Name': 'Grade 10', 'Section': 'A', 'Stream_or_Course': 'General Science', 'Room_No': '101', 'Class_Teacher': 'Prof. Robert Miller', 'Status': 'Active'},
                    {'Class_ID': 'CLS-102', 'Class_Name': 'Grade 10', 'Section': 'B', 'Stream_or_Course': 'General Science', 'Room_No': '102', 'Class_Teacher': 'Dr. Emily Watson', 'Status': 'Active'},
                    {'Class_ID': 'CLS-103', 'Class_Name': 'Grade 11', 'Section': 'A', 'Stream_or_Course': 'Computer Science', 'Room_No': '201', 'Class_Teacher': 'Prof. Alan Turing', 'Status': 'Active'},
                    {'Class_ID': 'CLS-104', 'Class_Name': 'Grade 12', 'Section': 'A', 'Stream_or_Course': 'Computer Science', 'Room_No': '301', 'Class_Teacher': 'Dr. Ada Lovelace', 'Status': 'Active'},
                    {'Class_ID': 'CLS-105', 'Class_Name': 'BCA Sem 1', 'Section': 'A', 'Stream_or_Course': 'Information Tech', 'Room_No': 'Lab 1', 'Class_Teacher': 'Prof. James Gosling', 'Status': 'Active'},
                ]
                cls.save_df('classes', pd.DataFrame(initial_classes), custom_data_dir=data_dir, create_backup=False)

            # 3. Teachers Workbook
            teachers_path = cls.get_file_path('teachers', data_dir)
            if not teachers_path.exists():
                initial_teachers = [
                    {'Teacher_ID': 'TCH-1001', 'Full_Name': 'Prof. Robert Miller', 'Email': 'robert.miller@apexcollege.edu', 'Phone': '+1-555-0191', 'Department': 'Science', 'Designation': 'Senior Lecturer', 'Assigned_Classes': 'Grade 10-A, Grade 11-A', 'Assigned_Subjects': 'Physics, Mathematics', 'Status': 'Active'},
                    {'Teacher_ID': 'TCH-1002', 'Full_Name': 'Dr. Emily Watson', 'Email': 'emily.w@apexcollege.edu', 'Phone': '+1-555-0192', 'Department': 'Humanities', 'Designation': 'Associate Professor', 'Assigned_Classes': 'Grade 10-B', 'Assigned_Subjects': 'English, Literature', 'Status': 'Active'},
                    {'Teacher_ID': 'TCH-1003', 'Full_Name': 'Prof. Alan Turing', 'Email': 'alan.turing@apexcollege.edu', 'Phone': '+1-555-0193', 'Department': 'Computer Science', 'Designation': 'Professor & HOD', 'Assigned_Classes': 'Grade 11-A, BCA Sem 1-A', 'Assigned_Subjects': 'Algorithms, Data Structures', 'Status': 'Active'}
                ]
                cls.save_df('teachers', pd.DataFrame(initial_teachers), custom_data_dir=data_dir, create_backup=False)

            # 4. Students Workbook
            students_path = cls.get_file_path('students', data_dir)
            if not students_path.exists():
                sample_students = [
                    {'Student_ID': 'STU-1001', 'Roll_No': '101', 'Full_Name': 'Alexander Smith', 'Email': 'alexander.s@student.edu', 'Phone': '+1-555-1101', 'Class': 'Grade 10', 'Section': 'A', 'Course': 'General Science', 'Admission_Date': '2025-08-15', 'Status': 'Active'},
                    {'Student_ID': 'STU-1002', 'Roll_No': '102', 'Full_Name': 'Sophia Johnson', 'Email': 'sophia.j@student.edu', 'Phone': '+1-555-1102', 'Class': 'Grade 10', 'Section': 'A', 'Course': 'General Science', 'Admission_Date': '2025-08-15', 'Status': 'Active'},
                    {'Student_ID': 'STU-1003', 'Roll_No': '103', 'Full_Name': 'Liam Brown', 'Email': 'liam.b@student.edu', 'Phone': '+1-555-1103', 'Class': 'Grade 10', 'Section': 'A', 'Course': 'General Science', 'Admission_Date': '2025-08-16', 'Status': 'Active'},
                    {'Student_ID': 'STU-1004', 'Roll_No': '104', 'Full_Name': 'Emma Davis', 'Email': 'emma.d@student.edu', 'Phone': '+1-555-1104', 'Class': 'Grade 10', 'Section': 'A', 'Course': 'General Science', 'Admission_Date': '2025-08-16', 'Status': 'Active'},
                    {'Student_ID': 'STU-1005', 'Roll_No': '105', 'Full_Name': 'Noah Wilson', 'Email': 'noah.w@student.edu', 'Phone': '+1-555-1105', 'Class': 'Grade 10', 'Section': 'A', 'Course': 'General Science', 'Admission_Date': '2025-08-17', 'Status': 'Active'},
                    {'Student_ID': 'STU-1006', 'Roll_No': '106', 'Full_Name': 'Olivia Martinez', 'Email': 'olivia.m@student.edu', 'Phone': '+1-555-1106', 'Class': 'Grade 10', 'Section': 'A', 'Course': 'General Science', 'Admission_Date': '2025-08-17', 'Status': 'Active'},
                    {'Student_ID': 'STU-1007', 'Roll_No': '201', 'Full_Name': 'Ethan Taylor', 'Email': 'ethan.t@student.edu', 'Phone': '+1-555-1201', 'Class': 'Grade 11', 'Section': 'A', 'Course': 'Computer Science', 'Admission_Date': '2025-08-18', 'Status': 'Active'},
                    {'Student_ID': 'STU-1008', 'Roll_No': '202', 'Full_Name': 'Ava Anderson', 'Email': 'ava.a@student.edu', 'Phone': '+1-555-1202', 'Class': 'Grade 11', 'Section': 'A', 'Course': 'Computer Science', 'Admission_Date': '2025-08-18', 'Status': 'Active'},
                    {'Student_ID': 'STU-1009', 'Roll_No': '203', 'Full_Name': 'Lucas Thomas', 'Email': 'lucas.t@student.edu', 'Phone': '+1-555-1203', 'Class': 'Grade 11', 'Section': 'A', 'Course': 'Computer Science', 'Admission_Date': '2025-08-19', 'Status': 'Active'},
                    {'Student_ID': 'STU-1010', 'Roll_No': '301', 'Full_Name': 'Isabella White', 'Email': 'isabella.w@student.edu', 'Phone': '+1-555-1301', 'Class': 'BCA Sem 1', 'Section': 'A', 'Course': 'Information Tech', 'Admission_Date': '2025-08-20', 'Status': 'Active'}
                ]
                cls.save_df('students', pd.DataFrame(sample_students), custom_data_dir=data_dir, create_backup=False)

            # 5. Attendance Workbook
            attendance_path = cls.get_file_path('attendance', data_dir)
            if not attendance_path.exists():
                today_str = datetime.now().strftime('%Y-%m-%d')
                initial_attendance = [
                    {'Attendance_ID': 'ATT-10001', 'Student_ID': 'STU-1001', 'Student_Name': 'Alexander Smith', 'Date': today_str, 'Class': 'Grade 10', 'Section': 'A', 'Subject': 'Mathematics', 'Period': 'Period 1', 'Status': 'Present', 'Marked_By': 'admin', 'Remarks': 'On time', 'Timestamp': f"{today_str} 09:05:00"},
                    {'Attendance_ID': 'ATT-10002', 'Student_ID': 'STU-1002', 'Student_Name': 'Sophia Johnson', 'Date': today_str, 'Class': 'Grade 10', 'Section': 'A', 'Subject': 'Mathematics', 'Period': 'Period 1', 'Status': 'Present', 'Marked_By': 'admin', 'Remarks': 'On time', 'Timestamp': f"{today_str} 09:05:00"},
                    {'Attendance_ID': 'ATT-10003', 'Student_ID': 'STU-1003', 'Student_Name': 'Liam Brown', 'Date': today_str, 'Class': 'Grade 10', 'Section': 'A', 'Subject': 'Mathematics', 'Period': 'Period 1', 'Status': 'Absent', 'Marked_By': 'admin', 'Remarks': 'Unexcused', 'Timestamp': f"{today_str} 09:05:00"},
                    {'Attendance_ID': 'ATT-10004', 'Student_ID': 'STU-1004', 'Student_Name': 'Emma Davis', 'Date': today_str, 'Class': 'Grade 10', 'Section': 'A', 'Subject': 'Mathematics', 'Period': 'Period 1', 'Status': 'Late', 'Marked_By': 'admin', 'Remarks': '15 mins late bus issue', 'Timestamp': f"{today_str} 09:20:00"},
                    {'Attendance_ID': 'ATT-10005', 'Student_ID': 'STU-1005', 'Student_Name': 'Noah Wilson', 'Date': today_str, 'Class': 'Grade 10', 'Section': 'A', 'Subject': 'Mathematics', 'Period': 'Period 1', 'Status': 'Leave', 'Marked_By': 'admin', 'Remarks': 'Medical sick note', 'Timestamp': f"{today_str} 09:05:00"},
                    {'Attendance_ID': 'ATT-10006', 'Student_ID': 'STU-1006', 'Student_Name': 'Olivia Martinez', 'Date': today_str, 'Class': 'Grade 10', 'Section': 'A', 'Subject': 'Mathematics', 'Period': 'Period 1', 'Status': 'Present', 'Marked_By': 'admin', 'Remarks': 'On time', 'Timestamp': f"{today_str} 09:05:00"},
                ]
                cls.save_df('attendance', pd.DataFrame(initial_attendance), custom_data_dir=data_dir, create_backup=False)

            # 6. Holidays Workbook
            holidays_path = cls.get_file_path('holidays', data_dir)
            if not holidays_path.exists():
                initial_holidays = [
                    {'Holiday_ID': 'HOL-101', 'Holiday_Name': 'New Year Day', 'Start_Date': '2026-01-01', 'End_Date': '2026-01-01', 'Type': 'Public Holiday', 'Description': 'National Holiday'},
                    {'Holiday_ID': 'HOL-102', 'Holiday_Name': 'Spring Break', 'Start_Date': '2026-03-23', 'End_Date': '2026-03-27', 'Type': 'Institutional Holiday', 'Description': 'Spring Recess'},
                    {'Holiday_ID': 'HOL-103', 'Holiday_Name': 'Labor Day', 'Start_Date': '2026-05-01', 'End_Date': '2026-05-01', 'Type': 'Public Holiday', 'Description': 'International Workers Day'},
                    {'Holiday_ID': 'HOL-104', 'Holiday_Name': 'Independence Day', 'Start_Date': '2026-07-04', 'End_Date': '2026-07-04', 'Type': 'National Holiday', 'Description': 'Independence Day'}
                ]
                cls.save_df('holidays', pd.DataFrame(initial_holidays), custom_data_dir=data_dir, create_backup=False)

            # 7. Settings Workbook
            settings_path = cls.get_file_path('settings', data_dir)
            if not settings_path.exists():
                initial_settings = [
                    {'Key': 'institution_name', 'Value': 'Apex International College', 'Category': 'General', 'Description': 'Official Institution Name', 'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                    {'Key': 'academic_year', 'Value': '2026-2027', 'Category': 'General', 'Description': 'Current Active Academic Year', 'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                    {'Key': 'low_attendance_threshold', 'Value': '75', 'Category': 'Attendance', 'Description': 'Minimum required attendance percentage', 'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                    {'Key': 'late_weight', 'Value': '0.5', 'Category': 'Attendance', 'Description': 'Weight of Late arrival in calculation (0 = Absent, 0.5 = Half, 1.0 = Present)', 'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                    {'Key': 'leave_counted_in_total', 'Value': 'no', 'Category': 'Attendance', 'Description': 'Include approved leave in total applicable sessions (yes/no)', 'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                    {'Key': 'date_format', 'Value': '%Y-%m-%d', 'Category': 'Display', 'Description': 'Date presentation format', 'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                    {'Key': 'default_class', 'Value': 'Grade 10', 'Category': 'Attendance', 'Description': 'Default class pre-selected in forms', 'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                    {'Key': 'default_section', 'Value': 'A', 'Category': 'Attendance', 'Description': 'Default section pre-selected in forms', 'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                    {'Key': 'system_version', 'Value': '2.5.0-Enterprise', 'Category': 'System', 'Description': 'Software version', 'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                ]
                cls.save_df('settings', pd.DataFrame(initial_settings), custom_data_dir=data_dir, create_backup=False)

            return True
