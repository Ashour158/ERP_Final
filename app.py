#!/usr/bin/env python3
"""
Complete ERP System - Main Application
Beyond Zoho, SAP, Oracle NetSuite, Microsoft Dynamics, Azure, and Odoo Combined
Version 2.0 - All 14 Modules with Full Integration and Complete CRUD Operations
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import uuid
from functools import wraps
import logging

# Initialize Flask app with config-driven setup
app = Flask(__name__)

# Load configuration based on environment
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    from config import ProductionConfig
    app.config.from_object(ProductionConfig)
elif env == 'testing':
    from config import TestingConfig
    app.config.from_object(TestingConfig)
else:
    from config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)

# Override with environment variables for production deployment
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', app.config.get('SECRET_KEY'))
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.config.get('JWT_SECRET_KEY'))

# Database configuration
if env == 'development':
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DEV_DATABASE_URL', 'sqlite:///dev_erp.db')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI'))

# Upload folder configuration
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500MB default

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE MODELS - ALL 14 MODULES
# ============================================================================

class Company(db.Model):
    """Multi-company data isolation"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    domain = db.Column(db.String(100))
    logo_url = db.Column(db.String(500))
    address = db.Column(db.Text)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    customers = db.relationship('Customer', backref='company', lazy=True)
    vendors = db.relationship('Vendor', backref='company', lazy=True)

class User(db.Model):
    """Enhanced user profile system with GPS and full customization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(500))
    phone = db.Column(db.String(50))
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    birth_date = db.Column(db.Date)
    marital_status = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(200))
    skills = db.Column(db.Text)  # JSON string
    certifications = db.Column(db.Text)  # JSON string
    role = db.Column(db.String(50), default='user')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    current_location_lat = db.Column(db.Float)
    current_location_lng = db.Column(db.Float)
    current_location_address = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    manager = db.relationship('User', remote_side=[id], backref='subordinates')
    kpis = db.relationship('UserKPI', backref='user', lazy=True)

class Vendor(db.Model):
    """Integrated vendor management across all modules"""
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    website = db.Column(db.String(200))
    tax_id = db.Column(db.String(50))
    payment_terms = db.Column(db.String(100))
    credit_limit = db.Column(db.Numeric(15, 2))
    vendor_type = db.Column(db.String(50))  # supplier, service_provider, partner
    status = db.Column(db.String(20), default='active')
    performance_score = db.Column(db.Float, default=0.0)
    risk_score = db.Column(db.Float, default=0.0)
    certifications = db.Column(db.Text)  # JSON string
    compliance_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contracts = db.relationship('Contract', backref='vendor', lazy=True)
    purchase_orders = db.relationship('PurchaseOrder', backref='vendor', lazy=True)

class Customer(db.Model):
    """CRM customer management with 360-degree view"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    website = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    customer_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')
    credit_limit = db.Column(db.Numeric(15, 2))
    payment_terms = db.Column(db.String(100))
    assigned_sales_rep = db.Column(db.Integer, db.ForeignKey('users.id'))
    lead_score = db.Column(db.Float, default=0.0)
    lifetime_value = db.Column(db.Numeric(15, 2), default=0.0)
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sales_rep = db.relationship('User', backref='customers')
    deals = db.relationship('Deal', backref='customer', lazy=True)
    tickets = db.relationship('Ticket', backref='customer', lazy=True)
    invoices = db.relationship('Invoice', backref='customer', lazy=True)

class Deal(db.Model):
    """CRM deals and opportunities with forecasting"""
    __tablename__ = 'deals'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    stage = db.Column(db.String(50), default='prospecting')
    probability = db.Column(db.Float, default=0.0)
    expected_close_date = db.Column(db.Date)
    actual_close_date = db.Column(db.Date)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source = db.Column(db.String(100))
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = db.relationship('User', backref='deals')
    quotes = db.relationship('Quote', backref='deal', lazy=True)

class Quote(db.Model):
    """Quote and RFQ management with multi-level approval"""
    __tablename__ = 'quotes'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(15, 2), default=0.0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0.0)
    valid_until = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')  # draft, pending_approval, approved, sent, accepted, rejected
    approval_level = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_quotes')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_quotes')

class Product(db.Model):
    """Product management with batch/lot tracking and temperature control"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    unit_of_measure = db.Column(db.String(50))
    cost_price = db.Column(db.Numeric(15, 2))
    selling_price = db.Column(db.Numeric(15, 2))
    weight = db.Column(db.Float)
    dimensions = db.Column(db.String(100))
    barcode = db.Column(db.String(100))
    qr_code = db.Column(db.String(100))
    track_by_batch = db.Column(db.Boolean, default=False)
    track_by_lot = db.Column(db.Boolean, default=False)
    requires_temperature_control = db.Column(db.Boolean, default=False)
    min_temperature = db.Column(db.Float)
    max_temperature = db.Column(db.Float)
    shelf_life_days = db.Column(db.Integer)
    reorder_level = db.Column(db.Float, default=0.0)
    max_stock_level = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_items = db.relationship('InventoryItem', backref='product', lazy=True)

class InventoryItem(db.Model):
    """Advanced inventory management with FIFO/LIFO and expiry tracking"""
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location = db.Column(db.String(100))
    batch_number = db.Column(db.String(50))
    lot_number = db.Column(db.String(50))
    quantity = db.Column(db.Float, nullable=False)
    reserved_quantity = db.Column(db.Float, default=0.0)
    unit_cost = db.Column(db.Numeric(15, 2))
    expiry_date = db.Column(db.Date)
    manufacturing_date = db.Column(db.Date)
    received_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='available')
    temperature_log = db.Column(db.Text)  # JSON string for temperature readings
    photos = db.Column(db.Text)  # JSON string for photo URLs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PurchaseOrder(db.Model):
    """Purchase order management with vendor integration"""
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    order_date = db.Column(db.Date, default=datetime.utcnow)
    expected_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(15, 2), default=0.0)
    status = db.Column(db.String(20), default='draft')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_pos')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_pos')

class Invoice(db.Model):
    """Advanced finance module with multi-currency and VAT"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, default=datetime.utcnow)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Numeric(15, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(15, 2), default=0.0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0.0)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    exchange_rate = db.Column(db.Float, default=1.0)
    payment_terms = db.Column(db.String(100))
    status = db.Column(db.String(20), default='draft')
    payment_status = db.Column(db.String(20), default='unpaid')
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_invoices')

class Ticket(db.Model):
    """Enhanced desk module with multi-channel support and SLA"""
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='open')
    category = db.Column(db.String(100))
    channel = db.Column(db.String(50))  # email, whatsapp, web, phone, social
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    sla_response_time = db.Column(db.Integer)  # minutes
    sla_resolution_time = db.Column(db.Integer)  # minutes
    first_response_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    customer_satisfaction = db.Column(db.Integer)  # 1-5 rating
    tags = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tickets')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tickets')
    work_orders = db.relationship('WorkOrder', backref='ticket', lazy=True)

class WorkOrder(db.Model):
    """Work order management with GPS tracking"""
    __tablename__ = 'work_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    wo_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='assigned')
    scheduled_date = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    location_address = db.Column(db.String(500))
    checkin_lat = db.Column(db.Float)
    checkin_lng = db.Column(db.Float)
    checkin_time = db.Column(db.DateTime)
    checkout_lat = db.Column(db.Float)
    checkout_lng = db.Column(db.Float)
    checkout_time = db.Column(db.DateTime)
    labor_hours = db.Column(db.Float, default=0.0)
    labor_cost = db.Column(db.Numeric(15, 2), default=0.0)
    parts_cost = db.Column(db.Numeric(15, 2), default=0.0)
    total_cost = db.Column(db.Numeric(15, 2), default=0.0)
    completion_notes = db.Column(db.Text)
    completion_photos = db.Column(db.Text)  # JSON string
    customer_signature = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignee = db.relationship('User', backref='work_orders')

class Contract(db.Model):
    """Contract management with AI-powered analysis"""
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    contract_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    contract_type = db.Column(db.String(50))  # sales, purchase, service, employment, nda
    status = db.Column(db.String(20), default='draft')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    auto_renewal = db.Column(db.Boolean, default=False)
    renewal_period = db.Column(db.Integer)  # months
    contract_value = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(3), default='USD')
    payment_terms = db.Column(db.String(200))
    risk_score = db.Column(db.Float, default=0.0)
    compliance_status = db.Column(db.String(50), default='pending')
    document_url = db.Column(db.String(500))
    digital_signature_url = db.Column(db.String(500))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_contracts')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_contracts')

class Employee(db.Model):
    """Comprehensive HR module with L&D and payroll"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    termination_date = db.Column(db.Date)
    employment_type = db.Column(db.String(50))  # full_time, part_time, contract, intern
    job_title = db.Column(db.String(100))
    department = db.Column(db.String(100))
    location = db.Column(db.String(100))
    salary = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(3), default='USD')
    pay_frequency = db.Column(db.String(20))  # monthly, bi_weekly, weekly
    benefits_eligible = db.Column(db.Boolean, default=True)
    vacation_days_per_year = db.Column(db.Integer, default=20)
    sick_days_per_year = db.Column(db.Integer, default=10)
    current_vacation_balance = db.Column(db.Float, default=0.0)
    current_sick_balance = db.Column(db.Float, default=0.0)
    performance_rating = db.Column(db.Float)
    last_review_date = db.Column(db.Date)
    next_review_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='employee_profile')
    attendance_records = db.relationship('AttendanceRecord', backref='employee', lazy=True)
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True)
    training_records = db.relationship('TrainingRecord', backref='employee', lazy=True)
    payroll_records = db.relationship('PayrollRecord', backref='employee', lazy=True)

class AttendanceRecord(db.Model):
    """GPS-enabled attendance tracking"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    checkin_time = db.Column(db.DateTime)
    checkout_time = db.Column(db.DateTime)
    checkin_lat = db.Column(db.Float)
    checkin_lng = db.Column(db.Float)
    checkin_address = db.Column(db.String(500))
    checkout_lat = db.Column(db.Float)
    checkout_lng = db.Column(db.Float)
    checkout_address = db.Column(db.String(500))
    total_hours = db.Column(db.Float, default=0.0)
    overtime_hours = db.Column(db.Float, default=0.0)
    break_hours = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='present')  # present, absent, late, half_day
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LeaveRequest(db.Model):
    """Leave management with approval workflows"""
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # vacation, sick, personal, maternity
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, cancelled
    applied_date = db.Column(db.Date, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_date = db.Column(db.Date)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    approver = db.relationship('User', backref='approved_leaves')

class TrainingRecord(db.Model):
    """L&D module for training and development"""
    __tablename__ = 'training_records'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    training_program_id = db.Column(db.Integer, db.ForeignKey('training_programs.id'), nullable=False)
    enrollment_date = db.Column(db.Date, default=datetime.utcnow)
    start_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='enrolled')  # enrolled, in_progress, completed, cancelled
    progress_percentage = db.Column(db.Float, default=0.0)
    score = db.Column(db.Float)
    certification_earned = db.Column(db.Boolean, default=False)
    certification_expiry_date = db.Column(db.Date)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TrainingProgram(db.Model):
    """Training program management"""
    __tablename__ = 'training_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    duration_hours = db.Column(db.Float)
    delivery_method = db.Column(db.String(50))  # online, classroom, blended
    instructor = db.Column(db.String(100))
    max_participants = db.Column(db.Integer)
    cost_per_participant = db.Column(db.Numeric(15, 2))
    certification_provided = db.Column(db.Boolean, default=False)
    certification_validity_months = db.Column(db.Integer)
    prerequisites = db.Column(db.Text)
    learning_objectives = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    training_records = db.relationship('TrainingRecord', backref='training_program', lazy=True)

class PayrollRecord(db.Model):
    """Payroll module with multi-country compliance"""
    __tablename__ = 'payroll_records'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)
    pay_date = db.Column(db.Date, nullable=False)
    basic_salary = db.Column(db.Numeric(15, 2), nullable=False)
    overtime_pay = db.Column(db.Numeric(15, 2), default=0.0)
    bonus = db.Column(db.Numeric(15, 2), default=0.0)
    commission = db.Column(db.Numeric(15, 2), default=0.0)
    allowances = db.Column(db.Numeric(15, 2), default=0.0)
    gross_pay = db.Column(db.Numeric(15, 2), nullable=False)
    tax_deduction = db.Column(db.Numeric(15, 2), default=0.0)
    social_security = db.Column(db.Numeric(15, 2), default=0.0)
    health_insurance = db.Column(db.Numeric(15, 2), default=0.0)
    other_deductions = db.Column(db.Numeric(15, 2), default=0.0)
    total_deductions = db.Column(db.Numeric(15, 2), default=0.0)
    net_pay = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), default='draft')  # draft, approved, paid
    payment_method = db.Column(db.String(50))  # bank_transfer, check, cash
    bank_account = db.Column(db.String(100))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_payrolls')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_payrolls')

class MarketingCampaign(db.Model):
    """Marketing module with e-commerce and social media"""
    __tablename__ = 'marketing_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    campaign_type = db.Column(db.String(50))  # email, social, ppc, content, event
    status = db.Column(db.String(20), default='draft')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Numeric(15, 2))
    actual_cost = db.Column(db.Numeric(15, 2), default=0.0)
    target_audience = db.Column(db.Text)  # JSON string
    channels = db.Column(db.Text)  # JSON string - facebook, linkedin, instagram, email
    goals = db.Column(db.Text)  # JSON string
    kpis = db.Column(db.Text)  # JSON string
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    leads_generated = db.Column(db.Integer, default=0)
    revenue_generated = db.Column(db.Numeric(15, 2), default=0.0)
    roi = db.Column(db.Float, default=0.0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='marketing_campaigns')

class Survey(db.Model):
    """Survey module with multi-channel distribution"""
    __tablename__ = 'surveys'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    survey_type = db.Column(db.String(50))  # customer_satisfaction, employee_engagement, market_research
    status = db.Column(db.String(20), default='draft')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    target_audience = db.Column(db.Text)  # JSON string
    distribution_channels = db.Column(db.Text)  # JSON string
    questions = db.Column(db.Text)  # JSON string
    total_responses = db.Column(db.Integer, default=0)
    completion_rate = db.Column(db.Float, default=0.0)
    average_rating = db.Column(db.Float, default=0.0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='surveys')
    responses = db.relationship('SurveyResponse', backref='survey', lazy=True)

class SurveyResponse(db.Model):
    """Survey responses with analytics"""
    __tablename__ = 'survey_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'), nullable=False)
    respondent_email = db.Column(db.String(120))
    respondent_name = db.Column(db.String(100))
    responses = db.Column(db.Text)  # JSON string
    completion_time_seconds = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class CommunityPost(db.Model):
    """Internal community app with location and mentioning"""
    __tablename__ = 'community_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_type = db.Column(db.String(20), default='text')  # text, image, video, event, announcement
    media_urls = db.Column(db.Text)  # JSON string for unlimited file size media
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    location_name = db.Column(db.String(200))
    mentioned_users = db.Column(db.Text)  # JSON string of user IDs
    tags = db.Column(db.Text)  # JSON string
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    visibility = db.Column(db.String(20), default='company')  # company, department, team, public
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='community_posts')
    comments = db.relationship('CommunityComment', backref='post', lazy=True)
    likes = db.relationship('CommunityLike', backref='post', lazy=True)

class CommunityComment(db.Model):
    """Community post comments"""
    __tablename__ = 'community_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('community_posts.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mentioned_users = db.Column(db.Text)  # JSON string
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='community_comments')

class CommunityLike(db.Model):
    """Community post and comment likes"""
    __tablename__ = 'community_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('community_posts.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('community_comments.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reaction_type = db.Column(db.String(20), default='like')  # like, love, laugh, wow, sad, angry
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='community_likes')

class ComplianceAudit(db.Model):
    """Compliance and quality management with ISO 9001"""
    __tablename__ = 'compliance_audits'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    audit_type = db.Column(db.String(50), nullable=False)  # internal, external, compliance, quality
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    standard = db.Column(db.String(50))  # ISO9001, ISO27001, SOX, GDPR
    scope = db.Column(db.Text)
    auditor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    auditee_department = db.Column(db.String(100))
    scheduled_date = db.Column(db.Date)
    actual_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed, cancelled
    findings = db.Column(db.Text)  # JSON string
    non_conformances = db.Column(db.Text)  # JSON string
    corrective_actions = db.Column(db.Text)  # JSON string
    preventive_actions = db.Column(db.Text)  # JSON string
    overall_rating = db.Column(db.String(20))  # excellent, good, satisfactory, needs_improvement
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    auditor = db.relationship('User', backref='conducted_audits')

class BusinessAnalytics(db.Model):
    """Business analysis module with cross-module intelligence"""
    __tablename__ = 'business_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    report_name = db.Column(db.String(200), nullable=False)
    report_type = db.Column(db.String(50))  # sales, financial, operational, customer, hr
    data_sources = db.Column(db.Text)  # JSON string of modules/tables
    metrics = db.Column(db.Text)  # JSON string of KPIs and metrics
    filters = db.Column(db.Text)  # JSON string
    date_range_start = db.Column(db.Date)
    date_range_end = db.Column(db.Date)
    results = db.Column(db.Text)  # JSON string of analysis results
    insights = db.Column(db.Text)  # AI-generated insights
    recommendations = db.Column(db.Text)  # AI-generated recommendations
    visualization_config = db.Column(db.Text)  # JSON string for charts/graphs
    is_automated = db.Column(db.Boolean, default=False)
    schedule_frequency = db.Column(db.String(20))  # daily, weekly, monthly, quarterly
    last_run_at = db.Column(db.DateTime)
    next_run_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='business_analytics')

class UserKPI(db.Model):
    """Universal KPI system for all users across all modules"""
    __tablename__ = 'user_kpis'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module = db.Column(db.String(50), nullable=False)  # crm, finance, hr, desk, etc.
    kpi_name = db.Column(db.String(100), nullable=False)
    kpi_description = db.Column(db.Text)
    target_value = db.Column(db.Float)
    current_value = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(20))  # percentage, currency, count, hours
    period = db.Column(db.String(20))  # daily, weekly, monthly, quarterly, yearly
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    achievement_percentage = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')  # active, achieved, missed, paused
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VigilanceAlert(db.Model):
    """System-wide vigilance and monitoring alerts"""
    __tablename__ = 'vigilance_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # security, compliance, performance, business
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    module = db.Column(db.String(50))  # source module
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    affected_entity_type = db.Column(db.String(50))  # user, customer, vendor, product, etc.
    affected_entity_id = db.Column(db.Integer)
    threshold_value = db.Column(db.Float)
    actual_value = db.Column(db.Float)
    status = db.Column(db.String(20), default='open')  # open, acknowledged, resolved, false_positive
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    auto_generated = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_alerts')
    acknowledger = db.relationship('User', foreign_keys=[acknowledged_by], backref='acknowledged_alerts')
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_alerts')

class CourierShipment(db.Model):
    """Courier management system for supply chain"""
    __tablename__ = 'courier_shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    shipment_number = db.Column(db.String(50), unique=True, nullable=False)
    courier_company = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50))  # standard, express, overnight, same_day
    tracking_number = db.Column(db.String(100))
    sender_name = db.Column(db.String(100))
    sender_address = db.Column(db.Text)
    sender_phone = db.Column(db.String(50))
    recipient_name = db.Column(db.String(100))
    recipient_address = db.Column(db.Text)
    recipient_phone = db.Column(db.String(50))
    package_weight = db.Column(db.Float)
    package_dimensions = db.Column(db.String(100))
    declared_value = db.Column(db.Numeric(15, 2))
    shipping_cost = db.Column(db.Numeric(15, 2))
    insurance_cost = db.Column(db.Numeric(15, 2), default=0.0)
    pickup_date = db.Column(db.Date)
    expected_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='created')  # created, picked_up, in_transit, delivered, exception
    delivery_proof = db.Column(db.String(500))  # signature or photo URL
    special_instructions = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='courier_shipments')

class DocumentSignature(db.Model):
    """Digital signature module with OCR and auto-archiving"""
    __tablename__ = 'document_signatures'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    document_name = db.Column(db.String(200), nullable=False)
    document_type = db.Column(db.String(50))  # contract, invoice, quote, hr_document, compliance
    document_url = db.Column(db.String(500), nullable=False)
    original_document_url = db.Column(db.String(500))
    module_source = db.Column(db.String(50))  # crm, finance, hr, compliance
    source_record_id = db.Column(db.Integer)
    signers = db.Column(db.Text)  # JSON string of signer details
    signature_status = db.Column(db.String(20), default='pending')  # pending, partial, completed, expired
    signing_order = db.Column(db.Text)  # JSON string for sequential signing
    current_signer_index = db.Column(db.Integer, default=0)
    expiry_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    certificate_url = db.Column(db.String(500))  # digital certificate for trust
    ocr_extracted_data = db.Column(db.Text)  # JSON string of OCR results
    auto_archive_code = db.Column(db.String(50))  # preconfigured coding for archiving
    archive_location = db.Column(db.String(500))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='document_signatures')

# ============================================================================
# HELPER FUNCTIONS AND DECORATORS
# ============================================================================

def company_required(f):
    """Decorator to ensure company context"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.company_id:
            return jsonify({'error': 'Company context required'}), 400
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user with company context"""
    current_user_id = get_jwt_identity()
    return User.query.get(current_user_id)

def get_current_company():
    """Get current user's company"""
    user = get_current_user()
    return user.company if user else None

def create_vigilance_alert(company_id, alert_type, severity, module, title, description, 
                          affected_entity_type=None, affected_entity_id=None, 
                          threshold_value=None, actual_value=None):
    """Create vigilance alert for monitoring"""
    alert = VigilanceAlert(
        company_id=company_id,
        alert_type=alert_type,
        severity=severity,
        module=module,
        title=title,
        description=description,
        affected_entity_type=affected_entity_type,
        affected_entity_id=affected_entity_id,
        threshold_value=threshold_value,
        actual_value=actual_value
    )
    db.session.add(alert)
    db.session.commit()
    return alert

def update_user_kpi(user_id, module, kpi_name, current_value, target_value=None):
    """Update user KPI across all modules"""
    company_id = get_current_company().id
    
    kpi = UserKPI.query.filter_by(
        company_id=company_id,
        user_id=user_id,
        module=module,
        kpi_name=kpi_name
    ).first()
    
    if not kpi:
        kpi = UserKPI(
            company_id=company_id,
            user_id=user_id,
            module=module,
            kpi_name=kpi_name,
            target_value=target_value or 100.0,
            current_value=current_value
        )
        db.session.add(kpi)
    else:
        kpi.current_value = current_value
        if target_value:
            kpi.target_value = target_value
    
    # Calculate achievement percentage
    if kpi.target_value and kpi.target_value > 0:
        kpi.achievement_percentage = (kpi.current_value / kpi.target_value) * 100
    
    kpi.last_updated = datetime.utcnow()
    db.session.commit()
    
    # Create vigilance alert if KPI is significantly below target
    if kpi.achievement_percentage < 70:  # Below 70% of target
        create_vigilance_alert(
            company_id=company_id,
            alert_type='performance',
            severity='medium',
            module=module,
            title=f'KPI Below Target: {kpi_name}',
            description=f'User {user_id} KPI "{kpi_name}" is at {kpi.achievement_percentage:.1f}% of target',
            affected_entity_type='user',
            affected_entity_id=user_id,
            threshold_value=kpi.target_value,
            actual_value=kpi.current_value
        )

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User authentication with company context"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Update last login and location if provided
            user.last_login = datetime.utcnow()
            if data.get('location'):
                user.current_location_lat = data['location'].get('lat')
                user.current_location_lng = data['location'].get('lng')
                user.current_location_address = data['location'].get('address')
            
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Update login KPI
            update_user_kpi(user.id, 'system', 'login_count', 1)
            
            return jsonify({
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile_picture': user.profile_picture,
                    'role': user.role,
                    'company': {
                        'id': user.company.id,
                        'name': user.company.name,
                        'code': user.company.code
                    }
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration with company setup"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'company_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create company if it doesn't exist
        company = Company.query.filter_by(name=data['company_name']).first()
        if not company:
            company = Company(
                name=data['company_name'],
                code=data.get('company_code', data['company_name'].upper().replace(' ', '_')),
                email=data.get('company_email'),
                phone=data.get('company_phone'),
                address=data.get('company_address')
            )
            db.session.add(company)
            db.session.flush()  # Get company ID
        
        # Create user
        user = User(
            company_id=company.id,
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            department=data.get('department'),
            position=data.get('position'),
            role=data.get('role', 'user')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User registered successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

# ============================================================================
# CRM MODULE ROUTES
# ============================================================================

@app.route('/api/crm/customers', methods=['GET', 'POST'])
@jwt_required()
@company_required
def crm_customers():
    """CRM customer management with 360-degree view"""
    company = get_current_company()
    
    if request.method == 'GET':
        customers = Customer.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'code': c.code,
            'email': c.email,
            'phone': c.phone,
            'address': c.address,
            'contact_person': c.contact_person,
            'industry': c.industry,
            'customer_type': c.customer_type,
            'status': c.status,
            'lead_score': float(c.lead_score) if c.lead_score else 0.0,
            'lifetime_value': float(c.lifetime_value) if c.lifetime_value else 0.0,
            'sales_rep': {
                'id': c.sales_rep.id,
                'name': f"{c.sales_rep.first_name} {c.sales_rep.last_name}",
                'profile_picture': c.sales_rep.profile_picture
            } if c.sales_rep else None,
            'location': {
                'lat': c.location_lat,
                'lng': c.location_lng
            } if c.location_lat and c.location_lng else None,
            'created_at': c.created_at.isoformat()
        } for c in customers])
    
    elif request.method == 'POST':
        data = request.get_json()
        current_user = get_current_user()
        
        customer = Customer(
            company_id=company.id,
            name=data['name'],
            code=data.get('code', f"CUST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            contact_person=data.get('contact_person'),
            website=data.get('website'),
            industry=data.get('industry'),
            customer_type=data.get('customer_type', 'prospect'),
            assigned_sales_rep=data.get('assigned_sales_rep', current_user.id),
            location_lat=data.get('location', {}).get('lat'),
            location_lng=data.get('location', {}).get('lng')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        # Update CRM KPI for customer creation
        update_user_kpi(current_user.id, 'crm', 'customers_created', 1)
        
        # Create vigilance alert for new customer
        create_vigilance_alert(
            company_id=company.id,
            alert_type='business',
            severity='low',
            module='crm',
            title='New Customer Created',
            description=f"Customer {customer.name} has been added to the system",
            affected_entity_type='customer',
            affected_entity_id=customer.id
        )
        
        return jsonify({'message': 'Customer created successfully', 'id': customer.id}), 201

@app.route('/api/crm/deals', methods=['GET', 'POST'])
@jwt_required()
@company_required
def crm_deals():
    """Deal management with forecasting and GPS check-ins"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        deals = Deal.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': d.id,
            'name': d.name,
            'description': d.description,
            'amount': float(d.amount),
            'stage': d.stage,
            'probability': d.probability,
            'expected_close_date': d.expected_close_date.isoformat() if d.expected_close_date else None,
            'customer': {
                'id': d.customer.id,
                'name': d.customer.name,
                'location': {
                    'lat': d.customer.location_lat,
                    'lng': d.customer.location_lng
                } if d.customer.location_lat else None
            },
            'owner': {
                'id': d.owner.id,
                'name': f"{d.owner.first_name} {d.owner.last_name}",
                'profile_picture': d.owner.profile_picture
            },
            'status': d.status,
            'created_at': d.created_at.isoformat()
        } for d in deals])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        deal = Deal(
            company_id=company.id,
            customer_id=data['customer_id'],
            name=data['name'],
            description=data.get('description'),
            amount=data['amount'],
            stage=data.get('stage', 'prospecting'),
            probability=data.get('probability', 0.0),
            expected_close_date=datetime.strptime(data['expected_close_date'], '%Y-%m-%d').date() if data.get('expected_close_date') else None,
            owner_id=data.get('owner_id', current_user.id),
            source=data.get('source')
        )
        
        db.session.add(deal)
        db.session.commit()
        
        # Update CRM KPI for deal creation
        update_user_kpi(current_user.id, 'crm', 'deals_created', 1)
        
        # Create vigilance alert for high-value deals
        if deal.amount > 50000:
            create_vigilance_alert(
                company_id=company.id,
                alert_type='business',
                severity='medium',
                module='crm',
                title='High-Value Deal Created',
                description=f"Deal {deal.name} worth ${deal.amount:,.2f} has been created",
                affected_entity_type='deal',
                affected_entity_id=deal.id,
                actual_value=float(deal.amount)
            )
        
        return jsonify({'message': 'Deal created successfully', 'id': deal.id}), 201

@app.route('/api/crm/checkin', methods=['POST'])
@jwt_required()
@company_required
def crm_checkin():
    """GPS check-in for sales rep visits"""
    data = request.get_json()
    current_user = get_current_user()
    
    # Update user location
    current_user.current_location_lat = data['location']['lat']
    current_user.current_location_lng = data['location']['lng']
    current_user.current_location_address = data['location'].get('address')
    
    db.session.commit()
    
    # Update CRM KPI
    update_user_kpi(current_user.id, 'crm', 'customer_visits', 1)
    
    # Create vigilance alert for location tracking
    create_vigilance_alert(
        company_id=current_user.company_id,
        alert_type='business',
        severity='low',
        module='crm',
        title='Sales Rep Check-in',
        description=f"{current_user.first_name} {current_user.last_name} checked in at {data['location'].get('address', 'Unknown location')}",
        affected_entity_type='user',
        affected_entity_id=current_user.id
    )
    
    return jsonify({'message': 'Check-in successful'}), 200

@app.route('/api/crm/quotes', methods=['GET', 'POST'])
@jwt_required()
@company_required
def crm_quotes():
    """Quote and RFQ management with multi-level approval"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        quotes = Quote.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': q.id,
            'quote_number': q.quote_number,
            'title': q.title,
            'total_amount': float(q.total_amount),
            'status': q.status,
            'approval_level': q.approval_level,
            'valid_until': q.valid_until.isoformat() if q.valid_until else None,
            'customer': {
                'id': q.customer.id,
                'name': q.customer.name
            },
            'creator': {
                'id': q.creator.id,
                'name': f"{q.creator.first_name} {q.creator.last_name}",
                'profile_picture': q.creator.profile_picture
            },
            'created_at': q.created_at.isoformat()
        } for q in quotes])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        quote = Quote(
            company_id=company.id,
            customer_id=data['customer_id'],
            deal_id=data.get('deal_id'),
            quote_number=f"QUO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            title=data['title'],
            description=data.get('description'),
            total_amount=data['total_amount'],
            tax_amount=data.get('tax_amount', 0.0),
            discount_amount=data.get('discount_amount', 0.0),
            valid_until=datetime.strptime(data['valid_until'], '%Y-%m-%d').date() if data.get('valid_until') else None,
            created_by=current_user.id
        )
        
        db.session.add(quote)
        db.session.commit()
        
        # Update CRM KPI for quote creation
        update_user_kpi(current_user.id, 'crm', 'quotes_created', 1)
        
        # Create vigilance alert for high-value quotes
        if quote.total_amount > 25000:
            create_vigilance_alert(
                company_id=company.id,
                alert_type='business',
                severity='low',
                module='crm',
                title='High-Value Quote Created',
                description=f"Quote {quote.quote_number} worth ${quote.total_amount:,.2f} has been created",
                affected_entity_type='quote',
                affected_entity_id=quote.id,
                actual_value=float(quote.total_amount)
            )
        
        return jsonify({'message': 'Quote created successfully', 'id': quote.id}), 201

# ============================================================================
# FINANCE MODULE ROUTES
# ============================================================================

@app.route('/api/finance/invoices', methods=['GET', 'POST'])
@jwt_required()
@company_required
def finance_invoices():
    """Advanced finance module with multi-currency and VAT"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        invoices = Invoice.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': i.id,
            'invoice_number': i.invoice_number,
            'invoice_date': i.invoice_date.isoformat(),
            'due_date': i.due_date.isoformat() if i.due_date else None,
            'total_amount': float(i.total_amount),
            'currency': i.currency,
            'status': i.status,
            'payment_status': i.payment_status,
            'customer': {
                'id': i.customer.id,
                'name': i.customer.name
            },
            'creator': {
                'id': i.creator.id,
                'name': f"{i.creator.first_name} {i.creator.last_name}",
                'profile_picture': i.creator.profile_picture
            },
            'created_at': i.created_at.isoformat()
        } for i in invoices])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        invoice = Invoice(
            company_id=company.id,
            customer_id=data['customer_id'],
            invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            invoice_date=datetime.strptime(data['invoice_date'], '%Y-%m-%d').date(),
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None,
            subtotal=data['subtotal'],
            tax_amount=data.get('tax_amount', 0.0),
            discount_amount=data.get('discount_amount', 0.0),
            total_amount=data['total_amount'],
            currency=data.get('currency', 'USD'),
            exchange_rate=data.get('exchange_rate', 1.0),
            payment_terms=data.get('payment_terms'),
            notes=data.get('notes'),
            created_by=current_user.id
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        # Update Finance KPI
        update_user_kpi(current_user.id, 'finance', 'invoices_created', 1)
        
        # Create vigilance alert for high-value invoices
        if invoice.total_amount > 10000:
            create_vigilance_alert(
                company_id=company.id,
                alert_type='business',
                severity='medium',
                module='finance',
                title='High-Value Invoice Created',
                description=f"Invoice {invoice.invoice_number} for {invoice.total_amount} {invoice.currency} created",
                affected_entity_type='invoice',
                affected_entity_id=invoice.id,
                actual_value=float(invoice.total_amount)
            )
        
        return jsonify({'message': 'Invoice created successfully', 'id': invoice.id}), 201

@app.route('/api/finance/vendor-payments', methods=['GET', 'POST'])
@jwt_required()
@company_required
def finance_vendor_payments():
    """Vendor payment processing with risk mitigation"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        # Get vendor payment summary
        vendors = Vendor.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': v.id,
            'name': v.name,
            'payment_terms': v.payment_terms,
            'credit_limit': float(v.credit_limit) if v.credit_limit else 0.0,
            'performance_score': v.performance_score,
            'risk_score': v.risk_score,
            'status': v.status
        } for v in vendors])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        # Risk mitigation check
        vendor = Vendor.query.get(data['vendor_id'])
        if vendor.risk_score > 0.7:  # High risk vendor
            create_vigilance_alert(
                company_id=company.id,
                alert_type='business',
                severity='high',
                module='finance',
                title='High-Risk Vendor Payment',
                description=f"Payment to high-risk vendor {vendor.name} (Risk Score: {vendor.risk_score})",
                affected_entity_type='vendor',
                affected_entity_id=vendor.id,
                threshold_value=0.7,
                actual_value=vendor.risk_score
            )
        
        # Update Finance KPI
        update_user_kpi(current_user.id, 'finance', 'vendor_payments_processed', 1)
        
        return jsonify({'message': 'Vendor payment processed successfully'}), 200

# ============================================================================
# HR MODULE ROUTES
# ============================================================================

@app.route('/api/hr/employees', methods=['GET', 'POST'])
@jwt_required()
@company_required
def hr_employees():
    """Comprehensive HR module with L&D and payroll"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        employees = Employee.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': e.id,
            'employee_id': e.employee_id,
            'user': {
                'id': e.user.id,
                'name': f"{e.user.first_name} {e.user.last_name}",
                'email': e.user.email,
                'profile_picture': e.user.profile_picture,
                'phone': e.user.phone
            },
            'job_title': e.job_title,
            'department': e.department,
            'hire_date': e.hire_date.isoformat(),
            'employment_type': e.employment_type,
            'salary': float(e.salary) if e.salary else 0.0,
            'currency': e.currency,
            'vacation_balance': e.current_vacation_balance,
            'sick_balance': e.current_sick_balance,
            'performance_rating': e.performance_rating,
            'status': e.status
        } for e in employees])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        employee = Employee(
            company_id=company.id,
            user_id=data['user_id'],
            employee_id=data.get('employee_id', f"EMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            hire_date=datetime.strptime(data['hire_date'], '%Y-%m-%d').date(),
            employment_type=data.get('employment_type', 'full_time'),
            job_title=data.get('job_title'),
            department=data.get('department'),
            location=data.get('location'),
            salary=data.get('salary'),
            currency=data.get('currency', 'USD'),
            pay_frequency=data.get('pay_frequency', 'monthly'),
            vacation_days_per_year=data.get('vacation_days_per_year', 20),
            sick_days_per_year=data.get('sick_days_per_year', 10)
        )
        
        db.session.add(employee)
        db.session.commit()
        
        # Update HR KPI
        update_user_kpi(current_user.id, 'hr', 'employees_onboarded', 1)
        
        return jsonify({'message': 'Employee created successfully', 'id': employee.id}), 201

@app.route('/api/hr/attendance/checkin', methods=['POST'])
@jwt_required()
@company_required
def hr_checkin():
    """GPS-enabled attendance check-in"""
    data = request.get_json()
    current_user = get_current_user()
    company = get_current_company()
    
    # Get employee record
    employee = Employee.query.filter_by(company_id=company.id, user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'Employee record not found'}), 404
    
    # Check if already checked in today
    today = datetime.utcnow().date()
    existing_record = AttendanceRecord.query.filter_by(
        company_id=company.id,
        employee_id=employee.id,
        date=today
    ).first()
    
    if existing_record and existing_record.checkin_time:
        return jsonify({'error': 'Already checked in today'}), 400
    
    # Create or update attendance record
    if not existing_record:
        attendance = AttendanceRecord(
            company_id=company.id,
            employee_id=employee.id,
            date=today
        )
        db.session.add(attendance)
    else:
        attendance = existing_record
    
    attendance.checkin_time = datetime.utcnow()
    attendance.checkin_lat = data['location']['lat']
    attendance.checkin_lng = data['location']['lng']
    attendance.checkin_address = data['location'].get('address')
    
    db.session.commit()
    
    # Update HR KPI
    update_user_kpi(current_user.id, 'hr', 'attendance_checkins', 1)
    
    return jsonify({'message': 'Check-in successful'}), 200

@app.route('/api/hr/attendance/checkout', methods=['POST'])
@jwt_required()
@company_required
def hr_checkout():
    """GPS-enabled attendance check-out"""
    data = request.get_json()
    current_user = get_current_user()
    company = get_current_company()
    
    # Get employee record
    employee = Employee.query.filter_by(company_id=company.id, user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'Employee record not found'}), 404
    
    # Get today's attendance record
    today = datetime.utcnow().date()
    attendance = AttendanceRecord.query.filter_by(
        company_id=company.id,
        employee_id=employee.id,
        date=today
    ).first()
    
    if not attendance or not attendance.checkin_time:
        return jsonify({'error': 'No check-in record found for today'}), 400
    
    if attendance.checkout_time:
        return jsonify({'error': 'Already checked out today'}), 400
    
    # Update attendance record
    checkout_time = datetime.utcnow()
    attendance.checkout_time = checkout_time
    attendance.checkout_lat = data['location']['lat']
    attendance.checkout_lng = data['location']['lng']
    attendance.checkout_address = data['location'].get('address')
    
    # Calculate total hours
    time_diff = checkout_time - attendance.checkin_time
    attendance.total_hours = time_diff.total_seconds() / 3600
    
    # Calculate overtime (assuming 8 hours standard)
    if attendance.total_hours > 8:
        attendance.overtime_hours = attendance.total_hours - 8
    
    db.session.commit()
    
    # Update HR KPI
    update_user_kpi(current_user.id, 'hr', 'total_work_hours', attendance.total_hours)
    
    return jsonify({'message': 'Check-out successful', 'total_hours': attendance.total_hours}), 200

@app.route('/api/hr/leave-requests', methods=['GET', 'POST'])
@jwt_required()
@company_required
def hr_leave_requests():
    """Leave management with approval workflows"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        leave_requests = LeaveRequest.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': lr.id,
            'employee': {
                'id': lr.employee.id,
                'name': f"{lr.employee.user.first_name} {lr.employee.user.last_name}",
                'profile_picture': lr.employee.user.profile_picture
            },
            'leave_type': lr.leave_type,
            'start_date': lr.start_date.isoformat(),
            'end_date': lr.end_date.isoformat(),
            'total_days': lr.total_days,
            'reason': lr.reason,
            'status': lr.status,
            'applied_date': lr.applied_date.isoformat(),
            'approver': {
                'id': lr.approver.id,
                'name': f"{lr.approver.first_name} {lr.approver.last_name}"
            } if lr.approver else None
        } for lr in leave_requests])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        # Get employee record
        employee = Employee.query.filter_by(company_id=company.id, user_id=current_user.id).first()
        if not employee:
            return jsonify({'error': 'Employee record not found'}), 404
        
        leave_request = LeaveRequest(
            company_id=company.id,
            employee_id=employee.id,
            leave_type=data['leave_type'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            total_days=data['total_days'],
            reason=data.get('reason')
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        # Update HR KPI
        update_user_kpi(current_user.id, 'hr', 'leave_requests_submitted', 1)
        
        return jsonify({'message': 'Leave request submitted successfully', 'id': leave_request.id}), 201

@app.route('/api/hr/training-programs', methods=['GET', 'POST'])
@jwt_required()
@company_required
def hr_training_programs():
    """L&D module for training and development"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        programs = TrainingProgram.query.filter_by(company_id=company.id, is_active=True).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'category': p.category,
            'duration_hours': p.duration_hours,
            'delivery_method': p.delivery_method,
            'instructor': p.instructor,
            'cost_per_participant': float(p.cost_per_participant) if p.cost_per_participant else 0.0,
            'certification_provided': p.certification_provided,
            'max_participants': p.max_participants
        } for p in programs])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        program = TrainingProgram(
            company_id=company.id,
            name=data['name'],
            description=data.get('description'),
            category=data.get('category'),
            duration_hours=data.get('duration_hours'),
            delivery_method=data.get('delivery_method', 'online'),
            instructor=data.get('instructor'),
            max_participants=data.get('max_participants'),
            cost_per_participant=data.get('cost_per_participant'),
            certification_provided=data.get('certification_provided', False),
            certification_validity_months=data.get('certification_validity_months'),
            prerequisites=data.get('prerequisites'),
            learning_objectives=data.get('learning_objectives')
        )
        
        db.session.add(program)
        db.session.commit()
        
        # Update HR KPI
        update_user_kpi(current_user.id, 'hr', 'training_programs_created', 1)
        
        return jsonify({'message': 'Training program created successfully', 'id': program.id}), 201

@app.route('/api/hr/payroll', methods=['GET', 'POST'])
@jwt_required()
@company_required
def hr_payroll():
    """Payroll module with multi-country compliance"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        payroll_records = PayrollRecord.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': pr.id,
            'employee': {
                'id': pr.employee.id,
                'name': f"{pr.employee.user.first_name} {pr.employee.user.last_name}",
                'employee_id': pr.employee.employee_id
            },
            'pay_period_start': pr.pay_period_start.isoformat(),
            'pay_period_end': pr.pay_period_end.isoformat(),
            'pay_date': pr.pay_date.isoformat(),
            'gross_pay': float(pr.gross_pay),
            'total_deductions': float(pr.total_deductions),
            'net_pay': float(pr.net_pay),
            'currency': pr.currency,
            'status': pr.status
        } for pr in payroll_records])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        payroll = PayrollRecord(
            company_id=company.id,
            employee_id=data['employee_id'],
            pay_period_start=datetime.strptime(data['pay_period_start'], '%Y-%m-%d').date(),
            pay_period_end=datetime.strptime(data['pay_period_end'], '%Y-%m-%d').date(),
            pay_date=datetime.strptime(data['pay_date'], '%Y-%m-%d').date(),
            basic_salary=data['basic_salary'],
            overtime_pay=data.get('overtime_pay', 0.0),
            bonus=data.get('bonus', 0.0),
            commission=data.get('commission', 0.0),
            allowances=data.get('allowances', 0.0),
            gross_pay=data['gross_pay'],
            tax_deduction=data.get('tax_deduction', 0.0),
            social_security=data.get('social_security', 0.0),
            health_insurance=data.get('health_insurance', 0.0),
            other_deductions=data.get('other_deductions', 0.0),
            total_deductions=data['total_deductions'],
            net_pay=data['net_pay'],
            currency=data.get('currency', 'USD'),
            payment_method=data.get('payment_method', 'bank_transfer'),
            bank_account=data.get('bank_account'),
            created_by=current_user.id
        )
        
        db.session.add(payroll)
        db.session.commit()
        
        # Update HR KPI
        update_user_kpi(current_user.id, 'hr', 'payroll_records_processed', 1)
        
        return jsonify({'message': 'Payroll record created successfully', 'id': payroll.id}), 201

# ============================================================================
# SUPPLY CHAIN MODULE ROUTES
# ============================================================================

@app.route('/api/supply-chain/inventory', methods=['GET', 'POST'])
@jwt_required()
@company_required
def supply_chain_inventory():
    """Advanced inventory management with FIFO/LIFO and expiry tracking"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        inventory_items = InventoryItem.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': item.id,
            'product': {
                'id': item.product.id,
                'name': item.product.name,
                'code': item.product.code,
                'requires_temperature_control': item.product.requires_temperature_control,
                'min_temperature': item.product.min_temperature,
                'max_temperature': item.product.max_temperature
            },
            'location': item.location,
            'batch_number': item.batch_number,
            'lot_number': item.lot_number,
            'quantity': item.quantity,
            'reserved_quantity': item.reserved_quantity,
            'available_quantity': item.quantity - item.reserved_quantity,
            'unit_cost': float(item.unit_cost) if item.unit_cost else 0.0,
            'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
            'manufacturing_date': item.manufacturing_date.isoformat() if item.manufacturing_date else None,
            'status': item.status,
            'temperature_log': json.loads(item.temperature_log) if item.temperature_log else [],
            'photos': json.loads(item.photos) if item.photos else []
        } for item in inventory_items])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        inventory_item = InventoryItem(
            company_id=company.id,
            product_id=data['product_id'],
            location=data.get('location'),
            batch_number=data.get('batch_number'),
            lot_number=data.get('lot_number'),
            quantity=data['quantity'],
            unit_cost=data.get('unit_cost'),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
            manufacturing_date=datetime.strptime(data['manufacturing_date'], '%Y-%m-%d').date() if data.get('manufacturing_date') else None,
            temperature_log=json.dumps(data.get('temperature_log', [])),
            photos=json.dumps(data.get('photos', []))
        )
        
        db.session.add(inventory_item)
        db.session.commit()
        
        # Update Supply Chain KPI
        update_user_kpi(current_user.id, 'supply_chain', 'inventory_items_added', 1)
        
        # Check for expiry alerts
        if inventory_item.expiry_date:
            days_to_expiry = (inventory_item.expiry_date - datetime.utcnow().date()).days
            if days_to_expiry <= 30:  # Alert 30 days before expiry
                create_vigilance_alert(
                    company_id=company.id,
                    alert_type='business',
                    severity='medium' if days_to_expiry > 7 else 'high',
                    module='supply_chain',
                    title='Product Expiry Alert',
                    description=f"Product {inventory_item.product.name} (Batch: {inventory_item.batch_number}) expires in {days_to_expiry} days",
                    affected_entity_type='inventory_item',
                    affected_entity_id=inventory_item.id,
                    threshold_value=30,
                    actual_value=days_to_expiry
                )
        
        return jsonify({'message': 'Inventory item added successfully', 'id': inventory_item.id}), 201

@app.route('/api/supply-chain/purchase-orders', methods=['GET', 'POST'])
@jwt_required()
@company_required
def supply_chain_purchase_orders():
    """Purchase order management with vendor integration"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        purchase_orders = PurchaseOrder.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': po.id,
            'po_number': po.po_number,
            'order_date': po.order_date.isoformat(),
            'expected_delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
            'actual_delivery_date': po.actual_delivery_date.isoformat() if po.actual_delivery_date else None,
            'total_amount': float(po.total_amount),
            'status': po.status,
            'vendor': {
                'id': po.vendor.id,
                'name': po.vendor.name,
                'performance_score': po.vendor.performance_score,
                'risk_score': po.vendor.risk_score
            },
            'creator': {
                'id': po.creator.id,
                'name': f"{po.creator.first_name} {po.creator.last_name}",
                'profile_picture': po.creator.profile_picture
            }
        } for po in purchase_orders])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        purchase_order = PurchaseOrder(
            company_id=company.id,
            vendor_id=data['vendor_id'],
            po_number=f"PO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            order_date=datetime.strptime(data['order_date'], '%Y-%m-%d').date(),
            expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() if data.get('expected_delivery_date') else None,
            total_amount=data['total_amount'],
            tax_amount=data.get('tax_amount', 0.0),
            created_by=current_user.id
        )
        
        db.session.add(purchase_order)
        db.session.commit()
        
        # Update Supply Chain KPI for purchase order creation
        update_user_kpi(current_user.id, 'supply_chain', 'purchase_orders_created', 1)
        
        # Create vigilance alert for high-value purchase orders
        if purchase_order.total_amount > 10000:
            create_vigilance_alert(
                company_id=company.id,
                alert_type='business',
                severity='medium',
                module='supply_chain',
                title='High-Value Purchase Order',
                description=f"Purchase Order {purchase_order.po_number} worth ${purchase_order.total_amount:,.2f} has been created",
                affected_entity_type='purchase_order',
                affected_entity_id=purchase_order.id,
                actual_value=float(purchase_order.total_amount)
            )
        
        return jsonify({'message': 'Purchase order created successfully', 'id': purchase_order.id}), 201

@app.route('/api/supply-chain/courier-shipments', methods=['GET', 'POST'])
@jwt_required()
@company_required
def supply_chain_courier_shipments():
    """Courier management system"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        shipments = CourierShipment.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': s.id,
            'shipment_number': s.shipment_number,
            'courier_company': s.courier_company,
            'service_type': s.service_type,
            'tracking_number': s.tracking_number,
            'recipient_name': s.recipient_name,
            'recipient_address': s.recipient_address,
            'package_weight': s.package_weight,
            'shipping_cost': float(s.shipping_cost) if s.shipping_cost else 0.0,
            'pickup_date': s.pickup_date.isoformat() if s.pickup_date else None,
            'expected_delivery_date': s.expected_delivery_date.isoformat() if s.expected_delivery_date else None,
            'actual_delivery_date': s.actual_delivery_date.isoformat() if s.actual_delivery_date else None,
            'status': s.status,
            'creator': {
                'id': s.creator.id,
                'name': f"{s.creator.first_name} {s.creator.last_name}"
            }
        } for s in shipments])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        shipment = CourierShipment(
            company_id=company.id,
            shipment_number=f"SHIP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            courier_company=data['courier_company'],
            service_type=data.get('service_type', 'standard'),
            tracking_number=data.get('tracking_number'),
            sender_name=data.get('sender_name'),
            sender_address=data.get('sender_address'),
            sender_phone=data.get('sender_phone'),
            recipient_name=data['recipient_name'],
            recipient_address=data['recipient_address'],
            recipient_phone=data.get('recipient_phone'),
            package_weight=data.get('package_weight'),
            package_dimensions=data.get('package_dimensions'),
            declared_value=data.get('declared_value'),
            shipping_cost=data.get('shipping_cost'),
            insurance_cost=data.get('insurance_cost', 0.0),
            pickup_date=datetime.strptime(data['pickup_date'], '%Y-%m-%d').date() if data.get('pickup_date') else None,
            expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() if data.get('expected_delivery_date') else None,
            special_instructions=data.get('special_instructions'),
            created_by=current_user.id
        )
        
        db.session.add(shipment)
        db.session.commit()
        
        # Update Supply Chain KPI
        update_user_kpi(current_user.id, 'supply_chain', 'shipments_created', 1)
        
        return jsonify({'message': 'Courier shipment created successfully', 'id': shipment.id}), 201

# ============================================================================
# DESK MODULE ROUTES
# ============================================================================

@app.route('/api/desk/tickets', methods=['GET', 'POST'])
@jwt_required()
@company_required
def desk_tickets():
    """Enhanced desk module with multi-channel support and SLA"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        tickets = Ticket.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': t.id,
            'ticket_number': t.ticket_number,
            'subject': t.subject,
            'description': t.description,
            'priority': t.priority,
            'status': t.status,
            'category': t.category,
            'channel': t.channel,
            'customer': {
                'id': t.customer.id,
                'name': t.customer.name,
                'email': t.customer.email
            },
            'assignee': {
                'id': t.assignee.id,
                'name': f"{t.assignee.first_name} {t.assignee.last_name}",
                'profile_picture': t.assignee.profile_picture
            } if t.assignee else None,
            'sla_response_time': t.sla_response_time,
            'sla_resolution_time': t.sla_resolution_time,
            'first_response_at': t.first_response_at.isoformat() if t.first_response_at else None,
            'resolved_at': t.resolved_at.isoformat() if t.resolved_at else None,
            'customer_satisfaction': t.customer_satisfaction,
            'created_at': t.created_at.isoformat()
        } for t in tickets])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        ticket = Ticket(
            company_id=company.id,
            customer_id=data['customer_id'],
            ticket_number=f"TKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            subject=data['subject'],
            description=data['description'],
            priority=data.get('priority', 'medium'),
            category=data.get('category'),
            channel=data.get('channel', 'web'),
            assigned_to=data.get('assigned_to'),
            created_by=current_user.id,
            sla_response_time=data.get('sla_response_time', 240),  # 4 hours default
            sla_resolution_time=data.get('sla_resolution_time', 1440),  # 24 hours default
            tags=json.dumps(data.get('tags', []))
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        # Update Desk KPI
        update_user_kpi(current_user.id, 'desk', 'tickets_created', 1)
        
        # Create SLA vigilance alert
        create_vigilance_alert(
            company_id=company.id,
            alert_type='business',
            severity='low',
            module='desk',
            title='New Ticket Created',
            description=f"Ticket {ticket.ticket_number} created with {ticket.priority} priority",
            affected_entity_type='ticket',
            affected_entity_id=ticket.id
        )
        
        return jsonify({'message': 'Ticket created successfully', 'id': ticket.id}), 201

@app.route('/api/desk/work-orders', methods=['GET', 'POST'])
@jwt_required()
@company_required
def desk_work_orders():
    """Work order management with GPS tracking"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        work_orders = WorkOrder.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': wo.id,
            'wo_number': wo.wo_number,
            'title': wo.title,
            'description': wo.description,
            'priority': wo.priority,
            'status': wo.status,
            'scheduled_date': wo.scheduled_date.isoformat() if wo.scheduled_date else None,
            'location': {
                'lat': wo.location_lat,
                'lng': wo.location_lng,
                'address': wo.location_address
            } if wo.location_lat else None,
            'assignee': {
                'id': wo.assignee.id,
                'name': f"{wo.assignee.first_name} {wo.assignee.last_name}",
                'profile_picture': wo.assignee.profile_picture
            },
            'ticket': {
                'id': wo.ticket.id,
                'ticket_number': wo.ticket.ticket_number,
                'subject': wo.ticket.subject
            },
            'labor_hours': wo.labor_hours,
            'total_cost': float(wo.total_cost) if wo.total_cost else 0.0,
            'checkin_time': wo.checkin_time.isoformat() if wo.checkin_time else None,
            'checkout_time': wo.checkout_time.isoformat() if wo.checkout_time else None
        } for wo in work_orders])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        work_order = WorkOrder(
            company_id=company.id,
            ticket_id=data['ticket_id'],
            wo_number=f"WO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            title=data['title'],
            description=data.get('description'),
            assigned_to=data['assigned_to'],
            priority=data.get('priority', 'medium'),
            scheduled_date=datetime.strptime(data['scheduled_date'], '%Y-%m-%d %H:%M:%S') if data.get('scheduled_date') else None,
            location_lat=data.get('location', {}).get('lat'),
            location_lng=data.get('location', {}).get('lng'),
            location_address=data.get('location', {}).get('address')
        )
        
        db.session.add(work_order)
        db.session.commit()
        
        # Update Desk KPI
        update_user_kpi(current_user.id, 'desk', 'work_orders_created', 1)
        
        return jsonify({'message': 'Work order created successfully', 'id': work_order.id}), 201

@app.route('/api/desk/work-orders/<int:wo_id>/checkin', methods=['POST'])
@jwt_required()
@company_required
def desk_work_order_checkin(wo_id):
    """Field agent GPS check-in for work orders"""
    data = request.get_json()
    current_user = get_current_user()
    company = get_current_company()
    
    work_order = WorkOrder.query.filter_by(id=wo_id, company_id=company.id).first()
    if not work_order:
        return jsonify({'error': 'Work order not found'}), 404
    
    if work_order.assigned_to != current_user.id:
        return jsonify({'error': 'Not authorized to check in to this work order'}), 403
    
    work_order.checkin_lat = data['location']['lat']
    work_order.checkin_lng = data['location']['lng']
    work_order.checkin_time = datetime.utcnow()
    work_order.status = 'in_progress'
    work_order.started_at = datetime.utcnow()
    
    db.session.commit()
    
    # Update Desk KPI
    update_user_kpi(current_user.id, 'desk', 'work_order_checkins', 1)
    
    return jsonify({'message': 'Work order check-in successful'}), 200

# ============================================================================
# VENDOR MANAGEMENT ROUTES
# ============================================================================

@app.route('/api/vendors', methods=['GET', 'POST'])
@jwt_required()
@company_required
def vendors():
    """Integrated vendor management across all modules"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        vendors = Vendor.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': v.id,
            'name': v.name,
            'code': v.code,
            'email': v.email,
            'phone': v.phone,
            'address': v.address,
            'contact_person': v.contact_person,
            'website': v.website,
            'vendor_type': v.vendor_type,
            'status': v.status,
            'performance_score': v.performance_score,
            'risk_score': v.risk_score,
            'payment_terms': v.payment_terms,
            'credit_limit': float(v.credit_limit) if v.credit_limit else 0.0,
            'compliance_status': v.compliance_status,
            'certifications': json.loads(v.certifications) if v.certifications else [],
            'created_at': v.created_at.isoformat()
        } for v in vendors])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        vendor = Vendor(
            company_id=company.id,
            name=data['name'],
            code=data.get('code', f"VEN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            contact_person=data.get('contact_person'),
            website=data.get('website'),
            tax_id=data.get('tax_id'),
            payment_terms=data.get('payment_terms'),
            credit_limit=data.get('credit_limit'),
            vendor_type=data.get('vendor_type', 'supplier'),
            certifications=json.dumps(data.get('certifications', []))
        )
        
        db.session.add(vendor)
        db.session.commit()
        
        # Update vendor management KPI
        update_user_kpi(current_user.id, 'vendor_management', 'vendors_onboarded', 1)
        
        return jsonify({'message': 'Vendor created successfully', 'id': vendor.id}), 201

@app.route('/api/vendors/<int:vendor_id>/performance', methods=['GET', 'PUT'])
@jwt_required()
@company_required
def vendor_performance(vendor_id):
    """Vendor performance tracking and scorecards"""
    company = get_current_company()
    
    vendor = Vendor.query.filter_by(id=vendor_id, company_id=company.id).first()
    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'vendor_id': vendor.id,
            'name': vendor.name,
            'performance_score': vendor.performance_score,
            'risk_score': vendor.risk_score,
            'compliance_status': vendor.compliance_status,
            'total_orders': len(vendor.purchase_orders),
            'total_contracts': len(vendor.contracts),
            'on_time_delivery_rate': 0.95,  # Calculate from actual data
            'quality_rating': 4.2,  # Calculate from actual data
            'cost_competitiveness': 0.85  # Calculate from actual data
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        vendor.performance_score = data.get('performance_score', vendor.performance_score)
        vendor.risk_score = data.get('risk_score', vendor.risk_score)
        vendor.compliance_status = data.get('compliance_status', vendor.compliance_status)
        
        db.session.commit()
        
        # Create vigilance alert for performance changes
        if vendor.performance_score < 0.6:  # Low performance
            create_vigilance_alert(
                company_id=company.id,
                alert_type='business',
                severity='medium',
                module='vendor_management',
                title='Low Vendor Performance',
                description=f"Vendor {vendor.name} performance score dropped to {vendor.performance_score}",
                affected_entity_type='vendor',
                affected_entity_id=vendor.id,
                threshold_value=0.6,
                actual_value=vendor.performance_score
            )
        
        return jsonify({'message': 'Vendor performance updated successfully'})

# ============================================================================
# MARKETING MODULE ROUTES
# ============================================================================

@app.route('/api/marketing/campaigns', methods=['GET', 'POST'])
@jwt_required()
@company_required
def marketing_campaigns():
    """Marketing module with e-commerce and social media"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        campaigns = MarketingCampaign.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'campaign_type': c.campaign_type,
            'status': c.status,
            'start_date': c.start_date.isoformat() if c.start_date else None,
            'end_date': c.end_date.isoformat() if c.end_date else None,
            'budget': float(c.budget) if c.budget else 0.0,
            'actual_cost': float(c.actual_cost),
            'target_audience': json.loads(c.target_audience) if c.target_audience else [],
            'channels': json.loads(c.channels) if c.channels else [],
            'impressions': c.impressions,
            'clicks': c.clicks,
            'conversions': c.conversions,
            'leads_generated': c.leads_generated,
            'revenue_generated': float(c.revenue_generated),
            'roi': c.roi,
            'creator': {
                'id': c.creator.id,
                'name': f"{c.creator.first_name} {c.creator.last_name}",
                'profile_picture': c.creator.profile_picture
            }
        } for c in campaigns])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        campaign = MarketingCampaign(
            company_id=company.id,
            name=data['name'],
            description=data.get('description'),
            campaign_type=data.get('campaign_type', 'email'),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
            budget=data.get('budget'),
            target_audience=json.dumps(data.get('target_audience', [])),
            channels=json.dumps(data.get('channels', [])),
            goals=json.dumps(data.get('goals', [])),
            kpis=json.dumps(data.get('kpis', [])),
            created_by=current_user.id
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        # Update Marketing KPI
        update_user_kpi(current_user.id, 'marketing', 'campaigns_created', 1)
        
        return jsonify({'message': 'Marketing campaign created successfully', 'id': campaign.id}), 201

# ============================================================================
# SURVEY MODULE ROUTES
# ============================================================================

@app.route('/api/surveys', methods=['GET', 'POST'])
@jwt_required()
@company_required
def surveys():
    """Survey module with multi-channel distribution"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        surveys = Survey.query.filter_by(company_id=company.id).all()
        return jsonify([{
            'id': s.id,
            'title': s.title,
            'description': s.description,
            'survey_type': s.survey_type,
            'status': s.status,
            'start_date': s.start_date.isoformat() if s.start_date else None,
            'end_date': s.end_date.isoformat() if s.end_date else None,
            'total_responses': s.total_responses,
            'completion_rate': s.completion_rate,
            'average_rating': s.average_rating,
            'target_audience': json.loads(s.target_audience) if s.target_audience else [],
            'distribution_channels': json.loads(s.distribution_channels) if s.distribution_channels else [],
            'questions': json.loads(s.questions) if s.questions else [],
            'creator': {
                'id': s.creator.id,
                'name': f"{s.creator.first_name} {s.creator.last_name}"
            }
        } for s in surveys])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        survey = Survey(
            company_id=company.id,
            title=data['title'],
            description=data.get('description'),
            survey_type=data.get('survey_type', 'customer_satisfaction'),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
            target_audience=json.dumps(data.get('target_audience', [])),
            distribution_channels=json.dumps(data.get('distribution_channels', [])),
            questions=json.dumps(data.get('questions', [])),
            created_by=current_user.id
        )
        
        db.session.add(survey)
        db.session.commit()
        
        # Update Survey KPI
        update_user_kpi(current_user.id, 'surveys', 'surveys_created', 1)
        
        return jsonify({'message': 'Survey created successfully', 'id': survey.id}), 201

# ============================================================================
# COMMUNITY MODULE ROUTES
# ============================================================================

@app.route('/api/community/posts', methods=['GET', 'POST'])
@jwt_required()
@company_required
def community_posts():
    """Internal community app with location and mentioning"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        posts = CommunityPost.query.filter_by(company_id=company.id).order_by(CommunityPost.created_at.desc()).all()
        return jsonify([{
            'id': p.id,
            'content': p.content,
            'post_type': p.post_type,
            'media_urls': json.loads(p.media_urls) if p.media_urls else [],
            'location': {
                'lat': p.location_lat,
                'lng': p.location_lng,
                'name': p.location_name
            } if p.location_lat else None,
            'mentioned_users': json.loads(p.mentioned_users) if p.mentioned_users else [],
            'tags': json.loads(p.tags) if p.tags else [],
            'likes_count': p.likes_count,
            'comments_count': p.comments_count,
            'shares_count': p.shares_count,
            'is_pinned': p.is_pinned,
            'visibility': p.visibility,
            'author': {
                'id': p.author.id,
                'name': f"{p.author.first_name} {p.author.last_name}",
                'profile_picture': p.author.profile_picture,
                'department': p.author.department,
                'position': p.author.position
            },
            'created_at': p.created_at.isoformat()
        } for p in posts])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        post = CommunityPost(
            company_id=company.id,
            author_id=current_user.id,
            content=data['content'],
            post_type=data.get('post_type', 'text'),
            media_urls=json.dumps(data.get('media_urls', [])),
            location_lat=data.get('location', {}).get('lat'),
            location_lng=data.get('location', {}).get('lng'),
            location_name=data.get('location', {}).get('name'),
            mentioned_users=json.dumps(data.get('mentioned_users', [])),
            tags=json.dumps(data.get('tags', [])),
            visibility=data.get('visibility', 'company')
        )
        
        db.session.add(post)
        db.session.commit()
        
        # Update Community KPI
        update_user_kpi(current_user.id, 'community', 'posts_created', 1)
        
        # Send notifications to mentioned users
        if data.get('mentioned_users'):
            for user_id in data['mentioned_users']:
                create_vigilance_alert(
                    company_id=company.id,
                    alert_type='business',
                    severity='low',
                    module='community',
                    title='You were mentioned in a post',
                    description=f"{current_user.first_name} {current_user.last_name} mentioned you in a community post",
                    affected_entity_type='user',
                    affected_entity_id=user_id
                )
        
        return jsonify({'message': 'Community post created successfully', 'id': post.id}), 201

@app.route('/api/community/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
@company_required
def community_like_post(post_id):
    """Like/unlike community posts"""
    company = get_current_company()
    current_user = get_current_user()
    
    post = CommunityPost.query.filter_by(id=post_id, company_id=company.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Check if already liked
    existing_like = CommunityLike.query.filter_by(
        post_id=post_id,
        user_id=current_user.id,
        company_id=company.id
    ).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
        action = 'unliked'
    else:
        # Like
        like = CommunityLike(
            company_id=company.id,
            post_id=post_id,
            user_id=current_user.id,
            reaction_type='like'
        )
        db.session.add(like)
        post.likes_count += 1
        action = 'liked'
    
    db.session.commit()
    
    # Update Community KPI
    update_user_kpi(current_user.id, 'community', 'post_interactions', 1)
    
    return jsonify({'message': f'Post {action} successfully', 'likes_count': post.likes_count}), 200

# ============================================================================
# CRUD UTILITIES AND HELPERS
# ============================================================================

def roles_required(*roles):
    """Decorator to enforce role-based access control"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Authentication required'}), 401
            
            if current_user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def paginate_query(query, page=1, per_page=20):
    """Utility function for pagination with metadata"""
    max_per_page = 100
    per_page = min(per_page, max_per_page)
    
    paginated = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': paginated.items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'pages': paginated.pages,
            'has_prev': paginated.has_prev,
            'has_next': paginated.has_next,
            'prev_num': paginated.prev_num,
            'next_num': paginated.next_num
        }
    }

def validate_required_fields(data, required_fields):
    """Validate required fields in request data"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        return {'error': f'Missing required fields: {", ".join(missing_fields)}'}
    return None

def serialize_datetime(dt):
    """Serialize datetime to ISO8601 format"""
    return dt.isoformat() if dt else None

def serialize_decimal(decimal_val):
    """Serialize Decimal to float"""
    return float(decimal_val) if decimal_val else 0.0

def parse_search_query(query_string, searchable_fields):
    """Parse search query for filtering"""
    if not query_string:
        return []
    
    filters = []
    for field in searchable_fields:
        if hasattr(field, 'like'):
            filters.append(field.like(f'%{query_string}%'))
    return filters

def apply_filters(query, filters):
    """Apply filters to SQLAlchemy query"""
    if filters:
        # Use db.or_ instead of importing or_
        query = query.filter(db.or_(*filters))
    return query

def handle_database_error(e):
    """Centralized database error handling"""
    db.session.rollback()
    logger.error(f"Database error: {str(e)}")
    
    error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
    
    if 'unique constraint' in error_message.lower() or 'duplicate' in error_message.lower():
        return jsonify({'error': 'A record with this information already exists'}), 409
    elif 'foreign key constraint' in error_message.lower():
        return jsonify({'error': 'Referenced record does not exist'}), 400
    elif 'not null constraint' in error_message.lower():
        return jsonify({'error': 'Required field is missing'}), 400
    else:
        return jsonify({'error': 'Database operation failed'}), 500

def create_safe_filename(filename):
    """Create safe filename for uploads"""
    import re
    # Remove any dangerous characters and limit length
    filename = re.sub(r'[^\w\-_\.]', '', filename)
    return filename[:100]  # Limit length

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# ============================================================================
# COMPLETE CRUD ENDPOINTS FOR ALL MODULES
# ============================================================================

# Company Management (Admin only)
@app.route('/api/companies', methods=['GET', 'POST'])
@jwt_required()
def companies():
    """Company management - Admin only"""
    current_user = get_current_user()
    
    if request.method == 'GET':
        # Only admins can list all companies
        if current_user.role != 'admin':
            # Regular users can only see their own company
            companies = [current_user.company]
        else:
            companies = Company.query.all()
        
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'code': c.code,
            'domain': c.domain,
            'logo_url': c.logo_url,
            'address': c.address,
            'phone': c.phone,
            'email': c.email,
            'is_active': c.is_active,
            'created_at': serialize_datetime(c.created_at)
        } for c in companies])
    
    elif request.method == 'POST':
        # Only admins can create companies
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        try:
            data = request.get_json()
            
            # Validate required fields
            validation_error = validate_required_fields(data, ['name', 'code'])
            if validation_error:
                return jsonify(validation_error), 400
            
            company = Company(
                name=data['name'],
                code=data['code'],
                domain=data.get('domain'),
                logo_url=data.get('logo_url'),
                address=data.get('address'),
                phone=data.get('phone'),
                email=data.get('email')
            )
            
            db.session.add(company)
            db.session.commit()
            
            return jsonify({'message': 'Company created successfully', 'id': company.id}), 201
            
        except Exception as e:
            return handle_database_error(e)

@app.route('/api/companies/<int:company_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
@roles_required('admin')
def company_detail(company_id):
    """Company detail operations - Admin only"""
    company = Company.query.get(company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': company.id,
            'name': company.name,
            'code': company.code,
            'domain': company.domain,
            'logo_url': company.logo_url,
            'address': company.address,
            'phone': company.phone,
            'email': company.email,
            'is_active': company.is_active,
            'created_at': serialize_datetime(company.created_at),
            'user_count': len(company.users),
            'customer_count': len(company.customers),
            'vendor_count': len(company.vendors)
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            company.name = data.get('name', company.name)
            company.code = data.get('code', company.code)
            company.domain = data.get('domain', company.domain)
            company.logo_url = data.get('logo_url', company.logo_url)
            company.address = data.get('address', company.address)
            company.phone = data.get('phone', company.phone)
            company.email = data.get('email', company.email)
            company.is_active = data.get('is_active', company.is_active)
            
            db.session.commit()
            
            return jsonify({'message': 'Company updated successfully'})
            
        except Exception as e:
            return handle_database_error(e)
    
    elif request.method == 'DELETE':
        try:
            # Soft delete by deactivating
            company.is_active = False
            db.session.commit()
            
            return jsonify({'message': 'Company deactivated successfully'})
            
        except Exception as e:
            return handle_database_error(e)

# User Management
@app.route('/api/users', methods=['GET', 'POST'])
@jwt_required()
@company_required
def users():
    """User management with company isolation"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        # Parse pagination and search parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('q', '')
        
        # Build query with company filter
        query = User.query.filter_by(company_id=company.id)
        
        # Apply search filters
        if search:
            searchable_fields = [User.username, User.email, User.first_name, User.last_name]
            filters = parse_search_query(search, searchable_fields)
            query = apply_filters(query, filters)
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify({
            'users': [{
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'profile_picture': u.profile_picture,
                'phone': u.phone,
                'department': u.department,
                'position': u.position,
                'role': u.role,
                'is_active': u.is_active,
                'last_login': serialize_datetime(u.last_login),
                'created_at': serialize_datetime(u.created_at)
            } for u in result['items']],
            'pagination': result['pagination']
        })
    
    elif request.method == 'POST':
        # Only admins and managers can create users
        if current_user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        try:
            data = request.get_json()
            
            # Validate required fields
            validation_error = validate_required_fields(data, 
                ['username', 'email', 'password', 'first_name', 'last_name'])
            if validation_error:
                return jsonify(validation_error), 400
            
            # Check if user already exists
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'error': 'Username already exists'}), 409
            
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 409
            
            user = User(
                company_id=company.id,  # Force company isolation
                username=data['username'],
                email=data['email'],
                password_hash=generate_password_hash(data['password']),
                first_name=data['first_name'],
                last_name=data['last_name'],
                profile_picture=data.get('profile_picture'),
                phone=data.get('phone'),
                department=data.get('department'),
                position=data.get('position'),
                manager_id=data.get('manager_id'),
                birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d').date() if data.get('birth_date') else None,
                marital_status=data.get('marital_status'),
                emergency_contact=data.get('emergency_contact'),
                skills=json.dumps(data.get('skills', [])),
                certifications=json.dumps(data.get('certifications', [])),
                role=data.get('role', 'user')
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Update HR KPI
            update_user_kpi(current_user.id, 'hr', 'users_created', 1)
            
            return jsonify({'message': 'User created successfully', 'id': user.id}), 201
            
        except Exception as e:
            return handle_database_error(e)

@app.route('/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
@company_required
def user_detail(user_id):
    """User detail operations with company isolation"""
    company = get_current_company()
    current_user = get_current_user()
    
    user = User.query.filter_by(id=user_id, company_id=company.id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_picture': user.profile_picture,
            'phone': user.phone,
            'department': user.department,
            'position': user.position,
            'manager': {
                'id': user.manager.id,
                'name': f"{user.manager.first_name} {user.manager.last_name}"
            } if user.manager else None,
            'birth_date': user.birth_date.isoformat() if user.birth_date else None,
            'marital_status': user.marital_status,
            'emergency_contact': user.emergency_contact,
            'skills': json.loads(user.skills) if user.skills else [],
            'certifications': json.loads(user.certifications) if user.certifications else [],
            'role': user.role,
            'is_active': user.is_active,
            'last_login': serialize_datetime(user.last_login),
            'current_location': {
                'lat': user.current_location_lat,
                'lng': user.current_location_lng,
                'address': user.current_location_address
            } if user.current_location_lat else None,
            'created_at': serialize_datetime(user.created_at),
            'updated_at': serialize_datetime(user.updated_at)
        })
    
    elif request.method == 'PUT':
        # Users can update their own profile, admins/managers can update others
        if user.id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        try:
            data = request.get_json()
            
            # Update allowed fields
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.profile_picture = data.get('profile_picture', user.profile_picture)
            user.phone = data.get('phone', user.phone)
            
            # Only admins can change role and department
            if current_user.role == 'admin':
                user.department = data.get('department', user.department)
                user.position = data.get('position', user.position)
                user.role = data.get('role', user.role)
                user.is_active = data.get('is_active', user.is_active)
                user.manager_id = data.get('manager_id', user.manager_id)
            
            # Personal info updates
            if data.get('birth_date'):
                user.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            user.marital_status = data.get('marital_status', user.marital_status)
            user.emergency_contact = data.get('emergency_contact', user.emergency_contact)
            
            if data.get('skills'):
                user.skills = json.dumps(data['skills'])
            if data.get('certifications'):
                user.certifications = json.dumps(data['certifications'])
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'message': 'User updated successfully'})
            
        except Exception as e:
            return handle_database_error(e)
    
    elif request.method == 'DELETE':
        # Only admins can delete users
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        try:
            # Soft delete by deactivating
            user.is_active = False
            db.session.commit()
            
            return jsonify({'message': 'User deactivated successfully'})
            
        except Exception as e:
            return handle_database_error(e)

# Products Management
@app.route('/api/products', methods=['GET', 'POST'])
@jwt_required()
@company_required
def products():
    """Product catalog management with company isolation"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        # Parse pagination and search parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('q', '')
        category = request.args.get('category', '')
        
        # Build query with company filter
        query = Product.query.filter_by(company_id=company.id, is_active=True)
        
        # Apply category filter
        if category:
            query = query.filter_by(category=category)
        
        # Apply search filters
        if search:
            searchable_fields = [Product.name, Product.code, Product.description]
            filters = parse_search_query(search, searchable_fields)
            query = apply_filters(query, filters)
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify({
            'products': [{
                'id': p.id,
                'name': p.name,
                'code': p.code,
                'description': p.description,
                'category': p.category,
                'unit_of_measure': p.unit_of_measure,
                'cost_price': serialize_decimal(p.cost_price),
                'selling_price': serialize_decimal(p.selling_price),
                'weight': p.weight,
                'dimensions': p.dimensions,
                'barcode': p.barcode,
                'qr_code': p.qr_code,
                'track_by_batch': p.track_by_batch,
                'track_by_lot': p.track_by_lot,
                'requires_temperature_control': p.requires_temperature_control,
                'min_temperature': p.min_temperature,
                'max_temperature': p.max_temperature,
                'shelf_life_days': p.shelf_life_days,
                'reorder_level': p.reorder_level,
                'max_stock_level': p.max_stock_level,
                'created_at': serialize_datetime(p.created_at),
                'updated_at': serialize_datetime(p.updated_at)
            } for p in result['items']],
            'pagination': result['pagination']
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            validation_error = validate_required_fields(data, ['name', 'code'])
            if validation_error:
                return jsonify(validation_error), 400
            
            product = Product(
                company_id=company.id,
                name=data['name'],
                code=data['code'],
                description=data.get('description'),
                category=data.get('category'),
                unit_of_measure=data.get('unit_of_measure'),
                cost_price=data.get('cost_price'),
                selling_price=data.get('selling_price'),
                weight=data.get('weight'),
                dimensions=data.get('dimensions'),
                barcode=data.get('barcode'),
                qr_code=data.get('qr_code'),
                track_by_batch=data.get('track_by_batch', False),
                track_by_lot=data.get('track_by_lot', False),
                requires_temperature_control=data.get('requires_temperature_control', False),
                min_temperature=data.get('min_temperature'),
                max_temperature=data.get('max_temperature'),
                shelf_life_days=data.get('shelf_life_days'),
                reorder_level=data.get('reorder_level', 0.0),
                max_stock_level=data.get('max_stock_level')
            )
            
            db.session.add(product)
            db.session.commit()
            
            # Update product management KPI
            update_user_kpi(current_user.id, 'product_management', 'products_created', 1)
            
            return jsonify({'message': 'Product created successfully', 'id': product.id}), 201
            
        except Exception as e:
            return handle_database_error(e)

@app.route('/api/products/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
@company_required
def product_detail(product_id):
    """Product detail operations with company isolation"""
    company = get_current_company()
    current_user = get_current_user()
    
    product = Product.query.filter_by(id=product_id, company_id=company.id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if request.method == 'GET':
        # Get inventory information
        inventory_items = InventoryItem.query.filter_by(product_id=product.id, company_id=company.id).all()
        total_quantity = sum(item.quantity for item in inventory_items)
        available_quantity = sum(item.quantity - item.reserved_quantity for item in inventory_items)
        
        return jsonify({
            'id': product.id,
            'name': product.name,
            'code': product.code,
            'description': product.description,
            'category': product.category,
            'unit_of_measure': product.unit_of_measure,
            'cost_price': serialize_decimal(product.cost_price),
            'selling_price': serialize_decimal(product.selling_price),
            'weight': product.weight,
            'dimensions': product.dimensions,
            'barcode': product.barcode,
            'qr_code': product.qr_code,
            'track_by_batch': product.track_by_batch,
            'track_by_lot': product.track_by_lot,
            'requires_temperature_control': product.requires_temperature_control,
            'min_temperature': product.min_temperature,
            'max_temperature': product.max_temperature,
            'shelf_life_days': product.shelf_life_days,
            'reorder_level': product.reorder_level,
            'max_stock_level': product.max_stock_level,
            'is_active': product.is_active,
            'inventory': {
                'total_quantity': total_quantity,
                'available_quantity': available_quantity,
                'reserved_quantity': total_quantity - available_quantity,
                'below_reorder_level': available_quantity < product.reorder_level
            },
            'created_at': serialize_datetime(product.created_at),
            'updated_at': serialize_datetime(product.updated_at)
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Update product fields
            product.name = data.get('name', product.name)
            product.code = data.get('code', product.code)
            product.description = data.get('description', product.description)
            product.category = data.get('category', product.category)
            product.unit_of_measure = data.get('unit_of_measure', product.unit_of_measure)
            product.cost_price = data.get('cost_price', product.cost_price)
            product.selling_price = data.get('selling_price', product.selling_price)
            product.weight = data.get('weight', product.weight)
            product.dimensions = data.get('dimensions', product.dimensions)
            product.barcode = data.get('barcode', product.barcode)
            product.qr_code = data.get('qr_code', product.qr_code)
            product.track_by_batch = data.get('track_by_batch', product.track_by_batch)
            product.track_by_lot = data.get('track_by_lot', product.track_by_lot)
            product.requires_temperature_control = data.get('requires_temperature_control', product.requires_temperature_control)
            product.min_temperature = data.get('min_temperature', product.min_temperature)
            product.max_temperature = data.get('max_temperature', product.max_temperature)
            product.shelf_life_days = data.get('shelf_life_days', product.shelf_life_days)
            product.reorder_level = data.get('reorder_level', product.reorder_level)
            product.max_stock_level = data.get('max_stock_level', product.max_stock_level)
            product.is_active = data.get('is_active', product.is_active)
            product.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({'message': 'Product updated successfully'})
            
        except Exception as e:
            return handle_database_error(e)
    
    elif request.method == 'DELETE':
        try:
            # Soft delete by deactivating
            product.is_active = False
            product.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'message': 'Product deactivated successfully'})
            
        except Exception as e:
            return handle_database_error(e)

# Contract Management
@app.route('/api/contracts', methods=['GET', 'POST'])
@jwt_required()
@company_required
def contracts():
    """Contract lifecycle management with company isolation"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        # Parse pagination and search parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('q', '')
        contract_type = request.args.get('type', '')
        status = request.args.get('status', '')
        
        # Build query with company filter
        query = Contract.query.filter_by(company_id=company.id)
        
        # Apply filters
        if contract_type:
            query = query.filter_by(contract_type=contract_type)
        if status:
            query = query.filter_by(status=status)
        
        # Apply search filters
        if search:
            searchable_fields = [Contract.title, Contract.contract_number, Contract.description]
            filters = parse_search_query(search, searchable_fields)
            query = apply_filters(query, filters)
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify({
            'contracts': [{
                'id': c.id,
                'contract_number': c.contract_number,
                'title': c.title,
                'description': c.description,
                'contract_type': c.contract_type,
                'status': c.status,
                'start_date': c.start_date.isoformat() if c.start_date else None,
                'end_date': c.end_date.isoformat() if c.end_date else None,
                'auto_renewal': c.auto_renewal,
                'renewal_period': c.renewal_period,
                'contract_value': serialize_decimal(c.contract_value),
                'currency': c.currency,
                'payment_terms': c.payment_terms,
                'risk_score': c.risk_score,
                'compliance_status': c.compliance_status,
                'vendor': {
                    'id': c.vendor.id,
                    'name': c.vendor.name
                } if c.vendor else None,
                'customer': {
                    'id': c.customer.id,
                    'name': c.customer.name
                } if c.customer else None,
                'creator': {
                    'id': c.creator.id,
                    'name': f"{c.creator.first_name} {c.creator.last_name}"
                },
                'created_at': serialize_datetime(c.created_at),
                'updated_at': serialize_datetime(c.updated_at)
            } for c in result['items']],
            'pagination': result['pagination']
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            validation_error = validate_required_fields(data, ['title', 'contract_type'])
            if validation_error:
                return jsonify(validation_error), 400
            
            contract = Contract(
                company_id=company.id,
                vendor_id=data.get('vendor_id'),
                customer_id=data.get('customer_id'),
                contract_number=f"CTR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                title=data['title'],
                description=data.get('description'),
                contract_type=data['contract_type'],
                start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
                end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
                auto_renewal=data.get('auto_renewal', False),
                renewal_period=data.get('renewal_period'),
                contract_value=data.get('contract_value'),
                currency=data.get('currency', 'USD'),
                payment_terms=data.get('payment_terms'),
                document_url=data.get('document_url'),
                created_by=current_user.id
            )
            
            db.session.add(contract)
            db.session.commit()
            
            # Update contract management KPI
            update_user_kpi(current_user.id, 'contract_management', 'contracts_created', 1)
            
            return jsonify({'message': 'Contract created successfully', 'id': contract.id}), 201
            
        except Exception as e:
            return handle_database_error(e)

@app.route('/api/contracts/<int:contract_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
@company_required
def contract_detail(contract_id):
    """Contract detail operations with company isolation"""
    company = get_current_company()
    current_user = get_current_user()
    
    contract = Contract.query.filter_by(id=contract_id, company_id=company.id).first()
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': contract.id,
            'contract_number': contract.contract_number,
            'title': contract.title,
            'description': contract.description,
            'contract_type': contract.contract_type,
            'status': contract.status,
            'start_date': contract.start_date.isoformat() if contract.start_date else None,
            'end_date': contract.end_date.isoformat() if contract.end_date else None,
            'auto_renewal': contract.auto_renewal,
            'renewal_period': contract.renewal_period,
            'contract_value': serialize_decimal(contract.contract_value),
            'currency': contract.currency,
            'payment_terms': contract.payment_terms,
            'risk_score': contract.risk_score,
            'compliance_status': contract.compliance_status,
            'document_url': contract.document_url,
            'digital_signature_url': contract.digital_signature_url,
            'vendor': {
                'id': contract.vendor.id,
                'name': contract.vendor.name,
                'email': contract.vendor.email,
                'phone': contract.vendor.phone
            } if contract.vendor else None,
            'customer': {
                'id': contract.customer.id,
                'name': contract.customer.name,
                'email': contract.customer.email,
                'phone': contract.customer.phone
            } if contract.customer else None,
            'creator': {
                'id': contract.creator.id,
                'name': f"{contract.creator.first_name} {contract.creator.last_name}",
                'email': contract.creator.email
            },
            'approver': {
                'id': contract.approver.id,
                'name': f"{contract.approver.first_name} {contract.approver.last_name}"
            } if contract.approver else None,
            'created_at': serialize_datetime(contract.created_at),
            'updated_at': serialize_datetime(contract.updated_at)
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Update contract fields
            contract.title = data.get('title', contract.title)
            contract.description = data.get('description', contract.description)
            contract.contract_type = data.get('contract_type', contract.contract_type)
            contract.status = data.get('status', contract.status)
            
            if data.get('start_date'):
                contract.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            if data.get('end_date'):
                contract.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                
            contract.auto_renewal = data.get('auto_renewal', contract.auto_renewal)
            contract.renewal_period = data.get('renewal_period', contract.renewal_period)
            contract.contract_value = data.get('contract_value', contract.contract_value)
            contract.currency = data.get('currency', contract.currency)
            contract.payment_terms = data.get('payment_terms', contract.payment_terms)
            contract.risk_score = data.get('risk_score', contract.risk_score)
            contract.compliance_status = data.get('compliance_status', contract.compliance_status)
            contract.document_url = data.get('document_url', contract.document_url)
            contract.digital_signature_url = data.get('digital_signature_url', contract.digital_signature_url)
            
            # Only certain roles can approve contracts
            if data.get('approved_by') and current_user.role in ['admin', 'manager']:
                contract.approved_by = data['approved_by']
            
            contract.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Create vigilance alert for high-risk contracts
            if contract.risk_score and contract.risk_score > 0.7:
                create_vigilance_alert(
                    company_id=company.id,
                    alert_type='business',
                    severity='high',
                    module='contract_management',
                    title='High-Risk Contract',
                    description=f"Contract {contract.contract_number} has a high risk score of {contract.risk_score}",
                    affected_entity_type='contract',
                    affected_entity_id=contract.id,
                    threshold_value=0.7,
                    actual_value=contract.risk_score
                )
            
            return jsonify({'message': 'Contract updated successfully'})
            
        except Exception as e:
            return handle_database_error(e)
    
    elif request.method == 'DELETE':
        try:
            # Only admins can delete contracts
            if current_user.role != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            # Change status to cancelled instead of hard delete
            contract.status = 'cancelled'
            contract.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'message': 'Contract cancelled successfully'})
            
        except Exception as e:
            return handle_database_error(e)

# Business Analytics Management
@app.route('/api/business-analytics', methods=['GET', 'POST'])
@jwt_required()
@company_required
def business_analytics():
    """Business analysis and reporting with company isolation"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        # Parse pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        report_type = request.args.get('type', '')
        
        # Build query with company filter
        query = BusinessAnalytics.query.filter_by(company_id=company.id)
        
        if report_type:
            query = query.filter_by(report_type=report_type)
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify({
            'reports': [{
                'id': r.id,
                'report_name': r.report_name,
                'report_type': r.report_type,
                'data_sources': json.loads(r.data_sources) if r.data_sources else [],
                'metrics': json.loads(r.metrics) if r.metrics else [],
                'filters': json.loads(r.filters) if r.filters else {},
                'date_range_start': r.date_range_start.isoformat() if r.date_range_start else None,
                'date_range_end': r.date_range_end.isoformat() if r.date_range_end else None,
                'insights': r.insights,
                'recommendations': r.recommendations,
                'is_automated': r.is_automated,
                'schedule_frequency': r.schedule_frequency,
                'last_run_at': serialize_datetime(r.last_run_at),
                'next_run_at': serialize_datetime(r.next_run_at),
                'creator': {
                    'id': r.creator.id,
                    'name': f"{r.creator.first_name} {r.creator.last_name}"
                },
                'created_at': serialize_datetime(r.created_at),
                'updated_at': serialize_datetime(r.updated_at)
            } for r in result['items']],
            'pagination': result['pagination']
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            validation_error = validate_required_fields(data, ['report_name', 'report_type'])
            if validation_error:
                return jsonify(validation_error), 400
            
            analytics = BusinessAnalytics(
                company_id=company.id,
                report_name=data['report_name'],
                report_type=data['report_type'],
                data_sources=json.dumps(data.get('data_sources', [])),
                metrics=json.dumps(data.get('metrics', [])),
                filters=json.dumps(data.get('filters', {})),
                date_range_start=datetime.strptime(data['date_range_start'], '%Y-%m-%d').date() if data.get('date_range_start') else None,
                date_range_end=datetime.strptime(data['date_range_end'], '%Y-%m-%d').date() if data.get('date_range_end') else None,
                visualization_config=json.dumps(data.get('visualization_config', {})),
                is_automated=data.get('is_automated', False),
                schedule_frequency=data.get('schedule_frequency'),
                created_by=current_user.id
            )
            
            db.session.add(analytics)
            db.session.commit()
            
            # Update analytics KPI
            update_user_kpi(current_user.id, 'business_analytics', 'reports_created', 1)
            
            return jsonify({'message': 'Business analytics report created successfully', 'id': analytics.id}), 201
            
        except Exception as e:
            return handle_database_error(e)

# Compliance Audit Management
@app.route('/api/compliance-audits', methods=['GET', 'POST'])
@jwt_required()
@company_required
def compliance_audits():
    """Compliance and quality management with company isolation"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        # Parse pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        audit_type = request.args.get('type', '')
        status = request.args.get('status', '')
        
        # Build query with company filter
        query = ComplianceAudit.query.filter_by(company_id=company.id)
        
        if audit_type:
            query = query.filter_by(audit_type=audit_type)
        if status:
            query = query.filter_by(status=status)
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify({
            'audits': [{
                'id': a.id,
                'audit_type': a.audit_type,
                'title': a.title,
                'description': a.description,
                'standard': a.standard,
                'scope': a.scope,
                'auditee_department': a.auditee_department,
                'scheduled_date': a.scheduled_date.isoformat() if a.scheduled_date else None,
                'actual_date': a.actual_date.isoformat() if a.actual_date else None,
                'status': a.status,
                'findings': json.loads(a.findings) if a.findings else [],
                'non_conformances': json.loads(a.non_conformances) if a.non_conformances else [],
                'corrective_actions': json.loads(a.corrective_actions) if a.corrective_actions else [],
                'preventive_actions': json.loads(a.preventive_actions) if a.preventive_actions else [],
                'overall_rating': a.overall_rating,
                'follow_up_required': a.follow_up_required,
                'follow_up_date': a.follow_up_date.isoformat() if a.follow_up_date else None,
                'auditor': {
                    'id': a.auditor.id,
                    'name': f"{a.auditor.first_name} {a.auditor.last_name}"
                },
                'created_at': serialize_datetime(a.created_at),
                'updated_at': serialize_datetime(a.updated_at)
            } for a in result['items']],
            'pagination': result['pagination']
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            validation_error = validate_required_fields(data, ['audit_type', 'title', 'auditor_id'])
            if validation_error:
                return jsonify(validation_error), 400
            
            audit = ComplianceAudit(
                company_id=company.id,
                audit_type=data['audit_type'],
                title=data['title'],
                description=data.get('description'),
                standard=data.get('standard'),
                scope=data.get('scope'),
                auditor_id=data['auditor_id'],
                auditee_department=data.get('auditee_department'),
                scheduled_date=datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date() if data.get('scheduled_date') else None
            )
            
            db.session.add(audit)
            db.session.commit()
            
            # Update compliance KPI
            update_user_kpi(current_user.id, 'compliance', 'audits_scheduled', 1)
            
            return jsonify({'message': 'Compliance audit created successfully', 'id': audit.id}), 201
            
        except Exception as e:
            return handle_database_error(e)

# Document Signature Management
@app.route('/api/document-signatures', methods=['GET', 'POST'])
@jwt_required()
@company_required
def document_signatures():
    """Digital signature workflow with company isolation"""
    company = get_current_company()
    current_user = get_current_user()
    
    if request.method == 'GET':
        # Parse pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        document_type = request.args.get('type', '')
        status = request.args.get('status', '')
        
        # Build query with company filter
        query = DocumentSignature.query.filter_by(company_id=company.id)
        
        if document_type:
            query = query.filter_by(document_type=document_type)
        if status:
            query = query.filter_by(signature_status=status)
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify({
            'documents': [{
                'id': d.id,
                'document_name': d.document_name,
                'document_type': d.document_type,
                'document_url': d.document_url,
                'original_document_url': d.original_document_url,
                'module_source': d.module_source,
                'source_record_id': d.source_record_id,
                'signers': json.loads(d.signers) if d.signers else [],
                'signature_status': d.signature_status,
                'signing_order': json.loads(d.signing_order) if d.signing_order else [],
                'current_signer_index': d.current_signer_index,
                'expiry_date': serialize_datetime(d.expiry_date),
                'completed_at': serialize_datetime(d.completed_at),
                'certificate_url': d.certificate_url,
                'ocr_extracted_data': json.loads(d.ocr_extracted_data) if d.ocr_extracted_data else {},
                'auto_archive_code': d.auto_archive_code,
                'archive_location': d.archive_location,
                'creator': {
                    'id': d.creator.id,
                    'name': f"{d.creator.first_name} {d.creator.last_name}"
                },
                'created_at': serialize_datetime(d.created_at),
                'updated_at': serialize_datetime(d.updated_at)
            } for d in result['items']],
            'pagination': result['pagination']
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            validation_error = validate_required_fields(data, ['document_name', 'document_url', 'signers'])
            if validation_error:
                return jsonify(validation_error), 400
            
            document = DocumentSignature(
                company_id=company.id,
                document_name=data['document_name'],
                document_type=data.get('document_type', 'contract'),
                document_url=data['document_url'],
                original_document_url=data.get('original_document_url'),
                module_source=data.get('module_source'),
                source_record_id=data.get('source_record_id'),
                signers=json.dumps(data['signers']),
                signing_order=json.dumps(data.get('signing_order', [])),
                expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d %H:%M:%S') if data.get('expiry_date') else None,
                auto_archive_code=data.get('auto_archive_code'),
                created_by=current_user.id
            )
            
            db.session.add(document)
            db.session.commit()
            
            # Update document management KPI
            update_user_kpi(current_user.id, 'document_management', 'documents_created', 1)
            
            return jsonify({'message': 'Document signature workflow created successfully', 'id': document.id}), 201
            
        except Exception as e:
            return handle_database_error(e)

# File Upload Endpoints
@app.route('/api/upload', methods=['POST'])
@jwt_required()
@company_required
def file_upload():
    """Safe file upload with validation"""
    try:
        current_user = get_current_user()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Create safe filename
        filename = create_safe_filename(file.filename)
        
        # Create upload folder if it doesn't exist
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        import os
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_folder, f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}")
        file.save(file_path)
        
        # Update file upload KPI
        update_user_kpi(current_user.id, 'system', 'files_uploaded', 1)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'file_url': f'/uploads/{os.path.basename(file_path)}',
            'file_size': os.path.getsize(file_path)
        }), 201
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500

# API Metadata Endpoint
@app.route('/api/meta', methods=['GET'])
@jwt_required()
def api_metadata():
    """API metadata and resource information"""
    return jsonify({
        'version': '2.0',
        'modules': {
            'crm': {
                'resources': ['customers', 'deals', 'quotes'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'finance': {
                'resources': ['invoices', 'vendor-payments'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'hr': {
                'resources': ['employees', 'attendance', 'leave-requests', 'training-programs', 'payroll'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'supply-chain': {
                'resources': ['inventory', 'purchase-orders', 'courier-shipments'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'desk': {
                'resources': ['tickets', 'work-orders'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'vendor-management': {
                'resources': ['vendors'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'marketing': {
                'resources': ['campaigns'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'surveys': {
                'resources': ['surveys', 'survey-responses'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'community': {
                'resources': ['posts', 'comments', 'likes'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'core': {
                'resources': ['companies', 'users', 'products', 'contracts'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'compliance': {
                'resources': ['compliance-audits'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'business-analytics': {
                'resources': ['business-analytics'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            },
            'document-management': {
                'resources': ['document-signatures'],
                'operations': ['list', 'create', 'read', 'update', 'delete']
            }
        },
        'features': {
            'pagination': True,
            'search': True,
            'filtering': True,
            'company_isolation': True,
            'rbac': True,
            'kpi_tracking': True,
            'vigilance_alerts': True,
            'file_uploads': True
        },
        'authentication': {
            'type': 'JWT',
            'endpoints': {
                'login': '/api/auth/login',
                'register': '/api/auth/register'
            }
        }
    })

# Health Check Endpoint (maintain existing)
@app.route('/api/health', methods=['GET'])
def health_check():
    """System health check"""
    return jsonify({
        'status': 'ok',
        'env': os.environ.get('FLASK_ENV', 'development'),
        'version': '2.0',
        'timestamp': datetime.utcnow().isoformat()
    })

# Profile endpoint (maintain existing functionality)
@app.route('/api/profile', methods=['GET'])
@jwt_required()
def profile():
    """Get current user profile"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'profile_picture': current_user.profile_picture,
        'phone': current_user.phone,
        'department': current_user.department,
        'position': current_user.position,
        'role': current_user.role,
        'company': {
            'id': current_user.company.id,
            'name': current_user.company.name,
            'code': current_user.company.code
        },
        'last_login': serialize_datetime(current_user.last_login),
        'current_location': {
            'lat': current_user.current_location_lat,
            'lng': current_user.current_location_lng,
            'address': current_user.current_location_address
        } if current_user.current_location_lat else None
    })

# ============================================================================
# SURVEY RESPONSE MANAGEMENT
# ============================================================================

@app.route('/api/surveys/<int:survey_id>/responses', methods=['GET', 'POST'])
@jwt_required()
@company_required
def survey_responses(survey_id):
    """Survey response management"""
    company = get_current_company()
    current_user = get_current_user()
    
    # Verify survey exists and belongs to company
    survey = Survey.query.filter_by(id=survey_id, company_id=company.id).first()
    if not survey:
        return jsonify({'error': 'Survey not found'}), 404
    
    if request.method == 'GET':
        # Parse pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Build query
        query = SurveyResponse.query.filter_by(survey_id=survey_id, company_id=company.id)
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify({
            'responses': [{
                'id': r.id,
                'respondent_email': r.respondent_email,
                'respondent_name': r.respondent_name,
                'responses': json.loads(r.responses) if r.responses else {},
                'completion_time_seconds': r.completion_time_seconds,
                'ip_address': r.ip_address,
                'user_agent': r.user_agent,
                'submitted_at': serialize_datetime(r.submitted_at)
            } for r in result['items']],
            'pagination': result['pagination']
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            response = SurveyResponse(
                company_id=company.id,
                survey_id=survey_id,
                respondent_email=data.get('respondent_email'),
                respondent_name=data.get('respondent_name'),
                responses=json.dumps(data.get('responses', {})),
                completion_time_seconds=data.get('completion_time_seconds'),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            db.session.add(response)
            
            # Update survey stats
            survey.total_responses += 1
            
            db.session.commit()
            
            # Update survey KPI
            update_user_kpi(current_user.id, 'surveys', 'survey_responses_collected', 1)
            
            return jsonify({'message': 'Survey response submitted successfully', 'id': response.id}), 201
            
        except Exception as e:
            return handle_database_error(e)

# ============================================================================
# ENHANCED EXISTING ENDPOINTS
# ============================================================================

# Enhanced CRM endpoints with proper CRUD patterns
@app.route('/api/crm/customers/<int:customer_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
@company_required
def crm_customer_detail(customer_id):
    """Enhanced customer detail operations"""
    company = get_current_company()
    current_user = get_current_user()
    
    customer = Customer.query.filter_by(id=customer_id, company_id=company.id).first()
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': customer.id,
            'name': customer.name,
            'code': customer.code,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'contact_person': customer.contact_person,
            'website': customer.website,
            'industry': customer.industry,
            'customer_type': customer.customer_type,
            'status': customer.status,
            'credit_limit': serialize_decimal(customer.credit_limit),
            'payment_terms': customer.payment_terms,
            'lead_score': customer.lead_score,
            'lifetime_value': serialize_decimal(customer.lifetime_value),
            'location': {
                'lat': customer.location_lat,
                'lng': customer.location_lng
            } if customer.location_lat else None,
            'sales_rep': {
                'id': customer.sales_rep.id,
                'name': f"{customer.sales_rep.first_name} {customer.sales_rep.last_name}",
                'email': customer.sales_rep.email,
                'profile_picture': customer.sales_rep.profile_picture
            } if customer.sales_rep else None,
            'deals': [{
                'id': d.id,
                'name': d.name,
                'amount': serialize_decimal(d.amount),
                'stage': d.stage,
                'status': d.status
            } for d in customer.deals],
            'tickets': [{
                'id': t.id,
                'ticket_number': t.ticket_number,
                'subject': t.subject,
                'status': t.status,
                'priority': t.priority
            } for t in customer.tickets],
            'invoices': [{
                'id': i.id,
                'invoice_number': i.invoice_number,
                'total_amount': serialize_decimal(i.total_amount),
                'status': i.status,
                'payment_status': i.payment_status
            } for i in customer.invoices],
            'created_at': serialize_datetime(customer.created_at),
            'updated_at': serialize_datetime(customer.updated_at)
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Update customer fields
            customer.name = data.get('name', customer.name)
            customer.code = data.get('code', customer.code)
            customer.email = data.get('email', customer.email)
            customer.phone = data.get('phone', customer.phone)
            customer.address = data.get('address', customer.address)
            customer.contact_person = data.get('contact_person', customer.contact_person)
            customer.website = data.get('website', customer.website)
            customer.industry = data.get('industry', customer.industry)
            customer.customer_type = data.get('customer_type', customer.customer_type)
            customer.status = data.get('status', customer.status)
            customer.credit_limit = data.get('credit_limit', customer.credit_limit)
            customer.payment_terms = data.get('payment_terms', customer.payment_terms)
            customer.assigned_sales_rep = data.get('assigned_sales_rep', customer.assigned_sales_rep)
            customer.lead_score = data.get('lead_score', customer.lead_score)
            customer.lifetime_value = data.get('lifetime_value', customer.lifetime_value)
            
            if data.get('location'):
                customer.location_lat = data['location'].get('lat')
                customer.location_lng = data['location'].get('lng')
            
            customer.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'message': 'Customer updated successfully'})
            
        except Exception as e:
            return handle_database_error(e)
    
    elif request.method == 'DELETE':
        try:
            # Only admins can delete customers
            if current_user.role != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            # Soft delete by changing status
            customer.status = 'inactive'
            customer.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'message': 'Customer deactivated successfully'})
            
        except Exception as e:
            return handle_database_error(e)

# ============================================================================
# MAIN APPLICATION SETUP
# ============================================================================

if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)

