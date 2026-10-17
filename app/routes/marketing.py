from datetime import date, datetime, timezone
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import MarketingCampaign, CampaignInquiry, Lead, Roles
from app.services.auth_service import marketing_required, log_audit
from app.extensions import db

marketing_bp = Blueprint('marketing', __name__)

@marketing_bp.before_request
def check_marketing_access():
    if current_user.is_authenticated and not current_user.can_access_marketing():
        abort(403)

@marketing_bp.route('/')
@login_required
@marketing_required
def index():
    campaigns = MarketingCampaign.query.order_by(MarketingCampaign.created_at.desc()).all()
    inquiries = CampaignInquiry.query.order_by(CampaignInquiry.inquiry_date.desc()).limit(15).all()

    total_campaigns = len(campaigns)
    active_campaigns = sum(1 for c in campaigns if c.status == 'Active')
    total_budget = sum(c.budget for c in campaigns if c.budget) or Decimal('0')
    total_spent = sum(c.spent_amount for c in campaigns if c.spent_amount) or Decimal('0')
    total_leads = sum(c.leads_generated for c in campaigns if c.leads_generated) or 0
    total_impressions = sum(c.impressions for c in campaigns if c.impressions) or 0
    total_clicks = sum(c.clicks for c in campaigns if c.clicks) or 0

    avg_cpl = (float(total_spent) / total_leads) if total_leads > 0 else 0.0
    overall_ctr = ((total_clicks / total_impressions) * 100) if total_impressions > 0 else 0.0

    # Platform breakdown
    platform_stats = {}
    for c in campaigns:
        p = c.platform
        if p not in platform_stats:
            platform_stats[p] = {'count': 0, 'spent': Decimal('0'), 'leads': 0}
        platform_stats[p]['count'] += 1
        platform_stats[p]['spent'] += (c.spent_amount or Decimal('0'))
        platform_stats[p]['leads'] += (c.leads_generated or 0)

    return render_template(
        'marketing/index.html',
        campaigns=campaigns[:6],
        inquiries=inquiries,
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_budget=total_budget,
        total_spent=total_spent,
        total_leads=total_leads,
        avg_cpl=avg_cpl,
        overall_ctr=overall_ctr,
        platform_stats=platform_stats
    )

@marketing_bp.route('/campaigns')
@login_required
@marketing_required
def campaigns_list():
    status_filter = request.args.get('status', '').strip()
    platform_filter = request.args.get('platform', '').strip()

    query = MarketingCampaign.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if platform_filter:
        query = query.filter_by(platform=platform_filter)

    campaigns = query.order_by(MarketingCampaign.created_at.desc()).all()
    return render_template('marketing/campaigns_list.html', campaigns=campaigns, status_filter=status_filter, platform_filter=platform_filter)

@marketing_bp.route('/campaigns/create', methods=['GET', 'POST'])
@login_required
@marketing_required
def create_campaign():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        platform = request.form.get('platform', 'Google Ads').strip()
        target_audience = request.form.get('target_audience', '').strip()
        budget = Decimal(request.form.get('budget', '0') or '0')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        utm_source = request.form.get('utm_source', '').strip()
        utm_campaign = request.form.get('utm_campaign', '').strip()
        landing_page_url = request.form.get('landing_page_url', '').strip()
        notes = request.form.get('notes', '').strip()

        if not name:
            flash('Campaign Name is required.', 'danger')
            return render_template('marketing/campaign_form.html', campaign=None)

        # Generate unique code
        count = MarketingCampaign.query.count() + 1
        code = f"CMP-{datetime.now().year}-{count:03d}"

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

        campaign = MarketingCampaign(
            campaign_code=code,
            name=name,
            platform=platform,
            target_audience=target_audience,
            budget=budget,
            spent_amount=Decimal('0'),
            start_date=start_date,
            end_date=end_date,
            status='Active',
            utm_source=utm_source,
            utm_campaign=utm_campaign,
            landing_page_url=landing_page_url,
            notes=notes,
            created_by_id=current_user.id
        )
        db.session.add(campaign)
        db.session.commit()

        log_audit('CREATE', 'MarketingCampaign', campaign.id, f"Launched digital marketing campaign {campaign.campaign_code}")
        flash(f'Campaign {campaign.campaign_code} ({campaign.name}) launched successfully!', 'success')
        return redirect(url_for('marketing.campaigns_list'))

    return render_template('marketing/campaign_form.html', campaign=None)

@marketing_bp.route('/campaigns/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
@marketing_required
def edit_campaign(campaign_id):
    campaign = MarketingCampaign.query.get_or_404(campaign_id)
    if request.method == 'POST':
        campaign.name = request.form.get('name', campaign.name).strip()
        campaign.platform = request.form.get('platform', campaign.platform).strip()
        campaign.target_audience = request.form.get('target_audience', campaign.target_audience).strip()
        campaign.budget = Decimal(request.form.get('budget', '0') or '0')
        campaign.spent_amount = Decimal(request.form.get('spent_amount', '0') or '0')
        campaign.impressions = int(request.form.get('impressions', '0') or 0)
        campaign.clicks = int(request.form.get('clicks', '0') or 0)
        campaign.leads_generated = int(request.form.get('leads_generated', '0') or 0)
        campaign.qualified_leads = int(request.form.get('qualified_leads', '0') or 0)
        campaign.status = request.form.get('status', campaign.status).strip()
        campaign.utm_source = request.form.get('utm_source', campaign.utm_source).strip()
        campaign.utm_campaign = request.form.get('utm_campaign', campaign.utm_campaign).strip()
        campaign.landing_page_url = request.form.get('landing_page_url', campaign.landing_page_url).strip()
        campaign.notes = request.form.get('notes', campaign.notes).strip()

        db.session.commit()
        log_audit('UPDATE', 'MarketingCampaign', campaign.id, f"Updated metrics for {campaign.campaign_code}")
        flash(f'Campaign {campaign.campaign_code} updated successfully!', 'success')
        return redirect(url_for('marketing.campaigns_list'))

    return render_template('marketing/campaign_form.html', campaign=campaign)

@marketing_bp.route('/campaigns/<int:campaign_id>/toggle-status', methods=['POST'])
@login_required
@marketing_required
def toggle_status(campaign_id):
    campaign = MarketingCampaign.query.get_or_404(campaign_id)
    campaign.status = 'Paused' if campaign.status == 'Active' else 'Active'
    db.session.commit()
    flash(f"Campaign {campaign.campaign_code} status set to {campaign.status}.", 'info')
    return redirect(url_for('marketing.campaigns_list'))

@marketing_bp.route('/attribution')
@login_required
@marketing_required
def attribution():
    inquiries = CampaignInquiry.query.order_by(CampaignInquiry.inquiry_date.desc()).all()
    channel_counts = db.session.query(
        CampaignInquiry.source_channel,
        func.count(CampaignInquiry.id)
    ).group_by(CampaignInquiry.source_channel).all()

    return render_template('marketing/attribution.html', inquiries=inquiries, channel_counts=channel_counts)
