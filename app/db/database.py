# =============================================================================
# 3. Database Connection (app/db/database.py)
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from contextlib import contextmanager
from app.config import settings
from .models import Base
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url: str):
        # If an async driver is configured (e.g. postgresql+asyncpg), create
        # a synchronous engine for the application's synchronous DB usage by
        # stripping the async driver suffix.
        sync_db_url = database_url.replace('+asyncpg', '')
        connect_args = {}
        if sync_db_url.startswith('sqlite'):
            connect_args = {"check_same_thread": False}

        self.engine = create_engine(
            sync_db_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
            connect_args=connect_args
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def get_db(self):
        """Dependency for FastAPI"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

# Initialize database manager
db_manager = DatabaseManager(settings.DATABASE_URL)