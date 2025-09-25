# =============================================================================
# 23. Database Setup Script (scripts/setup_db.py)
# =============================================================================
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models import Base, User, Job
from app.config import settings
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    # Create database tables
    try:
        logger.info("Creating database tables...")
        # Ensure we use a synchronous driver for setup (strip async driver suffix)
        sync_db_url = settings.DATABASE_URL.replace('+asyncpg', '')
        engine = create_engine(sync_db_url, pool_size=10, max_overflow=20)

        # Create tables using the sync engine
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Create indexes for performance (run outside transaction where necessary)
        conn = engine.connect()
        try:
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_full_text 
                ON jobs USING gin(to_tsvector('english', title || ' ' || description));
            """))

            conn.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_deadline_active 
                ON jobs (deadline_date, is_active) WHERE is_active = true;
            """))
        finally:
            conn.close()

        logger.info("Additional indexes created")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)

def create_sample_data():
    # reate sample data for testing
    try:
        # Use a local synchronous session for inserting sample data
        sync_db_url = settings.DATABASE_URL.replace('+asyncpg', '')
        engine = create_engine(sync_db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        with SessionLocal() as db:
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