from datetime import datetime, timezone, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import GPSTrackingLog, User, SiteVisit, Roles
from app.services.auth_service import log_audit
from app.extensions import db

gps_bp = Blueprint('gps', __name__)

@gps_bp.route('/')
@login_required
def index():
    user_id = request.args.get('user_id')
    tracking_type = request.args.get('type')
    department = request.args.get('department', 'All')
    
    query = GPSTrackingLog.query.join(User)
    if not current_user.is_management() and not current_user.is_hr() and not current_user.has_role(Roles.FIELD_EXEC):
        query = query.filter(GPSTrackingLog.user_id == current_user.id)
    else:
        if department and department != 'All':
            query = query.filter(User.department == department)
        if user_id and user_id.isdigit():
            query = query.filter(GPSTrackingLog.user_id == int(user_id))

    if tracking_type and tracking_type != 'All':
        query = query.filter(GPSTrackingLog.tracking_type.ilike(f"%{tracking_type}%"))

    logs = query.order_by(GPSTrackingLog.timestamp.desc()).limit(100).all()
    field_users = User.query.filter(User.is_active == True).all()

    # Calculate active status
    active_executives = []
    seen_users = set()
    for l in logs:
        if l.user_id not in seen_users:
            seen_users.add(l.user_id)
            active_executives.append({'user': l.user, 'last_log': l})

    departments = ['Sales', 'Field Operations', 'Finance', 'Human Resources', 'Marketing', 'Information Technology', 'Management']

    return render_template(
        'gps/index.html',
        logs=logs,
        field_users=field_users,
        selected_user_id=user_id,
        selected_department=department,
        departments=departments,
        tracking_type=tracking_type or 'All',
        today_logs=len(logs),
        unique_employees_tracked=len(seen_users),
        active_executives=active_executives
    )

@gps_bp.route('/checkin', methods=['POST'])
@gps_bp.route('/ping', endpoint='record_ping', methods=['POST'])
@login_required
def record_checkin():
    lat_str = request.form.get('latitude', '23.0338')
    lng_str = request.form.get('longitude', '72.5850')
    location_name = request.form.get('location_name', 'Ahmedabad On-Site Inspection').strip()
    tracking_type = request.form.get('tracking_type', 'Check-In')
    visit_id_str = request.form.get('visit_id')

    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except ValueError:
        lat, lng = 23.0338, 72.5850

    visit_id = int(visit_id_str) if visit_id_str and visit_id_str.isdigit() else None

    log_entry = GPSTrackingLog(
        user_id=current_user.id,
        latitude=lat,
        longitude=lng,
        location_name=location_name,
        tracking_type=tracking_type,
        visit_id=visit_id,
        device_info=request.user_agent.string[:120] if request.user_agent else 'Mobile / Chrome'
    )
    db.session.add(log_entry)

    # If linked to a visit, update the visit check-in time
    if visit_id:
        visit = SiteVisit.query.get(visit_id)
        if visit:
            visit.check_in_time = datetime.now(timezone.utc)
            visit.check_in_location = location_name
            visit.status = 'Completed'

    db.session.commit()
    log_audit('CREATE', 'GPSTrackingLog', log_entry.id, f"GPS {tracking_type} at {location_name}")
    flash(f"GPS {tracking_type} recorded at {location_name} successfully!", 'success')
    return redirect(request.referrer or url_for('gps.index'))

def func_date(col):
    from sqlalchemy import func
    return func.date(col)
