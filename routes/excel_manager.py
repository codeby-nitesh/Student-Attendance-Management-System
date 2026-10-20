from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
import pandas as pd

from config import Config
from services.auth_service import login_required, role_required
from services.excel_service import ExcelService, SCHEMAS
from services.backup_service import BackupService

excel_bp = Blueprint('excel_center', __name__)

@excel_bp.route('/excel-center')
@login_required
@role_required(['Admin'])
def index():
    stats = BackupService.get_workbook_stats()
    backups = BackupService.get_all_backups()
    return render_template('excel_center/index.html', stats=stats, backups=backups, schemas=SCHEMAS)

@excel_bp.route('/excel-center/download/<workbook_name>')
@login_required
@role_required(['Admin'])
def download_workbook(workbook_name):
    if workbook_name not in SCHEMAS:
        flash('Invalid workbook name.', 'danger')
        return redirect(url_for('excel_center.index'))

    path = Config.DATA_DIR / f"{workbook_name}.xlsx"
    if not path.exists():
        flash(f"Workbook {workbook_name}.xlsx does not exist on disk.", 'danger')
        return redirect(url_for('excel_center.index'))

    return send_file(
        path,
        as_attachment=True,
        download_name=f"{workbook_name}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@excel_bp.route('/excel-center/template/<schema_name>')
@login_required
def download_template(schema_name):
    file_stream = BackupService.generate_blank_template(schema_name)
    if not file_stream:
        flash('Invalid schema template requested.', 'danger')
        return redirect(url_for('excel_center.index'))

    return send_file(
        file_stream,
        as_attachment=True,
        download_name=f"{schema_name}_blank_template.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@excel_bp.route('/excel-center/backup-now', methods=['POST'])
@login_required
@role_required(['Admin'])
def create_backup():
    workbook_name = request.form.get('workbook_name', '').strip()
    success, msg = BackupService.create_backup_now(workbook_name if workbook_name else None)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('excel_center.index'))

@excel_bp.route('/excel-center/restore', methods=['POST'])
@login_required
@role_required(['Admin'])
def restore_backup():
    backup_filename = request.form.get('backup_filename', '').strip()
    success, msg = BackupService.restore_backup(backup_filename)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('excel_center.index'))

@excel_bp.route('/excel-center/upload/<workbook_name>', methods=['POST'])
@login_required
@role_required(['Admin'])
def upload_workbook(workbook_name):
    if workbook_name not in SCHEMAS:
        flash('Invalid target workbook.', 'danger')
        return redirect(url_for('excel_center.index'))

    if 'file' not in request.files:
        flash('No file uploaded.', 'warning')
        return redirect(url_for('excel_center.index'))

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('Only Excel files (.xlsx, .xls) are allowed.', 'danger')
        return redirect(url_for('excel_center.index'))

    try:
        df = pd.read_excel(file, dtype=str, engine='openpyxl').fillna('')
        expected_cols = SCHEMAS[workbook_name]

        # Validation: check all required columns are present
        missing_cols = [c for c in expected_cols if c not in df.columns]
        if missing_cols:
            flash(f"Validation Error: Uploaded file is missing required columns: {', '.join(missing_cols)}", 'danger')
            return redirect(url_for('excel_center.index'))

        # Backup current live file and replace
        ExcelService.save_df(workbook_name, df, create_backup=True)
        flash(f"Workbook '{workbook_name}.xlsx' was successfully validated and replaced with {len(df)} records.", 'success')
    except Exception as e:
        flash(f"Failed to process Excel workbook: {str(e)}", 'danger')

    return redirect(url_for('excel_center.index'))
