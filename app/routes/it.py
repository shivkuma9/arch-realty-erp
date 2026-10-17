from datetime import date, datetime, timezone
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import ITTicket, ITServiceHealth, Asset, User, Roles
from app.services.auth_service import it_required, log_audit
from app.extensions import db

it_bp = Blueprint('it', __name__)

@it_bp.before_request
def check_it_access():
    if current_user.is_authenticated and not current_user.can_access_it():
        abort(403)

@it_bp.route('/')
@login_required
@it_required
def index():
    # Tickets summary
    tickets = ITTicket.query.order_by(ITTicket.created_at.desc()).all()
    open_tickets = sum(1 for t in tickets if t.status in ['Open', 'In Progress'])
    critical_tickets = sum(1 for t in tickets if t.priority == 'Critical' and t.status in ['Open', 'In Progress'])
    resolved_tickets = sum(1 for t in tickets if t.status in ['Resolved', 'Closed'])

    # IT Assets summary
    assets = Asset.query.all()
    total_assets = len(assets)
    allocated_assets = sum(1 for a in assets if a.status == 'Allocated')
    available_assets = sum(1 for a in assets if a.status == 'Available')

    # Service health
    services = ITServiceHealth.query.all()
    all_healthy = all(s.status == 'Operational' for s in services) if services else True

    return render_template(
        'it/index.html',
        tickets=tickets[:8],
        open_tickets=open_tickets,
        critical_tickets=critical_tickets,
        resolved_tickets=resolved_tickets,
        total_assets=total_assets,
        allocated_assets=allocated_assets,
        available_assets=available_assets,
        services=services,
        all_healthy=all_healthy
    )

@it_bp.route('/assets')
@login_required
@it_required
def assets_list():
    category_filter = request.args.get('category', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Asset.query
    if category_filter:
        query = query.filter_by(category=category_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)

    assets = query.order_by(Asset.created_at.desc()).all()
    users = User.query.filter_by(is_active=True).all()
    return render_template('it/assets_list.html', assets=assets, users=users, category_filter=category_filter, status_filter=status_filter)

@it_bp.route('/assets/create', methods=['GET', 'POST'])
@login_required
@it_required
def create_asset():
    users = User.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        asset_name = request.form.get('asset_name', '').strip()
        category = request.form.get('category', 'Field Survey (Laser Disto Meter)').strip()
        serial_number = request.form.get('serial_number', '').strip()
        allocated_to_id = request.form.get('allocated_to_id')
        purchase_cost = Decimal(request.form.get('purchase_cost', '0') or '0')
        notes = request.form.get('notes', '').strip()

        if not asset_name:
            flash('Asset Name is required.', 'danger')
            return render_template('it/asset_form.html', users=users)

        count = Asset.query.count() + 1
        asset_code = f"AST-IT-{count:03d}"

        allocated_user_id = int(allocated_to_id) if allocated_to_id and allocated_to_id.isdigit() else None
        status = 'Allocated' if allocated_user_id else 'Available'

        asset = Asset(
            asset_code=asset_code,
            asset_name=asset_name,
            category=category,
            serial_number=serial_number,
            allocated_to_id=allocated_user_id,
            allocation_date=date.today() if allocated_user_id else None,
            purchase_date=date.today(),
            purchase_cost=purchase_cost,
            status=status,
            notes=notes
        )
        db.session.add(asset)
        db.session.commit()

        log_audit('CREATE', 'Asset', asset.id, f"Registered IT asset {asset.asset_code} ({asset.asset_name})")
        flash(f'Asset {asset.asset_code} registered successfully!', 'success')
        return redirect(url_for('it.assets_list'))

    return render_template('it/asset_form.html', users=users)

@it_bp.route('/tickets')
@login_required
@it_required
def tickets_list():
    status_filter = request.args.get('status', '').strip()
    priority_filter = request.args.get('priority', '').strip()

    query = ITTicket.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)

    tickets = query.order_by(ITTicket.created_at.desc()).all()
    return render_template('it/tickets_list.html', tickets=tickets, status_filter=status_filter, priority_filter=priority_filter)

@it_bp.route('/tickets/create', methods=['GET', 'POST'])
@login_required
@it_required
def create_ticket():
    users = User.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Portal Lead Sync').strip()
        priority = request.form.get('priority', 'Medium').strip()
        requested_by_id = int(request.form.get('requested_by_id') or current_user.id)
        description = request.form.get('description', '').strip()

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return render_template('it/ticket_form.html', users=users)

        count = ITTicket.query.count() + 1
        ticket_number = f"TKT-{datetime.now().year}-{count:03d}"

        ticket = ITTicket(
            ticket_number=ticket_number,
            title=title,
            category=category,
            priority=priority,
            status='Open',
            requested_by_id=requested_by_id,
            assigned_to_id=current_user.id,
            description=description
        )
        db.session.add(ticket)
        db.session.commit()

        log_audit('CREATE', 'ITTicket', ticket.id, f"Logged IT ticket {ticket.ticket_number}")
        flash(f'Ticket {ticket.ticket_number} created successfully!', 'success')
        return redirect(url_for('it.tickets_list'))

    return render_template('it/ticket_form.html', users=users)

@it_bp.route('/tickets/<int:ticket_id>/update', methods=['POST'])
@login_required
@it_required
def update_ticket(ticket_id):
    ticket = ITTicket.query.get_or_404(ticket_id)
    new_status = request.form.get('status', ticket.status).strip()
    resolution_notes = request.form.get('resolution_notes', '').strip()

    ticket.status = new_status
    if resolution_notes:
        ticket.resolution_notes = resolution_notes
    if new_status in ['Resolved', 'Closed'] and not ticket.resolved_at:
        ticket.resolved_at = datetime.now(timezone.utc)

    db.session.commit()
    log_audit('UPDATE', 'ITTicket', ticket.id, f"Updated IT ticket {ticket.ticket_number} status to {new_status}")
    flash(f"Ticket {ticket.ticket_number} updated to '{new_status}'.", 'success')
    return redirect(url_for('it.tickets_list'))

@it_bp.route('/infrastructure')
@login_required
@it_required
def infrastructure():
    services = ITServiceHealth.query.all()
    return render_template('it/infrastructure.html', services=services)
