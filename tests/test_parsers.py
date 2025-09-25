# =============================================================================
# tests/test_parsers.py
# =============================================================================


import pytest
from datetime import datetime
from app.parsers.job_parser import JobParser, ParsedJob
from app.parsers.field_extractor import FieldExtractor
from app.parsers.data_cleaner import DataCleaner

@pytest.fixture
def parser():
    return JobParser()

@pytest.fixture
def field_extractor():
    return FieldExtractor()

@pytest.fixture
def data_cleaner():
    return DataCleaner()

@pytest.fixture
def sample_job_data():
    return {
        'title': '  Software Engineer - Python Developer  ',
        'department': 'Information and Communication Technology Division',
        'location': 'dhaka, bangladesh',
        'grade': 'Grade 9',
        'salary': '22,000 - 53,870 Taka per month',
        'vacancies': '5 posts',
        'description': '''
        We are looking for a skilled Python developer with experience in 
        web development, Django, Flask, and database management. 
        Must have Bachelor degree in Computer Science or Engineering.
        Good communication skills and teamwork ability required.
        Age limit: 25 to 35 years. Computer literacy essential.
        ''',
        'deadline_date': '2024-12-31',
        'application_link': 'https://teletalk.com.bd/apply/12345',
        'source_url': 'https://gov.bd/jobs/software-engineer',
        'source_site': 'gov.bd'
    }

def test_job_parser_basic_fields(parser, sample_job_data):
    parsed_job = parser.parse_job(sample_job_data)
    
    assert parsed_job.title == "Software Engineer - Python Developer"
    assert parsed_job.department == "Information and Communication Technology Division"
    assert parsed_job.location == "Dhaka"
    assert parsed_job.grade == "Grade 9"
    assert parsed_job.vacancies == 5

def test_skill_extraction(parser):
    text = """
    Required skills: Python, Django, Flask, JavaScript, HTML, CSS, 
    SQL, PostgreSQL, Git, Linux, Docker, communication skills, 
    teamwork, problem solving, Microsoft Office
    """
    
    skills = parser._extract_skills(text)
    
    expected_skills = ['python', 'javascript', 'sql', 'communication', 'teamwork', 'microsoft office']
    
    for skill in expected_skills:
        assert any(skill in s.lower() for s in skills), f"Skill '{skill}' not found in {skills}"

def test_education_extraction(parser):
    text = """
    Bachelor degree in Computer Science, Engineering, or equivalent.
    Masters degree preferred. University graduation required.
    """
    
    education = parser._extract_education(text)
    
    assert education is not None
    assert 'bachelor' in education.lower()
    assert 'computer' in education.lower() or 'engineering' in education.lower()

def test_salary_extraction(parser):
    test_cases = [
        ("22,000 - 53,870 Taka", "22,000 - 53,870 Taka"),
        ("Grade 9 (22000-53870)", "Grade 9"),
        ("25000 taka per month", "25000 taka"),
        ("", None)
    ]
    
    for input_text, expected in test_cases:
        result = parser._extract_salary(input_text)
        if expected is None:
            assert result is None
        else:
            assert expected.lower() in result.lower()

def test_age_range_extraction(parser):
    test_cases = [
        ("25 to 35 years", (25, 35)),
        ("18-30 years", (18, 30)),
        ("maximum 35 years", (None, 35)),
        ("minimum 18 years", (18, None)),
        ("30 years", (30, 30)),
        ("", (None, None))
    ]
    
    for input_text, expected in test_cases:
        min_age, max_age = parser._extract_age_range(input_text)
        assert (min_age, max_age) == expected

def test_vacancy_extraction(parser):
    test_cases = [
        ("5 posts", 5),
        ("10 positions", 10),
        ("১৫ জন", 15),
        ("Multiple", None),
        ("", None)
    ]
    
    for input_text, expected in test_cases:
        result = parser._extract_vacancies(input_text)
        assert result == expected

def test_date_parsing(parser):
    test_cases = [
        ("2024-12-31", datetime(2024, 12, 31)),
        ("31-12-2024", datetime(2024, 12, 31)),
        ("31/12/2024", datetime(2024, 12, 31)),
        ("December 31, 2024", datetime(2024, 12, 31)),
        ("invalid date", None),
        ("", None)
    ]
    
    for input_text, expected in test_cases:
        result = parser._parse_date(input_text)
        if expected is None:
            assert result is None
        else:
            assert result == expected

def test_location_normalization(parser):
    test_cases = [
        ("dhaka", "Dhaka"),
        ("chittagong", "Chittagong"),
        ("sylhet", "Sylhet"),
        ("unknown city", "Unknown City"),
        ("RAJSHAHI", "Rajshahi")
    ]
    
    for input_text, expected in test_cases:
        result = parser._normalize_location(input_text)
        assert result == expected

def test_text_cleaning(parser):
    test_cases = [
        ("  Extra   spaces  ", "Extra spaces"),
        ("<p>HTML content</p>", "HTML content"),
        ("Mixed\n\nlines\tand   spaces", "Mixed lines and spaces"),
        ("", "")
    ]
    
    for input_text, expected in test_cases:
        result = parser._clean_text(input_text)
        assert result == expected

def test_field_extractor_salary_patterns():
    extractor = FieldExtractor()
    
    test_cases = [
        "Salary: 20,000-40,000 BDT",
        "Grade 10 (25000-50000)",
        "Monthly: 30000 taka",
        "Pay scale: 22,000 - 53,870"
    ]
    
    for text in test_cases:
        result = extractor.extract_salary_info(text)
        assert result is not None

def test_data_cleaner_normalization():
    cleaner = DataCleaner()
    
    # Test department normalization
    dept_cases = [
        ("ict division", "ICT Division"),
        ("ROADS AND HIGHWAYS", "Roads and Highways"),
        ("ministry of education", "Ministry of Education")
    ]
    
    for input_text, expected in dept_cases:
        result = cleaner.normalize_department(input_text)
        assert expected.lower() in result.lower()

def test_comprehensive_job_parsing(parser, sample_job_data):
    parsed_job = parser.parse_job(sample_job_data)
    
    # Check all fields are parsed
    assert parsed_job.job_id is not None
    assert len(parsed_job.job_id) == 16  # MD5 hash length
    assert parsed_job.title is not None
    assert parsed_job.department is not None
    assert parsed_job.location is not None
    assert parsed_job.skills is not None
    assert len(parsed_job.skills) > 0
    assert parsed_job.application_link is not None

def test_error_handling_missing_fields(parser):
    incomplete_data = {
        'title': 'Test Job',
        # Missing required fields
    }
    
    with pytest.raises(ValueError):
        parser.parse_job(incomplete_data)

def test_parser_accuracy_benchmark(parser):
    """Test parser accuracy with various job posting formats"""
    
    test_jobs = [
        {
            'title': 'Assistant Engineer (Civil)',
            'department': 'Roads and Highways Department',
            'location': 'Dhaka',
            'description': 'BSc in Civil Engineering required. AutoCAD, project management skills needed.',
            'salary': '22000-53870',
            'vacancies': '50',
            'deadline_date': '2024-12-31',
            'application_link': 'https://example.com/apply',
        },
        {
            'title': 'Software Developer',
            'department': 'ICT Division',
            'location': 'Chittagong',
            'description': 'Python, Django, JavaScript experience required. Communication skills essential.',
            'salary': 'Grade 9',
            'vacancies': '10 posts',
            'deadline_date': '31-12-2024',
            'application_link': 'https://example.com/apply2',
        }
    ]
    
    accuracy_count = 0
    total_fields = 0
    
    for job_data in test_jobs:
        try:
            parsed = parser.parse_job(job_data)
            
            # Check mandatory fields
            if parsed.title and parsed.department and parsed.location:
                accuracy_count += 3
            total_fields += 3
            
            # Check skill extraction
            if parsed.skills and len(parsed.skills) > 0:
                accuracy_count += 1
            total_fields += 1
            
            # Check numeric extraction
            if parsed.vacancies is not None:
                accuracy_count += 1
            total_fields += 1
            
        except Exception as e:
            print(f"Parsing failed for job: {e}")
    
    accuracy_percentage = (accuracy_count / total_fields) * 100 if total_fields > 0 else 0
    print(f"Parser accuracy: {accuracy_percentage:.1f}%")
    
    # Should achieve at least 95% accuracy
    assert accuracy_percentage >= 95.0