import os
import shutil
import io
from pathlib import Path
from datetime import datetime
import pandas as pd

from config import Config
from services.excel_service import ExcelService, SCHEMAS

class BackupService:
    @staticmethod
    def get_workbook_stats():
        stats = []
        data_dir = Config.DATA_DIR
        for name, cols in SCHEMAS.items():
            path = data_dir / f"{name}.xlsx"
            if path.exists():
                size_bytes = path.stat().st_size
                size_kb = round(size_bytes / 1024, 1)
                mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                try:
                    df = ExcelService.read_df(name)
                    row_count = len(df)
                    status = 'Healthy'
                except Exception as e:
                    row_count = 0
                    status = f'Error: {e}'
            else:
                size_kb = 0
                mtime = 'N/A'
                row_count = 0
                status = 'Missing'

            stats.append({
                'name': name,
                'filename': f"{name}.xlsx",
                'row_count': row_count,
                'columns_count': len(cols),
                'size_kb': size_kb,
                'last_modified': mtime,
                'status': status
            })
        return stats

    @staticmethod
    def get_all_backups():
        backup_dir = Config.BACKUP_DIR
        if not backup_dir.exists():
            return []

        backups = []
        for file in backup_dir.glob('*.xlsx'):
            size_kb = round(file.stat().st_size / 1024, 1)
            created = datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            parts = file.stem.split('_')
            source = parts[0] if parts else file.stem

            backups.append({
                'filename': file.name,
                'source': source,
                'size_kb': size_kb,
                'created_at': created,
                'path': str(file)
            })

        # Sort newest first
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups

    @staticmethod
    def create_backup_now(workbook_name=None):
        data_dir = Config.DATA_DIR
        if workbook_name:
            path = data_dir / f"{workbook_name}.xlsx"
            if not path.exists():
                return False, f"Workbook {workbook_name}.xlsx not found."
            bp = ExcelService.create_backup(path)
            return True, f"Backup created: {bp.name}"
        else:
            # Backup all
            count = 0
            for name in SCHEMAS.keys():
                path = data_dir / f"{name}.xlsx"
                if path.exists():
                    ExcelService.create_backup(path)
                    count += 1
            return True, f"Successfully created backups for {count} workbooks."

    @staticmethod
    def restore_backup(backup_filename):
        backup_path = Config.BACKUP_DIR / backup_filename
        if not backup_path.exists():
            return False, "Backup file does not exist."

        # Detect source workbook name (e.g. students_20261020_... -> students)
        parts = backup_filename.split('_')
        source_name = parts[0]
        if source_name not in SCHEMAS:
            return False, f"Unknown schema for backup {backup_filename}."

        dest_path = Config.DATA_DIR / f"{source_name}.xlsx"

        # Validate that the backup file is a valid Excel workbook
        try:
            df = pd.read_excel(backup_path, engine='openpyxl')
            if not all(col in df.columns for col in SCHEMAS[source_name]):
                return False, "Backup file does not contain all required columns for this schema."
        except Exception as e:
            return False, f"Corrupted backup file: {e}"

        # Safety: create a pre-restore backup of the current live file
        if dest_path.exists():
            ExcelService.create_backup(dest_path)

        # Restore
        shutil.copy2(backup_path, dest_path)
        return True, f"Successfully restored {source_name}.xlsx from {backup_filename}."

    @staticmethod
    def generate_blank_template(schema_name):
        if schema_name not in SCHEMAS:
            return None
        cols = SCHEMAS[schema_name]
        df = pd.DataFrame(columns=cols)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=schema_name.capitalize())
        output.seek(0)
        return output
