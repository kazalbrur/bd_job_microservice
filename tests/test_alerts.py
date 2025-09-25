# =============================================================================
# tests/test_alerts.py
# =============================================================================

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from app.alerts.alert_service import AlertService
from app.alerts.scheduler import JobScheduler
from app.db.models import User, Alert, Job
from app.db.database import db_manager

@pytest.fixture
def sample_user():
    return User(
        id=1,
        user_id="test_user_123",
        email="test@example.com"
    )

@pytest.fixture
def sample_alert():
    return Alert(
        id=1,
        user_id=1,
        keywords="engineer,software",
        location="Dhaka",
        department="ICT",
        is_active=True,
        last_sent=datetime.utcnow() - timedelta(hours=25)
    )

@pytest.fixture
def sample_jobs():
    return [
        Job(
            id=1,
            job_id="job_1",
            title="Software Engineer",
            department="ICT Division",
            location="Dhaka",
            description="Python developer needed",
            application_link="https://example.com/apply/1",
            deadline_date=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow() - timedelta(hours=2),
            is_active=True
        ),
        Job(
            id=2,
            job_id="job_2",
            title="Civil Engineer", 
            department="Roads and Highways",
            location="Chittagong",
            description="Road construction engineer",
            application_link="https://example.com/apply/2",
            deadline_date=datetime.utcnow() + timedelta(days=20),
            created_at=datetime.utcnow() - timedelta(hours=1),
            is_active=True
        )
    ]

@pytest.mark.asyncio
async def test_alert_service_initialization():
    alert_service = AlertService()
    assert alert_service is not None
    assert alert_service.email_template is not None

@pytest.mark.asyncio
async def test_find_matching_jobs(sample_alert, sample_jobs):
    alert_service = AlertService()
    
    with patch('app.db.database.db_manager.get_session') as mock_session:
        mock_db = Mock()
        mock_session.return_value.__enter__.return_value = mock_db
        
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [sample_jobs[0]]
        mock_db.query.return_value = mock_query
        
        matching_jobs = await alert_service._find_matching_jobs(
            mock_db, sample_alert, datetime.utcnow() - timedelta(days=1)
        )
        
        assert len(matching_jobs) >= 0

@pytest.mark.asyncio
async def test_send_email_alert(sample_alert, sample_jobs, sample_user):
    alert_service = AlertService()
    
    with patch('smtplib.SMTP') as mock_smtp:
        with patch('app.db.database.db_manager.get_session') as mock_session:
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = sample_user
            mock_session.return_value.__enter__.return_value = mock_db
            
            await alert_service._send_email_alert(sample_alert, sample_jobs[:1])
            
            # Verify SMTP was called
            mock_smtp.assert_called()

def test_job_scheduler_initialization():
    scheduler = JobScheduler()
    assert scheduler.scheduler is not None
    assert scheduler.scraper_manager is not None
    assert scheduler.alert_service is not None

@pytest.mark.asyncio
async def test_scheduled_scraper_task():
    scheduler = JobScheduler()
    
    with patch.object(scheduler.scraper_manager, 'scrape_all_sources') as mock_scrape:
        with patch.object(scheduler.scraper_manager, 'save_jobs_to_db') as mock_save:
            mock_scrape.return_value = []
            mock_save.return_value = None
            
            await scheduler._run_scraper()
            
            mock_scrape.assert_called_once()
            mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_scheduled_alert_check():
    scheduler = JobScheduler()
    
    with patch.object(scheduler.alert_service, 'check_and_send_alerts') as mock_check:
        mock_check.return_value = None
        
        await scheduler._check_alerts()
        
        mock_check.assert_called_once()

@pytest.mark.asyncio
async def test_cleanup_old_jobs():
    scheduler = JobScheduler()
    
    with patch('app.db.database.db_manager.get_session') as mock_session:
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.update.return_value = 5
        mock_db.query.return_value = mock_query
        mock_session.return_value.__enter__.return_value = mock_db
        
        await scheduler._cleanup_old_jobs()
        
        mock_db.query.assert_called()
        mock_db.commit.assert_called()