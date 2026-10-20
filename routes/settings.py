from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.auth_service import login_required, role_required
from services.settings_service import SettingsService
from services.class_service import ClassService

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def index():
    if request.method == 'POST':
        settings_map = {
            'institution_name': request.form.get('institution_name', '').strip(),
            'academic_year': request.form.get('academic_year', '').strip(),
            'low_attendance_threshold': request.form.get('low_attendance_threshold', '75').strip(),
            'late_weight': request.form.get('late_weight', '0.5').strip(),
            'leave_counted_in_total': request.form.get('leave_counted_in_total', 'no').strip(),
            'date_format': request.form.get('date_format', '%Y-%m-%d').strip(),
            'default_class': request.form.get('default_class', 'Grade 10').strip(),
            'default_section': request.form.get('default_section', 'A').strip(),
        }
        SettingsService.update_multiple(settings_map)
        flash('Settings successfully saved and applied across the system.', 'success')
        return redirect(url_for('settings.index'))

    settings_dict, records = SettingsService.get_all()
    class_options = ClassService.get_dropdown_options()

    return render_template('settings/index.html', settings=settings_dict, records=records, class_options=class_options)
