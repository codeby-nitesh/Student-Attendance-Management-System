import os
from datetime import datetime
from flask import Flask, render_template

from config import Config
from services.excel_service import ExcelService
from services.settings_service import SettingsService

# Import Blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.students import students_bp
from routes.student_profile import student_profile_bp
from routes.attendance import attendance_bp
from routes.reports import reports_bp
from routes.classes import classes_bp
from routes.teachers import teachers_bp
from routes.excel_manager import excel_bp
from routes.users import users_bp
from routes.settings import settings_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Excel files and directory structure
    with app.app_context():
        ExcelService.init_all_files()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(student_profile_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(teachers_bp)
    app.register_blueprint(excel_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)

    # Global template context
    @app.context_processor
    def inject_global_data():
        settings_dict, _ = SettingsService.get_all()
        return {
            'app_name': settings_dict.get('institution_name', 'Apex Attendance System'),
            'academic_year': settings_dict.get('academic_year', '2026-2027'),
            'low_threshold': SettingsService.get_attendance_threshold(),
            'current_year': datetime.now().year,
            'today_date': datetime.now().strftime('%Y-%m-%d')
        }

    # Template filters
    @app.template_filter('status_badge')
    def status_badge_filter(status):
        st = str(status).strip().lower()
        if st == 'present':
            return '<span class="badge badge-present"><i class="fas fa-check-circle me-1"></i>Present</span>'
        elif st == 'absent':
            return '<span class="badge badge-absent"><i class="fas fa-times-circle me-1"></i>Absent</span>'
        elif st == 'late':
            return '<span class="badge badge-late"><i class="fas fa-clock me-1"></i>Late</span>'
        elif st == 'leave':
            return '<span class="badge badge-leave"><i class="fas fa-calendar-minus me-1"></i>Leave</span>'
        elif st == 'active':
            return '<span class="badge bg-success-subtle text-success border border-success-subtle"><i class="fas fa-circle-dot me-1"></i>Active</span>'
        elif st == 'inactive':
            return '<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle"><i class="fas fa-ban me-1"></i>Inactive</span>'
        return f'<span class="badge bg-light text-dark">{status}</span>'

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
