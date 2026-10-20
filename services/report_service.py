import io
from datetime import datetime
import pandas as pd
import openpyxl
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from services.excel_service import ExcelService
from services.settings_service import SettingsService

class ReportService:
    @staticmethod
    def get_aggregated_student_report(date_from=None, date_to=None, class_filter=None, section_filter=None, low_only=False):
        att_df = ExcelService.read_df('attendance')
        students_df = ExcelService.read_df('students')

        # Apply date filters
        if date_from:
            att_df = att_df[att_df['Date'] >= date_from]
        if date_to:
            att_df = att_df[att_df['Date'] <= date_to]
        if class_filter:
            att_df = att_df[att_df['Class'].str.lower() == class_filter.lower()]
            students_df = students_df[students_df['Class'].str.lower() == class_filter.lower()]
        if section_filter:
            att_df = att_df[att_df['Section'].str.lower() == section_filter.lower()]
            students_df = students_df[students_df['Section'].str.lower() == section_filter.lower()]

        late_weight = SettingsService.get_late_weight()
        leave_in_total = SettingsService.is_leave_counted_in_total()
        threshold = SettingsService.get_attendance_threshold()

        results = []
        for _, s_row in students_df.iterrows():
            s_id = str(s_row.get('Student_ID', '')).strip()
            s_name = str(s_row.get('Full_Name', '')).strip()
            s_roll = str(s_row.get('Roll_No', '')).strip()
            s_class = str(s_row.get('Class', '')).strip()
            s_sec = str(s_row.get('Section', '')).strip()

            s_att = att_df[att_df['Student_ID'].astype(str) == s_id]
            total = len(s_att)
            present = len(s_att[s_att['Status'].str.lower() == 'present'])
            absent = len(s_att[s_att['Status'].str.lower() == 'absent'])
            late = len(s_att[s_att['Status'].str.lower() == 'late'])
            leave = len(s_att[s_att['Status'].str.lower() == 'leave'])

            if leave_in_total:
                applicable = total
            else:
                applicable = total - leave

            if applicable > 0:
                eff_p = present + (late * late_weight)
                pct = round((eff_p / applicable) * 100, 1)
            else:
                pct = 100.0 if total == 0 else 0.0

            is_low = pct < threshold

            if low_only and not is_low:
                continue

            results.append({
                'student_id': s_id,
                'roll_no': s_roll,
                'full_name': s_name,
                'class': s_class,
                'section': s_sec,
                'total_sessions': total,
                'present': present,
                'absent': absent,
                'late': late,
                'leave': leave,
                'percentage': pct,
                'is_low': is_low
            })

        # Sort by percentage ascending if low_only, else by Class, Section, Roll
        if low_only:
            results.sort(key=lambda x: x['percentage'])
        else:
            results.sort(key=lambda x: (x['class'], x['section'], x['roll_no']))

        return results

    @staticmethod
    def get_class_wise_report(date_from=None, date_to=None):
        att_df = ExcelService.read_df('attendance')
        classes_df = ExcelService.read_df('classes')

        if date_from:
            att_df = att_df[att_df['Date'] >= date_from]
        if date_to:
            att_df = att_df[att_df['Date'] <= date_to]

        late_weight = SettingsService.get_late_weight()
        leave_in_total = SettingsService.is_leave_counted_in_total()
        results = []

        for _, c_row in classes_df.iterrows():
            c_name = str(c_row.get('Class_Name', '')).strip()
            c_sec = str(c_row.get('Section', '')).strip()
            c_teacher = str(c_row.get('Class_Teacher', '')).strip()

            c_att = att_df[
                (att_df['Class'].str.lower() == c_name.lower()) &
                (att_df['Section'].str.lower() == c_sec.lower())
            ]

            total = len(c_att)
            present = len(c_att[c_att['Status'].str.lower() == 'present'])
            absent = len(c_att[c_att['Status'].str.lower() == 'absent'])
            late = len(c_att[c_att['Status'].str.lower() == 'late'])
            leave = len(c_att[c_att['Status'].str.lower() == 'leave'])

            if leave_in_total:
                applicable = total
            else:
                applicable = total - leave

            if applicable > 0:
                eff_p = present + (late * late_weight)
                pct = round((eff_p / applicable) * 100, 1)
            else:
                pct = 0.0

            results.append({
                'class_name': c_name,
                'section': c_sec,
                'class_teacher': c_teacher,
                'total_records': total,
                'present': present,
                'absent': absent,
                'late': late,
                'leave': leave,
                'percentage': pct
            })

        return results

    @staticmethod
    def get_subject_wise_report(date_from=None, date_to=None):
        att_df = ExcelService.read_df('attendance')
        if date_from:
            att_df = att_df[att_df['Date'] >= date_from]
        if date_to:
            att_df = att_df[att_df['Date'] <= date_to]

        late_weight = SettingsService.get_late_weight()
        subjects = att_df['Subject'].dropna().unique()
        results = []

        for sub in sorted(subjects):
            sub_str = str(sub).strip()
            if not sub_str:
                continue
            sub_att = att_df[att_df['Subject'] == sub_str]
            total = len(sub_att)
            present = len(sub_att[sub_att['Status'].str.lower() == 'present'])
            absent = len(sub_att[sub_att['Status'].str.lower() == 'absent'])
            late = len(sub_att[sub_att['Status'].str.lower() == 'late'])
            leave = len(sub_att[sub_att['Status'].str.lower() == 'leave'])

            eff_p = present + (late * late_weight)
            pct = round((eff_p / total) * 100, 1) if total > 0 else 0.0

            results.append({
                'subject': sub_str,
                'total_records': total,
                'present': present,
                'absent': absent,
                'late': late,
                'leave': leave,
                'percentage': pct
            })
        return results

    @staticmethod
    def export_report_to_excel(report_type, data):
        output = io.BytesIO()
        df = pd.DataFrame(data)
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=f"{report_type[:25]}")
        output.seek(0)
        return output

    @staticmethod
    def export_report_to_pdf(title, subtitle, table_headers, table_data):
        """
        Generates a professional styled PDF report using ReportLab.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=6
        )
        sub_style = ParagraphStyle(
            'ReportSub',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4B5563'),
            spaceAfter=14
        )

        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(subtitle, sub_style))

        # Build table
        table_content = [table_headers] + table_data
        t = Table(table_content, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ]))

        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer
