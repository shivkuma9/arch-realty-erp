from datetime import datetime, date, timezone
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app.models import (
    User, Attendance, LeaveRequest, Task, EmployeeTarget, Payroll, Recruitment,
    Asset, Roles, EmployeeDocument, EmployeeOnboarding, HRRequest, ExitClearance, PerformanceReview,
    GPSTrackingLog
)
from app.forms import TaskForm, LeaveRequestForm, UserForm, TargetForm, RecruitmentForm, AssetForm
from app.services.auth_service import hr_required, log_audit
from app.extensions import db

hr_bp = Blueprint('hr', __name__)

# --- HR COMMAND CENTER & DASHBOARD ---

@hr_bp.route('/')
@hr_bp.route('/dashboard')
@login_required
@hr_required
def hr_dashboard():
    today = date.today()
    total_workforce = User.query.filter_by(is_active=True).count()
    
    # Real-time attendance counts for today
    present_count = Attendance.query.filter(
        Attendance.attendance_date == today,
        Attendance.status.in_(['Present', 'Field Duty'])
    ).count()
    leave_count = Attendance.query.filter_by(attendance_date=today, status='On Leave').count()
    attendance_rate = round((present_count / total_workforce * 100), 1) if total_workforce > 0 else 0

    # Pending Action Items
    pending_leaves = LeaveRequest.query.filter_by(status='Pending').order_by(LeaveRequest.created_at.desc()).all()
    pending_docs = EmployeeDocument.query.filter_by(status='Pending Review').order_by(EmployeeDocument.upload_date.desc()).all()
    in_progress_onboarding = EmployeeOnboarding.query.filter_by(status='In Progress').order_by(EmployeeOnboarding.joined_date.desc()).all()
    notice_exits = ExitClearance.query.filter_by(status='Notice Period').order_by(ExitClearance.resignation_date.desc()).all()
    pending_requests = HRRequest.query.filter_by(status='Pending').order_by(HRRequest.request_date.desc()).all()
    
    pending_actions_count = len(pending_leaves) + len(pending_docs) + len(in_progress_onboarding) + len(notice_exits) + len(pending_requests)

    # Attendance Snapshot
    attendance_today = Attendance.query.filter_by(attendance_date=today).all()

    # Recent Documents for verification table
    recent_docs = EmployeeDocument.query.order_by(EmployeeDocument.created_at.desc()).limit(10).all()

    return render_template(
        'hr/dashboard.html',
        today=today,
        total_workforce=total_workforce,
        present_count=present_count,
        leave_count=leave_count,
        attendance_rate=attendance_rate,
        pending_actions_count=pending_actions_count,
        pending_leaves=pending_leaves,
        pending_docs=pending_docs,
        in_progress_onboarding=in_progress_onboarding,
        notice_exits=notice_exits,
        pending_requests=pending_requests,
        attendance_today=attendance_today,
        recent_docs=recent_docs
    )

# --- EMPLOYEES DIRECTORY & PROFILES ---

@hr_bp.route('/employees')
@login_required
def employees_list():
    query = User.query
    search = request.args.get('search', '').strip()
    department = request.args.get('department', 'All').strip()
    status = request.args.get('status', 'All').strip()

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_fmt)) |
            (User.email.ilike(search_fmt)) |
            (User.employee_code.ilike(search_fmt)) |
            (User.role.ilike(search_fmt))
        )

    if department and department != 'All':
        query = query.filter_by(department=department)

    if status and status != 'All':
        query = query.filter_by(emp_status=status)

    employees = query.order_by(User.full_name.asc()).all()
    departments = ['All', 'Sales', 'Field Operations', 'Finance', 'Human Resources', 'Marketing', 'Information Technology', 'Management']
    
    return render_template(
        'hr/employees_list.html',
        employees=employees,
        departments=departments,
        current_department=department,
        current_status=status,
        search_query=search
    )

@hr_bp.route('/employees/<int:user_id>')
@login_required
def employee_profile(user_id):
    # Only HR, Management, or employee themselves can view profile
    if not (current_user.is_management() or current_user.is_hr() or current_user.id == user_id):
        abort(403)

    user = User.query.get_or_404(user_id)
    documents = EmployeeDocument.query.filter_by(user_id=user.id).order_by(EmployeeDocument.created_at.desc()).all()
    onboarding = EmployeeOnboarding.query.filter_by(user_id=user.id).first()
    exit_record = ExitClearance.query.filter_by(user_id=user.id).first()
    attendance_history = Attendance.query.filter_by(user_id=user.id).order_by(Attendance.attendance_date.desc()).limit(30).all()
    leave_requests = LeaveRequest.query.filter_by(user_id=user.id).order_by(LeaveRequest.created_at.desc()).all()
    targets = EmployeeTarget.query.filter_by(user_id=user.id).order_by(EmployeeTarget.created_at.desc()).all()
    tasks = Task.query.filter_by(assigned_to_id=user.id).order_by(Task.due_date.asc()).all()
    reviews = PerformanceReview.query.filter_by(user_id=user.id).order_by(PerformanceReview.id.desc()).all()

    return render_template(
        'hr/employee_profile.html',
        user=user,
        documents=documents,
        onboarding=onboarding,
        exit_record=exit_record,
        attendance_history=attendance_history,
        leave_requests=leave_requests,
        targets=targets,
        tasks=tasks,
        reviews=reviews
    )

# --- EMPLOYEE COMPLIANCE DOCUMENTS ---

@hr_bp.route('/documents')
@login_required
@hr_required
def documents_list():
    query = EmployeeDocument.query
    status = request.args.get('status', 'All')
    category = request.args.get('category', 'All')

    if status and status != 'All':
        query = query.filter_by(status=status)
    if category and category != 'All':
        query = query.filter_by(category=category)

    documents = query.order_by(EmployeeDocument.created_at.desc()).all()
    users = User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()
    
    categories = ['All', 'Identity Proof', 'Address Proof', 'Education Certificate', 'Experience Letter', 'Bank Details']
    return render_template(
        'hr/documents.html',
        documents=documents,
        users=users,
        categories=categories,
        current_status=status,
        current_category=category
    )

@hr_bp.route('/documents/<int:doc_id>/verify', methods=['POST'])
@login_required
@hr_required
def verify_document(doc_id):
    doc = EmployeeDocument.query.get_or_404(doc_id)
    doc.status = 'Verified'
    doc.verified_by_id = current_user.id
    doc.verified_at = datetime.now(timezone.utc)
    db.session.commit()
    log_audit('VERIFY_DOC', 'EmployeeDocument', doc.id, f"Verified document {doc.document_name} for User {doc.user_id}")
    flash(f"Document '{doc.document_name}' verified successfully.", 'success')
    return redirect(request.referrer or url_for('hr.documents_list'))

@hr_bp.route('/documents/<int:doc_id>/reject', methods=['POST'])
@login_required
@hr_required
def reject_document(doc_id):
    doc = EmployeeDocument.query.get_or_404(doc_id)
    rejection_notes = request.form.get('notes', 'Document verification rejected due to mismatch.')
    doc.status = 'Rejected'
    doc.notes = rejection_notes
    doc.verified_by_id = current_user.id
    doc.verified_at = datetime.now(timezone.utc)
    db.session.commit()
    log_audit('REJECT_DOC', 'EmployeeDocument', doc.id, f"Rejected document {doc.document_name} for User {doc.user_id}")
    flash(f"Document '{doc.document_name}' has been marked as Rejected.", 'warning')
    return redirect(request.referrer or url_for('hr.documents_list'))

@hr_bp.route('/documents/upload', methods=['POST'])
@login_required
@hr_required
def upload_document():
    user_id = request.form.get('user_id', type=int)
    category = request.form.get('category')
    document_name = request.form.get('document_name')
    notes = request.form.get('notes', '')

    if not user_id or not category or not document_name:
        flash('Please fill out all required document fields.', 'danger')
        return redirect(request.referrer or url_for('hr.documents_list'))

    count = EmployeeDocument.query.count() + 1
    doc_code = f"DOC-{count:03d}"
    doc = EmployeeDocument(
        doc_code=doc_code,
        user_id=user_id,
        category=category,
        document_name=document_name,
        upload_date=date.today(),
        status='Pending Review',
        notes=notes
    )
    db.session.add(doc)
    db.session.commit()
    log_audit('UPLOAD_DOC', 'EmployeeDocument', doc.id, f"Uploaded compliance document {doc_code}")
    flash(f"Document '{document_name}' ({doc_code}) recorded and queued for review.", 'success')
    return redirect(request.referrer or url_for('hr.documents_list'))

# --- NEW JOINERS & ONBOARDING TRACKER ---

@hr_bp.route('/onboarding')
@login_required
@hr_required
def onboarding_list():
    onboardings = EmployeeOnboarding.query.order_by(EmployeeOnboarding.joined_date.desc()).all()
    users = User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()
    return render_template('hr/onboarding.html', onboardings=onboardings, users=users)

@hr_bp.route('/onboarding/<int:id>/update-step', methods=['POST'])
@login_required
@hr_required
def update_onboarding_step(id):
    ob = EmployeeOnboarding.query.get_or_404(id)
    if ob.checklist_completed < ob.total_checklist_items:
        ob.checklist_completed += 1
        if ob.checklist_completed == ob.total_checklist_items:
            ob.status = 'Completed'
        db.session.commit()
        log_audit('UPDATE_ONBOARDING', 'EmployeeOnboarding', ob.id, f"Checklist step advanced to {ob.checklist_completed}/{ob.total_checklist_items}")
        flash(f"Onboarding progress updated for {ob.user.full_name}.", 'success')
    return redirect(request.referrer or url_for('hr.onboarding_list'))

@hr_bp.route('/onboarding/<int:id>/complete', methods=['POST'])
@login_required
@hr_required
def complete_onboarding(id):
    ob = EmployeeOnboarding.query.get_or_404(id)
    ob.checklist_completed = ob.total_checklist_items
    ob.status = 'Completed'
    db.session.commit()
    log_audit('COMPLETE_ONBOARDING', 'EmployeeOnboarding', ob.id, f"Onboarding marked fully completed for {ob.user.full_name}")
    flash(f"Onboarding marked 100% completed for {ob.user.full_name}.", 'success')
    return redirect(request.referrer or url_for('hr.onboarding_list'))

@hr_bp.route('/onboarding/new', methods=['POST'])
@login_required
@hr_required
def create_onboarding():
    user_id = request.form.get('user_id', type=int)
    role_title = request.form.get('role_title', '')
    notes = request.form.get('notes', '')
    
    if not user_id:
        flash('Please select an employee.', 'danger')
        return redirect(url_for('hr.onboarding_list'))

    existing = EmployeeOnboarding.query.filter_by(user_id=user_id).first()
    if existing:
        flash('Onboarding profile already exists for this employee.', 'info')
        return redirect(url_for('hr.onboarding_list'))

    ob = EmployeeOnboarding(
        user_id=user_id,
        role_title=role_title,
        joined_date=date.today(),
        checklist_completed=1,
        total_checklist_items=6,
        status='In Progress',
        notes=notes
    )
    db.session.add(ob)
    db.session.commit()
    log_audit('CREATE_ONBOARDING', 'EmployeeOnboarding', ob.id, f"Started onboarding for user {user_id}")
    flash('New joiner onboarding workflow initialized.', 'success')
    return redirect(url_for('hr.onboarding_list'))

# --- LEAVE REQUESTS & MANAGEMENT ---

@hr_bp.route('/leaves')
@login_required
@hr_required
def leaves_list():
    pending_leaves = LeaveRequest.query.filter_by(status='Pending').order_by(LeaveRequest.created_at.desc()).all()
    all_leaves = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).limit(50).all()
    return render_template('hr/leaves.html', pending_leaves=pending_leaves, all_leaves=all_leaves)

@hr_bp.route('/leave/new', methods=['GET', 'POST'])
@login_required
def request_leave():
    form = LeaveRequestForm()
    if form.validate_on_submit():
        leave = LeaveRequest(
            user_id=current_user.id,
            leave_type=form.leave_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            reason=form.reason.data,
            status='Pending'
        )
        db.session.add(leave)
        db.session.commit()
        log_audit('CREATE', 'LeaveRequest', leave.id, f"Applied for {leave.leave_type}")
        flash('Leave application submitted for approval.', 'success')
        return redirect(url_for('hr.attendance'))

    return render_template('hr/leave_form.html', form=form)

@hr_bp.route('/leave/<int:leave_id>/review', methods=['POST'])
@login_required
def review_leave(leave_id):
    if not current_user.is_management() and not current_user.is_hr():
        abort(403)

    leave = LeaveRequest.query.get_or_404(leave_id)
    action = request.form.get('action') # Approved or Rejected
    remarks = request.form.get('remarks', '')

    if action in ['Approved', 'Rejected']:
        leave.status = action
        leave.reviewed_by_id = current_user.id
        leave.review_remarks = remarks
        db.session.commit()
        log_audit('REVIEW_LEAVE', 'LeaveRequest', leave.id, f"Marked leave as {action}")
        flash(f"Leave application marked as {action}.", 'success')

    return redirect(request.referrer or url_for('hr.leaves_list'))

# --- RESIGNATIONS & EXIT CLEARANCE ---

@hr_bp.route('/exits')
@login_required
@hr_required
def exits_list():
    exits = ExitClearance.query.order_by(ExitClearance.resignation_date.desc()).all()
    users = User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()
    return render_template('hr/exits.html', exits=exits, users=users)

@hr_bp.route('/exits/<int:id>/complete', methods=['POST'])
@login_required
@hr_required
def complete_exit(id):
    ex = ExitClearance.query.get_or_404(id)
    ex.status = 'Cleared'
    ex.clearance_progress = '7 / 7 Full Clearance Done'
    ex.user.emp_status = 'Exited'
    db.session.commit()
    log_audit('COMPLETE_EXIT', 'ExitClearance', ex.id, f"Exit clearance finalized for {ex.user.full_name}")
    flash(f"Exit clearance signed off for {ex.user.full_name}.", 'success')
    return redirect(request.referrer or url_for('hr.exits_list'))

@hr_bp.route('/exits/<int:id>/update-progress', methods=['POST'])
@login_required
@hr_required
def update_exit_progress(id):
    ex = ExitClearance.query.get_or_404(id)
    progress = request.form.get('clearance_progress')
    notes = request.form.get('notes')
    if progress:
        ex.clearance_progress = progress
    if notes:
        ex.notes = notes
    db.session.commit()
    flash('Exit clearance checkpoint updated.', 'success')
    return redirect(request.referrer or url_for('hr.exits_list'))

@hr_bp.route('/exits/new', methods=['POST'])
@login_required
@hr_required
def create_exit():
    user_id = request.form.get('user_id', type=int)
    last_day_str = request.form.get('last_working_day')
    notes = request.form.get('notes', '')

    if not user_id or not last_day_str:
        flash('Please select employee and last working day.', 'danger')
        return redirect(url_for('hr.exits_list'))

    last_working_day = datetime.strptime(last_day_str, '%Y-%m-%d').date()
    user = User.query.get(user_id)
    if user:
        user.emp_status = 'Notice Period'

    ex = ExitClearance(
        user_id=user_id,
        resignation_date=date.today(),
        last_working_day=last_working_day,
        clearance_progress='1 / 7 Handover Initiated',
        status='Notice Period',
        notes=notes
    )
    db.session.add(ex)
    db.session.commit()
    log_audit('INIT_EXIT', 'ExitClearance', ex.id, f"Initiated exit clearance for user {user_id}")
    flash('Resignation & exit clearance registered.', 'success')
    return redirect(url_for('hr.exits_list'))

# --- INTERNAL HR SERVICE REQUESTS & CERTIFICATES ---

@hr_bp.route('/requests')
@login_required
@hr_required
def requests_list():
    requests = HRRequest.query.order_by(HRRequest.request_date.desc()).all()
    users = User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()
    return render_template('hr/requests.html', requests=requests, users=users)

@hr_bp.route('/requests/<int:id>/fulfill', methods=['POST'])
@login_required
@hr_required
def fulfill_request(id):
    req = HRRequest.query.get_or_404(id)
    req.status = 'Completed'
    req.processed_by_id = current_user.id
    db.session.commit()
    log_audit('FULFILL_REQUEST', 'HRRequest', req.id, f"Processed HR request {req.request_code}")
    flash(f"HR Request {req.request_code} fulfilled and marked as completed.", 'success')
    return redirect(request.referrer or url_for('hr.requests_list'))

@hr_bp.route('/requests/new', methods=['POST'])
@login_required
def create_hr_request():
    user_id = current_user.id
    if (current_user.is_management() or current_user.is_hr()) and request.form.get('user_id'):
        user_id = int(request.form.get('user_id'))

    request_type = request.form.get('request_type')
    details = request.form.get('details')

    count = HRRequest.query.count() + 1
    req_code = f"REQ-HR-{count:03d}"
    req = HRRequest(
        request_code=req_code,
        user_id=user_id,
        request_type=request_type,
        details=details,
        status='Pending'
    )
    db.session.add(req)
    db.session.commit()
    log_audit('CREATE_REQUEST', 'HRRequest', req.id, f"Created HR request {req_code}")
    flash(f"HR Request {req_code} submitted successfully.", 'success')
    return redirect(request.referrer or url_for('hr.requests_list'))

# --- PERFORMANCE REVIEWS & APPRAISALS ---

@hr_bp.route('/performance')
@login_required
@hr_required
def performance_list():
    reviews = PerformanceReview.query.order_by(PerformanceReview.id.desc()).all()
    users = User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()
    return render_template('hr/performance.html', reviews=reviews, users=users)

@hr_bp.route('/performance/new', methods=['POST'])
@login_required
@hr_required
def create_performance_review():
    user_id = request.form.get('user_id', type=int)
    quarter = request.form.get('quarter')
    rating = request.form.get('rating')
    feedback = request.form.get('feedback')

    if not user_id or not quarter or not rating:
        flash('Please fill in employee, quarter, and appraisal rating.', 'danger')
        return redirect(url_for('hr.performance_list'))

    review = PerformanceReview(
        user_id=user_id,
        reviewer_id=current_user.id,
        quarter=quarter,
        rating=rating,
        status='Completed',
        feedback=feedback
    )
    db.session.add(review)
    db.session.commit()
    log_audit('CREATE_REVIEW', 'PerformanceReview', review.id, f"Created review for user {user_id}")
    flash('Performance review recorded.', 'success')
    return redirect(url_for('hr.performance_list'))

# --- ATTENDANCE & CHECK-IN ---

@hr_bp.route('/attendance')
@login_required
def attendance():
    today = date.today()
    my_today_record = Attendance.query.filter_by(user_id=current_user.id, attendance_date=today).first()
    
    # Authorized department scoping:
    # 1. Management and HR: full company-wide visibility across all departments with department filter
    # 2. Department Managers (e.g. Sales Manager): visibility into their department team
    # 3. Regular employees: personal shift records & history
    selected_dept = request.args.get('department', 'All')
    is_authorized = current_user.is_management() or current_user.is_hr() or current_user.is_manager()
    
    team_records = []
    if current_user.is_management() or current_user.is_hr():
        team_q = Attendance.query.join(User).filter(Attendance.attendance_date == today)
        if selected_dept and selected_dept != 'All':
            team_q = team_q.filter(User.department == selected_dept)
        team_records = team_q.order_by(Attendance.check_in_time.desc()).all()
    elif current_user.is_manager():
        team_q = Attendance.query.join(User).filter(
            Attendance.attendance_date == today,
            User.department == current_user.department
        )
        team_records = team_q.order_by(Attendance.check_in_time.desc()).all()
        selected_dept = current_user.department

    departments = ['Sales', 'Field Operations', 'Finance', 'Human Resources', 'Marketing', 'Information Technology', 'Management']
    
    # Pre-calculate department breakdown for authorized users
    all_today_punches = Attendance.query.join(User).filter(Attendance.attendance_date == today).all() if is_authorized else []
    dept_counts = {}
    for p in all_today_punches:
        d = p.user.department if p.user else 'Other'
        dept_counts[d] = dept_counts.get(d, 0) + 1

    my_history = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.attendance_date.desc()).limit(30).all()
    leave_requests = LeaveRequest.query.filter_by(user_id=current_user.id).order_by(LeaveRequest.created_at.desc()).all()

    return render_template(
        'hr/attendance.html',
        today=today,
        my_today_record=my_today_record,
        team_records=team_records,
        my_history=my_history,
        leave_requests=leave_requests,
        is_authorized=is_authorized,
        selected_dept=selected_dept,
        departments=departments,
        dept_counts=dept_counts,
        all_today_punches=all_today_punches
    )

@hr_bp.route('/attendance/check-in', methods=['POST'])
@login_required
def check_in():
    today = date.today()
    now_time = datetime.now().time()
    work_mode = request.form.get('work_mode', 'Office')
    notes = request.form.get('notes', '').strip()
    
    # Extract GPS Geolocation
    lat_val = request.form.get('latitude')
    lng_val = request.form.get('longitude')
    loc_name = request.form.get('location_name', '').strip()
    device_info = request.form.get('device_info', '')
    if not device_info and request.user_agent:
        device_info = request.user_agent.string[:120]

    lat = None
    lng = None
    if lat_val and lng_val:
        try:
            lat = float(lat_val)
            lng = float(lng_val)
        except (ValueError, TypeError):
            lat, lng = None, None

    if not loc_name:
        if lat and lng:
            loc_name = f"Ahmedabad GPS ({lat:.4f}, {lng:.4f})"
        else:
            loc_name = f"{current_user.department} HQ / Office"

    record = Attendance.query.filter_by(user_id=current_user.id, attendance_date=today).first()
    if not record:
        record = Attendance(
            user_id=current_user.id,
            attendance_date=today,
            check_in_time=now_time,
            work_mode=work_mode,
            status='Present' if work_mode != 'Field' else 'Field Duty',
            notes=notes,
            latitude=lat,
            longitude=lng,
            check_in_location=loc_name,
            device_info=device_info,
            ip_address=request.remote_addr
        )
        db.session.add(record)
        
        # Also log to GPSTrackingLog so location tracking is unified and mapped
        if lat and lng:
            gps_log = GPSTrackingLog(
                user_id=current_user.id,
                latitude=lat,
                longitude=lng,
                location_name=loc_name,
                tracking_type=f"Check-In ({current_user.department or 'General'})",
                device_info=device_info,
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(gps_log)

        db.session.commit()
        log_audit('CHECK_IN', 'Attendance', record.id, f"Checked in ({work_mode}) at {now_time.strftime('%H:%M:%S')} - Location: {loc_name}")
        flash(f"Check-in successfully recorded at {loc_name} ({now_time.strftime('%I:%M %p')})!", 'success')
    else:
        flash('You have already checked in today.', 'info')

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'time': now_time.strftime('%I:%M %p'),
            'location': loc_name,
            'status': record.status
        })

    return redirect(request.referrer or url_for('hr.attendance'))

@hr_bp.route('/attendance/check-out', methods=['POST'])
@login_required
def check_out():
    today = date.today()
    now_time = datetime.now().time()
    
    lat_val = request.form.get('latitude')
    lng_val = request.form.get('longitude')
    loc_name = request.form.get('location_name', '').strip()

    lat = None
    lng = None
    if lat_val and lng_val:
        try:
            lat = float(lat_val)
            lng = float(lng_val)
        except (ValueError, TypeError):
            lat, lng = None, None

    if not loc_name:
        if lat and lng:
            loc_name = f"Ahmedabad GPS ({lat:.4f}, {lng:.4f})"
        else:
            loc_name = f"{current_user.department} HQ / Office"

    record = Attendance.query.filter_by(user_id=current_user.id, attendance_date=today).first()
    if record:
        record.check_out_time = now_time
        record.check_out_latitude = lat
        record.check_out_longitude = lng
        record.check_out_location = loc_name
        if record.check_in_time:
            td = datetime.combine(today, now_time) - datetime.combine(today, record.check_in_time)
            record.working_hours = Decimal(f"{td.total_seconds() / 3600:.2f}")
        
        # Also log to GPSTrackingLog
        if lat and lng:
            gps_log = GPSTrackingLog(
                user_id=current_user.id,
                latitude=lat,
                longitude=lng,
                location_name=loc_name,
                tracking_type=f"Check-Out ({current_user.department or 'General'})",
                device_info=request.user_agent.string[:120] if request.user_agent else 'Browser',
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(gps_log)

        db.session.commit()
        log_audit('CHECK_OUT', 'Attendance', record.id, f"Checked out at {now_time.strftime('%H:%M:%S')} - Location: {loc_name} ({record.working_hours} hrs)")
        flash(f"Check-out recorded at {loc_name} ({now_time.strftime('%I:%M %p')}, {record.working_hours} hrs). Have a great evening!", 'success')
    else:
        flash('No check-in record found for today.', 'warning')

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'time': now_time.strftime('%I:%M %p'),
            'location': loc_name,
            'working_hours': float(record.working_hours) if record and record.working_hours else 0.0
        })

    return redirect(request.referrer or url_for('hr.attendance'))

# --- TASKS MANAGEMENT ---

@hr_bp.route('/tasks')
@login_required
def tasks_list():
    status = request.args.get('status', 'Pending')
    query = Task.query
    if not current_user.is_management():
        query = query.filter_by(assigned_to_id=current_user.id)
    if status and status != 'All':
        query = query.filter_by(status=status)

    tasks = query.order_by(Task.due_date.asc()).all()
    return render_template('hr/tasks_list.html', tasks=tasks, status=status)

@hr_bp.route('/tasks/new', methods=['GET', 'POST'])
@login_required
def create_task():
    form = TaskForm()
    users = User.query.filter_by(is_active=True).all()
    form.assigned_to_id.choices = [(u.id, f"{u.full_name} ({u.role})") for u in users]
    form.lead_id.choices = [(0, '-- None --')]
    form.client_id.choices = [(0, '-- None --')]
    form.property_id.choices = [(0, '-- None --')]
    form.deal_id.choices = [(0, '-- None --')]

    if request.method == 'GET' and not current_user.is_management():
        form.assigned_to_id.data = current_user.id

    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            assigned_to_id=form.assigned_to_id.data,
            created_by_id=current_user.id,
            priority=form.priority.data,
            due_date=form.due_date.data,
            status=form.status.data,
            completion_notes=form.completion_notes.data
        )
        db.session.add(task)
        db.session.commit()
        log_audit('CREATE', 'Task', task.id, f"Created task {task.title}")
        flash('Task assigned successfully.', 'success')
        return redirect(url_for('hr.tasks_list'))

    return render_template('hr/task_form.html', form=form, title="Create New Task")

@hr_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_management() and task.assigned_to_id != current_user.id:
        abort(403)

    notes = request.form.get('notes', 'Completed')
    task.status = 'Completed'
    task.completion_notes = notes
    db.session.commit()
    log_audit('COMPLETE', 'Task', task.id, "Task marked as completed.")
    flash('Task completed.', 'success')
    return redirect(url_for('hr.tasks_list'))

# --- BDE / SALES TARGETS & KPI TRACKER ---

@hr_bp.route('/targets')
@login_required
def targets_list():
    if not current_user.can_access_crm():
        abort(403)
    query = EmployeeTarget.query
    if not current_user.is_management():
        query = query.filter_by(user_id=current_user.id)
    targets = query.order_by(EmployeeTarget.created_at.desc()).all()
    return render_template('hr/targets_list.html', targets=targets)

@hr_bp.route('/targets/new', methods=['GET', 'POST'])
@login_required
def create_target():
    if not current_user.is_management() and not current_user.is_hr():
        abort(403)

    form = TargetForm()
    users = User.query.filter_by(is_active=True).all()
    form.user_id.choices = [(u.id, f"{u.full_name} ({u.department} - {u.role})") for u in users]

    if form.validate_on_submit():
        target = EmployeeTarget(
            user_id=form.user_id.data,
            month_year=form.month_year.data,
            working_days=form.working_days.data,
            call_target=form.call_target.data,
            actual_calls=form.actual_calls.data or 0,
            lead_target=form.lead_target.data,
            actual_leads=form.actual_leads.data or 0,
            site_visit_target=form.site_visit_target.data,
            actual_site_visits=form.actual_site_visits.data or 0,
            revenue_target=form.revenue_target.data or 0,
            actual_revenue=form.actual_revenue.data or 0,
            notes=form.notes.data
        )
        db.session.add(target)
        db.session.commit()
        log_audit('CREATE_TARGET', 'EmployeeTarget', target.id, f"Allocated target for {target.month_year}")
        flash('Monthly targets allocated successfully.', 'success')
        return redirect(url_for('hr.targets_list'))

    return render_template('hr/target_form.html', form=form, title="Allocate Employee Target")

# --- RECRUITMENT / CANDIDATE TRACKER ---

@hr_bp.route('/recruitment')
@hr_bp.route('/recruitments')
@login_required
@hr_required
def recruitment_list():
    candidates = Recruitment.query.order_by(Recruitment.created_at.desc()).all()
    return render_template('hr/recruitment_list.html', candidates=candidates)

@hr_bp.route('/recruitment/new', methods=['GET', 'POST'])
@login_required
@hr_required
def create_recruitment():
    form = RecruitmentForm()
    managers = User.query.filter_by(is_active=True).all()
    form.hiring_manager_id.choices = [(0, '-- None --')] + [(m.id, f"{m.full_name} ({m.role})") for m in managers]

    if form.validate_on_submit():
        count = Recruitment.query.count() + 1
        rec_code = f"REC-{count:03d}"
        rec = Recruitment(
            recruitment_code=rec_code,
            candidate_name=form.candidate_name.data,
            position=form.position.data,
            department=form.department.data,
            phone=form.phone.data,
            email=form.email.data,
            source=form.source.data,
            stage=form.stage.data,
            interview_date=datetime.combine(form.interview_date.data, datetime.min.time()) if form.interview_date.data else None,
            hiring_manager_id=form.hiring_manager_id.data if form.hiring_manager_id.data != 0 else None,
            notes=form.notes.data
        )
        db.session.add(rec)
        db.session.commit()
        log_audit('CREATE_CANDIDATE', 'Recruitment', rec.id, f"Candidate {rec.candidate_name} added")
        flash(f"Candidate {rec.candidate_name} ({rec.recruitment_code}) registered.", 'success')
        return redirect(url_for('hr.recruitment_list'))

    return render_template('hr/recruitment_form.html', form=form, title="Register New Candidate")

# --- OFFICE ASSETS MANAGEMENT ---

@hr_bp.route('/assets')
@login_required
@hr_required
def assets_list():
    assets = Asset.query.order_by(Asset.created_at.desc()).all()
    return render_template('hr/assets_list.html', assets=assets)

@hr_bp.route('/assets/new', methods=['GET', 'POST'])
@login_required
@hr_required
def create_asset():
    form = AssetForm()
    users = User.query.filter_by(is_active=True).all()
    form.allocated_to_id.choices = [(0, '-- In Office / Storage --')] + [(u.id, f"{u.full_name} ({u.role})") for u in users]

    if form.validate_on_submit():
        asset = Asset(
            asset_code=form.asset_code.data,
            asset_name=form.asset_name.data,
            category=form.category.data,
            serial_number=form.serial_number.data,
            allocated_to_id=form.allocated_to_id.data if form.allocated_to_id.data != 0 else None,
            allocation_date=form.allocation_date.data,
            purchase_date=form.purchase_date.data,
            purchase_cost=form.purchase_cost.data or 0,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(asset)
        db.session.commit()
        log_audit('CREATE_ASSET', 'Asset', asset.id, f"Asset {asset.asset_code} registered")
        flash(f"Asset {asset.asset_name} ({asset.asset_code}) recorded.", 'success')
        return redirect(url_for('hr.assets_list'))

    return render_template('hr/asset_form.html', form=form, title="Register Office Asset")

# --- PAYROLL MANAGEMENT ---

@hr_bp.route('/payroll')
@hr_bp.route('/payrolls')
@login_required
def payroll_list():
    if not current_user.is_accounts() and not current_user.is_hr():
        abort(403)
    payrolls = Payroll.query.order_by(Payroll.created_at.desc()).all()
    return render_template('hr/payroll_list.html', payrolls=payrolls)
