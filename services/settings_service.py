from datetime import datetime
import pandas as pd
from services.excel_service import ExcelService
from config import Config

class SettingsService:
    @staticmethod
    def get_all():
        """Returns all settings as a dict of {key: value} and a list of setting records."""
        df = ExcelService.read_df('settings')
        settings_dict = {}
        records = []
        for _, row in df.iterrows():
            key = str(row.get('Key', '')).strip()
            val = str(row.get('Value', '')).strip()
            cat = str(row.get('Category', 'General')).strip()
            desc = str(row.get('Description', '')).strip()
            updated = str(row.get('Updated_At', '')).strip()
            if key:
                settings_dict[key] = val
                records.append({
                    'key': key,
                    'value': val,
                    'category': cat,
                    'description': desc,
                    'updated_at': updated
                })
        return settings_dict, records

    @staticmethod
    def get(key, default=None):
        settings_dict, _ = SettingsService.get_all()
        return settings_dict.get(key, default)

    @staticmethod
    def get_attendance_threshold():
        val = SettingsService.get('low_attendance_threshold', str(Config.DEFAULT_LOW_ATTENDANCE_THRESHOLD))
        try:
            return float(val)
        except ValueError:
            return 75.0

    @staticmethod
    def get_late_weight():
        val = SettingsService.get('late_weight', '0.5')
        try:
            return float(val)
        except ValueError:
            return 0.5

    @staticmethod
    def is_leave_counted_in_total():
        val = SettingsService.get('leave_counted_in_total', 'no').lower()
        return val in ('yes', 'true', '1')

    @staticmethod
    def update(key, value, category='General', description=''):
        df = ExcelService.read_df('settings')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'Key' in df.columns and (df['Key'] == key).any():
            df.loc[df['Key'] == key, 'Value'] = str(value)
            df.loc[df['Key'] == key, 'Updated_At'] = now_str
            if category:
                df.loc[df['Key'] == key, 'Category'] = category
            if description:
                df.loc[df['Key'] == key, 'Description'] = description
        else:
            new_row = {
                'Key': key,
                'Value': str(value),
                'Category': category,
                'Description': description,
                'Updated_At': now_str
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        ExcelService.save_df('settings', df)
        return True

    @staticmethod
    def update_multiple(settings_map):
        df = ExcelService.read_df('settings')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for key, val in settings_map.items():
            if (df['Key'] == key).any():
                df.loc[df['Key'] == key, 'Value'] = str(val)
                df.loc[df['Key'] == key, 'Updated_At'] = now_str
            else:
                new_row = {
                    'Key': key,
                    'Value': str(val),
                    'Category': 'General',
                    'Description': '',
                    'Updated_At': now_str
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        ExcelService.save_df('settings', df)
        return True
