import os
from datetime import datetime, timezone, date
from decimal import Decimal
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app.models import Property, PropertyImage, Owner, Mandate, Requirement, PropertyMatch, User, Roles
from app.forms import PropertyForm, OwnerForm, MandateForm
from app.services.matching_service import generate_matches_for_requirement
from app.services.auth_service import log_audit
from app.extensions import db

properties_bp = Blueprint('properties', __name__)

@properties_bp.before_request
def check_properties_access():
    if current_user.is_authenticated and not current_user.can_access_inventory():
        abort(403)



# --- PROPERTIES ---

@properties_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    sub_category = request.args.get('sub_category', '').strip()
    locality = request.args.get('locality', '').strip()
    tx_type = request.args.get('tx_type', '').strip()
    status = request.args.get('status', 'Available').strip()
    pre_leased = request.args.get('pre_leased', '').strip()

    query = Property.query.filter_by(is_archived=False)

    if search:
        query = query.filter(
            (Property.title.ilike(f'%{search}%')) |
            (Property.property_code.ilike(f'%{search}%')) |
            (Property.locality.ilike(f'%{search}%')) |
            (Property.building_name.ilike(f'%{search}%')) |
            (Property.tenant_name.ilike(f'%{search}%')) |
            (Property.address.ilike(f'%{search}%'))
        )
    if category:
        query = query.filter_by(category=category)
    if sub_category:
        query = query.filter_by(sub_category=sub_category)
    if locality:
        query = query.filter(Property.locality.ilike(f'%{locality}%'))
    if tx_type:
        query = query.filter_by(transaction_type=tx_type)
    if status and status != 'All':
        query = query.filter_by(availability_status=status)
    if pre_leased == '1':
        query = query.filter_by(is_pre_leased=True)

    pagination = query.order_by(Property.created_at.desc()).paginate(page=page, per_page=12, error_out=False)

    return render_template(
        'properties/properties_list.html',
        pagination=pagination,
        search=search,
        category=category,
        sub_category=sub_category,
        locality=locality,
        tx_type=tx_type,
        status=status,
        pre_leased=pre_leased
    )

@properties_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_property():
    form = PropertyForm()
    owners = Owner.query.all()
    users = User.query.filter_by(is_active=True).all()
    form.owner_id.choices = [(0, '-- None / Unlinked --')] + [(o.id, f"{o.name} ({o.phone})") for o in owners]
    form.assigned_to_id.choices = [(0, '-- Unassigned --')] + [(u.id, f"{u.full_name} ({u.role})") for u in users]

    if form.validate_on_submit():
        count = Property.query.count() + 1
        property_code = f"PROP-AHM-{count:05d}"
        
        prop = Property(
            property_code=property_code,
            title=form.title.data,
            category=form.category.data,
            sub_category=form.sub_category.data,
            transaction_type=form.transaction_type.data,
            building_name=form.building_name.data,
            unit_number=form.unit_number.data,
            locality=form.locality.data,
            address=form.address.data,
            city=form.city.data,
            latitude=float(form.latitude.data) if form.latitude.data else None,
            longitude=float(form.longitude.data) if form.longitude.data else None,
            google_maps_link=form.google_maps_link.data,
            carpet_area=form.carpet_area.data or 0,
            builtup_area=form.builtup_area.data or 0,
            super_builtup_area=form.super_builtup_area.data or 0,
            plot_area_sqyd=form.plot_area_sqyd.data or 0,
            sale_price=form.sale_price.data or 0,
            rent_price=form.rent_price.data or 0,
            rate_per_sqft=form.rate_per_sqft.data or 0,
            security_deposit=form.security_deposit.data or 0,
            brokerage_terms=form.brokerage_terms.data,
            is_pre_leased=form.is_pre_leased.data or (form.category.data == 'Pre-Leased'),
            tenant_name=form.tenant_name.data,
            tenant_business_type=form.tenant_business_type.data,
            monthly_rental_income=form.monthly_rental_income.data or 0,
            roi_percentage=form.roi_percentage.data or 0,
            lock_in_period_months=form.lock_in_period_months.data or 0,
            escalation_percentage=form.escalation_percentage.data or 0,
            furnishing=form.furnishing.data,
            construction_type=form.construction_type.data,
            zone_type=form.zone_type.data,
            amenities=form.amenities.data,
            floors=form.floors.data,
            availability_status=form.availability_status.data,
            owner_id=form.owner_id.data if form.owner_id.data != 0 else None,
            assigned_to_id=form.assigned_to_id.data if form.assigned_to_id.data != 0 else current_user.id,
            description=form.description.data,
            internal_notes=form.internal_notes.data
        )
        db.session.add(prop)
        db.session.commit()
        log_audit('CREATE', 'Property', prop.id, f"Created property {prop.property_code} - {prop.title}")
        flash(f"Property {prop.property_code} created successfully!", 'success')
        return redirect(url_for('properties.detail', property_id=prop.id))

    return render_template('properties/property_form.html', form=form, title="Add New Property Listing")

@properties_bp.route('/<int:property_id>')
@login_required
def detail(property_id):
    prop = Property.query.get_or_404(property_id)
    return render_template('properties/property_detail.html', property=prop)

@properties_bp.route('/<int:property_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    prop = Property.query.get_or_404(property_id)
    form = PropertyForm(obj=prop)
    owners = Owner.query.all()
    users = User.query.filter_by(is_active=True).all()
    form.owner_id.choices = [(0, '-- None / Unlinked --')] + [(o.id, f"{o.name} ({o.phone})") for o in owners]
    form.assigned_to_id.choices = [(0, '-- Unassigned --')] + [(u.id, f"{u.full_name} ({u.role})") for u in users]

    if form.validate_on_submit():
        prop.title = form.title.data
        prop.category = form.category.data
        prop.sub_category = form.sub_category.data
        prop.transaction_type = form.transaction_type.data
        prop.building_name = form.building_name.data
        prop.unit_number = form.unit_number.data
        prop.locality = form.locality.data
        prop.address = form.address.data
        prop.city = form.city.data
        prop.latitude = float(form.latitude.data) if form.latitude.data else None
        prop.longitude = float(form.longitude.data) if form.longitude.data else None
        prop.google_maps_link = form.google_maps_link.data
        prop.carpet_area = form.carpet_area.data or 0
        prop.builtup_area = form.builtup_area.data or 0
        prop.super_builtup_area = form.super_builtup_area.data or 0
        prop.plot_area_sqyd = form.plot_area_sqyd.data or 0
        prop.sale_price = form.sale_price.data or 0
        prop.rent_price = form.rent_price.data or 0
        prop.rate_per_sqft = form.rate_per_sqft.data or 0
        prop.security_deposit = form.security_deposit.data or 0
        prop.brokerage_terms = form.brokerage_terms.data
        prop.is_pre_leased = form.is_pre_leased.data or (form.category.data == 'Pre-Leased')
        prop.tenant_name = form.tenant_name.data
        prop.tenant_business_type = form.tenant_business_type.data
        prop.monthly_rental_income = form.monthly_rental_income.data or 0
        prop.roi_percentage = form.roi_percentage.data or 0
        prop.lock_in_period_months = form.lock_in_period_months.data or 0
        prop.escalation_percentage = form.escalation_percentage.data or 0
        prop.furnishing = form.furnishing.data
        prop.construction_type = form.construction_type.data
        prop.zone_type = form.zone_type.data
        prop.amenities = form.amenities.data
        prop.floors = form.floors.data
        prop.availability_status = form.availability_status.data
        prop.owner_id = form.owner_id.data if form.owner_id.data != 0 else None
        prop.assigned_to_id = form.assigned_to_id.data if form.assigned_to_id.data != 0 else None
        prop.description = form.description.data
        prop.internal_notes = form.internal_notes.data

        log_audit('UPDATE', 'Property', prop.id, f"Updated property {prop.property_code}")
        db.session.commit()
        flash('Property listing updated successfully!', 'success')
        return redirect(url_for('properties.detail', property_id=prop.id))

    return render_template('properties/property_form.html', form=form, title=f"Edit Property {prop.property_code}", property=prop)

@properties_bp.route('/<int:property_id>/archive', methods=['POST'])
@login_required
def archive_property(property_id):
    prop = Property.query.get_or_404(property_id)
    prop.is_archived = True
    log_audit('ARCHIVE', 'Property', prop.id, f"Archived property {prop.property_code}")
    db.session.commit()
    flash(f"Property {prop.property_code} archived.", 'info')
    return redirect(url_for('properties.index'))

# Map view of properties
@properties_bp.route('/map')
@login_required
def map_view():
    props = Property.query.filter_by(availability_status='Available', is_archived=False).all()
    map_properties = []
    for p in props:
        if p.latitude and p.longitude:
            map_properties.append({
                'id': p.id,
                'code': p.property_code,
                'title': p.title,
                'category': p.category,
                'sub_category': p.sub_category,
                'locality': p.locality,
                'tx_type': p.transaction_type,
                'price': f"₹ {p.sale_price or p.rent_price:,.2f}",
                'roi': f"{p.roi_percentage}% ROI" if p.is_pre_leased else "",
                'lat': p.latitude,
                'lng': p.longitude,
                'url': url_for('properties.detail', property_id=p.id)
            })
    return render_template('properties/map_view.html', properties=props, map_properties=map_properties)

# --- OWNERS & MANDATES ---

@properties_bp.route('/owners')
@login_required
def owners_list():
    owners = Owner.query.order_by(Owner.created_at.desc()).all()
    return render_template('properties/owners_list.html', owners=owners)

@properties_bp.route('/owners/new', methods=['GET', 'POST'])
@login_required
def create_owner():
    form = OwnerForm()
    if form.validate_on_submit():
        count = Owner.query.count() + 1
        owner_code = f"OWN-AHM-{count:04d}"
        
        owner = Owner(
            owner_code=owner_code,
            name=form.name.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            preferred_contact_method=form.preferred_contact_method.data,
            pan_or_id=form.pan_or_id.data,
            notes=form.notes.data
        )
        db.session.add(owner)
        db.session.commit()
        log_audit('CREATE', 'Owner', owner.id, f"Created owner {owner.owner_code} - {owner.name}")
        flash(f"Owner {owner.name} registered successfully!", 'success')
        return redirect(url_for('properties.owners_list'))

    return render_template('properties/owner_form.html', form=form, title="Register Property Owner")

@properties_bp.route('/mandates')
@login_required
def mandates_list():
    mandates = Mandate.query.order_by(Mandate.start_date.desc()).all()
    return render_template('properties/mandates_list.html', mandates=mandates)

@properties_bp.route('/mandates/new', methods=['GET', 'POST'])
@login_required
def create_mandate():
    form = MandateForm()
    owners = Owner.query.all()
    props = Property.query.filter_by(is_archived=False).all()
    form.owner_id.choices = [(o.id, f"{o.name} ({o.phone})") for o in owners]
    form.property_id.choices = [(0, '-- Unlinked / General --')] + [(p.id, f"{p.property_code} - {p.title}") for p in props]

    if form.validate_on_submit():
        count = Mandate.query.count() + 1
        mandate_code = f"MAN-AHM-{count:04d}"

        mandate = Mandate(
            mandate_code=mandate_code,
            owner_id=form.owner_id.data,
            property_id=form.property_id.data if form.property_id.data != 0 else None,
            mandate_type=form.mandate_type.data,
            asking_price=form.asking_price.data or 0,
            asking_rent=form.asking_rent.data or 0,
            start_date=form.start_date.data,
            expiry_date=form.expiry_date.data,
            terms=form.terms.data,
            status=form.status.data
        )
        db.session.add(mandate)
        db.session.commit()
        log_audit('CREATE', 'Mandate', mandate.id, f"Created mandate {mandate.mandate_code}")
        flash(f"Mandate {mandate.mandate_code} registered successfully!", 'success')
        return redirect(url_for('properties.mandates_list'))

    return render_template('properties/mandate_form.html', form=form, title="Record Owner Mandate")

# --- MATCHING MODULE ---
@properties_bp.route('/matching')
@login_required
def matching():
    requirements = Requirement.query.filter_by(status='Active').all()
    req_id = request.args.get('requirement_id', type=int)
    matches = []
    selected_req = None

    if req_id:
        selected_req = Requirement.query.get(req_id)
        if selected_req:
            generate_matches_for_requirement(selected_req.id)
            matches = PropertyMatch.query.filter_by(requirement_id=selected_req.id).order_by(PropertyMatch.match_score.desc()).all()
    elif requirements:
        selected_req = requirements[0]
        generate_matches_for_requirement(selected_req.id)
        matches = PropertyMatch.query.filter_by(requirement_id=selected_req.id).order_by(PropertyMatch.match_score.desc()).all()

    return render_template('properties/matching.html', requirements=requirements, selected_req=selected_req, matches=matches)

# --- PROPERTY APPROVAL WORKFLOW & EMPLOYEE SUBMISSIONS ---

@properties_bp.route('/approvals')
@login_required
def approvals():
    if not (current_user.is_admin() or current_user.is_manager()):
        abort(403)
    status_filter = request.args.get('status', 'Pending Approval').strip()
    query = Property.query.filter_by(is_archived=False)
    if status_filter != 'All':
        query = query.filter_by(approval_status=status_filter)
    pending_properties = query.order_by(Property.created_at.desc()).all()
    pending_count = Property.query.filter_by(approval_status='Pending Approval', is_archived=False).count()
    approved_count = Property.query.filter_by(approval_status='Approved', is_archived=False).count()
    rejected_count = Property.query.filter_by(approval_status='Rejected', is_archived=False).count()
    
    return render_template(
        'properties/approvals.html',
        properties=pending_properties,
        status_filter=status_filter,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count
    )

@properties_bp.route('/<int:property_id>/approve', methods=['POST'])
@login_required
def approve_property(property_id):
    if not (current_user.is_admin() or current_user.is_manager()):
        abort(403)
    prop = Property.query.get_or_404(property_id)
    prop.approval_status = 'Approved'
    prop.approved_by_id = current_user.id
    prop.approval_notes = request.form.get('approval_notes', 'Approved by administrator.')
    prop.availability_status = 'Available'
    db.session.commit()
    log_audit('APPROVE', 'Property', prop.id, f"Approved property {prop.property_code} - {prop.title}")
    flash(f"Property {prop.property_code} has been approved and is now live in inventory!", 'success')
    return redirect(request.referrer or url_for('properties.approvals'))

@properties_bp.route('/<int:property_id>/reject', methods=['POST'])
@login_required
def reject_property(property_id):
    if not (current_user.is_admin() or current_user.is_manager()):
        abort(403)
    prop = Property.query.get_or_404(property_id)
    prop.approval_status = 'Rejected'
    prop.approved_by_id = current_user.id
    prop.approval_notes = request.form.get('approval_notes', 'Listing does not meet criteria or missing documents.')
    db.session.commit()
    log_audit('REJECT', 'Property', prop.id, f"Rejected property {prop.property_code}: {prop.approval_notes}")
    flash(f"Property {prop.property_code} has been marked as Rejected.", 'warning')
    return redirect(request.referrer or url_for('properties.approvals'))

@properties_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_property():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Commercial')
        sub_category = request.form.get('sub_category', 'Office Space')
        transaction_type = request.form.get('transaction_type', 'Rent')
        building_name = request.form.get('building_name', '').strip()
        locality = request.form.get('locality', '').strip()
        address = request.form.get('address', '').strip()
        carpet_area = float(request.form.get('carpet_area') or 0)
        builtup_area = float(request.form.get('builtup_area') or 0)
        sale_price = float(request.form.get('sale_price') or 0)
        rent_price = float(request.form.get('rent_price') or 0)
        video_url = request.form.get('video_url', '').strip()
        google_maps_link = request.form.get('google_maps_link', '').strip()
        description = request.form.get('description', '').strip()
        internal_notes = request.form.get('internal_notes', '').strip()

        count = Property.query.count() + 1
        prop_code = f"PROP-SUB-{count:05d}"

        prop = Property(
            property_code=prop_code,
            title=title,
            category=category,
            sub_category=sub_category,
            transaction_type=transaction_type,
            building_name=building_name,
            locality=locality,
            address=address,
            carpet_area=carpet_area,
            builtup_area=builtup_area,
            sale_price=sale_price,
            rent_price=rent_price,
            video_url=video_url,
            google_maps_link=google_maps_link,
            description=description,
            internal_notes=internal_notes,
            approval_status='Pending Approval',
            availability_status='Available',
            submitted_by_id=current_user.id,
            assigned_to_id=current_user.id
        )
        db.session.add(prop)
        db.session.commit()

        # Handle image upload if provided
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(f"prop_{prop.id}_{int(datetime.now().timestamp())}_{file.filename}")
                upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'instance/uploads'), 'properties')
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                image_rec = PropertyImage(
                    property_id=prop.id,
                    image_path=os.path.join('properties', filename).replace('\\', '/'),
                    is_primary=True,
                    caption="Front View / Main"
                )
                db.session.add(image_rec)
                db.session.commit()

        log_audit('SUBMIT_PROPERTY', 'Property', prop.id, f"Employee {current_user.full_name} submitted property {prop.property_code}")
        flash(f"Property submission '{prop.title}' ({prop.property_code}) submitted for Admin Approval!", 'success')
        return redirect(url_for('properties.detail', property_id=prop.id))

    return render_template('properties/submit_property.html')

@properties_bp.route('/<int:property_id>/upload-image', methods=['POST'])
@login_required
def upload_property_image(property_id):
    prop = Property.query.get_or_404(property_id)
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            filename = secure_filename(f"prop_{prop.id}_{int(datetime.now().timestamp())}_{file.filename}")
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'instance/uploads'), 'properties')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            caption = request.form.get('caption', 'Property Photo')
            is_primary = (len(prop.images) == 0)
            img = PropertyImage(
                property_id=prop.id,
                image_path=os.path.join('properties', filename).replace('\\', '/'),
                caption=caption,
                is_primary=is_primary
            )
            db.session.add(img)
            db.session.commit()
            flash('Image uploaded successfully!', 'success')
    return redirect(url_for('properties.detail', property_id=prop.id))

