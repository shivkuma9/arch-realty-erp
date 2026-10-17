from datetime import date, datetime, timezone
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import SourcingAssignment, SourcingSubmission, Property, Lead, Client, User, Roles, Notification
from app.services.auth_service import role_required, log_audit
from app.extensions import db

sourcing_bp = Blueprint('sourcing', __name__)

@sourcing_bp.route('/')
@login_required
def index():
    # If admin/manager, show all sourcing assignments. If employee, show their assigned ones.
    if current_user.is_management():
        assignments = SourcingAssignment.query.order_by(SourcingAssignment.created_at.desc()).all()
        submissions = SourcingSubmission.query.order_by(SourcingSubmission.created_at.desc()).limit(10).all()
    else:
        assignments = SourcingAssignment.query.filter_by(assigned_to_id=current_user.id).order_by(SourcingAssignment.created_at.desc()).all()
        submissions = SourcingSubmission.query.filter_by(employee_id=current_user.id).order_by(SourcingSubmission.created_at.desc()).limit(10).all()

    total_assignments = len(assignments)
    active_assignments = sum(1 for a in assignments if a.status in ['Assigned', 'In Progress'])
    lead_wise_count = sum(1 for a in assignments if a.sourcing_type == 'Lead-Wise')
    targeted_count = sum(1 for a in assignments if a.sourcing_type == 'Targeted Wise Sourcing')
    completed_count = sum(1 for a in assignments if a.status == 'Completed')

    return render_template(
        'sourcing/index.html',
        assignments=assignments,
        submissions=submissions,
        total_assignments=total_assignments,
        active_assignments=active_assignments,
        active_count=active_assignments,
        submissions_count=len(submissions),
        lead_wise_count=lead_wise_count,
        targeted_count=targeted_count,
        completed_count=completed_count
    )

@sourcing_bp.route('/assign', methods=['GET', 'POST'])
@sourcing_bp.route('/assign-task', endpoint='assign_sourcing', methods=['GET', 'POST'])
@login_required
@role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER)
def assign():
    users = User.query.filter_by(is_active=True).all()
    leads = Lead.query.filter_by(is_archived=False).all()
    clients = Client.query.filter_by(is_archived=False).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        sourcing_type = request.form.get('sourcing_type', 'Lead-Wise')
        lead_id = request.form.get('lead_id')
        client_id = request.form.get('client_id')
        assigned_to_id = int(request.form.get('assigned_to_id'))
        locality = request.form.get('locality', '').strip()
        category = request.form.get('category', 'Commercial')
        min_area_sqft = Decimal(request.form.get('min_area_sqft', '0') or '0')
        max_area_sqft = Decimal(request.form.get('max_area_sqft', '0') or '0')
        target_budget = Decimal(request.form.get('target_budget', '0') or '0')
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'Medium')
        instructions = request.form.get('instructions', '').strip()

        if not title or not locality or not assigned_to_id:
            flash('Title, locality, and assigned employee are required.', 'danger')
            return render_template('sourcing/assign.html', users=users, leads=leads, clients=clients)

        count = SourcingAssignment.query.count() + 1
        sourcing_code = f"SRC-{datetime.now().year}-{count:03d}"
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

        assignment = SourcingAssignment(
            sourcing_code=sourcing_code,
            title=title,
            sourcing_type=sourcing_type,
            lead_id=int(lead_id) if lead_id and lead_id.isdigit() else None,
            client_id=int(client_id) if client_id and client_id.isdigit() else None,
            assigned_to_id=assigned_to_id,
            assigned_by_id=current_user.id,
            locality=locality,
            category=category,
            min_area_sqft=min_area_sqft,
            max_area_sqft=max_area_sqft,
            target_budget=target_budget,
            due_date=due_date,
            priority=priority,
            instructions=instructions,
            status='Assigned'
        )
        db.session.add(assignment)
        db.session.flush()

        # Send Sourcing Alert notification
        notif = Notification(
            user_id=assigned_to_id,
            title="New Sourcing Assignment",
            message=f"You have been assigned to source: {title} in {locality}.",
            link=url_for('sourcing.detail', assignment_id=assignment.id),
            category='Sourcing Alerts'
        )
        db.session.add(notif)
        db.session.commit()

        log_audit('CREATE', 'SourcingAssignment', assignment.id, f"Assigned sourcing task {assignment.sourcing_code} to user {assigned_to_id}")
        flash(f'Sourcing assignment {assignment.sourcing_code} created successfully!', 'success')
        return redirect(url_for('sourcing.index'))

    return render_template('sourcing/assign.html', users=users, leads=leads, clients=clients)

@sourcing_bp.route('/<int:assignment_id>')
@login_required
def detail(assignment_id):
    assignment = SourcingAssignment.query.get_or_404(assignment_id)
    # Check permission
    if not current_user.is_management() and assignment.assigned_to_id != current_user.id:
        abort(403)

    return render_template('sourcing/detail.html', assignment=assignment)

@sourcing_bp.route('/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_property(assignment_id):
    assignment = SourcingAssignment.query.get_or_404(assignment_id)
    if not current_user.is_management() and assignment.assigned_to_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        property_title = request.form.get('property_title', '').strip()
        locality = request.form.get('locality', assignment.locality).strip()
        category = request.form.get('category', assignment.category)
        expected_price_or_rent = Decimal(request.form.get('expected_price_or_rent', '0') or '0')
        carpet_area = Decimal(request.form.get('carpet_area', '0') or '0')
        owner_contact = request.form.get('owner_contact', '').strip()
        admin_feedback = request.form.get('admin_feedback', '').strip()

        if not property_title:
            flash('Property Title is required.', 'danger')
            return render_template('sourcing/submit_property.html', assignment=assignment)

        submission = SourcingSubmission(
            sourcing_assignment_id=assignment.id,
            employee_id=current_user.id,
            property_title=property_title,
            locality=locality,
            category=category,
            expected_price_or_rent=expected_price_or_rent,
            carpet_area=carpet_area,
            owner_contact=owner_contact,
            admin_feedback=admin_feedback,
            status='Submitted'
        )
        assignment.status = 'Submitted'
        db.session.add(submission)
        db.session.commit()

        log_audit('CREATE', 'SourcingSubmission', submission.id, f"Submitted sourced property for {assignment.sourcing_code}")
        flash('Sourced property submitted for verification!', 'success')
        return redirect(url_for('sourcing.detail', assignment_id=assignment.id))

    return render_template('sourcing/submit_property.html', assignment=assignment)

@sourcing_bp.route('/<int:assignment_id>/status', methods=['POST'])
@login_required
def update_status(assignment_id):
    assignment = SourcingAssignment.query.get_or_404(assignment_id)
    new_status = request.form.get('status', assignment.status)
    assignment.status = new_status
    db.session.commit()
    flash(f"Sourcing task status updated to '{new_status}'.", 'success')
    return redirect(url_for('sourcing.detail', assignment_id=assignment.id))

@sourcing_bp.route('/my-sourcing')
@login_required
def my_sourcing():
    assignments = SourcingAssignment.query.filter_by(assigned_to_id=current_user.id).order_by(SourcingAssignment.created_at.desc()).all()
    submissions = SourcingSubmission.query.filter_by(employee_id=current_user.id).order_by(SourcingSubmission.created_at.desc()).all()
    return render_template('sourcing/my_sourcing.html', assignments=assignments, submissions=submissions)
