from decimal import Decimal
from app.models import Brokerage, Invoice, Payment, Deal
from app.extensions import db

def calculate_brokerage_for_deal(deal: Deal, client_percent: float = 1.0, owner_percent: float = 1.0, rule_type: str = 'Percentage') -> Brokerage:
    """
    Calculates brokerage receivable for a closed or agreed deal.
    Rule Types:
      - 'Percentage': Calculated as % of final transaction consideration.
      - 'RentMonths': E.g., 1 month rent from client, 1 month rent from owner.
    """
    deal_value = Decimal(str(deal.final_value or deal.expected_value or 0))
    client_p = Decimal(str(client_percent))
    owner_p = Decimal(str(owner_percent))
    
    if rule_type == 'RentMonths':
        # Here deal_value is monthly rent
        client_brokerage = deal_value * client_p
        owner_brokerage = deal_value * owner_p
    else:
        # Sale percentage
        client_brokerage = (deal_value * client_p) / Decimal('100.0')
        owner_brokerage = (deal_value * owner_p) / Decimal('100.0')
        
    total_expected = client_brokerage + owner_brokerage

    brokerage = Brokerage.query.filter_by(deal_id=deal.id).first()
    if not brokerage:
        brokerage = Brokerage(
            deal_id=deal.id,
            rule_type=rule_type,
            client_percentage=client_p,
            owner_percentage=owner_p,
            expected_amount=total_expected,
            invoiced_amount=Decimal('0.0'),
            received_amount=Decimal('0.0'),
            outstanding_amount=total_expected,
            status='Pending'
        )
        db.session.add(brokerage)
    else:
        brokerage.expected_amount = total_expected
        brokerage.outstanding_amount = total_expected - brokerage.received_amount
        if brokerage.outstanding_amount <= Decimal('0.0'):
            brokerage.status = 'Fully Paid'
        elif brokerage.received_amount > Decimal('0.0'):
            brokerage.status = 'Partially Paid'
        else:
            brokerage.status = 'Pending'

    db.session.commit()
    return brokerage

def record_brokerage_payment(brokerage_id: int, amount: Decimal, payment_date, payment_mode: str, transaction_ref: str, recorded_by_id: int, invoice_id: int = None, notes: str = None) -> Payment:
    """Safely record a payment receipt and adjust outstanding balances."""
    brokerage = Brokerage.query.get(brokerage_id)
    if not brokerage:
        raise ValueError("Brokerage record not found.")

    # Unique receipt number
    count = Payment.query.count() + 1
    receipt_no = f"REC-ARCH-{count:05d}"

    payment = Payment(
        receipt_number=receipt_no,
        brokerage_id=brokerage.id,
        invoice_id=invoice_id,
        amount=amount,
        payment_date=payment_date,
        payment_mode=payment_mode,
        transaction_ref=transaction_ref,
        recorded_by_id=recorded_by_id,
        notes=notes
    )
    db.session.add(payment)

    # Adjust brokerage numbers
    brokerage.received_amount += amount
    brokerage.outstanding_amount = max(Decimal('0.0'), brokerage.expected_amount - brokerage.received_amount)
    
    if brokerage.outstanding_amount <= Decimal('0.0'):
        brokerage.status = 'Fully Paid'
    else:
        brokerage.status = 'Partially Paid'

    if invoice_id:
        invoice = Invoice.query.get(invoice_id)
        if invoice:
            invoice.status = 'Paid'

    db.session.commit()
    return payment
