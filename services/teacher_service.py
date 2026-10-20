import io
import pandas as pd
from services.excel_service import ExcelService, SCHEMAS

class TeacherService:
    @staticmethod
    def get_all_teachers(search=None, department=None, status=None):
        df = ExcelService.read_df('teachers')
        if search:
            s = str(search).lower().strip()
            df = df[
                df['Full_Name'].str.lower().str.contains(s, na=False) |
                df['Teacher_ID'].str.lower().str.contains(s, na=False) |
                df['Email'].str.lower().str.contains(s, na=False) |
                df['Department'].str.lower().str.contains(s, na=False)
            ]
        if department:
            df = df[df['Department'].str.lower() == department.lower()]
        if status:
            df = df[df['Status'].str.lower() == status.lower()]

        return df.to_dict(orient='records')

    @staticmethod
    def get_teacher_by_id(teacher_id):
        df = ExcelService.read_df('teachers')
        matched = df[df['Teacher_ID'] == teacher_id]
        if not matched.empty:
            return matched.iloc[0].to_dict()
        return None

    @staticmethod
    def add_teacher(data):
        df = ExcelService.read_df('teachers')
        full_name = str(data.get('Full_Name', '')).strip()
        email = str(data.get('Email', '')).strip()

        if not full_name:
            return False, "Teacher Name is required."

        if email and (df['Email'].str.lower() == email.lower()).any():
            return False, f"Teacher with email '{email}' already exists."

        teacher_id = str(data.get('Teacher_ID', '')).strip()
        if not teacher_id:
            teacher_id = ExcelService.generate_id('TCH', df['Teacher_ID'].tolist())

        new_row = {
            'Teacher_ID': teacher_id,
            'Full_Name': full_name,
            'Email': email,
            'Phone': str(data.get('Phone', '')).strip(),
            'Department': str(data.get('Department', '')).strip(),
            'Designation': str(data.get('Designation', '')).strip(),
            'Assigned_Classes': str(data.get('Assigned_Classes', '')).strip(),
            'Assigned_Subjects': str(data.get('Assigned_Subjects', '')).strip(),
            'Status': str(data.get('Status', 'Active')).strip()
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        ExcelService.save_df('teachers', df)
        return True, "Teacher added successfully."

    @staticmethod
    def update_teacher(teacher_id, data):
        df = ExcelService.read_df('teachers')
        matched_idx = df[df['Teacher_ID'] == teacher_id].index
        if matched_idx.empty:
            return False, "Teacher not found."

        idx = matched_idx[0]
        email = str(data.get('Email', df.at[idx, 'Email'])).strip()
        if email:
            dup = df[(df.index != idx) & (df['Email'].str.lower() == email.lower())]
            if not dup.empty:
                return False, f"Another teacher with email '{email}' already exists."

        df.at[idx, 'Full_Name'] = str(data.get('Full_Name', df.at[idx, 'Full_Name'])).strip()
        df.at[idx, 'Email'] = email
        df.at[idx, 'Phone'] = str(data.get('Phone', df.at[idx, 'Phone'])).strip()
        df.at[idx, 'Department'] = str(data.get('Department', df.at[idx, 'Department'])).strip()
        df.at[idx, 'Designation'] = str(data.get('Designation', df.at[idx, 'Designation'])).strip()
        df.at[idx, 'Assigned_Classes'] = str(data.get('Assigned_Classes', df.at[idx, 'Assigned_Classes'])).strip()
        df.at[idx, 'Assigned_Subjects'] = str(data.get('Assigned_Subjects', df.at[idx, 'Assigned_Subjects'])).strip()
        df.at[idx, 'Status'] = str(data.get('Status', df.at[idx, 'Status'])).strip()

        ExcelService.save_df('teachers', df)
        return True, "Teacher updated successfully."

    @staticmethod
    def delete_teacher(teacher_id):
        df = ExcelService.read_df('teachers')
        if not (df['Teacher_ID'] == teacher_id).any():
            return False, "Teacher not found."
        df = df[df['Teacher_ID'] != teacher_id]
        ExcelService.save_df('teachers', df)
        return True, "Teacher deleted successfully."

    @staticmethod
    def export_teachers_excel():
        teachers = TeacherService.get_all_teachers()
        df = pd.DataFrame(teachers)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Teachers')
        output.seek(0)
        return output
