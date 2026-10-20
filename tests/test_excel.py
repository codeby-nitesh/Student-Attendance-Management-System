import threading
import pandas as pd
from services.excel_service import ExcelService, sanitize_cell_value
from services.backup_service import BackupService

def test_formula_injection_sanitization():
    # Dangerous Excel formula strings
    payloads = [
        '=cmd|"/C calc"!A0',
        '+1+1',
        '-2+3',
        '@SUM(1,2)',
        '\t=2+2'
    ]
    for p in payloads:
        sanitized = sanitize_cell_value(p)
        assert sanitized.startswith("'"), f"Failed to sanitize: {p}"

    # Normal strings should remain untouched
    assert sanitize_cell_value('Alexander Smith') == 'Alexander Smith'
    assert sanitize_cell_value('STU-1001') == 'STU-1001'

def test_backup_and_restore():
    # 1. Create backup of classes
    success, msg = BackupService.create_backup_now('classes')
    assert success is True
    backups = BackupService.get_all_backups()
    assert len(backups) > 0
    classes_backup = next(b for b in backups if b['source'] == 'classes')
    assert classes_backup is not None

    # 2. Restore backup
    res_success, res_msg = BackupService.restore_backup(classes_backup['filename'])
    assert res_success is True

def test_missing_workbook_handling():
    # Read nonexistent workbook
    df = ExcelService.read_df('nonexistent_workbook_99')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_corrupted_workbook_handling(tmp_path):
    # Create corrupted file
    corrupt_file = tmp_path / "corrupt_test.xlsx"
    corrupt_file.write_bytes(b"This is not a valid zip/xlsx archive at all!")
    
    # Reading corrupted file should not crash the server, should return empty DataFrame with schema
    df = ExcelService.read_df(corrupt_file)
    assert isinstance(df, pd.DataFrame)

def test_pdf_report_generation():
    from services.report_service import ReportService
    title = "Test Attendance Report"
    subtitle = "Academic Year 2026-2027"
    headers = ["Roll No", "Student Name", "Class", "Percentage"]
    rows = [["101", "Alexander Smith", "Grade 10", "95%"], ["102", "Sophia Johnson", "Grade 10", "88%"]]
    
    pdf_buffer = ReportService.export_report_to_pdf(title, subtitle, headers, rows)
    assert pdf_buffer is not None
    pdf_bytes = pdf_buffer.getvalue()
    # Check PDF file magic header
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500

def test_concurrent_excel_writes():
    """Simulates concurrent threads writing to classes workbook to verify file locking."""
    errors = []

    def writer_task(worker_id):
        try:
            for i in range(3):
                def append_row(df):
                    new_row = {
                        'Class_ID': f"CLS-TH-{worker_id}-{i}",
                        'Class_Name': f"ThreadClass {worker_id}",
                        'Section': f"{i}",
                        'Stream_or_Course': 'Concurrency Test',
                        'Room_No': '100',
                        'Class_Teacher': 'Bot',
                        'Status': 'Active'
                    }
                    return pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

                ExcelService.transactional_update('classes', append_row, create_backup=False)
        except Exception as e:
            errors.append(e)

    threads = []
    for wid in range(4):
        t = threading.Thread(target=writer_task, args=(wid,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrency errors occurred: {errors}"
    final_df = ExcelService.read_df('classes')
    assert len(final_df) >= 12
