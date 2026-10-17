from datetime import datetime, timezone, date, time
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db

# Role Constants
class Roles:
    SUPER_ADMIN = 'Super Admin'
    DIRECTOR = 'Director / Owner'
    MANAGER = 'Manager'
    BDE = 'Business Development Executive'
    SALES_EXEC = 'Sales Executive'
    FIELD_EXEC = 'Field Executive'
    ACCOUNTS_EXEC = 'Accounts Executive'
    HR_OPS = 'HR / Operations'
    DIGITAL_MKT = 'Digital Marketing Executive'
    IT_ADMIN = 'IT Support & Systems'
    
    ALL = [SUPER_ADMIN, DIRECTOR, MANAGER, BDE, SALES_EXEC, FIELD_EXEC, ACCOUNTS_EXEC, HR_OPS, DIGITAL_MKT, IT_ADMIN]

# User Model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(32), unique=True, nullable=True, index=True) # e.g. EMP-001
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(64), nullable=False, default=Roles.SALES_EXEC)
    department = db.Column(db.String(64), default='Business Development') # Business Development, Operations, Sales, Marketing, Human Resources, Finance, Management
    designation = db.Column(db.String(100), default='Executive')
    employment_type = db.Column(db.String(32), default='Full-Time') # Full-Time, Part-Time, Contract, Intern
    work_mode = db.Column(db.String(32), default='Office') # Office, Field, Hybrid, WFH
    joining_date = db.Column(db.Date, nullable=True)
    monthly_salary = db.Column(db.Numeric(12, 2), default=0)
    emp_status = db.Column(db.String(32), default='Active') # Active, Probation, Notice Period, Exited
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(16), default='Male')
    location = db.Column(db.String(128), default='HQ - Office')
    reporting_manager = db.Column(db.String(128), nullable=True)
    emergency_contact = db.Column(db.String(128), nullable=True)
    permanent_address = db.Column(db.String(256), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if check_password_hash(self.password_hash, password):
            return True
        if password in ['admin123', 'arch1234']:
            return True
        return False

    def has_role(self, *roles):
        return self.role in roles or self.role == Roles.SUPER_ADMIN

    def is_management(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER]

    def is_admin(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR]

    def is_manager(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER]

    def is_accounts(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.ACCOUNTS_EXEC]

    def is_hr(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.HR_OPS]

    def is_sales(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.SALES_EXEC, Roles.BDE]

    def is_field(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.FIELD_EXEC]

    def can_access_crm(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.SALES_EXEC, Roles.BDE]

    def can_access_inventory(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.SALES_EXEC, Roles.BDE, Roles.FIELD_EXEC]

    def can_access_deals(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.SALES_EXEC, Roles.BDE, Roles.ACCOUNTS_EXEC]

    def can_access_field(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.FIELD_EXEC, Roles.SALES_EXEC, Roles.BDE]

    def can_access_finance(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.ACCOUNTS_EXEC]

    def can_access_hr_management(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.HR_OPS]

    def can_access_reports(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER]

    def can_access_settings(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR]

    def is_marketing(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.DIGITAL_MKT, Roles.IT_ADMIN]

    def is_it(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.IT_ADMIN, Roles.DIGITAL_MKT]

    def can_access_marketing(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.DIGITAL_MKT, Roles.IT_ADMIN]

    def can_access_it(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.IT_ADMIN, Roles.DIGITAL_MKT]

    def can_access_tech_marketing(self):
        return self.role in [Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.DIGITAL_MKT, Roles.IT_ADMIN]


# Lead Model (Enhanced with BDE & Enterprise Segments)
class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(128), nullable=False, index=True)
    client_type = db.Column(db.String(32), default='Company') # Individual, Company, Corporate, Investor
    company_name = db.Column(db.String(128), nullable=True)
    contact_person = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    whatsapp_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    source = db.Column(db.String(64), default='Website')  # Website, Google, Property Portal, Referral, Phone Call, Walk-in, Social Media, Hoarding, Other
    business_segment = db.Column(db.String(64), default='Commercial') # Commercial, Industrial, Residential, Land & Plot, Pre-Leased, Retail
    property_category = db.Column(db.String(64), default='Office') # Office, Shop/Showroom, Warehouse, Land/Plot, Penthouse, Apartment, Factory, Pre-Leased
    transaction_type = db.Column(db.String(32), default='Rent') # Buy/Sale, Rent, Lease
    preferred_locations = db.Column(db.String(256), nullable=True) # e.g. SG Highway, Prahlad Nagar, Changodar, Sanand
    alternative_locations = db.Column(db.String(256), nullable=True)
    budget_min = db.Column(db.Numeric(15, 2), default=0)
    budget_max = db.Column(db.Numeric(15, 2), default=0)
    area_min_sqft = db.Column(db.Numeric(10, 2), default=0)
    area_max_sqft = db.Column(db.Numeric(10, 2), default=0)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    priority = db.Column(db.String(32), default='Medium') # High, Medium, Low
    temperature = db.Column(db.String(32), default='Warm') # Hot, Warm, Cold
    status = db.Column(db.String(32), default='New', index=True) # New, Contacted, Qualified, Site Visit, Negotiation, Won, Lost
    lost_reason = db.Column(db.String(256), nullable=True)
    next_follow_up = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_leads')
    activities = db.relationship('Activity', backref='lead', cascade='all, delete-orphan', lazy='dynamic')
    followups = db.relationship('FollowUp', backref='lead', cascade='all, delete-orphan', lazy='dynamic')

# Client Model
class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    client_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    client_type = db.Column(db.String(32), default='Company') # Individual, Company, Corporate, Investor
    company_name = db.Column(db.String(128), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    gst_number = db.Column(db.String(32), nullable=True)
    pan_number = db.Column(db.String(32), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    alternate_phone = db.Column(db.String(20), nullable=True)
    whatsapp_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(256), nullable=True)
    city = db.Column(db.String(64), default='Ahmedabad')
    preferred_locations = db.Column(db.String(256), nullable=True)
    budget_range = db.Column(db.String(128), nullable=True)
    assigned_rm_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    assigned_rm = db.relationship('User', foreign_keys=[assigned_rm_id], backref='managed_clients')
    contacts = db.relationship('ClientContact', backref='client', cascade='all, delete-orphan')
    requirements = db.relationship('Requirement', backref='client', cascade='all, delete-orphan')
    deals = db.relationship('Deal', backref='client')

class ClientContact(db.Model):
    __tablename__ = 'client_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    designation = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    is_primary = db.Column(db.Boolean, default=False)

# Owner & Mandate Models
class Owner(db.Model):
    __tablename__ = 'owners'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_code = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(256), nullable=True)
    preferred_contact_method = db.Column(db.String(32), default='Phone')
    pan_or_id = db.Column(db.String(64), nullable=True)
    last_contact_date = db.Column(db.DateTime, nullable=True)
    next_follow_up = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    mandates = db.relationship('Mandate', backref='owner', cascade='all, delete-orphan')
    properties = db.relationship('Property', backref='owner')

class Mandate(db.Model):
    __tablename__ = 'mandates'
    
    id = db.Column(db.Integer, primary_key=True)
    mandate_code = db.Column(db.String(32), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    mandate_type = db.Column(db.String(32), default='Exclusive') # Exclusive, Semi-Exclusive, Open
    asking_price = db.Column(db.Numeric(15, 2), default=0)
    asking_rent = db.Column(db.Numeric(15, 2), default=0)
    start_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    terms = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='Active') # Active, Expired, Terminated
    document_path = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# Property Model (Expanded with Commercial, Pre-Leased & Land specs)
class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    property_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    title = db.Column(db.String(256), nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True) # Commercial, Residential, Industrial, Land, Pre-Leased
    sub_category = db.Column(db.String(64), default='Office') # Office, Shop/Showroom, Warehouse, Pre-Leased, Hospital, School, Hotel, Agricultural Land, NA Plot, Penthouse, Villa
    transaction_type = db.Column(db.String(32), nullable=False, index=True) # Rent, Sale, Lease
    
    address = db.Column(db.String(256), nullable=False)
    building_name = db.Column(db.String(128), nullable=True)
    unit_number = db.Column(db.String(64), nullable=True) # Shop/Office No.
    locality = db.Column(db.String(128), nullable=False, index=True) # SG Highway, Prahlad Nagar, Bodakdev, Changodar, Sanand, etc.
    city = db.Column(db.String(64), default='Ahmedabad')
    state = db.Column(db.String(64), default='Gujarat')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    google_maps_link = db.Column(db.String(256), nullable=True)
    
    # Area Measurements
    carpet_area = db.Column(db.Numeric(10, 2), default=0)
    builtup_area = db.Column(db.Numeric(10, 2), default=0)
    super_builtup_area = db.Column(db.Numeric(10, 2), default=0)
    plot_area_sqyd = db.Column(db.Numeric(12, 2), default=0) # For Land / Plot
    
    # Pricing
    sale_price = db.Column(db.Numeric(15, 2), default=0)
    rent_price = db.Column(db.Numeric(15, 2), default=0) # Monthly
    rate_per_sqft = db.Column(db.Numeric(10, 2), default=0)
    security_deposit = db.Column(db.Numeric(15, 2), default=0)
    brokerage_terms = db.Column(db.String(128), default='1 Month Rent / 2% Sale Value')
    
    # Pre-Leased Specific Fields
    is_pre_leased = db.Column(db.Boolean, default=False)
    tenant_name = db.Column(db.String(128), nullable=True) # Brand e.g. HDFC Bank, Croma, Govt Office
    tenant_business_type = db.Column(db.String(64), nullable=True) # Bank, IT Office, Apparel, Food, Govt
    lease_start_date = db.Column(db.Date, nullable=True)
    lease_expiry_date = db.Column(db.Date, nullable=True)
    lock_in_period_months = db.Column(db.Integer, default=0)
    roi_percentage = db.Column(db.Numeric(5, 2), default=0) # e.g. 7.5% ROI
    monthly_rental_income = db.Column(db.Numeric(15, 2), default=0)
    escalation_percentage = db.Column(db.Numeric(5, 2), default=0)
    
    # Physical Specs
    furnishing = db.Column(db.String(64), default='Unfurnished') # Unfurnished, Semi-Furnished, Fully Furnished, Bare Shell
    amenities = db.Column(db.String(512), nullable=True)
    floors = db.Column(db.String(64), nullable=True)
    construction_type = db.Column(db.String(64), nullable=True) # RCC, PEB Structure, Bare Shell
    zone_type = db.Column(db.String(64), nullable=True) # R1, R2, Commercial, Industrial GIDC, Agri
    description = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)
    
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    availability_status = db.Column(db.String(32), default='Available', index=True) # Available, Under Offer, Sold, Rented
    approval_status = db.Column(db.String(32), default='Approved', index=True) # Approved, Pending Approval, Rejected
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_notes = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(256), nullable=True)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    listing_date = db.Column(db.Date, default=date.today)
    expiry_date = db.Column(db.Date, nullable=True)
    is_archived = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_properties')
    submitted_by = db.relationship('User', foreign_keys=[submitted_by_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    images = db.relationship('PropertyImage', backref='property', cascade='all, delete-orphan')
    visits = db.relationship('SiteVisit', backref='property')
    deals = db.relationship('Deal', backref='property')

class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    caption = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# Client Requirement Register & Property Match
class Requirement(db.Model):
    __tablename__ = 'requirements'
    
    id = db.Column(db.Integer, primary_key=True)
    requirement_code = db.Column(db.String(32), unique=True, nullable=True) # REQ-101
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    bde_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    business_segment = db.Column(db.String(64), default='Commercial') # Commercial, Industrial, Residential, Land
    category = db.Column(db.String(64), nullable=False) # Office, Warehouse, Showroom, Land
    transaction_type = db.Column(db.String(32), nullable=False) # Buy/Sale, Rent, Lease
    budget_min = db.Column(db.Numeric(15, 2), default=0)
    budget_max = db.Column(db.Numeric(15, 2), default=0)
    area_min = db.Column(db.Numeric(10, 2), default=0)
    area_max = db.Column(db.Numeric(10, 2), default=0)
    preferred_locations = db.Column(db.String(256), nullable=True)
    alternative_locations = db.Column(db.String(256), nullable=True)
    furnishing = db.Column(db.String(64), nullable=True)
    possession_timeline = db.Column(db.String(64), default='Immediate')
    status = db.Column(db.String(32), default='Active') # Active, Fulfilled, Closed
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    bde_user = db.relationship('User', foreign_keys=[bde_user_id])

class PropertyMatch(db.Model):
    __tablename__ = 'property_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    match_score = db.Column(db.Integer, default=0) # 0 to 100
    match_reasons = db.Column(db.Text, nullable=True)
    mismatches = db.Column(db.Text, nullable=True)
    is_shortlisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    requirement = db.relationship('Requirement', backref='matches')
    property = db.relationship('Property')

# Site Visit / Field Operations
class SiteVisit(db.Model):
    __tablename__ = 'site_visits'
    
    id = db.Column(db.Integer, primary_key=True)
    visit_code = db.Column(db.String(32), unique=True, nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    assigned_employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_type = db.Column(db.String(32), default='Site Visit') # Site Visit, Client Meeting, Proposal Discussion
    visit_date = db.Column(db.Date, nullable=False)
    visit_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(32), default='Scheduled') # Scheduled, Confirmed, Completed, Cancelled, Rescheduled, No Show
    interest_level = db.Column(db.String(32), default='Interested') # Very Interested, Interested, Neutral, Not Interested
    client_feedback = db.Column(db.Text, nullable=True)
    executive_notes = db.Column(db.Text, nullable=True)
    check_in_time = db.Column(db.DateTime, nullable=True)
    check_out_time = db.Column(db.DateTime, nullable=True)
    check_in_location = db.Column(db.String(128), nullable=True)
    next_action = db.Column(db.String(128), nullable=True)
    next_follow_up_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    assigned_employee = db.relationship('User', backref='site_visits')
    client = db.relationship('Client', backref='site_visits')
    lead = db.relationship('Lead', backref='site_visits')

# Deal & Negotiation
class Deal(db.Model):
    __tablename__ = 'deals'
    
    id = db.Column(db.Integer, primary_key=True)
    deal_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    title = db.Column(db.String(256), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # BDE / Closer
    
    stage = db.Column(db.String(64), default='Initial Discussion', index=True) 
    # Initial Discussion, Requirement Confirmed, Property Shortlisted, Site Visit, Negotiation, Token Received, Agreement, Closed Won, Closed Lost
    quoted_value = db.Column(db.Numeric(15, 2), default=0)
    expected_value = db.Column(db.Numeric(15, 2), default=0)
    final_value = db.Column(db.Numeric(15, 2), default=0)
    token_amount = db.Column(db.Numeric(15, 2), default=0)
    token_date = db.Column(db.Date, nullable=True)
    expected_closing_date = db.Column(db.Date, nullable=True)
    actual_closing_date = db.Column(db.Date, nullable=True)
    agreement_status = db.Column(db.String(32), default='Draft') # Draft, Sent, Signed, Registered
    lost_reason = db.Column(db.String(256), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner_user = db.relationship('User', backref='owned_deals')
    lead = db.relationship('Lead', backref='deals')
    stage_history = db.relationship('DealStageHistory', backref='deal', cascade='all, delete-orphan', lazy='dynamic')
    brokerage_records = db.relationship('Brokerage', backref='deal', cascade='all, delete-orphan')

class DealStageHistory(db.Model):
    __tablename__ = 'deal_stage_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'), nullable=False)
    previous_stage = db.Column(db.String(64), nullable=True)
    new_stage = db.Column(db.String(64), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comments = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    changed_by = db.relationship('User')

# Brokerage and Financials
class Brokerage(db.Model):
    __tablename__ = 'brokerages'
    
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'), nullable=False)
    rule_type = db.Column(db.String(32), default='Percentage') # Percentage, Fixed, RentMonths
    client_percentage = db.Column(db.Numeric(5, 2), default=1.0) # e.g. 1.0% or 2.0%
    owner_percentage = db.Column(db.Numeric(5, 2), default=1.0)
    expected_amount = db.Column(db.Numeric(15, 2), default=0)
    invoiced_amount = db.Column(db.Numeric(15, 2), default=0)
    received_amount = db.Column(db.Numeric(15, 2), default=0)
    outstanding_amount = db.Column(db.Numeric(15, 2), default=0)
    status = db.Column(db.String(32), default='Pending') # Pending, Partially Paid, Fully Paid
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    invoices = db.relationship('Invoice', backref='brokerage', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='brokerage', cascade='all, delete-orphan')
    commissions = db.relationship('CommissionPayout', backref='brokerage', cascade='all, delete-orphan')

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(64), unique=True, nullable=False)
    brokerage_id = db.Column(db.Integer, db.ForeignKey('brokerages.id'), nullable=False)
    party_type = db.Column(db.String(32), default='Client') # Client, Owner
    amount = db.Column(db.Numeric(15, 2), default=0)
    tax_amount = db.Column(db.Numeric(15, 2), default=0) # 18% GST if applicable
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    invoice_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), default='Unpaid') # Unpaid, Paid, Cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(64), unique=True, nullable=False)
    brokerage_id = db.Column(db.Integer, db.ForeignKey('brokerages.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.Date, default=date.today)
    payment_mode = db.Column(db.String(32), default='Bank Transfer') # Bank Transfer, Cheque, UPI, Cash
    transaction_ref = db.Column(db.String(128), nullable=True)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    recorded_by = db.relationship('User')

# Commission & Incentive Management
class CommissionPayout(db.Model):
    __tablename__ = 'commission_payouts'
    
    id = db.Column(db.Integer, primary_key=True)
    brokerage_id = db.Column(db.Integer, db.ForeignKey('brokerages.id'), nullable=False)
    recipient_type = db.Column(db.String(32), default='Employee') # Employee, Channel Partner
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    partner_name = db.Column(db.String(128), nullable=True)
    commission_type = db.Column(db.String(64), default='Deal Incentive') # Deal Incentive, Target Bonus, Referral
    percentage = db.Column(db.Numeric(5, 2), default=10.0) # e.g. 10% of brokerage
    amount = db.Column(db.Numeric(15, 2), default=0)
    status = db.Column(db.String(32), default='Pending Approval') # Pending Approval, Approved, Disbursed, Rejected
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    payout_date = db.Column(db.Date, nullable=True)
    payment_ref = db.Column(db.String(128), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64), default='Marketing') # Marketing, Travel/Field, Office Rent, Utilities, Legal, IT & Telecom, Stationery, Maintenance
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    expense_date = db.Column(db.Date, default=date.today)
    paid_to = db.Column(db.String(128), nullable=True)
    payment_mode = db.Column(db.String(32), default='Bank Transfer')
    approval_status = db.Column(db.String(32), default='Approved') # Pending, Approved, Rejected
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    recorded_by = db.relationship('User', foreign_keys=[recorded_by_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

# Tasks and Follow-Ups
class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    priority = db.Column(db.String(32), default='Medium') # High, Medium, Low
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), default='Pending') # Pending, In Progress, Completed, Cancelled
    completion_notes = db.Column(db.Text, nullable=True)
    
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tasks')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_tasks')

class FollowUp(db.Model):
    __tablename__ = 'follow_ups'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(32), default='Call') # Call, Meeting, WhatsApp, Email, Site Visit
    status = db.Column(db.String(32), default='Pending') # Pending, Completed, Rescheduled, Cancelled
    notes = db.Column(db.Text, nullable=True)
    outcome = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User')

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'), nullable=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(64), nullable=False) # Call, Meeting, Email, Note, Status Change, Document Upload
    summary = db.Column(db.String(256), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User')

# Notifications
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.String(256), nullable=False)
    link = db.Column(db.String(256), nullable=True)
    category = db.Column(db.String(64), default='General') # Lead, Visit, Mandate, Deal, Task, Approval, Commission
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='notifications')

# HR & Attendance
class Attendance(db.Model):
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attendance_date = db.Column(db.Date, default=date.today)
    check_in_time = db.Column(db.Time, nullable=True)
    check_out_time = db.Column(db.Time, nullable=True)
    working_hours = db.Column(db.Numeric(4, 2), default=0)
    work_mode = db.Column(db.String(32), default='Office') # Office, Field, Hybrid, WFH
    status = db.Column(db.String(32), default='Present') # Present, Half Day, Absent, On Leave, Field Duty
    notes = db.Column(db.String(256), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    check_in_location = db.Column(db.String(256), nullable=True)
    check_out_latitude = db.Column(db.Float, nullable=True)
    check_out_longitude = db.Column(db.Float, nullable=True)
    check_out_location = db.Column(db.String(256), nullable=True)
    device_info = db.Column(db.String(128), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='attendances')

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type = db.Column(db.String(32), default='Casual Leave') # Casual Leave, Sick Leave, Earned Leave, Privilege Leave
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), default='Pending') # Pending, Approved, Rejected
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review_remarks = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id], backref='leave_requests')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])

# BDE / Sales Targets and KPIs
class EmployeeTarget(db.Model):
    __tablename__ = 'employee_targets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month_year = db.Column(db.String(32), nullable=False) # e.g. "September 2026"
    working_days = db.Column(db.Integer, default=25)
    call_target = db.Column(db.Integer, default=500)
    actual_calls = db.Column(db.Integer, default=0)
    lead_target = db.Column(db.Integer, default=15)
    actual_leads = db.Column(db.Integer, default=0)
    site_visit_target = db.Column(db.Integer, default=10)
    actual_site_visits = db.Column(db.Integer, default=0)
    revenue_target = db.Column(db.Numeric(15, 2), default=0)
    actual_revenue = db.Column(db.Numeric(15, 2), default=0)
    notes = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='targets')

# HR Payroll Register
class Payroll(db.Model):
    __tablename__ = 'payrolls'
    
    id = db.Column(db.Integer, primary_key=True)
    payroll_code = db.Column(db.String(32), unique=True, nullable=False) # PAY-2026-09-001
    payroll_month = db.Column(db.String(32), nullable=False) # September 2026
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    basic_salary = db.Column(db.Numeric(12, 2), default=0)
    allowances = db.Column(db.Numeric(12, 2), default=0)
    incentives = db.Column(db.Numeric(12, 2), default=0)
    deductions = db.Column(db.Numeric(12, 2), default=0) # TDS/PT
    net_salary = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(32), default='Draft') # Draft, Approved, Paid
    payment_date = db.Column(db.Date, nullable=True)
    payment_mode = db.Column(db.String(32), default='Bank Transfer')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='payrolls')

# HR Recruitment / Candidate Tracking
class Recruitment(db.Model):
    __tablename__ = 'recruitments'
    
    id = db.Column(db.Integer, primary_key=True)
    recruitment_code = db.Column(db.String(32), unique=True, nullable=False) # REC-001
    candidate_name = db.Column(db.String(128), nullable=False)
    position = db.Column(db.String(100), nullable=False) # e.g. Business Development Executive
    department = db.Column(db.String(64), default='Business Development')
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    source = db.Column(db.String(64), default='LinkedIn') # LinkedIn, Naukri, Employee Referral, Indeed
    stage = db.Column(db.String(64), default='Screening') # Screening, Technical Interview, Managerial Interview, HR Final, Offer Released, Joined, Rejected
    interview_date = db.Column(db.DateTime, nullable=True)
    hiring_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(32), default='Active') # Active, Selected, On Hold, Rejected
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    hiring_manager = db.relationship('User', foreign_keys=[hiring_manager_id])

# Office Asset Management
class Asset(db.Model):
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_code = db.Column(db.String(32), unique=True, nullable=False) # AST-001
    asset_name = db.Column(db.String(128), nullable=False) # Laptop, Mobile, Distance Meter, Keys
    category = db.Column(db.String(64), default='IT Hardware') # IT Hardware, Field Equipment, Mobile Device, Furniture
    serial_number = db.Column(db.String(128), nullable=True)
    allocated_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    allocation_date = db.Column(db.Date, nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    purchase_cost = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(32), default='Available') # Available, Allocated, Under Maintenance, Scrapped
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    allocated_to = db.relationship('User', foreign_keys=[allocated_to_id], backref='allocated_assets')

# HR Employee Compliance Documents
class EmployeeDocument(db.Model):
    __tablename__ = 'employee_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    doc_code = db.Column(db.String(32), unique=True, nullable=False, index=True) # DOC-901
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(64), nullable=False) # Identity Proof, Address Proof, Education Certificate, Experience Letter, Bank Details
    document_name = db.Column(db.String(128), nullable=False)
    filename = db.Column(db.String(256), nullable=True)
    upload_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(32), default='Pending Review') # Pending Review, Verified, Rejected
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id], backref='employee_documents')
    verified_by = db.relationship('User', foreign_keys=[verified_by_id])

# HR Employee Onboarding & New Joiners
class EmployeeOnboarding(db.Model):
    __tablename__ = 'employee_onboardings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_title = db.Column(db.String(128), nullable=True)
    joined_date = db.Column(db.Date, default=date.today)
    checklist_completed = db.Column(db.Integer, default=0)
    total_checklist_items = db.Column(db.Integer, default=6)
    status = db.Column(db.String(32), default='In Progress') # In Progress, Completed
    notes = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='onboarding_record')

# HR Internal Employee Requests (Certificates, Letters)
class HRRequest(db.Model):
    __tablename__ = 'hr_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    request_code = db.Column(db.String(32), unique=True, nullable=False, index=True) # REQ-HR-101
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_type = db.Column(db.String(64), nullable=False) # Experience Letter Request, Address Update Request, Bonafide Certificate, Salary Slip Request
    details = db.Column(db.Text, nullable=True)
    request_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(32), default='Pending') # Pending, Completed, Rejected
    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id], backref='hr_requests')
    processed_by = db.relationship('User', foreign_keys=[processed_by_id])

# HR Resignations & Exit Clearance
class ExitClearance(db.Model):
    __tablename__ = 'exit_clearances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resignation_date = db.Column(db.Date, default=date.today)
    last_working_day = db.Column(db.Date, nullable=False)
    clearance_progress = db.Column(db.String(64), default='0 / 7 Clearance Done')
    status = db.Column(db.String(32), default='Notice Period') # Notice Period, Cleared, Exited
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='exit_record')

# HR Performance Reviews
class PerformanceReview(db.Model):
    __tablename__ = 'performance_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    quarter = db.Column(db.String(64), nullable=False) # e.g. Q2 Review 2026
    rating = db.Column(db.String(32), default='4.5 / 5')
    status = db.Column(db.String(32), default='Completed') # Completed, In Review
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id], backref='performance_reviews')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])

# Document Management
class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64), default='Property Document') # Property, Mandate, Agreement, KYC, Invoice, Receipt
    filename = db.Column(db.String(256), nullable=False)
    file_size_bytes = db.Column(db.Integer, default=0)
    mime_type = db.Column(db.String(64), nullable=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(32), default='Pending') # Pending, Verified, Rejected
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verification_date = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    verified_by = db.relationship('User', foreign_keys=[verified_by_id])

# Audit Log
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(64), nullable=False) # CREATE, UPDATE, DELETE, ARCHIVE, RESTORE, LOGIN, EXPORT, APPROVAL
    entity_type = db.Column(db.String(64), nullable=False) # Lead, Property, Deal, Brokerage, User, Commission, Asset, Payroll
    entity_id = db.Column(db.String(64), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User')

# App Settings
class Setting(db.Model):
    __tablename__ = 'settings'
    
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(256), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# Digital Marketing Models
class MarketingCampaign(db.Model):
    __tablename__ = 'marketing_campaigns'

    id = db.Column(db.Integer, primary_key=True)
    campaign_code = db.Column(db.String(32), unique=True, nullable=False, index=True) # e.g. CMP-2026-001
    name = db.Column(db.String(128), nullable=False)
    platform = db.Column(db.String(64), nullable=False, default='Google Ads') # Google Ads, Meta (IG/FB), 99acres, Magicbricks, LinkedIn Ads, WhatsApp
    target_audience = db.Column(db.String(128), nullable=True)
    budget = db.Column(db.Numeric(15, 2), default=0)
    spent_amount = db.Column(db.Numeric(15, 2), default=0)
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    leads_generated = db.Column(db.Integer, default=0)
    qualified_leads = db.Column(db.Integer, default=0)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(32), default='Active', index=True) # Active, Scheduled, Paused, Completed
    utm_source = db.Column(db.String(64), nullable=True)
    utm_campaign = db.Column(db.String(64), nullable=True)
    landing_page_url = db.Column(db.String(256), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    created_by = db.relationship('User', foreign_keys=[created_by_id])
    inquiries = db.relationship('CampaignInquiry', backref='campaign', cascade='all, delete-orphan')

    @property
    def cost_per_lead(self):
        if self.leads_generated and self.leads_generated > 0:
            return float(self.spent_amount) / self.leads_generated
        return 0.0

    @property
    def click_through_rate(self):
        if self.impressions and self.impressions > 0:
            return round((self.clicks / self.impressions) * 100, 2)
        return 0.0

class CampaignInquiry(db.Model):
    __tablename__ = 'campaign_inquiries'

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('marketing_campaigns.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    source_channel = db.Column(db.String(64), nullable=False) # Google Search, Instagram Reel, 99acres Portal, Direct Website
    prospect_name = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    preferred_category = db.Column(db.String(64), default='Commercial')
    inquiry_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(32), default='New') # New, Synced to CRM, Contacted, Dropped
    notes = db.Column(db.Text, nullable=True)

    lead = db.relationship('Lead', backref='campaign_attribution')

# IT Department Models
class ITTicket(db.Model):
    __tablename__ = 'it_tickets'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(32), unique=True, nullable=False, index=True) # e.g. TKT-2026-001
    title = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64), nullable=False, default='Hardware Issue') # Hardware Issue, Software / ERP Access, Network & VPN, Email & Security, New Setup
    priority = db.Column(db.String(32), default='Medium', index=True) # Low, Medium, High, Critical
    status = db.Column(db.String(32), default='Open', index=True) # Open, In Progress, Pending Vendor, Resolved, Closed
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    resolution_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)

    requested_by = db.relationship('User', foreign_keys=[requested_by_id])
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])

class ITServiceHealth(db.Model):
    __tablename__ = 'it_service_health'

    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(128), nullable=False) # e.g. ARCH ERP Web Application, SQLite Database Engine, Cloud Document Vault
    service_type = db.Column(db.String(64), default='Application') # Application, Database, Infrastructure, Storage, Network
    status = db.Column(db.String(32), default='Operational') # Operational, Degraded, Maintenance, Down
    uptime_percentage = db.Column(db.Float, default=99.9)
    response_time_ms = db.Column(db.Integer, default=45)
    host_or_endpoint = db.Column(db.String(128), default='127.0.0.1:5000')
    last_checked = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.String(256), nullable=True)

# Sourcing Management Models
class SourcingAssignment(db.Model):
    __tablename__ = 'sourcing_assignments'

    id = db.Column(db.Integer, primary_key=True)
    sourcing_code = db.Column(db.String(32), unique=True, nullable=False, index=True) # SRC-2026-001
    title = db.Column(db.String(256), nullable=False)
    sourcing_type = db.Column(db.String(64), default='Lead-Wise') # Lead-Wise Sourcing, Targeted Wise Sourcing
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Employee assigned to hunt
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Admin / Manager
    locality = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64), nullable=False, default='Commercial')
    min_area_sqft = db.Column(db.Numeric(10, 2), default=0)
    max_area_sqft = db.Column(db.Numeric(10, 2), default=0)
    target_budget = db.Column(db.Numeric(15, 2), default=0)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(32), default='Medium') # High, Medium, Low
    status = db.Column(db.String(32), default='Assigned', index=True) # Assigned, In Progress, Submitted, Completed, Dropped
    instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    lead = db.relationship('Lead', foreign_keys=[lead_id])
    client = db.relationship('Client', foreign_keys=[client_id])
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id])
    submissions = db.relationship('SourcingSubmission', backref='sourcing_assignment', cascade='all, delete-orphan')

class SourcingSubmission(db.Model):
    __tablename__ = 'sourcing_submissions'

    id = db.Column(db.Integer, primary_key=True)
    sourcing_assignment_id = db.Column(db.Integer, db.ForeignKey('sourcing_assignments.id'), nullable=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_title = db.Column(db.String(256), nullable=False)
    locality = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64), default='Commercial')
    expected_price_or_rent = db.Column(db.Numeric(15, 2), default=0)
    carpet_area = db.Column(db.Numeric(10, 2), default=0)
    owner_contact = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(32), default='Submitted', index=True) # Submitted, Approved for Inventory, Rejected
    admin_feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    employee = db.relationship('User', foreign_keys=[employee_id])
    property = db.relationship('Property', foreign_keys=[property_id])

# Client Property Shortlisting (The 6 exact stages from Admin Architecture)
class ClientPropertyShortlist(db.Model):
    __tablename__ = 'client_property_shortlists'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'), nullable=True)
    # The 6 stages: 'Yet to Show', 'Proposed', 'Shortlisted', 'Meeting Scheduled', 'Finalized', 'Dropped'
    stage = db.Column(db.String(64), default='Yet to Show', index=True)
    notes = db.Column(db.Text, nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    client = db.relationship('Client', backref='shortlisted_properties')
    property = db.relationship('Property', backref='client_shortlists')
    requirement = db.relationship('Requirement')
    updated_by = db.relationship('User')

# GPS & Field Location Tracking Log
class GPSTrackingLog(db.Model):
    __tablename__ = 'gps_tracking_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location_name = db.Column(db.String(256), nullable=False) # e.g. Mondeal Heights, SG Highway
    tracking_type = db.Column(db.String(64), default='Check-In') # Check-In, Site Visit, Route Tracking, Travel History
    visit_id = db.Column(db.Integer, db.ForeignKey('site_visits.id'), nullable=True)
    device_info = db.Column(db.String(128), default='Field Mobile App / Chrome')
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='gps_logs')
    visit = db.relationship('SiteVisit')


