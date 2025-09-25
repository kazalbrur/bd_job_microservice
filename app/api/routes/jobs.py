# =============================================================================
# 10. Job API Routes (app/api/routes/jobs.py)
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.main import limiter
from app.db.database import db_manager
from app.cache.redis_cache import cache
from app.db.models import Job

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobResponse(BaseModel):
    id: int
    job_id: str
    title: str
    department: str
    location: str
    grade: Optional[str]
    salary: Optional[str]
    vacancies: Optional[int]
    education: Optional[str]
    experience: Optional[str]
    age_min: Optional[int]
    age_max: Optional[int]
    skills: Optional[List[str]]
    description: Optional[str]
    posting_date: Optional[datetime]
    deadline_date: Optional[datetime]
    application_link: str
    source_url: Optional[str]
    source_site: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class JobFilter(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None

@router.get("/", response_model=List[JobResponse])
@limiter.limit("100/minute")
async def get_jobs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    title: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(db_manager.get_db)
):
    """Get jobs with optional filtering"""
    
    # Check cache first
    cache_key = f"jobs_{skip}_{limit}_{title}_{department}_{location}_{active_only}"
    cached_jobs = await cache.get(cache_key)
    if cached_jobs:
        return cached_jobs
    
    # Build query
    query = db.query(Job)
    
    if active_only:
        query = query.filter(Job.is_active == True)
        query = query.filter(Job.deadline_date >= datetime.utcnow())
    
    if title:
        query = query.filter(Job.title.ilike(f"%{title}%"))
    
    if department:
        query = query.filter(Job.department.ilike(f"%{department}%"))
    
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    
    # Order by creation date (newest first)
    query = query.order_by(Job.created_at.desc())
    
    # Pagination
    jobs = query.offset(skip).limit(limit).all()
    
    # Cache results
    await cache.set(cache_key, jobs, ttl=300)  # 5 minutes
    
    return jobs

@router.get("/{job_id}", response_model=JobResponse)
@limiter.limit("200/minute")
async def get_job(
    request: Request,
    job_id: int,
    db: Session = Depends(db_manager.get_db)
):
    """Get specific job by ID"""
    
    # Check cache
    cache_key = f"job_{job_id}"
    cached_job = await cache.get(cache_key)
    if cached_job:
        return cached_job
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Cache result
    await cache.set(cache_key, job, ttl=3600)  # 1 hour
    
    return job

@router.get("/search/{query}")
@limiter.limit("50/minute")
async def search_jobs(
    request: Request,
    query: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=50),
    db: Session = Depends(db_manager.get_db)
):
    """Full-text search across jobs"""
    
    search_query = db.query(Job).filter(
        or_(
            Job.title.ilike(f"%{query}%"),
            Job.department.ilike(f"%{query}%"),
            Job.description.ilike(f"%{query}%"),
            Job.location.ilike(f"%{query}%")
        )
    ).filter(
        Job.is_active == True,
        Job.deadline_date >= datetime.utcnow()
    ).order_by(Job.created_at.desc())
    
    jobs = search_query.offset(skip).limit(limit).all()
    return jobs