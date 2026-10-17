from datetime import datetime, date, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import SiteVisit, Property, Client, Lead, User, Roles
from app.forms import SiteVisitForm
from app.services.auth_service import log_audit
from app.extensions import db

field_bp = Blueprint('field', __name__)

@field_bp.before_request
def check_field_access():
    if current_user.is_authenticated and not current_user.can_access_field():
        abort(403)



@field_bp.route('/visits')
@login_required
def visits_list():
    date_filter = request.args.get('date')
    status_filter = request.args.get('status')
    
    query = SiteVisit.query
    if not current_user.is_management():
        query = query.filter_by(assigned_employee_id=current_user.id)

    if date_filter:
        try:
            d = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(visit_date=d)
        except Exception:
            pass

    if status_filter:
        query = query.filter_by(status=status_filter)

    visits = query.order_by(SiteVisit.visit_date.desc(), SiteVisit.visit_time.asc()).all()
    return render_template('field/visits_list.html', visits=visits, date_filter=date_filter, status_filter=status_filter)

@field_bp.route('/visits/new', methods=['GET', 'POST'])
@login_required
def schedule_visit():
    form = SiteVisitForm()
    props = Property.query.filter_by(is_archived=False).all()
    clients = Client.query.filter_by(is_archived=False).all()
    leads = Lead.query.filter_by(is_archived=False).all()
    users = User.query.filter_by(is_active=True).all()

    form.property_id.choices = [(p.id, f"{p.property_code} - {p.title} ({p.locality})") for p in props]
    form.client_id.choices = [(0, '-- None / Unlinked --')] + [(c.id, f"{c.client_code} - {c.name}") for c in clients]
    form.lead_id.choices = [(0, '-- None / Unlinked --')] + [(l.id, f"{l.lead_code} - {l.full_name}") for l in leads]
    form.assigned_employee_id.choices = [(u.id, f"{u.full_name} ({u.role})") for u in users]

    if request.method == 'GET' and not current_user.is_management():
        form.assigned_employee_id.data = current_user.id

    if form.validate_on_submit():
        count = SiteVisit.query.count() + 1
        visit_code = f"VIS-AHM-{count:05d}"

        # Conflict detection: check if executive has another visit at exact same date & time
        conflict = SiteVisit.query.filter(
            SiteVisit.assigned_employee_id == form.assigned_employee_id.data,
            SiteVisit.visit_date == form.visit_date.data,
            SiteVisit.visit_time == form.visit_time.data,
            SiteVisit.status.in_(['Scheduled', 'Confirmed'])
        ).first()

        if conflict:
            flash(f"Warning: Field Executive already has a scheduled visit ({conflict.visit_code}) at this time!", 'warning')

        visit = SiteVisit(
            visit_code=visit_code,
            property_id=form.property_id.data,
            client_id=form.client_id.data if form.client_id.data != 0 else None,
            lead_id=form.lead_id.data if form.lead_id.data != 0 else None,
            assigned_employee_id=form.assigned_employee_id.data,
            visit_date=form.visit_date.data,
            visit_time=form.visit_time.data,
            status=form.status.data,
            client_feedback=form.client_feedback.data,
            executive_notes=form.executive_notes.data
        )
        db.session.add(visit)
        db.session.commit()
        log_audit('CREATE', 'SiteVisit', visit.id, f"Scheduled visit {visit.visit_code}")
        flash(f"Site visit {visit.visit_code} scheduled successfully!", 'success')
        return redirect(url_for('field.visits_list'))

    return render_template('field/visit_form.html', form=form, title="Schedule Site Visit")

@field_bp.route('/visits/<int:visit_id>/check-in', methods=['POST'])
@login_required
def check_in(visit_id):
    visit = SiteVisit.query.get_or_404(visit_id)
    if not current_user.is_management() and visit.assigned_employee_id != current_user.id:
        abort(403)

    loc = request.form.get('location', 'Ahmedabad On-Site')
    visit.check_in_time = datetime.now(timezone.utc)
    visit.check_in_location = loc
    visit.status = 'Completed'
    db.session.commit()
    log_audit('CHECK_IN', 'SiteVisit', visit.id, f"Checked in at {loc}")
    flash('Checked in successfully for site visit.', 'success')
    return redirect(url_for('field.visits_list'))

@field_bp.route('/visits/<int:visit_id>/feedback', methods=['POST'])
@login_required
def update_feedback(visit_id):
    visit = SiteVisit.query.get_or_404(visit_id)
    if not current_user.is_management() and visit.assigned_employee_id != current_user.id:
        abort(403)

    feedback = request.form.get('client_feedback')
    notes = request.form.get('executive_notes')
    status = request.form.get('status')

    if feedback:
        visit.client_feedback = feedback
    if notes:
        visit.executive_notes = notes
    if status:
        visit.status = status

    db.session.commit()
    flash('Visit feedback and outcome saved.', 'success')
    return redirect(url_for('field.visits_list'))

@field_bp.route('/calendar')
@login_required
def calendar_view():
    # Fetch visits for the calendar
    query = SiteVisit.query
    if not current_user.is_management():
        query = query.filter_by(assigned_employee_id=current_user.id)
    visits = query.order_by(SiteVisit.visit_date.asc(), SiteVisit.visit_time.asc()).all()

    # Group by date for easy template rendering
    calendar_events = {}
    for v in visits:
        d_str = v.visit_date.strftime('%Y-%m-%d') if v.visit_date else 'Unscheduled'
        if d_str not in calendar_events:
            calendar_events[d_str] = []
        calendar_events[d_str].append(v)

    return render_template('field/calendar.html', visits=visits, calendar_events=calendar_events)

