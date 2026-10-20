import io
import pandas as pd
from services.student_service import StudentService

def test_student_crud():
    # 1. Add student
    student_data = {
        'Roll_No': '999',
        'Full_Name': 'Test Student One',
        'Email': 'test1@student.edu',
        'Phone': '+1-555-9999',
        'Class': 'Grade 10',
        'Section': 'A',
        'Course': 'General Science'
    }
    success, student_id = StudentService.add_student(student_data)
    assert success is True
    assert student_id.startswith('STU-')

    # 2. Get student
    st = StudentService.get_student_by_id(student_id)
    assert st is not None
    assert st['Full_Name'] == 'Test Student One'
    assert st['Roll_No'] == '999'

    # 3. Update student
    update_data = {
        'Roll_No': '999',
        'Full_Name': 'Updated Test Student',
        'Class': 'Grade 10',
        'Section': 'A',
        'Course': 'Computer Science',
        'Status': 'Active'
    }
    up_success, up_msg = StudentService.update_student(student_id, update_data)
    assert up_success is True
    st_up = StudentService.get_student_by_id(student_id)
    assert st_up['Full_Name'] == 'Updated Test Student'

    # 4. Delete student
    del_success, del_msg = StudentService.delete_student(student_id)
    assert del_success is True
    assert StudentService.get_student_by_id(student_id) is None

def test_prevent_duplicate_roll_number():
    data1 = {
        'Roll_No': '888',
        'Full_Name': 'Alpha Student',
        'Class': 'Grade 10',
        'Section': 'B'
    }
    s1, id1 = StudentService.add_student(data1)
    assert s1 is True

    # Attempt to add same roll number in same class and section
    data2 = {
        'Roll_No': '888',
        'Full_Name': 'Beta Student',
        'Class': 'Grade 10',
        'Section': 'B'
    }
    s2, msg2 = StudentService.add_student(data2)
    assert s2 is False
    assert "already exists in Grade 10 Section B" in msg2

    # Cleanup
    StudentService.delete_student(id1)

def test_student_import_excel():
    # Create sample in-memory excel
    import_df = pd.DataFrame([
        {
            'Roll_No': '771',
            'Full_Name': 'Import Student 1',
            'Class': 'Grade 12',
            'Section': 'A',
            'Course': 'Science',
            'Email': 'imp1@test.com'
        },
        {
            'Roll_No': '772',
            'Full_Name': 'Import Student 2',
            'Class': 'Grade 12',
            'Section': 'A',
            'Course': 'Science',
            'Email': 'imp2@test.com'
        }
    ])
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine='openpyxl') as writer:
        import_df.to_excel(writer, index=False)
    stream.seek(0)

    success, count, errors, rows = StudentService.import_students_from_excel(stream)
    assert success is True
    assert count == 2
    assert len(errors) == 0

def test_student_export_excel():
    output = StudentService.export_students_excel()
    assert output is not None
    # Read back to verify
    df = pd.read_excel(output, engine='openpyxl')
    assert 'Student_ID' in df.columns
    assert 'Full_Name' in df.columns
    assert len(df) > 0

def test_invalid_student_form_submissions():
    # Empty name
    s1, msg1 = StudentService.add_student({'Roll_No': '10', 'Full_Name': '', 'Class': 'Grade 10', 'Section': 'A'})
    assert s1 is False
    assert "required" in msg1

    # Empty roll number
    s2, msg2 = StudentService.add_student({'Roll_No': '', 'Full_Name': 'Valid Name', 'Class': 'Grade 10', 'Section': 'A'})
    assert s2 is False
    assert "required" in msg2

    # Empty class
    s3, msg3 = StudentService.add_student({'Roll_No': '11', 'Full_Name': 'Valid Name', 'Class': '', 'Section': 'A'})
    assert s3 is False
    assert "required" in msg3
