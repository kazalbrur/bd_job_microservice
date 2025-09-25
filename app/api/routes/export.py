# =============================================================================
# 14. Export Routes (app/api/routes/export.py)
# =============================================================================

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import csv
import json
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

export_router = APIRouter(prefix="/export", tags=["export"])

@export_router.get("/csv")
@limiter.limit("10/minute")
async def export_jobs_csv(
    request: Request,
    title: Optional[str] = None,
    department: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(db_manager.get_db)
):
    """Export jobs to CSV format"""
    
    # Build query with filters
    query = db.query(Job).filter(
        Job.is_active == True,
        Job.deadline_date >= datetime.utcnow()
    )
    
    if title:
        query = query.filter(Job.title.ilike(f"%{title}%"))
    if department:
        query = query.filter(Job.department.ilike(f"%{department}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    
    jobs = query.limit(1000).all()  # Limit export size
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Title', 'Department', 'Location', 'Grade', 'Salary', 
        'Vacancies', 'Education', 'Experience', 'Skills',
        'Deadline', 'Application Link'
    ])
    
    # Data rows
    for job in jobs:
        writer.writerow([
            job.title, job.department, job.location, job.grade,
            job.salary, job.vacancies, job.education, job.experience,
            ', '.join(job.skills) if job.skills else '',
            job.deadline_date.strftime('%Y-%m-%d') if job.deadline_date else '',
            job.application_link
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bd_jobs.csv"}
    )

@export_router.get("/json")
@limiter.limit("10/minute")
async def export_jobs_json(
    request: Request,
    title: Optional[str] = None,
    department: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(db_manager.get_db)
):
    """Export jobs to JSON format"""
    
    # Similar query logic as CSV
    query = db.query(Job).filter(
        Job.is_active == True,
        Job.deadline_date >= datetime.utcnow()
    )
    
    if title:
        query = query.filter(Job.title.ilike(f"%{title}%"))
    if department:
        query = query.filter(Job.department.ilike(f"%{department}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    
    jobs = query.limit(1000).all()
    
    # Convert to dict
    jobs_data = []
    for job in jobs:
        job_dict = {
            'title': job.title,
            'department': job.department,
            'location': job.location,
            'grade': job.grade,
            'salary': job.salary,
            'vacancies': job.vacancies,
            'education': job.education,
            'experience': job.experience,
            'skills': job.skills,
            'description': job.description,
            'deadline_date': job.deadline_date.isoformat() if job.deadline_date else None,
            'application_link': job.application_link,
            'created_at': job.created_at.isoformat()
        }
        jobs_data.append(job_dict)
    
    json_data = json.dumps(jobs_data, indent=2)
    
    return StreamingResponse(
        io.BytesIO(json_data.encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=bd_jobs.json"}
    )
