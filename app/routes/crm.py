import csv
import io
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, abort
from flask_login import login_required, current_user
from app.models import Lead, Client, Activity, FollowUp, User, Roles
from app.forms import LeadForm, ClientForm
from app.services.matching_service import detect_duplicate_lead, create_in_app_notification
from app.services.auth_service import log_audit
from app.extensions import db

crm_bp = Blueprint('crm', __name__)

@crm_bp.before_request
def check_crm_access():
    if current_user.is_authenticated and not current_user.can_access_crm():
        abort(403)



# --- LEADS MANAGEMENT ---

@crm_bp.route('/leads')
@login_required
def leads_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    source = request.args.get('source', '').strip()
    category = request.args.get('category', '').strip()
    executive_id = request.args.get('executive_id', type=int)
    show_archived = request.args.get('archived', '0') == '1'

    query = Lead.query.filter(Lead.is_archived == show_archived)

    # Permission scoping
    if not current_user.is_management():
        query = query.filter(Lead.assigned_to_id == current_user.id)

    # Filters
    if search:
        query = query.filter(
            (Lead.full_name.ilike(f'%{search}%')) |
            (Lead.phone.ilike(f'%{search}%')) |
            (Lead.company_name.ilike(f'%{search}%')) |
            (Lead.lead_code.ilike(f'%{search}%'))
        )
    if status:
        query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.source == source)
    if category:
        query = query.filter(Lead.property_category == category)
    if executive_id and current_user.is_management():
        query = query.filter(Lead.assigned_to_id == executive_id)

    pagination = query.order_by(Lead.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    executives = User.query.filter_by(is_active=True).all() if current_user.is_management() else []

    return render_template(
        'crm/leads_list.html',
        pagination=pagination,
        search=search,
        status=status,
        source=source,
        category=category,
        executive_id=executive_id,
        show_archived=show_archived,
        executives=executives
    )

@crm_bp.route('/leads/new', methods=['GET', 'POST'])
@login_required
def lead_create():
    form = LeadForm()
    # Populate executives dropdown
    users = User.query.filter_by(is_active=True).all()
    form.assigned_to_id.choices = [(0, '-- Unassigned --')] + [(u.id, f"{u.full_name} ({u.role})") for u in users]
    
    # Default assign to creator if not management
    if request.method == 'GET' and not current_user.is_management():
        form.assigned_to_id.data = current_user.id

    if form.validate_on_submit():
        # Duplicate detection check
        is_dup, dup_msg = detect_duplicate_lead(form.phone.data, form.email.data)
        if is_dup:
            flash(f"Warning: {dup_msg}", 'warning')

        count = Lead.query.count() + 1
        lead_code = f"LEAD-AHM-{count:05d}"
        assigned_id = form.assigned_to_id.data if form.assigned_to_id.data != 0 else (current_user.id if not current_user.is_management() else None)

        lead = Lead(
            lead_code=lead_code,
            full_name=form.full_name.data,
            company_name=form.company_name.data,
            contact_person=form.contact_person.data if hasattr(form, 'contact_person') else None,
            client_type=form.client_type.data if hasattr(form, 'client_type') else 'Corporate',
            business_segment=form.business_segment.data if hasattr(form, 'business_segment') else None,
            temperature=form.temperature.data if hasattr(form, 'temperature') else 'Warm',
            phone=form.phone.data,
            whatsapp_number=form.whatsapp_number.data if hasattr(form, 'whatsapp_number') else None,
            email=form.email.data,
            source=form.source.data,
            property_category=form.property_category.data,
            transaction_type=form.transaction_type.data,
            preferred_locations=form.preferred_locations.data,
            alternative_locations=form.alternative_locations.data if hasattr(form, 'alternative_locations') else None,
            budget_min=form.budget_min.data or 0,
            budget_max=form.budget_max.data or 0,
            area_min_sqft=form.area_min_sqft.data or 0,
            area_max_sqft=form.area_max_sqft.data or 0,
            assigned_to_id=assigned_id,
            priority=form.priority.data,
            status=form.status.data,
            lost_reason=form.lost_reason.data,
            notes=form.notes.data
        )
        db.session.add(lead)
        db.session.commit()

        # Audit & Activity log
        log_audit('CREATE', 'Lead', lead.id, f"Created lead {lead.lead_code} - {lead.full_name}")
        act = Activity(lead_id=lead.id, user_id=current_user.id, activity_type='Note', summary='Lead Created', details=f"Lead registered from source: {lead.source}")
        db.session.add(act)

        # Notify assigned user if different from creator
        if assigned_id and assigned_id != current_user.id:
            create_in_app_notification(
                user_id=assigned_id,
                title="New Lead Assigned",
                message=f"You have been assigned lead: {lead.full_name} ({lead.lead_code})",
                link=url_for('crm.lead_detail', lead_id=lead.id),
                category="Lead"
            )

        db.session.commit()
        flash(f"Lead {lead.lead_code} created successfully!", 'success')
        return redirect(url_for('crm.lead_detail', lead_id=lead.id))

    return render_template('crm/lead_form.html', form=form, title="Create New Lead")

@crm_bp.route('/leads/<int:lead_id>')
@login_required
def lead_detail(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if not current_user.is_management() and lead.assigned_to_id != current_user.id:
        abort(403)

    activities = lead.activities.order_by(Activity.created_at.desc()).all()
    followups = lead.followups.order_by(FollowUp.scheduled_at.desc()).all()
    return render_template('crm/lead_detail.html', lead=lead, activities=activities, followups=followups)

@crm_bp.route('/leads/<int:lead_id>/edit', methods=['GET', 'POST'])
@login_required
def lead_edit(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if not current_user.is_management() and lead.assigned_to_id != current_user.id:
        abort(403)

    form = LeadForm(obj=lead)
    users = User.query.filter_by(is_active=True).all()
    form.assigned_to_id.choices = [(0, '-- Unassigned --')] + [(u.id, f"{u.full_name} ({u.role})") for u in users]

    if form.validate_on_submit():
        # Check duplicate
        is_dup, dup_msg = detect_duplicate_lead(form.phone.data, form.email.data, exclude_id=lead.id)
        if is_dup:
            flash(f"Warning: {dup_msg}", 'warning')

        old_status = lead.status
        old_assignee = lead.assigned_to_id

        lead.full_name = form.full_name.data
        lead.company_name = form.company_name.data
        if hasattr(form, 'contact_person'):
            lead.contact_person = form.contact_person.data
        if hasattr(form, 'client_type'):
            lead.client_type = form.client_type.data
        if hasattr(form, 'business_segment'):
            lead.business_segment = form.business_segment.data
        if hasattr(form, 'temperature'):
            lead.temperature = form.temperature.data
        lead.phone = form.phone.data
        if hasattr(form, 'whatsapp_number'):
            lead.whatsapp_number = form.whatsapp_number.data
        lead.email = form.email.data
        lead.source = form.source.data
        lead.property_category = form.property_category.data
        lead.transaction_type = form.transaction_type.data
        lead.preferred_locations = form.preferred_locations.data
        if hasattr(form, 'alternative_locations'):
            lead.alternative_locations = form.alternative_locations.data
        lead.budget_min = form.budget_min.data or 0
        lead.budget_max = form.budget_max.data or 0
        lead.area_min_sqft = form.area_min_sqft.data or 0
        lead.area_max_sqft = form.area_max_sqft.data or 0
        lead.priority = form.priority.data
        lead.status = form.status.data
        lead.lost_reason = form.lost_reason.data
        lead.notes = form.notes.data

        if current_user.is_management():
            lead.assigned_to_id = form.assigned_to_id.data if form.assigned_to_id.data != 0 else None

        # Log status change activity
        if old_status != lead.status:
            act = Activity(lead_id=lead.id, user_id=current_user.id, activity_type='Status Change', summary=f"Status changed: {old_status} -> {lead.status}", details=lead.lost_reason or '')
            db.session.add(act)

        # Log assignment change
        if old_assignee != lead.assigned_to_id and lead.assigned_to_id:
            create_in_app_notification(
                user_id=lead.assigned_to_id,
                title="Lead Reassigned to You",
                message=f"Lead {lead.full_name} ({lead.lead_code}) has been reassigned to you.",
                link=url_for('crm.lead_detail', lead_id=lead.id),
                category="Lead"
            )

        log_audit('UPDATE', 'Lead', lead.id, f"Updated lead {lead.lead_code}")
        db.session.commit()
        flash('Lead updated successfully!', 'success')
        return redirect(url_for('crm.lead_detail', lead_id=lead.id))

    return render_template('crm/lead_form.html', form=form, title=f"Edit Lead {lead.lead_code}", lead=lead)

@crm_bp.route('/leads/<int:lead_id>/archive', methods=['POST'])
@login_required
def lead_archive(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if not current_user.is_management() and lead.assigned_to_id != current_user.id:
        abort(403)
    lead.is_archived = True
    log_audit('ARCHIVE', 'Lead', lead.id, f"Archived lead {lead.lead_code}")
    db.session.commit()
    flash(f"Lead {lead.lead_code} archived.", 'info')
    return redirect(url_for('crm.leads_list'))

@crm_bp.route('/leads/<int:lead_id>/restore', methods=['POST'])
@login_required
def lead_restore(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if not current_user.is_management() and lead.assigned_to_id != current_user.id:
        abort(403)
    lead.is_archived = False
    log_audit('RESTORE', 'Lead', lead.id, f"Restored lead {lead.lead_code}")
    db.session.commit()
    flash(f"Lead {lead.lead_code} restored.", 'success')
    return redirect(url_for('crm.lead_detail', lead_id=lead.id))

@crm_bp.route('/leads/<int:lead_id>/convert', methods=['POST'])
@login_required
def lead_convert_to_client(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if not current_user.is_management() and lead.assigned_to_id != current_user.id:
        abort(403)
        
    # Check if client already exists
    count = Client.query.count() + 1
    client_code = f"CLI-AHM-{count:05d}"
    
    client = Client(
        client_code=client_code,
        name=lead.full_name,
        client_type='Corporate' if lead.company_name else 'Individual',
        company_name=lead.company_name,
        phone=lead.phone,
        email=lead.email,
        preferred_locations=lead.preferred_locations,
        budget_range=f"₹ {lead.budget_min} - ₹ {lead.budget_max}",
        assigned_rm_id=lead.assigned_to_id or current_user.id,
        notes=f"Converted from Lead {lead.lead_code}. Original Notes: {lead.notes or ''}"
    )
    db.session.add(client)
    lead.status = 'Won'
    
    act = Activity(lead_id=lead.id, user_id=current_user.id, activity_type='Conversion', summary=f"Lead converted to Client {client.client_code}")
    db.session.add(act)
    
    log_audit('CONVERT', 'Lead', lead.id, f"Converted lead {lead.lead_code} to client {client.client_code}")
    db.session.commit()
    flash(f"Lead successfully converted to Client {client.client_code}!", 'success')
    return redirect(url_for('crm.client_detail', client_id=client.id))

@crm_bp.route('/leads/<int:lead_id>/add-activity', methods=['POST'])
@login_required
def lead_add_activity(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    act_type = request.form.get('activity_type', 'Note')
    summary = request.form.get('summary', '').strip()
    details = request.form.get('details', '').strip()
    
    if summary:
        act = Activity(lead_id=lead.id, user_id=current_user.id, activity_type=act_type, summary=summary, details=details)
        db.session.add(act)
        db.session.commit()
        flash('Activity logged.', 'success')
    return redirect(url_for('crm.lead_detail', lead_id=lead.id))

@crm_bp.route('/leads/<int:lead_id>/schedule-followup', methods=['POST'])
@login_required
def lead_schedule_followup(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    scheduled_str = request.form.get('scheduled_at')
    f_type = request.form.get('type', 'Call')
    notes = request.form.get('notes', '').strip()
    
    if scheduled_str:
        try:
            dt = datetime.fromisoformat(scheduled_str)
            fu = FollowUp(lead_id=lead.id, user_id=current_user.id, scheduled_at=dt, type=f_type, notes=notes)
            lead.next_follow_up = dt
            db.session.add(fu)
            db.session.commit()
            flash('Follow-up scheduled.', 'success')
        except Exception as e:
            flash(f"Invalid date format: {e}", 'danger')
            
    return redirect(url_for('crm.lead_detail', lead_id=lead.id))

# --- CLIENTS MANAGEMENT ---

@crm_bp.route('/clients')
@login_required
def clients_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    c_type = request.args.get('type', '').strip()

    query = Client.query.filter_by(is_archived=False)
    if search:
        query = query.filter(
            (Client.name.ilike(f'%{search}%')) |
            (Client.phone.ilike(f'%{search}%')) |
            (Client.company_name.ilike(f'%{search}%')) |
            (Client.client_code.ilike(f'%{search}%'))
        )
    if c_type:
        query = query.filter_by(client_type=c_type)

    pagination = query.order_by(Client.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('crm/clients_list.html', pagination=pagination, search=search, c_type=c_type)

@crm_bp.route('/clients/new', methods=['GET', 'POST'])
@login_required
def client_create():
    form = ClientForm()
    users = User.query.filter_by(is_active=True).all()
    form.assigned_rm_id.choices = [(0, '-- Select RM --')] + [(u.id, f"{u.full_name} ({u.role})") for u in users]

    if form.validate_on_submit():
        count = Client.query.count() + 1
        client_code = f"CLI-AHM-{count:05d}"
        rm_id = form.assigned_rm_id.data if form.assigned_rm_id.data != 0 else current_user.id

        client = Client(
            client_code=client_code,
            name=form.name.data,
            client_type=form.client_type.data,
            company_name=form.company_name.data,
            gst_number=form.gst_number.data,
            pan_number=form.pan_number.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            city=form.city.data,
            preferred_locations=form.preferred_locations.data,
            budget_range=form.budget_range.data,
            assigned_rm_id=rm_id,
            notes=form.notes.data
        )
        db.session.add(client)
        db.session.commit()
        log_audit('CREATE', 'Client', client.id, f"Created client {client.client_code} - {client.name}")
        flash(f"Client {client.client_code} registered successfully!", 'success')
        return redirect(url_for('crm.client_detail', client_id=client.id))

    return render_template('crm/client_form.html', form=form, title="Register New Client")

@crm_bp.route('/clients/<int:client_id>')
@login_required
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('crm/client_detail.html', client=client)

@crm_bp.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def client_edit(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client)
    users = User.query.filter_by(is_active=True).all()
    form.assigned_rm_id.choices = [(0, '-- Select RM --')] + [(u.id, f"{u.full_name} ({u.role})") for u in users]

    if form.validate_on_submit():
        client.name = form.name.data
        client.client_type = form.client_type.data
        client.company_name = form.company_name.data
        client.gst_number = form.gst_number.data
        client.pan_number = form.pan_number.data
        client.phone = form.phone.data
        client.email = form.email.data
        client.address = form.address.data
        client.city = form.city.data
        client.preferred_locations = form.preferred_locations.data
        client.budget_range = form.budget_range.data
        client.assigned_rm_id = form.assigned_rm_id.data if form.assigned_rm_id.data != 0 else client.assigned_rm_id
        client.notes = form.notes.data

        log_audit('UPDATE', 'Client', client.id, f"Updated client {client.client_code}")
        db.session.commit()
        flash('Client details updated.', 'success')
        return redirect(url_for('crm.client_detail', client_id=client.id))

    return render_template('crm/client_form.html', form=form, title=f"Edit Client {client.client_code}", client=client)

# --- CSV EXPORT ---
@crm_bp.route('/leads/export-csv')
@login_required
def export_leads_csv():
    query = Lead.query.filter_by(is_archived=False)
    if not current_user.is_management():
        query = query.filter_by(assigned_to_id=current_user.id)

    leads = query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Lead Code', 'Full Name', 'Company', 'Phone', 'Email', 'Source', 'Category', 'Requirement', 'Status', 'Created Date'])

    for l in leads:
        writer.writerow([
            l.lead_code, l.full_name, l.company_name or '', l.phone, l.email or '',
            l.source, l.property_category, l.transaction_type, l.status, l.created_at.strftime('%Y-%m-%d')
        ])

    log_audit('EXPORT', 'Lead', None, f"Exported {len(leads)} leads to CSV")
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=arch_realty_leads.csv"}
    )
