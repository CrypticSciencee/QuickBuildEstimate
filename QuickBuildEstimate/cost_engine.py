from app import db
from models import MaterialItem, LaborItem
import logging

def calculate_estimate_totals(estimate):
    """Calculate estimate totals with layered PSF + unit-item + profit + contingency logic"""
    
    try:
        active_bundles = estimate.get_active_bundles()
        
        # Calculate material costs for active bundles
        material_total = 0.0
        materials = MaterialItem.query.filter_by(estimate_id=estimate.id).all()
        
        for material in materials:
            if not material.bundle or material.bundle in active_bundles:
                material_total += material.total_cost or 0.0
        
        # Calculate labor costs for active bundles  
        labor_total = 0.0
        labor_items = LaborItem.query.filter_by(estimate_id=estimate.id).all()
        
        for labor in labor_items:
            # For labor, we don't have bundles in the current schema, so include all
            labor_total += labor.total_cost or 0.0
        
        # Calculate area-based costs (PSF - per square foot)
        areas = estimate.get_areas()
        total_area = sum(area.get('area_ft2', 0) for area in areas)
        
        # Apply area-based pricing for different categories
        area_cost = 0.0
        for area in areas:
            area_ft2 = area.get('area_ft2', 0)
            category = area.get('category', 'Interior').lower()
            
            # Base PSF rates by category
            if category == 'exterior':
                psf_rate = 15.0  # $15/sq ft for exterior work
            elif category == 'utility':
                psf_rate = 25.0  # $25/sq ft for utility areas (plumbing, electrical)
            else:  # interior
                psf_rate = 20.0  # $20/sq ft for interior work
                
            area_cost += area_ft2 * psf_rate
        
        # Subtotal combines materials, labor, and area-based costs
        subtotal = material_total + labor_total + area_cost
        
        # Apply profit percentage
        profit_percentage = estimate.profit_percentage or 15.0
        profit_amount = subtotal * (profit_percentage / 100.0)
        
        # Apply contingency percentage to subtotal + profit
        contingency_percentage = estimate.contingency_percentage or 10.0
        contingency_amount = (subtotal + profit_amount) * (contingency_percentage / 100.0)
        
        # Calculate grand total
        grand_total = subtotal + profit_amount + contingency_amount
        
        # Update estimate
        estimate.subtotal = round(subtotal, 2)
        estimate.profit_amount = round(profit_amount, 2)
        estimate.contingency_amount = round(contingency_amount, 2)
        estimate.grand_total = round(grand_total, 2)
        
        logging.info(f"Estimate {estimate.id} totals calculated: Subtotal=${subtotal:.2f}, Total=${grand_total:.2f}")
        
    except Exception as e:
        logging.error(f"Error calculating estimate totals: {e}")
        raise Exception(f"Failed to calculate estimate totals: {str(e)}")

def get_cost_breakdown(estimate):
    """Get detailed cost breakdown for display"""
    
    active_bundles = estimate.get_active_bundles()
    
    breakdown = {
        'materials': {},
        'labor': {},
        'area_costs': {},
        'totals': {
            'materials': 0.0,
            'labor': 0.0,
            'area_costs': 0.0,
            'subtotal': estimate.subtotal,
            'profit': estimate.profit_amount,
            'contingency': estimate.contingency_amount,
            'grand_total': estimate.grand_total
        }
    }
    
    # Group materials by bundle
    materials = MaterialItem.query.filter_by(estimate_id=estimate.id).all()
    for material in materials:
        if not material.bundle or material.bundle in active_bundles:
            bundle = material.bundle or 'Miscellaneous'
            if bundle not in breakdown['materials']:
                breakdown['materials'][bundle] = []
            
            breakdown['materials'][bundle].append({
                'name': material.name,
                'quantity': material.quantity,
                'unit': material.unit,
                'unit_cost': material.unit_cost,
                'total_cost': material.total_cost
            })
            breakdown['totals']['materials'] += material.total_cost or 0.0
    
    # Group labor by category
    labor_items = LaborItem.query.filter_by(estimate_id=estimate.id).all()
    for labor in labor_items:
        category = labor.category or 'General Labor'
        if category not in breakdown['labor']:
            breakdown['labor'][category] = []
        
        breakdown['labor'][category].append({
            'task': labor.task,
            'hours': labor.hours,
            'hourly_rate': labor.hourly_rate,
            'total_cost': labor.total_cost
        })
        breakdown['totals']['labor'] += labor.total_cost or 0.0
    
    # Calculate area costs
    areas = estimate.get_areas()
    for area in areas:
        area_ft2 = area.get('area_ft2', 0)
        category = area.get('category', 'Interior')
        room = area.get('room', 'Unknown')
        
        # Base PSF rates by category
        if category.lower() == 'exterior':
            psf_rate = 15.0
        elif category.lower() == 'utility':
            psf_rate = 25.0
        else:
            psf_rate = 20.0
        
        area_cost = area_ft2 * psf_rate
        breakdown['area_costs'][room] = {
            'area_ft2': area_ft2,
            'psf_rate': psf_rate,
            'total_cost': area_cost,
            'category': category
        }
        breakdown['totals']['area_costs'] += area_cost
    
    return breakdown
