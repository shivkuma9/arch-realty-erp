from decimal import Decimal
from datetime import datetime, timezone
from app.models import PropertyMatch, Requirement, Property, Lead, Task, Notification
from app.extensions import db

def score_property_match(requirement: Requirement, prop: Property) -> tuple[int, list[str], list[str]]:
    """
    Rule-based matching engine for client requirements vs property inventory.
    Returns (score, match_reasons, mismatches).
    Max score: 100.
    """
    score = 0
    reasons = []
    mismatches = []
    
    # 1. Category check (30 pts)
    if requirement.category.lower() == prop.category.lower():
        score += 30
        reasons.append(f"Category matches: {prop.category}")
    else:
        mismatches.append(f"Category mismatch: Wanted {requirement.category}, listing is {prop.category}")
        
    # 2. Transaction type check (25 pts)
    req_tx = requirement.transaction_type.lower()
    prop_tx = prop.transaction_type.lower()
    if req_tx == prop_tx or (req_tx in ['rent', 'lease'] and prop_tx in ['rent', 'lease']):
        score += 25
        reasons.append(f"Transaction model fits: {prop.transaction_type}")
    else:
        mismatches.append(f"Transaction mismatch: Seeking {requirement.transaction_type}, property offered for {prop.transaction_type}")

    # 3. Location fit (20 pts)
    if requirement.preferred_locations:
        pref_locs = [loc.strip().lower() for loc in requirement.preferred_locations.split(',') if loc.strip()]
        prop_loc = prop.locality.lower()
        if any(pl in prop_loc or prop_loc in pl for pl in pref_locs):
            score += 20
            reasons.append(f"Location in preferred areas: {prop.locality}")
        else:
            mismatches.append(f"Location outside preferred localities ({prop.locality})")
    else:
        score += 10 # Neutral
        reasons.append("No strict location limitation specified")

    # 4. Budget fit (15 pts)
    price = prop.sale_price if prop.transaction_type == 'Sale' else prop.rent_price
    if requirement.budget_max and requirement.budget_max > 0:
        if price <= requirement.budget_max:
            if requirement.budget_min and price < requirement.budget_min * Decimal('0.8'):
                score += 8
                reasons.append(f"Price is well below minimum budget range (₹ {price:,.2f})")
            else:
                score += 15
                reasons.append(f"Within budget ceiling of ₹ {requirement.budget_max:,.2f}")
        else:
            mismatches.append(f"Exceeds max budget (₹ {price:,.2f} vs max ₹ {requirement.budget_max:,.2f})")
    else:
        score += 10
        reasons.append("Open / flexible budget")

    # 5. Area fit (10 pts)
    prop_area = prop.carpet_area or prop.builtup_area
    if requirement.area_min and requirement.area_min > 0:
        if prop_area >= requirement.area_min:
            if requirement.area_max and prop_area > requirement.area_max * Decimal('1.3'):
                score += 5
                mismatches.append(f"Area somewhat larger than maximum ({prop_area} sq.ft)")
            else:
                score += 10
                reasons.append(f"Sufficient area requirement ({prop_area} sq.ft)")
        else:
            mismatches.append(f"Below required minimum size ({prop_area} sq.ft vs min {requirement.area_min} sq.ft)")
    else:
        score += 10

    return min(score, 100), reasons, mismatches

def generate_matches_for_requirement(requirement_id: int):
    """Scan available properties and update property_matches for this requirement."""
    req = Requirement.query.get(requirement_id)
    if not req or req.status != 'Active':
        return []

    available_props = Property.query.filter_by(availability_status='Available', is_archived=False).all()
    results = []
    
    for prop in available_props:
        score, reasons, mismatches = score_property_match(req, prop)
        if score >= 40: # Quality threshold
            match = PropertyMatch.query.filter_by(requirement_id=req.id, property_id=prop.id).first()
            if not match:
                match = PropertyMatch(
                    requirement_id=req.id,
                    property_id=prop.id,
                    match_score=score,
                    match_reasons="; ".join(reasons),
                    mismatches="; ".join(mismatches)
                )
                db.session.add(match)
            else:
                match.match_score = score
                match.match_reasons = "; ".join(reasons)
                match.mismatches = "; ".join(mismatches)
            results.append((match, score))

    db.session.commit()
    return results

def detect_duplicate_lead(phone: str, email: str = None, exclude_id: int = None):
    """Identify if a lead with same contact info exists in CRM."""
    query = Lead.query.filter(Lead.phone == phone, Lead.is_archived == False)
    if exclude_id:
        query = query.filter(Lead.id != exclude_id)
    lead_by_phone = query.first()
    if lead_by_phone:
        return True, f"Lead with phone number '{phone}' already exists: {lead_by_phone.full_name} ({lead_by_phone.lead_code})"

    if email and email.strip():
        email_query = Lead.query.filter(Lead.email == email.strip(), Lead.is_archived == False)
        if exclude_id:
            email_query = email_query.filter(Lead.id != exclude_id)
        lead_by_email = email_query.first()
        if lead_by_email:
            return True, f"Lead with email '{email}' already exists: {lead_by_email.full_name} ({lead_by_email.lead_code})"

    return False, ""

def create_in_app_notification(user_id: int, title: str, message: str, link: str = None, category: str = 'General'):
    """Generate in-app notification for executive."""
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link,
            category=category
        )
        db.session.add(notif)
        db.session.commit()
    except Exception:
        db.session.rollback()
