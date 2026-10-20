from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from services.auth_service import login_required
from services.attendance_service import AttendanceService
from services.settings_service import SettingsService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    metrics = AttendanceService.get_dashboard_metrics(target_date)
    settings_dict, _ = SettingsService.get_all()
    
    return render_template(
        'dashboard.html',
        metrics=metrics,
        target_date=target_date,
        institution_name=settings_dict.get('institution_name', 'Apex College'),
        academic_year=settings_dict.get('academic_year', '2026-2027')
    )

@dashboard_bp.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    metrics = AttendanceService.get_dashboard_metrics(target_date)
    return jsonify(metrics)
