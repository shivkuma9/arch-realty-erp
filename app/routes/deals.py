from datetime import datetime, timezone, date
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import Deal, DealStageHistory, Client, Property, Lead, User, Roles, Brokerage
from app.forms import DealForm
from app.services.finance_service import calculate_brokerage_for_deal
from app.services.auth_service import log_audit
from app.extensions import db

deals_bp = Blueprint('deals', __name__)

@deals_bp.before_request
def check_deals_access():
    if current_user.is_authenticated and not current_user.can_access_deals():
        abort(403)



STAGES = [
    'Initial Discussion',
    'Requirement Confirmed',
    'Property Shortlisted',
    'Site Visit',
    'Negotiation',
    'Token Received',
    'Agreement',
    'Closed Won',
    'Closed Lost'
]

@deals_bp.route('/')
@login_required
def index():
    view_mode = request.args.get('view', 'kanban') # kanban or table
    stage_filter = request.args.get('stage', '').strip()

    query = Deal.query
    if not current_user.is_management() and not current_user.is_accounts():
        query = query.filter_by(owner_user_id=current_user.id)

    if stage_filter:
        query = query.filter_by(stage=stage_filter)

    all_deals = query.order_by(Deal.created_at.desc()).all()

    # Organize deals by stage for Kanban view
    kanban_columns = {stage: [] for stage in STAGES}
    for deal in all_deals:
        if deal.stage in kanban_columns:
            kanban_columns[deal.stage].append(deal)

    return render_template(
        'deals/deals_list.html',
        deals=all_deals,
        kanban_columns=kanban_columns,
        stages=STAGES,
        view_mode=view_mode,
        selected_stage=stage_filter
    )

@deals_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_deal():
    form = DealForm()
    clients = Client.query.filter_by(is_archived=False).all()
    props = Property.query.filter_by(is_archived=False).all()
    leads = Lead.query.filter_by(is_archived=False).all()
    users = User.query.filter_by(is_active=True).all()

    form.client_id.choices = [(c.id, f"{c.client_code} - {c.name}") for c in clients]
    form.property_id.choices = [(p.id, f"{p.property_code} - {p.title}") for p in props]
    form.lead_id.choices = [(0, '-- None --')] + [(l.id, f"{l.lead_code} - {l.full_name}") for l in leads]
    form.owner_user_id.choices = [(u.id, f"{u.full_name} ({u.role})") for u in users]

    if request.method == 'GET' and not current_user.is_management():
        form.owner_user_id.data = current_user.id

    if form.validate_on_submit():
        count = Deal.query.count() + 1
        deal_code = f"DEAL-AHM-{count:05d}"

        deal = Deal(
            deal_code=deal_code,
            title=form.title.data,
            client_id=form.client_id.data,
            property_id=form.property_id.data,
            lead_id=form.lead_id.data if form.lead_id.data != 0 else None,
            owner_user_id=form.owner_user_id.data,
            stage=form.stage.data,
            quoted_value=form.quoted_value.data or 0,
            expected_value=form.expected_value.data or 0,
            final_value=form.final_value.data or 0,
            token_amount=form.token_amount.data or 0,
            token_date=form.token_date.data,
            expected_closing_date=form.expected_closing_date.data,
            actual_closing_date=form.actual_closing_date.data,
            agreement_status=form.agreement_status.data,
            lost_reason=form.lost_reason.data,
            notes=form.notes.data
        )
        db.session.add(deal)
        db.session.commit()

        # Log Stage History
        sh = DealStageHistory(
            deal_id=deal.id,
            previous_stage=None,
            new_stage=deal.stage,
            changed_by_id=current_user.id,
            comments="Deal Created"
        )
        db.session.add(sh)

        # Calculate Brokerage if Won or In Negotiation
        if deal.stage == 'Closed Won':
            calculate_brokerage_for_deal(deal)

        log_audit('CREATE', 'Deal', deal.id, f"Created deal {deal.deal_code} - {deal.title}")
        db.session.commit()
        flash(f"Deal {deal.deal_code} created successfully!", 'success')
        return redirect(url_for('deals.detail', deal_id=deal.id))

    return render_template('deals/deal_form.html', form=form, title="Create New Deal / Negotiation")

@deals_bp.route('/<int:deal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_deal(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    if not current_user.is_management() and not current_user.is_accounts() and deal.owner_user_id != current_user.id:
        abort(403)

    form = DealForm(obj=deal)
    clients = Client.query.filter_by(is_archived=False).all()
    props = Property.query.filter_by(is_archived=False).all()
    leads = Lead.query.filter_by(is_archived=False).all()
    users = User.query.filter_by(is_active=True).all()

    form.client_id.choices = [(c.id, f"{c.client_code} - {c.name}") for c in clients]
    form.property_id.choices = [(p.id, f"{p.property_code} - {p.title}") for p in props]
    form.lead_id.choices = [(0, '-- None --')] + [(l.id, f"{l.lead_code} - {l.full_name}") for l in leads]
    form.owner_user_id.choices = [(u.id, f"{u.full_name} ({u.role})") for u in users]

    if form.validate_on_submit():
        old_stage = deal.stage
        deal.title = form.title.data
        deal.client_id = form.client_id.data
        deal.property_id = form.property_id.data
        deal.lead_id = form.lead_id.data if form.lead_id.data != 0 else None
        if current_user.is_management():
            deal.owner_user_id = form.owner_user_id.data
        deal.stage = form.stage.data
        deal.quoted_value = form.quoted_value.data or 0
        deal.expected_value = form.expected_value.data or 0
        deal.final_value = form.final_value.data or 0
        deal.token_amount = form.token_amount.data or 0
        deal.token_date = form.token_date.data
        deal.expected_closing_date = form.expected_closing_date.data
        deal.actual_closing_date = form.actual_closing_date.data
        deal.agreement_status = form.agreement_status.data
        deal.lost_reason = form.lost_reason.data
        deal.notes = form.notes.data

        if old_stage != deal.stage:
            sh = DealStageHistory(
                deal_id=deal.id,
                previous_stage=old_stage,
                new_stage=deal.stage,
                changed_by_id=current_user.id,
                comments=f"Stage modified during deal update"
            )
            db.session.add(sh)
            if deal.stage == 'Closed Won':
                calculate_brokerage_for_deal(deal)

        log_audit('UPDATE', 'Deal', deal.id, f"Updated deal {deal.deal_code}")
        db.session.commit()
        flash('Deal updated successfully!', 'success')
        return redirect(url_for('deals.detail', deal_id=deal.id))

    return render_template('deals/deal_form.html', form=form, title=f"Edit Deal {deal.deal_code}", deal=deal)

@deals_bp.route('/<int:deal_id>')
@login_required
def detail(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    if not current_user.is_management() and not current_user.is_accounts() and deal.owner_user_id != current_user.id:
        abort(403)

    stage_histories = deal.stage_history.order_by(DealStageHistory.created_at.desc()).all()
    brokerage = Brokerage.query.filter_by(deal_id=deal.id).first()
    return render_template('deals/deal_detail.html', deal=deal, stage_histories=stage_histories, brokerage=brokerage, stages=STAGES)

@deals_bp.route('/<int:deal_id>/update-stage', methods=['POST'])
@login_required
def update_stage(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    if not current_user.is_management() and deal.owner_user_id != current_user.id:
        abort(403)

    new_stage = request.form.get('stage')
    comments = request.form.get('comments', '').strip()
    final_val = request.form.get('final_value')

    if new_stage in STAGES:
        old_stage = deal.stage
        deal.stage = new_stage
        
        if final_val:
            try:
                deal.final_value = Decimal(final_val)
            except Exception:
                pass

        if new_stage == 'Closed Won':
            deal.actual_closing_date = date.today()
            # Automatically calculate brokerage
            calculate_brokerage_for_deal(deal)
        elif new_stage == 'Closed Lost':
            deal.lost_reason = comments

        sh = DealStageHistory(
            deal_id=deal.id,
            previous_stage=old_stage,
            new_stage=new_stage,
            changed_by_id=current_user.id,
            comments=comments
        )
        db.session.add(sh)
        log_audit('UPDATE_STAGE', 'Deal', deal.id, f"Changed stage {old_stage} -> {new_stage}")
        db.session.commit()
        flash(f"Deal stage updated to '{new_stage}'", 'success')

    return redirect(url_for('deals.detail', deal_id=deal.id))
