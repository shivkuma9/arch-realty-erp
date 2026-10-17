from datetime import date
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Brokerage, Invoice, Payment, Expense, CommissionPayout, User, Roles
from app.forms import PaymentForm, CommissionForm, ExpenseForm
from app.services.finance_service import record_brokerage_payment
from app.services.auth_service import accounts_required, log_audit
from app.extensions import db

finance_bp = Blueprint('finance', __name__)

@finance_bp.before_request
def check_finance_access():
    if current_user.is_authenticated and not current_user.can_access_finance():
        abort(403)



@finance_bp.route('/')
@login_required
@accounts_required
def index():
    # Brokerage overview
    brokerages = Brokerage.query.order_by(Brokerage.created_at.desc()).all()
    invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).all()
    payments = Payment.query.order_by(Payment.payment_date.desc()).limit(15).all()
    expenses = Expense.query.order_by(Expense.expense_date.desc()).limit(15).all()
    commissions = CommissionPayout.query.order_by(CommissionPayout.created_at.desc()).all()

    total_expected = db.session.query(func.coalesce(func.sum(Brokerage.expected_amount), 0)).scalar()
    total_received = db.session.query(func.coalesce(func.sum(Brokerage.received_amount), 0)).scalar()
    total_outstanding = db.session.query(func.coalesce(func.sum(Brokerage.outstanding_amount), 0)).scalar()
    total_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar()
    total_commissions = db.session.query(func.coalesce(func.sum(CommissionPayout.amount), 0)).filter_by(status='Disbursed').scalar()

    net_margin = total_received - total_expenses - total_commissions

    return render_template(
        'finance/finance_overview.html',
        brokerages=brokerages,
        invoices=invoices,
        payments=payments,
        expenses=expenses,
        commissions=commissions,
        total_expected=total_expected,
        total_received=total_received,
        total_outstanding=total_outstanding,
        total_expenses=total_expenses,
        total_commissions=total_commissions,
        net_margin=net_margin
    )

@finance_bp.route('/record-payment', methods=['GET', 'POST'])
@login_required
@accounts_required
def record_payment():
    form = PaymentForm()
    open_brokerages = Brokerage.query.filter(Brokerage.status != 'Fully Paid').all()
    form.brokerage_id.choices = [(b.id, f"{b.deal.deal_code} - Expected: ₹ {b.expected_amount:,.2f} (Due: ₹ {b.outstanding_amount:,.2f})") for b in open_brokerages]

    if form.validate_on_submit():
        try:
            payment = record_brokerage_payment(
                brokerage_id=form.brokerage_id.data,
                amount=Decimal(str(form.amount.data)),
                payment_date=form.payment_date.data,
                payment_mode=form.payment_mode.data,
                transaction_ref=form.transaction_ref.data,
                recorded_by_id=current_user.id,
                notes=form.notes.data
            )
            log_audit('PAYMENT', 'Brokerage', form.brokerage_id.data, f"Recorded receipt {payment.receipt_number} for ₹ {payment.amount:,.2f}")
            flash(f"Payment receipt {payment.receipt_number} recorded successfully!", 'success')
            return redirect(url_for('finance.index'))
        except Exception as e:
            flash(f"Error recording payment: {str(e)}", 'danger')

    return render_template('finance/payment_form.html', form=form, title="Record Brokerage Payment Receipt")

@finance_bp.route('/generate-invoice/<int:brokerage_id>', methods=['POST'])
@login_required
@accounts_required
def generate_invoice(brokerage_id):
    brokerage = Brokerage.query.get_or_404(brokerage_id)
    party_type = request.form.get('party_type', 'Client')
    amount = Decimal(request.form.get('amount', str(brokerage.outstanding_amount)))
    gst_rate = Decimal('0.18')
    tax = amount * gst_rate
    total = amount + tax

    count = Invoice.query.count() + 1
    inv_num = f"INV-ARCH-{date.today().year}-{count:04d}"

    invoice = Invoice(
        invoice_number=inv_num,
        brokerage_id=brokerage.id,
        party_type=party_type,
        amount=amount,
        tax_amount=tax,
        total_amount=total,
        invoice_date=date.today(),
        due_date=date.today(),
        status='Unpaid'
    )
    db.session.add(invoice)
    brokerage.invoiced_amount += total
    db.session.commit()
    log_audit('CREATE', 'Invoice', invoice.id, f"Generated invoice {inv_num}")
    flash(f"Invoice {inv_num} generated for ₹ {total:,.2f} (including 18% GST)", 'success')
    return redirect(url_for('finance.index'))

@finance_bp.route('/commissions/new', methods=['GET', 'POST'])
@finance_bp.route('/commissions/claim', methods=['GET', 'POST'], endpoint='create_commission')
@login_required
@accounts_required
def commission_claim():
    form = CommissionForm()
    brokerages = Brokerage.query.all()
    users = User.query.filter_by(is_active=True).all()
    form.brokerage_id.choices = [(b.id, f"{b.deal.deal_code} - {b.deal.title} (Fee: ₹ {b.received_amount:,.2f} realized)") for b in brokerages]
    form.user_id.choices = [(0, '-- External Partner --')] + [(u.id, f"{u.full_name} ({u.role} - {u.department})") for u in users]

    if form.validate_on_submit():
        comm = CommissionPayout(
            brokerage_id=form.brokerage_id.data,
            recipient_type=form.recipient_type.data,
            user_id=form.user_id.data if form.user_id.data != 0 else None,
            partner_name=form.partner_name.data,
            commission_type=form.commission_type.data,
            percentage=form.percentage.data,
            amount=form.amount.data,
            status='Pending Approval',
            notes=form.notes.data
        )
        db.session.add(comm)
        db.session.commit()
        log_audit('COMMISSION_CLAIM', 'CommissionPayout', comm.id, f"Created incentive claim of ₹ {comm.amount:,.2f}")
        flash('Commission & incentive payout claim submitted for management approval.', 'success')
        return redirect(url_for('finance.index'))

    return render_template('finance/commission_form.html', form=form, title="Submit Commission & Incentive Claim")

@finance_bp.route('/commissions/<int:comm_id>/approve', methods=['POST'])
@login_required
@accounts_required
def approve_commission(comm_id):
    comm = CommissionPayout.query.get_or_404(comm_id)
    action = request.form.get('action') # Approved or Disbursed
    if action in ['Approved', 'Disbursed', 'Rejected']:
        comm.status = action
        if action == 'Disbursed':
            comm.payout_date = date.today()
            comm.payment_ref = request.form.get('payment_ref', 'BANK-NEFT')
        comm.approved_by_id = current_user.id
        db.session.commit()
        log_audit('COMMISSION_APPROVAL', 'CommissionPayout', comm.id, f"Commission {comm_id} marked as {action}")
        flash(f"Commission marked as {action}.", 'success')

    return redirect(url_for('finance.index'))

@finance_bp.route('/expenses/new', methods=['GET', 'POST'])
@login_required
@accounts_required
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        exp = Expense(
            title=form.title.data,
            category=form.category.data,
            amount=form.amount.data,
            expense_date=form.expense_date.data,
            paid_to=form.paid_to.data,
            payment_mode=form.payment_mode.data,
            approval_status='Approved' if current_user.is_management() else 'Pending',
            recorded_by_id=current_user.id,
            notes=form.notes.data
        )
        db.session.add(exp)
        db.session.commit()
        log_audit('CREATE', 'Expense', exp.id, f"Recorded expense {exp.title} for ₹ {exp.amount:,.2f}")
        flash(f"Expense '{exp.title}' recorded successfully.", 'success')
        return redirect(url_for('finance.index'))

    return render_template('finance/expense_form.html', form=form, title="Record Operational Expense")
