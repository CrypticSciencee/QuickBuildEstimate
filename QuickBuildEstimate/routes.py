import os
import csv
import io
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import Estimate, MaterialItem, LaborItem, OpenAIUsage
from openai_services import analyze_blueprint, detect_csv_schema
from cost_engine import calculate_estimate_totals
from pdf_generator import generate_proposal_pdf
from auth import login_required, is_authenticated
from utils import allowed_file, purge_old_estimates
import logging

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    if not is_authenticated():
        return render_template('login.html')
    
    # Purge old estimates on each visit
    purge_old_estimates()
    
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['authenticated'] = True
            session.permanent = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid password. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('login'))

@app.route('/create_estimate', methods=['POST'])
@login_required
def create_estimate():
    try:
        # Get form data
        estimate_name = request.form.get('estimate_name', '').strip()
        if not estimate_name:
            flash('Please provide an estimate name.', 'error')
            return redirect(url_for('index'))
        
        # Check file uploads
        blueprint_file = request.files.get('blueprint')
        materials_file = request.files.get('materials')
        labor_file = request.files.get('labor')
        
        if not all([blueprint_file, materials_file, labor_file]):
            flash('Please upload all three required files.', 'error')
            return redirect(url_for('index'))
        
        if not (blueprint_file.filename and allowed_file(blueprint_file.filename, 'pdf') and
                materials_file.filename and allowed_file(materials_file.filename, 'csv') and
                labor_file.filename and allowed_file(labor_file.filename, 'csv')):
            flash('Invalid file types. Please upload PDF for blueprint and CSV for materials/labor.', 'error')
            return redirect(url_for('index'))
        
        # Create new estimate
        estimate = Estimate(name=estimate_name)
        db.session.add(estimate)
        db.session.flush()  # Get the ID
        
        # Save files
        blueprint_filename = f"blueprint_{estimate.id}_{secure_filename(blueprint_file.filename or 'blueprint.pdf')}"
        materials_filename = f"materials_{estimate.id}_{secure_filename(materials_file.filename or 'materials.csv')}"
        labor_filename = f"labor_{estimate.id}_{secure_filename(labor_file.filename or 'labor.csv')}"
        
        blueprint_path = os.path.join(app.config['UPLOAD_FOLDER'], blueprint_filename)
        materials_path = os.path.join(app.config['UPLOAD_FOLDER'], materials_filename)
        labor_path = os.path.join(app.config['UPLOAD_FOLDER'], labor_filename)
        
        blueprint_file.save(blueprint_path)
        materials_file.save(materials_path)
        labor_file.save(labor_path)
        
        estimate.blueprint_filename = blueprint_filename
        estimate.materials_filename = materials_filename
        estimate.labor_filename = labor_filename
        
        # Analyze blueprint with GPT-4 Vision
        try:
            areas = analyze_blueprint(blueprint_path)
            estimate.set_areas(areas)
            logging.info(f"Blueprint analysis completed: {len(areas)} areas detected")
        except Exception as e:
            logging.error(f"Blueprint analysis failed: {e}")
            flash(f'Blueprint analysis failed: {str(e)}', 'error')
            db.session.rollback()
            return redirect(url_for('index'))
        
        # Analyze CSV schemas
        try:
            materials_schema, materials_bundles = detect_csv_schema(materials_path, 'materials')
            labor_schema, labor_bundles = detect_csv_schema(labor_path, 'labor')
            
            estimate.set_materials_schema(materials_schema)
            estimate.set_labor_schema(labor_schema)
            
            # Combine bundles from both files
            all_bundles = list(set(materials_bundles + labor_bundles))
            estimate.set_detected_bundles(all_bundles)
            estimate.set_active_bundles(all_bundles)  # Enable all bundles by default
            
            logging.info(f"CSV analysis completed: {len(all_bundles)} bundles detected")
        except Exception as e:
            logging.error(f"CSV analysis failed: {e}")
            flash(f'CSV analysis failed: {str(e)}', 'error')
            db.session.rollback()
            return redirect(url_for('index'))
        
        # Load CSV data into database
        load_csv_data(estimate, materials_path, labor_path)
        
        # Calculate initial totals
        calculate_estimate_totals(estimate)
        
        db.session.commit()
        flash('Estimate created successfully!', 'success')
        return redirect(url_for('view_estimate', estimate_id=estimate.id))
        
    except Exception as e:
        logging.error(f"Error creating estimate: {e}")
        flash(f'Error creating estimate: {str(e)}', 'error')
        db.session.rollback()
        return redirect(url_for('index'))

def load_csv_data(estimate, materials_path, labor_path):
    """Load CSV data into database tables"""
    
    # Load materials
    materials_schema = estimate.get_materials_schema()
    with open(materials_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            material = MaterialItem(
                estimate_id=estimate.id,
                name=row.get(materials_schema.get('name', 'name'), ''),
                unit=row.get(materials_schema.get('unit', 'unit'), ''),
                unit_cost=float(row.get(materials_schema.get('unit_cost', 'unit_cost'), 0) or 0),
                quantity=float(row.get(materials_schema.get('quantity', 'quantity'), 0) or 0),
                bundle=row.get(materials_schema.get('bundle', 'bundle'), ''),
                category=row.get(materials_schema.get('category', 'category'), '')
            )
            material.total_cost = material.unit_cost * material.quantity
            db.session.add(material)
    
    # Load labor
    labor_schema = estimate.get_labor_schema()
    with open(labor_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            labor = LaborItem(
                estimate_id=estimate.id,
                task=row.get(labor_schema.get('task', 'task'), ''),
                hours=float(row.get(labor_schema.get('hours', 'hours'), 0) or 0),
                hourly_rate=float(row.get(labor_schema.get('hourly_rate', 'hourly_rate'), 0) or 0),
                category=row.get(labor_schema.get('category', 'category'), '')
            )
            labor.total_cost = labor.hours * labor.hourly_rate
            db.session.add(labor)

@app.route('/estimate/<int:estimate_id>')
@login_required
def view_estimate(estimate_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    return render_template('estimate.html', estimate=estimate)

@app.route('/estimate/<int:estimate_id>/toggle_bundle', methods=['POST'])
@login_required
def toggle_bundle(estimate_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    bundle_name = request.form.get('bundle_name')
    
    active_bundles = estimate.get_active_bundles()
    
    if bundle_name in active_bundles:
        active_bundles.remove(bundle_name)
    else:
        active_bundles.append(bundle_name)
    
    estimate.set_active_bundles(active_bundles)
    calculate_estimate_totals(estimate)
    
    db.session.commit()
    
    return redirect(url_for('view_estimate', estimate_id=estimate_id))

@app.route('/estimate/<int:estimate_id>/update_settings', methods=['POST'])
@login_required
def update_estimate_settings(estimate_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    
    try:
        profit_percentage = float(request.form.get('profit_percentage', 15))
        contingency_percentage = float(request.form.get('contingency_percentage', 10))
        
        estimate.profit_percentage = max(0, min(100, profit_percentage))
        estimate.contingency_percentage = max(0, min(100, contingency_percentage))
        
        calculate_estimate_totals(estimate)
        db.session.commit()
        
        flash('Settings updated successfully!', 'success')
    except ValueError:
        flash('Invalid percentage values. Please enter numbers only.', 'error')
    
    return redirect(url_for('view_estimate', estimate_id=estimate_id))

@app.route('/estimate/<int:estimate_id>/download_proposal')
@login_required
def download_proposal(estimate_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    
    try:
        pdf_buffer = generate_proposal_pdf(estimate)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"proposal_{estimate.name}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        logging.error(f"Error generating PDF: {e}")
        flash(f'Error generating PDF proposal: {str(e)}', 'error')
        return redirect(url_for('view_estimate', estimate_id=estimate_id))

@app.route('/history')
@login_required
def history():
    estimates = Estimate.query.order_by(Estimate.created_at.desc()).all()
    return render_template('history.html', estimates=estimates)

@app.route('/estimate/<int:estimate_id>/duplicate')
@login_required
def duplicate_estimate(estimate_id):
    original = Estimate.query.get_or_404(estimate_id)
    
    # Create new estimate with copied data
    duplicate = Estimate(
        name=f"{original.name} (Copy)",
        areas_json=original.areas_json,
        materials_schema_json=original.materials_schema_json,
        labor_schema_json=original.labor_schema_json,
        detected_bundles_json=original.detected_bundles_json,
        active_bundles_json=original.active_bundles_json,
        profit_percentage=original.profit_percentage,
        contingency_percentage=original.contingency_percentage
    )
    
    db.session.add(duplicate)
    db.session.flush()
    
    # Copy materials
    for material in original.materials:
        new_material = MaterialItem(
            estimate_id=duplicate.id,
            name=material.name,
            unit=material.unit,
            unit_cost=material.unit_cost,
            quantity=material.quantity,
            total_cost=material.total_cost,
            bundle=material.bundle,
            category=material.category
        )
        db.session.add(new_material)
    
    # Copy labor
    for labor in original.labor:
        new_labor = LaborItem(
            estimate_id=duplicate.id,
            task=labor.task,
            hours=labor.hours,
            hourly_rate=labor.hourly_rate,
            total_cost=labor.total_cost,
            category=labor.category
        )
        db.session.add(new_labor)
    
    calculate_estimate_totals(duplicate)
    db.session.commit()
    
    flash('Estimate duplicated successfully!', 'success')
    return redirect(url_for('view_estimate', estimate_id=duplicate.id))

@app.route('/estimate/<int:estimate_id>/delete', methods=['POST'])
@login_required
def delete_estimate(estimate_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    
    # Delete associated files
    for filename in [estimate.blueprint_filename, estimate.materials_filename, estimate.labor_filename]:
        if filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
    
    # Delete from database (cascades to materials and labor)
    db.session.delete(estimate)
    db.session.commit()
    
    flash('Estimate deleted successfully!', 'success')
    return redirect(url_for('history'))

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    logging.error(f"Internal server error: {e}")
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))
