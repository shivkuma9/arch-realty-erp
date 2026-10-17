import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, abort, current_app
from flask_login import login_required, current_user
from app.models import Document, Property, Deal, Client
from app.services.auth_service import log_audit
from app.extensions import db

documents_bp = Blueprint('documents', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@documents_bp.route('/')
@login_required
def index():
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()

    query = Document.query
    if category and category != 'All':
        query = query.filter_by(category=category)
    if status and status != 'All':
        query = query.filter_by(verification_status=status)

    docs = query.order_by(Document.created_at.desc()).all()
    pending_count = Document.query.filter_by(verification_status='Pending').count()
    verified_count = Document.query.filter_by(verification_status='Verified').count()
    rejected_count = Document.query.filter_by(verification_status='Rejected').count()

    return render_template(
        'documents/documents_list.html',
        documents=docs,
        selected_category=category,
        selected_status=status,
        pending_count=pending_count,
        verified_count=verified_count,
        rejected_count=rejected_count
    )

@documents_bp.route('/<int:doc_id>/verify', methods=['POST'])
@login_required
def verify_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    new_status = request.form.get('verification_status', 'Verified')
    
    doc.verification_status = new_status
    doc.is_verified = (new_status == 'Verified')
    doc.verified_by_id = current_user.id
    doc.verification_date = datetime.utcnow()
    db.session.commit()
    
    log_audit('VERIFY', 'Document', doc.id, f"Document '{doc.title}' marked as {new_status}")
    flash(f"Document '{doc.title}' has been marked as {new_status}.", 'success')
    return redirect(request.referrer or url_for('documents.index'))

@documents_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part provided.', 'danger')
        return redirect(request.referrer or url_for('documents.index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file.', 'warning')
        return redirect(request.referrer or url_for('documents.index'))

    if file and allowed_file(file.filename):
        title = request.form.get('title', file.filename)
        category = request.form.get('category', 'Property Document')
        prop_id = request.form.get('property_id', type=int)
        deal_id = request.form.get('deal_id', type=int)
        client_id = request.form.get('client_id', type=int)

        orig_filename = secure_filename(file.filename)
        timestamp_prefix = datetime.now().strftime('%Y%m%d%H%M%S_')
        saved_filename = f"{timestamp_prefix}{orig_filename}"

        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(upload_path)
        file_size = os.path.getsize(upload_path)

        doc = Document(
            title=title,
            category=category,
            filename=saved_filename,
            file_size_bytes=file_size,
            mime_type=file.content_type,
            uploaded_by_id=current_user.id,
            property_id=prop_id if prop_id else None,
            deal_id=deal_id if deal_id else None,
            client_id=client_id if client_id else None,
            verification_status='Pending'
        )
        db.session.add(doc)
        db.session.commit()
        log_audit('UPLOAD', 'Document', doc.id, f"Uploaded document {saved_filename}")
        flash(f"Document '{title}' uploaded securely and queued for verification.", 'success')
    else:
        flash('File type not allowed. Supported formats: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, CSV.', 'danger')

    return redirect(request.referrer or url_for('documents.index'))

@documents_bp.route('/download/<int:doc_id>')
@login_required
def download_file(doc_id):
    doc = Document.query.get_or_404(doc_id)
    # Protected download: serve outside public static
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, doc.filename)
    if not os.path.exists(file_path):
        abort(404)
        
    log_audit('DOWNLOAD', 'Document', doc.id, f"Downloaded file {doc.filename}")
    return send_from_directory(upload_folder, doc.filename, as_attachment=True, download_name=doc.title)

