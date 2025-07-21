import json
import os
import base64
import csv
from io import StringIO
from openai import OpenAI
from models import OpenAIUsage
from app import db
from datetime import datetime
import logging

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_SPEND_CAP = float(os.environ.get("OPENAI_SPEND_CAP", "50"))

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

openai = OpenAI(api_key=OPENAI_API_KEY)

def check_spend_limit():
    """Check if we've exceeded the monthly spend limit"""
    current_month = datetime.now().strftime("%Y-%m")
    usage = OpenAIUsage.query.filter_by(month=current_month).first()
    
    if usage and usage.total_spent >= OPENAI_SPEND_CAP:
        raise Exception(f"Monthly OpenAI spend limit of ${OPENAI_SPEND_CAP} exceeded")

def update_spend_tracking(estimated_cost):
    """Update the monthly spend tracking"""
    current_month = datetime.now().strftime("%Y-%m")
    usage = OpenAIUsage.query.filter_by(month=current_month).first()
    
    if not usage:
        usage = OpenAIUsage()
        usage.month = current_month
        usage.total_spent = 0.0
        db.session.add(usage)
    
    usage.total_spent += estimated_cost
    db.session.commit()

def analyze_blueprint(pdf_path):
    """Analyze PDF blueprint using GPT-4 Vision for area takeoff"""
    check_spend_limit()
    
    try:
        # Convert PDF to base64 for Vision API
        # For simplicity, we'll assume the PDF is a single page image
        # In production, you might want to use pdf2image library
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
            base64_pdf = base64.b64encode(pdf_content).decode('utf-8')
        
        prompt = """
        Analyze this construction blueprint and extract room/area information. 
        For each distinct room or area visible in the blueprint, identify:
        1. Room name/type (e.g., "Kitchen", "Living Room", "Bedroom 1", etc.)
        2. Category (e.g., "Interior", "Exterior", "Utility")
        3. Area in square feet (estimate based on dimensions if visible)
        
        Return your response as a JSON object with this exact format:
        {
            "areas": [
                {
                    "room": "Kitchen",
                    "category": "Interior", 
                    "area_ft2": 150.0
                }
            ]
        }
        
        If you cannot clearly identify specific rooms, provide reasonable estimates for typical construction areas.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:application/pdf;base64,{base64_pdf}"}
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            areas = result.get("areas", [])
        else:
            areas = []
        
        # Estimate cost (rough calculation for tracking)
        estimated_cost = 0.02  # Approximate cost for vision analysis
        update_spend_tracking(estimated_cost)
        
        logging.info(f"Blueprint analysis completed: {len(areas)} areas detected")
        return areas
        
    except Exception as e:
        logging.error(f"Blueprint analysis failed: {e}")
        raise Exception(f"Failed to analyze blueprint: {str(e)}")

def detect_csv_schema(csv_path, file_type):
    """Detect CSV schema and bundles using GPT-4 JSON mode"""
    check_spend_limit()
    
    try:
        # Read first 10 rows of CSV
        sample_rows = []
        headers = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                headers = list(reader.fieldnames)
                for i, row in enumerate(reader):
                    if i >= 10:
                        break
                    sample_rows.append(row)
        
        # Create sample data string
        sample_csv = StringIO()
        writer = csv.DictWriter(sample_csv, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sample_rows)
        sample_data = sample_csv.getvalue()
        
        if file_type == 'materials':
            prompt = """
            Analyze this materials CSV sample and detect the column schema and bundles.
            
            Expected columns to map:
            - name: item/material name
            - unit: unit of measurement (sq ft, linear ft, each, etc.)
            - unit_cost: cost per unit
            - quantity: how many units needed
            - bundle: grouping/package name (optional)
            - category: material category (optional)
            
            Also identify unique bundle names from the data.
            
            Return JSON with this format:
            {
                "column_roles": {
                    "actual_column_name": "expected_role"
                },
                "detected_bundles": ["bundle1", "bundle2"]
            }
            """
        else:  # labor
            prompt = """
            Analyze this labor CSV sample and detect the column schema.
            
            Expected columns to map:
            - task: labor task description
            - hours: number of hours required
            - hourly_rate: cost per hour
            - category: labor category (optional)
            
            Also identify any bundle/grouping names if present.
            
            Return JSON with this format:
            {
                "column_roles": {
                    "actual_column_name": "expected_role"
                },
                "detected_bundles": ["bundle1", "bundle2"]
            }
            """
        
        full_prompt = f"{prompt}\n\nCSV Sample:\n{sample_data}"
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a CSV schema detection expert."},
                {"role": "user", "content": full_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            column_roles = result.get("column_roles", {})
            detected_bundles = result.get("detected_bundles", [])
        else:
            column_roles = {}
            detected_bundles = []
        
        # Estimate cost
        estimated_cost = 0.01  # Approximate cost for schema detection
        update_spend_tracking(estimated_cost)
        
        logging.info(f"CSV schema detection completed for {file_type}: {len(detected_bundles)} bundles")
        return column_roles, detected_bundles
        
    except Exception as e:
        logging.error(f"CSV schema detection failed: {e}")
        raise Exception(f"Failed to detect CSV schema: {str(e)}")

def generate_proposal_summary(estimate):
    """Generate client-friendly proposal summary using GPT-4"""
    check_spend_limit()
    
    try:
        # Prepare estimate data
        areas = estimate.get_areas()
        active_bundles = estimate.get_active_bundles()
        
        areas_text = "\n".join([f"- {area['room']}: {area['area_ft2']} sq ft" for area in areas])
        bundles_text = "\n".join([f"- {bundle}" for bundle in active_bundles])
        
        prompt = f"""
        Generate a professional, client-friendly construction estimate summary.
        
        Project Details:
        - Project Name: {estimate.name}
        - Total Area: {sum(area['area_ft2'] for area in areas)} sq ft
        
        Room Breakdown:
        {areas_text}
        
        Included Packages:
        {bundles_text}
        
        Financial Summary:
        - Subtotal: ${estimate.subtotal:,.2f}
        - Profit ({estimate.profit_percentage}%): ${estimate.profit_amount:,.2f}
        - Contingency ({estimate.contingency_percentage}%): ${estimate.contingency_amount:,.2f}
        - Grand Total: ${estimate.grand_total:,.2f}
        
        Create a professional summary that includes:
        1. Project overview
        2. Scope of work based on the packages
        3. Timeline expectations (general)
        4. Terms and conditions (standard construction)
        
        Write in a professional but approachable tone suitable for presenting to clients.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional construction estimator writing client proposals."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        
        summary = response.choices[0].message.content
        
        # Estimate cost
        estimated_cost = 0.015  # Approximate cost for summary generation
        update_spend_tracking(estimated_cost)
        
        return summary
        
    except Exception as e:
        logging.error(f"Proposal summary generation failed: {e}")
        raise Exception(f"Failed to generate proposal summary: {str(e)}")
