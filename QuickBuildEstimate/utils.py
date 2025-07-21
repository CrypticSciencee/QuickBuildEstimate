import os
from datetime import datetime, timedelta
from app import db
from models import Estimate
import logging

def allowed_file(filename, file_type):
    """Check if file has allowed extension"""
    if not filename:
        return False
    
    if file_type == 'pdf':
        return filename.lower().endswith('.pdf')
    elif file_type == 'csv':
        return filename.lower().endswith('.csv')
    
    return False

def purge_old_estimates():
    """Delete estimates older than 90 days"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_estimates = Estimate.query.filter(Estimate.created_at < cutoff_date).all()
        
        for estimate in old_estimates:
            # Delete associated files
            for filename in [estimate.blueprint_filename, estimate.materials_filename, estimate.labor_filename]:
                if filename:
                    file_path = os.path.join('uploads', filename)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logging.info(f"Deleted file: {filename}")
                        except OSError as e:
                            logging.warning(f"Could not delete file {filename}: {e}")
            
            # Delete from database
            db.session.delete(estimate)
            logging.info(f"Purged estimate: {estimate.name} (ID: {estimate.id})")
        
        if old_estimates:
            db.session.commit()
            logging.info(f"Purged {len(old_estimates)} old estimates")
            
    except Exception as e:
        logging.error(f"Error purging old estimates: {e}")
        db.session.rollback()

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"

def get_file_size_mb(file_path):
    """Get file size in MB"""
    if os.path.exists(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)
    return 0
