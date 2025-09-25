# =============================================================================
# 23. Database Setup Script (scripts/setup_db.py)
# =============================================================================
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import db_manager
from app.db.models import User, Job
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    # Create database tables
    try:
        logger.info("Creating database tables...")
        db_manager.create_tables()
        logger.info("Database tables created successfully")
        
        # Create indexes for performance
        with db_manager.get_session() as db:
            # Additional custom indexes
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_full_text 
                ON jobs USING gin(to_tsvector('english', title || ' ' || description));
            """))
            
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_deadline_active 
                ON jobs (deadline_date, is_active) WHERE is_active = true;
            """))
            
        logger.info("Additional indexes created")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)

def create_sample_data():
    # reate sample data for testing
    try:
        with db_manager.get_session() as db:
            # Create sample user
            sample_user = User(
                user_id="sample_user_123",
                email="test@example.com"
            )
            db.add(sample_user)
            
            # Create sample jobs
            sample_jobs = [
                Job(
                    job_id="sample_job_1",
                    title="Software Engineer",
                    department="ICT Division",
                    location="Dhaka",
                    grade="Grade 9",
                    salary="30000-60000",
                    vacancies=5,
                    skills=["Python", "JavaScript", "SQL"],
                    description="Develop and maintain government web applications",
                    application_link="https://example.com/apply/1",
                    source_site="gov.bd"
                ),
                Job(
                    job_id="sample_job_2",
                    title="Civil Engineer",
                    department="Roads and Highways",
                    location="Chittagong",
                    grade="Grade 10",
                    salary="25000-50000",
                    vacancies=10,
                    skills=["AutoCAD", "Project Management"],
                    description="Design and supervise road construction projects",
                    application_link="https://example.com/apply/2",
                    source_site="gov.bd"
                )
            ]
            
            for job in sample_jobs:
                db.add(job)
            
            db.commit()
            logger.info("Sample data created successfully")
            
    except Exception as e:
        logger.error(f"Sample data creation failed: {e}")

if __name__ == "__main__":
    print("Setting up database...")
    create_database()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--sample-data":
        create_sample_data()
    
    print("Database setup completed!")