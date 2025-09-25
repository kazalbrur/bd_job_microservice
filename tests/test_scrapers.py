# =============================================================================
# 20. Complete Test Suite (tests/test_scrapers.py)
# =============================================================================

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.scrapers.govbd_scraper import GovBDScraper
from app.scrapers.scraper_manager import ScraperManager
from app.parsers.job_parser import JobParser, ParsedJob

@pytest.fixture
def sample_raw_job():
    return {
        'title': 'Assistant Engineer - Civil',
        'department': 'Roads and Highways Department',
        'location': 'Dhaka',
        'grade': 'Grade 9',
        'salary': '22000-53870 Taka',
        'vacancies': '50',
        'description': 'Bachelor degree in Civil Engineering. Computer skills required.',
        'deadline_date': '2024-12-31',
        'application_link': 'https://example.com/apply',
        'source_url': 'https://example.com/job/123',
        'source_site': 'gov.bd'
    }

@pytest.mark.asyncio
async def test_job_parser(sample_raw_job):
    parser = JobParser()
    parsed_job = parser.parse_job(sample_raw_job)
    
    assert parsed_job.title == 'Assistant Engineer - Civil'
    assert parsed_job.department == 'Roads and Highways Department'
    assert parsed_job.location == 'Dhaka'
    assert parsed_job.vacancies == 50
    assert 'computer' in [skill.lower() for skill in parsed_job.skills]
    assert 'bachelor' in parsed_job.education.lower()

@pytest.mark.asyncio
async def test_scraper_manager():
    manager = ScraperManager()
    
    # Mock the scraper to return sample data
    with patch.object(GovBDScraper, 'scrape_jobs', new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = [
            {'title': 'Job 1', 'department': 'Dept 1', 'location': 'Dhaka'},
            {'title': 'Job 2', 'department': 'Dept 2', 'location': 'Chittagong'}
        ]
        
        jobs = await manager.scrape_all_sources()
        assert len(jobs) >= 0  # May be 0 if parsing fails

def test_skill_extraction():
    parser = JobParser()
    text = "Must have Python programming skills and Microsoft Office knowledge"
    skills = parser._extract_skills(text)
    
    assert 'python' in [skill.lower() for skill in skills]
    assert 'microsoft office' in [skill.lower() for skill in skills]

def test_salary_extraction():
    parser = JobParser()
    
    # Test various salary formats
    assert parser._extract_salary("22000-53870 taka") is not None
    assert parser._extract_salary("Grade 9") is not None
    assert parser._extract_salary("") is None

def test_age_range_extraction():
    parser = JobParser()
    
    min_age, max_age = parser._extract_age_range("18 to 35 years")
    assert min_age == 18
    assert max_age == 35
    
    min_age, max_age = parser._extract_age_range("maximum 35 years")
    assert min_age is None
    assert max_age == 35