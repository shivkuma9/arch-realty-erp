from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import (
    Lead, Client, Property, Deal, SiteVisit, Brokerage, Task, FollowUp, User, Roles, Notification,
    Attendance, LeaveRequest, Recruitment, Invoice, Expense, Asset, MarketingCampaign, ITTicket, ITServiceHealth,
    SourcingAssignment, GPSTrackingLog, EmployeeDocument, ExitClearance, EmployeeOnboarding
)
from app.extensions import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Date filter parsing
    period = request.args.get('period', 'month') # today, week, month, year, all
    today = date.today()
    
    if period == 'today':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = date(2000, 1, 1)

    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)

    # Base queries with role filtering
    lead_q = Lead.query.filter(Lead.is_archived == False)
    deal_q = Deal.query
    visit_q = SiteVisit.query
    task_q = Task.query

    if not current_user.is_management() and not current_user.is_accounts():
        # Sales/Field Executives see assigned records
        lead_q = lead_q.filter(Lead.assigned_to_id == current_user.id)
        deal_q = deal_q.filter(Deal.owner_user_id == current_user.id)
        visit_q = visit_q.filter(SiteVisit.assigned_employee_id == current_user.id)
        task_q = task_q.filter(Task.assigned_to_id == current_user.id)

    # KPIs
    total_leads = lead_q.count()
    new_leads = lead_q.filter(Lead.status == 'New', Lead.created_at >= start_datetime).count()
    qualified_leads = lead_q.filter(Lead.status == 'Qualified').count()
    
    active_clients = Client.query.filter_by(is_archived=False).count()
    available_properties = Property.query.filter_by(availability_status='Available', is_archived=False).count()
    
    upcoming_visits = visit_q.filter(SiteVisit.visit_date >= today, SiteVisit.status.in_(['Scheduled', 'Confirmed'])).count()
    
    open_deals = deal_q.filter(~Deal.stage.in_(['Closed Won', 'Closed Lost'])).count()
    won_deals = deal_q.filter(Deal.stage == 'Closed Won').count()
    
    # Financial metrics
    deal_value_sum = db.session.query(func.coalesce(func.sum(Deal.final_value), 0)).filter(Deal.stage == 'Closed Won').scalar()
    
    brokerage_stats = db.session.query(
        func.coalesce(func.sum(Brokerage.expected_amount), 0),
        func.coalesce(func.sum(Brokerage.received_amount), 0),
        func.coalesce(func.sum(Brokerage.outstanding_amount), 0)
    ).first()
    
    expected_brokerage = brokerage_stats[0]
    received_brokerage = brokerage_stats[1]
    outstanding_brokerage = brokerage_stats[2]

    # Follow-ups & Tasks
    followups_due = FollowUp.query.filter(
        FollowUp.status == 'Pending',
        func.date(FollowUp.scheduled_at) <= today
    )
    if not current_user.is_management():
        followups_due = followups_due.filter(FollowUp.user_id == current_user.id)
    followups_due_count = followups_due.count()

    overdue_tasks_count = task_q.filter(Task.status.in_(['Pending', 'In Progress']), Task.due_date < today).count()

    # Recent items
    recent_leads = lead_q.order_by(Lead.created_at.desc()).limit(6).all()
    upcoming_visits_list = visit_q.filter(SiteVisit.visit_date >= today).order_by(SiteVisit.visit_date.asc(), SiteVisit.visit_time.asc()).limit(5).all()
    my_tasks = task_q.filter(Task.status.in_(['Pending', 'In Progress'])).order_by(Task.due_date.asc()).limit(5).all()

    # Stage distribution for funnel
    stage_counts = db.session.query(Lead.status, func.count(Lead.id)).filter(Lead.is_archived == False).group_by(Lead.status).all()
    funnel_data = {s: 0 for s in ['New', 'Contacted', 'Qualified', 'Site Visit', 'Negotiation', 'Won', 'Lost']}
    for s, c in stage_counts:
        if s in funnel_data:
            funnel_data[s] = c

    # Category distribution for properties
    cat_counts = db.session.query(Property.category, func.count(Property.id)).filter(Property.is_archived == False).group_by(Property.category).all()
    prop_cats = {c: count for c, count in cat_counts}

    # Departmental metrics
    today_attendance_count = Attendance.query.filter_by(attendance_date=today, status='Present').count()
    pending_leaves_count = LeaveRequest.query.filter_by(status='Pending').count()
    open_recruitments_count = Recruitment.query.filter_by(status='Active').count()
    allocated_assets_count = Asset.query.filter_by(status='Allocated').count()
    unpaid_invoices_count = Invoice.query.filter_by(status='Unpaid').count()
    total_expenses_amount = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar()
    my_today_visits_count = SiteVisit.query.filter_by(assigned_employee_id=current_user.id, visit_date=today).count()
    my_today_punch = Attendance.query.filter_by(user_id=current_user.id, attendance_date=today).first()

    pending_invoices_list = Invoice.query.filter_by(status='Unpaid').order_by(Invoice.due_date.asc()).limit(5).all()
    recent_expenses_list = Expense.query.order_by(Expense.expense_date.desc()).limit(5).all()
    pending_leaves_list = LeaveRequest.query.filter_by(status='Pending').order_by(LeaveRequest.created_at.desc()).limit(5).all()
    today_team_attendance = Attendance.query.filter_by(attendance_date=today).order_by(Attendance.created_at.desc()).limit(6).all()

    # Marketing & IT Metrics
    active_campaigns_count = MarketingCampaign.query.filter_by(status='Active').count()
    total_marketing_spend = db.session.query(func.coalesce(func.sum(MarketingCampaign.spent_amount), 0)).scalar()
    total_marketing_leads = db.session.query(func.coalesce(func.sum(MarketingCampaign.leads_generated), 0)).scalar()
    avg_marketing_cpl = (float(total_marketing_spend) / total_marketing_leads) if total_marketing_leads > 0 else 0.0

    open_tickets_count = ITTicket.query.filter(ITTicket.status.in_(['Open', 'In Progress'])).count()
    critical_tickets_count = ITTicket.query.filter(ITTicket.priority == 'Critical', ITTicket.status.in_(['Open', 'In Progress'])).count()
    services_count = ITServiceHealth.query.count()
    operational_services_count = ITServiceHealth.query.filter_by(status='Operational').count()

    recent_campaigns_list = MarketingCampaign.query.order_by(MarketingCampaign.created_at.desc()).limit(5).all()
    recent_tickets_list = ITTicket.query.order_by(ITTicket.created_at.desc()).limit(5).all()

    # Additional Department Metrics for Executive Slot Hub
    pre_leased_properties_count = Property.query.filter_by(is_pre_leased=True, is_archived=False).count()
    commercial_properties_count = Property.query.filter_by(category='Commercial', is_archived=False).count()
    residential_properties_count = Property.query.filter_by(category='Residential', is_archived=False).count()

    sourcing_assignments_count = SourcingAssignment.query.count()
    gps_pings_today_count = GPSTrackingLog.query.filter(func.date(GPSTrackingLog.timestamp) == today).count()

    pending_docs_count = EmployeeDocument.query.filter_by(status='Pending Review').count()
    notice_exits_count = ExitClearance.query.filter_by(status='Notice Period').count()
    in_progress_onboarding_count = EmployeeOnboarding.query.filter_by(status='In Progress').count()

    all_active_properties = Property.query.filter_by(is_archived=False).order_by(Property.created_at.desc()).limit(5).all()
    recent_sourcing_list = SourcingAssignment.query.order_by(SourcingAssignment.created_at.desc()).limit(5).all()
    recent_gps_logs = GPSTrackingLog.query.order_by(GPSTrackingLog.timestamp.desc()).limit(5).all()

    return render_template(
        'dashboard/index.html',
        period=period,
        total_leads=total_leads,
        new_leads=new_leads,
        qualified_leads=qualified_leads,
        active_clients=active_clients,
        available_properties=available_properties,
        upcoming_visits=upcoming_visits,
        open_deals=open_deals,
        won_deals=won_deals,
        deal_value_sum=deal_value_sum,
        expected_brokerage=expected_brokerage,
        received_brokerage=received_brokerage,
        outstanding_brokerage=outstanding_brokerage,
        followups_due_count=followups_due_count,
        overdue_tasks_count=overdue_tasks_count,
        recent_leads=recent_leads,
        upcoming_visits_list=upcoming_visits_list,
        my_tasks=my_tasks,
        funnel_data=funnel_data,
        prop_cats=prop_cats,
        today_attendance_count=today_attendance_count,
        pending_leaves_count=pending_leaves_count,
        open_recruitments_count=open_recruitments_count,
        allocated_assets_count=allocated_assets_count,
        unpaid_invoices_count=unpaid_invoices_count,
        total_expenses_amount=total_expenses_amount,
        my_today_visits_count=my_today_visits_count,
        my_today_punch=my_today_punch,
        pending_invoices_list=pending_invoices_list,
        recent_expenses_list=recent_expenses_list,
        pending_leaves_list=pending_leaves_list,
        today_team_attendance=today_team_attendance,
        active_campaigns_count=active_campaigns_count,
        total_marketing_spend=total_marketing_spend,
        total_marketing_leads=total_marketing_leads,
        avg_marketing_cpl=avg_marketing_cpl,
        open_tickets_count=open_tickets_count,
        critical_tickets_count=critical_tickets_count,
        services_count=services_count,
        operational_services_count=operational_services_count,
        recent_campaigns_list=recent_campaigns_list,
        recent_tickets_list=recent_tickets_list,
        pre_leased_properties_count=pre_leased_properties_count,
        commercial_properties_count=commercial_properties_count,
        residential_properties_count=residential_properties_count,
        sourcing_assignments_count=sourcing_assignments_count,
        gps_pings_today_count=gps_pings_today_count,
        pending_docs_count=pending_docs_count,
        notice_exits_count=notice_exits_count,
        in_progress_onboarding_count=in_progress_onboarding_count,
        all_active_properties=all_active_properties,
        recent_sourcing_list=recent_sourcing_list,
        recent_gps_logs=recent_gps_logs
    )



@dashboard_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('dashboard/notifications.html', notifications=notifs)

@dashboard_bp.route('/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})
