
# =============================================================================
# 2. Database Models (app/db/models.py)
# =============================================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True)  # Unique job identifier
    title = Column(String(500), nullable=False, index=True)
    department = Column(String(200), nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)
    grade = Column(String(50))
    salary = Column(String(100))
    vacancies = Column(Integer)
    
    # Eligibility
    education = Column(Text)
    experience = Column(String(200))
    age_min = Column(Integer)
    age_max = Column(Integer)
    
    # Skills and requirements
    skills = Column(JSON)  # List of extracted skills
    description = Column(Text)
    
    # Dates
    posting_date = Column(DateTime)
    deadline_date = Column(DateTime, index=True)
    
    # Metadata
    application_link = Column(String(1000), nullable=False)
    source_url = Column(String(1000))
    source_site = Column(String(100))
    
    # Processing
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookmarks = relationship("Bookmark", back_populates="job")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_job_search', 'title', 'department', 'location'),
        Index('idx_job_deadline', 'deadline_date', 'is_active'),
        Index('idx_job_created', 'created_at', 'is_active'),
    )

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bookmarks = relationship("Bookmark", back_populates="user")
    alerts = relationship("Alert", back_populates="user")

class Bookmark(Base):
    __tablename__ = "bookmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="bookmarks")
    job = relationship("Job", back_populates="bookmarks")
    
    # Unique constraint
    __table_args__ = (Index('idx_unique_bookmark', 'user_id', 'job_id', unique=True),)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keywords = Column(Text)  # Comma-separated keywords
    location = Column(String(100))
    department = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sent = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="alerts")