import io
import pandas as pd
from services.excel_service import ExcelService, SCHEMAS

class ClassService:
    @staticmethod
    def get_all_classes():
        df = ExcelService.read_df('classes')
        students_df = ExcelService.read_df('students')

        classes = []
        for _, row in df.iterrows():
            c_id = str(row.get('Class_ID', '')).strip()
            c_name = str(row.get('Class_Name', '')).strip()
            sec = str(row.get('Section', '')).strip()
            stream = str(row.get('Stream_or_Course', '')).strip()
            room = str(row.get('Room_No', '')).strip()
            teacher = str(row.get('Class_Teacher', '')).strip()
            status = str(row.get('Status', 'Active')).strip()

            # Count students in this class and section
            st_count = len(students_df[
                (students_df['Class'].str.strip().str.lower() == c_name.lower()) &
                (students_df['Section'].str.strip().str.lower() == sec.lower())
            ])

            classes.append({
                'class_id': c_id,
                'class_name': c_name,
                'section': sec,
                'stream': stream,
                'room_no': room,
                'class_teacher': teacher,
                'status': status,
                'student_count': st_count
            })
        return classes

    @staticmethod
    def get_class_by_id(class_id):
        df = ExcelService.read_df('classes')
        matched = df[df['Class_ID'] == class_id]
        if not matched.empty:
            return matched.iloc[0].to_dict()
        return None

    @staticmethod
    def add_class(data):
        df = ExcelService.read_df('classes')
        c_name = str(data.get('Class_Name', '')).strip()
        sec = str(data.get('Section', '')).strip()

        if not c_name or not sec:
            return False, "Class Name and Section are required."

        # Check existing
        dup = df[
            (df['Class_Name'].str.lower() == c_name.lower()) &
            (df['Section'].str.lower() == sec.lower())
        ]
        if not dup.empty:
            return False, f"Class {c_name} Section {sec} already exists."

        class_id = str(data.get('Class_ID', '')).strip()
        if not class_id:
            class_id = ExcelService.generate_id('CLS', df['Class_ID'].tolist())

        new_row = {
            'Class_ID': class_id,
            'Class_Name': c_name,
            'Section': sec,
            'Stream_or_Course': str(data.get('Stream_or_Course', '')).strip(),
            'Room_No': str(data.get('Room_No', '')).strip(),
            'Class_Teacher': str(data.get('Class_Teacher', '')).strip(),
            'Status': str(data.get('Status', 'Active')).strip()
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        ExcelService.save_df('classes', df)
        return True, "Class added successfully."

    @staticmethod
    def update_class(class_id, data):
        df = ExcelService.read_df('classes')
        matched_idx = df[df['Class_ID'] == class_id].index
        if matched_idx.empty:
            return False, "Class not found."

        idx = matched_idx[0]
        c_name = str(data.get('Class_Name', df.at[idx, 'Class_Name'])).strip()
        sec = str(data.get('Section', df.at[idx, 'Section'])).strip()

        # Check duplicate in others
        dup = df[
            (df.index != idx) &
            (df['Class_Name'].str.lower() == c_name.lower()) &
            (df['Section'].str.lower() == sec.lower())
        ]
        if not dup.empty:
            return False, f"Another class with name {c_name} and Section {sec} already exists."

        df.at[idx, 'Class_Name'] = c_name
        df.at[idx, 'Section'] = sec
        df.at[idx, 'Stream_or_Course'] = str(data.get('Stream_or_Course', df.at[idx, 'Stream_or_Course'])).strip()
        df.at[idx, 'Room_No'] = str(data.get('Room_No', df.at[idx, 'Room_No'])).strip()
        df.at[idx, 'Class_Teacher'] = str(data.get('Class_Teacher', df.at[idx, 'Class_Teacher'])).strip()
        df.at[idx, 'Status'] = str(data.get('Status', df.at[idx, 'Status'])).strip()

        ExcelService.save_df('classes', df)
        return True, "Class updated successfully."

    @staticmethod
    def delete_class(class_id):
        df = ExcelService.read_df('classes')
        if not (df['Class_ID'] == class_id).any():
            return False, "Class not found."
        df = df[df['Class_ID'] != class_id]
        ExcelService.save_df('classes', df)
        return True, "Class deleted successfully."

    @staticmethod
    def get_dropdown_options():
        classes_df = ExcelService.read_df('classes')
        options = {}
        for _, row in classes_df.iterrows():
            c = str(row.get('Class_Name', '')).strip()
            s = str(row.get('Section', '')).strip()
            if c:
                if c not in options:
                    options[c] = []
                if s and s not in options[c]:
                    options[c].append(s)
        return options

    @staticmethod
    def export_classes_excel():
        classes = ClassService.get_all_classes()
        df = pd.DataFrame(classes)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Classes')
        output.seek(0)
        return output
