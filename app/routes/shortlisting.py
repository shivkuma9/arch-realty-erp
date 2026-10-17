from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import ClientPropertyShortlist, Client, Property, Requirement, User, Roles, Notification
from app.services.auth_service import log_audit
from app.extensions import db

shortlisting_bp = Blueprint('shortlisting', __name__)

STAGES = [
    'Yet to Show',
    'Proposed',
    'Shortlisted',
    'Meeting Scheduled',
    'Finalized',
    'Dropped'
]

@shortlisting_bp.route('/')
@login_required
def index():
    client_id = request.args.get('client_id')
    property_id = request.args.get('property_id')
    stage_filter = request.args.get('stage', '').strip()

    query = ClientPropertyShortlist.query
    if client_id and client_id.isdigit():
        query = query.filter_by(client_id=int(client_id))
    if property_id and property_id.isdigit():
        query = query.filter_by(property_id=int(property_id))
    if stage_filter:
        query = query.filter_by(stage=stage_filter)

    shortlists = query.order_by(ClientPropertyShortlist.updated_at.desc()).all()

    # Group into stages for Kanban board
    board_data = {stage: [] for stage in STAGES}
    for item in shortlists:
        if item.stage in board_data:
            board_data[item.stage].append(item)
        else:
            board_data['Yet to Show'].append(item)

    clients = Client.query.filter_by(is_archived=False).all()
    properties = Property.query.filter_by(is_archived=False, availability_status='Available').all()

    return render_template(
        'shortlisting/index.html',
        shortlists=shortlists,
        board_data=board_data,
        stage_buckets=board_data,
        stages=STAGES,
        clients=clients,
        properties=properties,
        client_filter=client_id,
        stage_filter=stage_filter
    )

@shortlisting_bp.route('/add', methods=['POST'])
@shortlisting_bp.route('/create', endpoint='create_shortlist', methods=['POST'])
@login_required
def add():
    client_id = int(request.form.get('client_id'))
    property_id = int(request.form.get('property_id'))
    stage = request.form.get('stage', 'Yet to Show')
    notes = request.form.get('notes', '').strip()

    # Check if already exists
    existing = ClientPropertyShortlist.query.filter_by(client_id=client_id, property_id=property_id).first()
    if existing:
        existing.stage = stage
        if notes:
            existing.notes = notes
        existing.updated_by_id = current_user.id
        db.session.commit()
        flash('Shortlist item updated!', 'info')
    else:
        item = ClientPropertyShortlist(
            client_id=client_id,
            property_id=property_id,
            stage=stage,
            notes=notes,
            updated_by_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        log_audit('CREATE', 'ClientPropertyShortlist', item.id, f"Added property {property_id} to client {client_id} shortlist in stage {stage}")
        flash('Property added to client shortlist successfully!', 'success')

    return redirect(url_for('shortlisting.index', client_id=client_id))

@shortlisting_bp.route('/<int:item_id>/stage', methods=['POST'])
@login_required
def update_stage(item_id):
    item = ClientPropertyShortlist.query.get_or_404(item_id)
    new_stage = request.form.get('stage')
    if new_stage in STAGES:
        old_stage = item.stage
        item.stage = new_stage
        item.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'ClientPropertyShortlist', item.id, f"Moved stage from {old_stage} to {new_stage}")
        flash(f"Updated status to '{new_stage}'.", 'success')
    return redirect(url_for('shortlisting.index', client_id=item.client_id))

@shortlisting_bp.route('/<int:item_id>/remove', methods=['POST'])
@login_required
def remove(item_id):
    item = ClientPropertyShortlist.query.get_or_404(item_id)
    client_id = item.client_id
    db.session.delete(item)
    db.session.commit()
    flash('Property removed from client shortlist.', 'info')
    return redirect(url_for('shortlisting.index', client_id=client_id))
