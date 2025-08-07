from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    plan_type = Column(String(50), nullable=False)  # 'ai' or 'expert'
    subscription_status = Column(String(50), default='active')
    stripe_customer_id = Column(String(255))
    auth_token = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="user")

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    website_url = Column(String(500), nullable=False)
    source = Column(String(100), default='landing_page')
    status = Column(String(50), default='new')  # new, contacted, converted, lost
    checkout_token = Column(String(255), unique=True)
    latest_analysis_id = Column(PG_UUID(as_uuid=True), ForeignKey('analyses.id'))
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="leads")
    analyses = relationship("Analysis", back_populates="lead")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    website_url = Column(String(500), nullable=False)
    project_name = Column(String(255))
    status = Column(String(50), default='analyzing')
    current_score = Column(Integer, default=0)
    target_score = Column(Integer, default=95)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    analyses = relationship("Analysis", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("ComplianceIssue", back_populates="project", cascade="all, delete-orphan")

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=True)
    lead_id = Column(PG_UUID(as_uuid=True), ForeignKey('leads.id'), nullable=True)
    analysis_data = Column(JSON, nullable=False)
    overall_score = Column(Integer, nullable=False)
    total_issues = Column(Integer, nullable=False)
    scan_timestamp = Column(DateTime, default=datetime.utcnow)
    analysis_type = Column(String(50), default='full')
    
    # Relationships
    project = relationship("Project", back_populates="analyses")
    lead = relationship("Lead", back_populates="analyses")
    issues = relationship("ComplianceIssue", back_populates="analysis", cascade="all, delete-orphan")

class ComplianceIssue(Base):
    __tablename__ = "compliance_issues"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    analysis_id = Column(PG_UUID(as_uuid=True), ForeignKey('analyses.id'), nullable=False)
    category = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), default='open')
    title = Column(String(255), nullable=False)
    description = Column(Text)
    fix_instructions = Column(Text)
    ai_fix_available = Column(Boolean, default=False)
    estimated_fix_time = Column(Integer)
    estimated_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="issues")
    analysis = relationship("Analysis", back_populates="issues")
    fix_tasks = relationship("FixTask", back_populates="issue", cascade="all, delete-orphan")

class FixTask(Base):
    __tablename__ = "fix_tasks"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(PG_UUID(as_uuid=True), ForeignKey('compliance_issues.id'), nullable=False)
    task_type = Column(String(50), nullable=False)
    status = Column(String(50), default='pending')
    assigned_to = Column(String(255))
    fix_data = Column(JSON)
    completion_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    issue = relationship("ComplianceIssue", back_populates="fix_tasks")

class ExpertAppointment(Base):
    __tablename__ = "expert_appointments"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    calendly_event_id = Column(String(255))
    appointment_datetime = Column(DateTime)
    expert_email = Column(String(255))
    status = Column(String(50), default='scheduled')
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
