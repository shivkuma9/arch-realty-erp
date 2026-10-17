import csv
import io
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, Response
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Lead, Property, Deal, Brokerage, Expense, SiteVisit, User, Attendance
from app.services.auth_service import management_required, log_audit
from app.extensions import db

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
@management_required
def index():
    report_type = request.args.get('type', 'leads')
    
    # Lead source analytics
    lead_sources = db.session.query(Lead.source, func.count(Lead.id)).group_by(Lead.source).all()
    
    # Executive performance
    exec_performance = db.session.query(
        User.full_name,
        func.count(Lead.id).label('leads_handled'),
        func.coalesce(func.sum(Deal.final_value), 0).label('deals_closed_value')
    ).outerjoin(Lead, Lead.assigned_to_id == User.id)\
     .outerjoin(Deal, (Deal.owner_user_id == User.id) & (Deal.stage == 'Closed Won'))\
     .group_by(User.id).all()

    # Financial Summary
    financials = {
        'expected': db.session.query(func.coalesce(func.sum(Brokerage.expected_amount), 0)).scalar(),
        'received': db.session.query(func.coalesce(func.sum(Brokerage.received_amount), 0)).scalar(),
        'outstanding': db.session.query(func.coalesce(func.sum(Brokerage.outstanding_amount), 0)).scalar(),
        'expenses': db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar()
    }
    financials['net'] = financials['received'] - financials['expenses']

    # Property Inventory by Category & Status
    inv_by_cat = db.session.query(Property.category, Property.availability_status, func.count(Property.id))\
        .group_by(Property.category, Property.availability_status).all()

    return render_template(
        'reports/reports_index.html',
        report_type=report_type,
        lead_sources=lead_sources,
        exec_performance=exec_performance,
        financials=financials,
        inv_by_cat=inv_by_cat
    )

@reports_bp.route('/crm')
@login_required
def crm_reports():
    tab = request.args.get('tab', 'inquiry')
    leads = Lead.query.filter_by(is_archived=False).order_by(Lead.created_at.desc()).limit(100).all()
    from app.models import Client, SourcingAssignment
    clients = Client.query.filter_by(is_archived=False).order_by(Client.created_at.desc()).limit(100).all()
    deals = Deal.query.order_by(Deal.created_at.desc()).limit(100).all()
    brokerages = Brokerage.query.order_by(Brokerage.created_at.desc()).limit(100).all()
    sourcing_items = SourcingAssignment.query.order_by(SourcingAssignment.created_at.desc()).limit(100).all()
    attendances = Attendance.query.order_by(Attendance.attendance_date.desc()).limit(100).all()

    return render_template(
        'reports/crm_reports.html',
        tab=tab,
        leads=leads,
        clients=clients,
        deals=deals,
        brokerages=brokerages,
        sourcing_items=sourcing_items,
        attendances=attendances
    )

@reports_bp.route('/export/<report_type>')
@login_required
def export_report_csv(report_type):
    from app.models import Client, SourcingAssignment
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type in ['financials', 'broker', 'brokerage']:
        writer.writerow(['Deal Code', 'Client', 'Property', 'Expected Brokerage (INR)', 'Received Brokerage (INR)', 'Outstanding (INR)', 'Status'])
        records = Brokerage.query.all()
        for b in records:
            writer.writerow([
                b.deal.deal_code if b.deal else 'N/A',
                b.deal.client.name if (b.deal and b.deal.client) else 'N/A',
                b.deal.property.title if (b.deal and b.deal.property) else 'N/A',
                f"{b.expected_amount:.2f}",
                f"{b.received_amount:.2f}",
                f"{b.outstanding_amount:.2f}",
                b.status
            ])
        filename = "arch_realty_broker_report.csv"

    elif report_type in ['inventory', 'properties', 'property']:
        writer.writerow(['Property Code', 'Title', 'Category', 'Transaction', 'Locality', 'Price/Rent (INR)', 'Approval Status', 'Availability'])
        props = Property.query.filter_by(is_archived=False).all()
        for p in props:
            writer.writerow([
                p.property_code, p.title, p.category, p.transaction_type, p.locality,
                f"{p.sale_price or p.rent_price:.2f}", getattr(p, 'approval_status', 'Approved'), p.availability_status
            ])
        filename = "arch_realty_property_report.csv"

    elif report_type in ['clients', 'client']:
        writer.writerow(['Client Code', 'Name', 'Company', 'Phone', 'Email', 'Type', 'Category', 'Created Date'])
        clients = Client.query.filter_by(is_archived=False).all()
        for c in clients:
            writer.writerow([
                c.client_code, c.name, c.company_name or '', c.phone, c.email or '',
                c.client_type, c.category, c.created_at.strftime('%Y-%m-%d') if c.created_at else ''
            ])
        filename = "arch_realty_clients_report.csv"

    elif report_type in ['deals', 'deal']:
        writer.writerow(['Deal Code', 'Client', 'Property', 'Stage', 'Deal Value (INR)', 'Target Closing', 'Executive'])
        deals = Deal.query.all()
        for d in deals:
            writer.writerow([
                d.deal_code,
                d.client.name if d.client else 'N/A',
                d.property.title if d.property else 'N/A',
                d.stage,
                f"{d.final_value or d.expected_value or 0:.2f}",
                d.expected_closing_date.strftime('%Y-%m-%d') if d.expected_closing_date else '',
                d.owner.full_name if d.owner else 'Unassigned'
            ])
        filename = "arch_realty_deals_report.csv"

    elif report_type in ['sourcing', 'sourcing_report']:
        writer.writerow(['Sourcing Code', 'Title', 'Type', 'Locality', 'Category', 'Priority', 'Status', 'Assigned Executive', 'Due Date'])
        assignments = SourcingAssignment.query.all()
        for a in assignments:
            writer.writerow([
                a.sourcing_code, a.title, a.sourcing_type, a.locality, a.category or '',
                a.priority, a.status, a.assigned_to.full_name if a.assigned_to else 'Unassigned',
                a.due_date.strftime('%Y-%m-%d') if a.due_date else ''
            ])
        filename = "arch_realty_sourcing_report.csv"

    elif report_type in ['attendance', 'attendance_report']:
        writer.writerow(['Date', 'Employee', 'Status', 'Check In', 'Check Out', 'Working Hours'])
        atts = Attendance.query.order_by(Attendance.attendance_date.desc()).all()
        for att in atts:
            writer.writerow([
                att.attendance_date.strftime('%Y-%m-%d') if att.attendance_date else '',
                att.user.full_name if att.user else 'Unknown',
                att.status,
                att.check_in_time.strftime('%H:%M:%S') if att.check_in_time else '',
                att.check_out_time.strftime('%H:%M:%S') if att.check_out_time else '',
                f"{att.working_hours:.2f}" if att.working_hours else ''
            ])
        filename = "arch_realty_attendance_report.csv"

    else: # inquiries / leads
        writer.writerow(['Lead Code', 'Name', 'Phone', 'Source', 'Category', 'Transaction', 'Budget Max', 'Status', 'Assigned Executive'])
        leads = Lead.query.filter_by(is_archived=False).all()
        for l in leads:
            writer.writerow([
                l.lead_code, l.full_name, l.phone, l.source, l.property_category,
                l.transaction_type, f"{l.budget_max:.2f}" if l.budget_max else '0',
                l.status, l.assigned_to.full_name if l.assigned_to else 'Unassigned'
            ])
        filename = "arch_realty_inquiry_report.csv"

    log_audit('EXPORT_REPORT', 'Report', None, f"Exported {report_type} CSV report")
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

