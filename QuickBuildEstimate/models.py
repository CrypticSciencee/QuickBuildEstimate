from datetime import datetime, timedelta
from app import db
import json

class Estimate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    blueprint_filename = db.Column(db.String(200))
    materials_filename = db.Column(db.String(200))
    labor_filename = db.Column(db.String(200))
    
    # Vision analysis results
    areas_json = db.Column(db.Text)  # JSON string of room areas
    
    # CSV schema and bundles
    materials_schema_json = db.Column(db.Text)
    labor_schema_json = db.Column(db.Text)
    detected_bundles_json = db.Column(db.Text)
    
    # Cost calculations
    active_bundles_json = db.Column(db.Text)  # JSON of enabled bundle names
    profit_percentage = db.Column(db.Float, default=15.0)
    contingency_percentage = db.Column(db.Float, default=10.0)
    
    # Totals
    subtotal = db.Column(db.Float, default=0.0)
    profit_amount = db.Column(db.Float, default=0.0)
    contingency_amount = db.Column(db.Float, default=0.0)
    grand_total = db.Column(db.Float, default=0.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_areas(self):
        if self.areas_json:
            return json.loads(self.areas_json)
        return []
    
    def set_areas(self, areas):
        self.areas_json = json.dumps(areas)
    
    def get_materials_schema(self):
        if self.materials_schema_json:
            return json.loads(self.materials_schema_json)
        return {}
    
    def set_materials_schema(self, schema):
        self.materials_schema_json = json.dumps(schema)
    
    def get_labor_schema(self):
        if self.labor_schema_json:
            return json.loads(self.labor_schema_json)
        return {}
    
    def set_labor_schema(self, schema):
        self.labor_schema_json = json.dumps(schema)
    
    def get_detected_bundles(self):
        if self.detected_bundles_json:
            return json.loads(self.detected_bundles_json)
        return []
    
    def set_detected_bundles(self, bundles):
        self.detected_bundles_json = json.dumps(bundles)
    
    def get_active_bundles(self):
        if self.active_bundles_json:
            return json.loads(self.active_bundles_json)
        return []
    
    def set_active_bundles(self, bundles):
        self.active_bundles_json = json.dumps(bundles)
    
    def is_expired(self):
        """Check if estimate is older than 90 days"""
        return datetime.utcnow() - self.created_at > timedelta(days=90)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MaterialItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estimate_id = db.Column(db.Integer, db.ForeignKey('estimate.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(50))
    unit_cost = db.Column(db.Float)
    quantity = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    bundle = db.Column(db.String(100))
    category = db.Column(db.String(100))
    
    estimate = db.relationship('Estimate', backref=db.backref('materials', lazy=True))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class LaborItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estimate_id = db.Column(db.Integer, db.ForeignKey('estimate.id'), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    hours = db.Column(db.Float)
    hourly_rate = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    category = db.Column(db.String(100))
    
    estimate = db.relationship('Estimate', backref=db.backref('labor', lazy=True))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class OpenAIUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM format
    total_spent = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
