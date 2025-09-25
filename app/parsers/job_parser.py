# =============================================================================
# 5. Enhanced Parser with NLP (app/parsers/job_parser.py)
# =============================================================================

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
from dataclasses import dataclass

@dataclass
class ParsedJob:
    job_id: str
    title: str
    department: str
    location: str
    grade: Optional[str] = None
    salary: Optional[str] = None
    vacancies: Optional[int] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    skills: List[str] = None
    description: Optional[str] = None
    posting_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None
    application_link: Optional[str] = None
    source_url: Optional[str] = None
    source_site: Optional[str] = None

class JobParser:
    def __init__(self):
        self.skill_patterns = [
            r'\b(python|java|javascript|php|sql|html|css|react|angular|vue|node\.?js)\b',
            r'\b(microsoft office|excel|word|powerpoint|outlook)\b',
            r'\b(communication|leadership|teamwork|problem solving|analytical)\b',
            r'\b(project management|time management|critical thinking)\b',
            r'\b(computer|typing|internet|email|database)\b'
        ]
        
        self.education_patterns = [
            r'\b(bachelor|masters?|phd|doctorate|diploma|certificate)\b',
            r'\b(bsc|msc|ba|ma|bba|mba|llb|mbbs)\b',
            r'\b(engineering|medicine|arts|science|commerce|law)\b',
            r'\b(university|college|institute|board)\b'
        ]
        
        self.location_mapping = {
            'dhaka': 'Dhaka',
            'chittagong': 'Chittagong',
            'sylhet': 'Sylhet',
            'rajshahi': 'Rajshahi',
            'khulna': 'Khulna',
            'barisal': 'Barisal',
            'rangpur': 'Rangpur',
            'mymensingh': 'Mymensingh'
        }
    
    def parse_job(self, raw_data: Dict) -> ParsedJob:
        """Parse raw job data into structured format"""
        try:
            # Generate unique job ID
            job_id = self._generate_job_id(raw_data)
            
            # Extract and clean basic fields
            title = self._clean_text(raw_data.get('title', ''))
            department = self._clean_text(raw_data.get('department', ''))
            location = self._normalize_location(raw_data.get('location', ''))
            
            # Validate mandatory fields
            if not all([title, department, location]):
                raise ValueError("Missing mandatory fields")
            
            # Extract numeric fields
            salary = self._extract_salary(raw_data.get('salary', ''))
            vacancies = self._extract_vacancies(raw_data.get('vacancies', ''))
            age_min, age_max = self._extract_age_range(raw_data.get('age', ''))
            
            # Extract skills from description
            description = raw_data.get('description', '')
            skills = self._extract_skills(description + ' ' + raw_data.get('requirements', ''))
            
            # Extract education requirements
            education = self._extract_education(description + ' ' + raw_data.get('education', ''))
            
            # Parse dates
            posting_date = self._parse_date(raw_data.get('posting_date'))
            deadline_date = self._parse_date(raw_data.get('deadline_date'))
            
            return ParsedJob(
                job_id=job_id,
                title=title,
                department=department,
                location=location,
                grade=self._clean_text(raw_data.get('grade', '')),
                salary=salary,
                vacancies=vacancies,
                education=education,
                experience=self._clean_text(raw_data.get('experience', '')),
                age_min=age_min,
                age_max=age_max,
                skills=skills,
                description=self._clean_text(description),
                posting_date=posting_date,
                deadline_date=deadline_date,
                application_link=raw_data.get('application_link'),
                source_url=raw_data.get('source_url'),
                source_site=raw_data.get('source_site')
            )
            
        except Exception as e:
            logger.error(f"Job parsing error: {e}")
            raise
    
    def _generate_job_id(self, raw_data: Dict) -> str:
        """Generate unique job ID from title, department, and location"""
        key_data = f"{raw_data.get('title', '')}{raw_data.get('department', '')}{raw_data.get('location', '')}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace, HTML tags, special characters
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location names"""
        location = self._clean_text(location.lower())
        for key, value in self.location_mapping.items():
            if key in location:
                return value
        return location.title()
    
    def _extract_salary(self, salary_text: str) -> Optional[str]:
        """Extract and normalize salary information"""
        if not salary_text:
            return None
        
        # Extract salary patterns
        patterns = [
            r'(\d+(?:,\d+)*)\s*(?:to|-)?\s*(\d+(?:,\d+)*)?\s*taka',
            r'(\d+(?:,\d+)*)\s*(?:to|-)?\s*(\d+(?:,\d+)*)?',
            r'grade\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, salary_text.lower())
            if match:
                return match.group(0)
        
        return self._clean_text(salary_text)
    
    def _extract_vacancies(self, vacancy_text: str) -> Optional[int]:
        """Extract number of vacancies"""
        if not vacancy_text:
            return None
        
        match = re.search(r'(\d+)', str(vacancy_text))
        if match:
            return int(match.group(1))
        return None
    
    def _extract_age_range(self, age_text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract age range"""
        if not age_text:
            return None, None
        
        # Patterns for age ranges
        patterns = [
            r'(\d+)\s*(?:to|-)\s*(\d+)',  # "25 to 35" or "25-35"
            r'maximum\s*(\d+)',           # "maximum 35"
            r'minimum\s*(\d+)',           # "minimum 18"
            r'(\d+)\s*years?'             # "30 years"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, age_text.lower())
            if match:
                if 'to' in age_text.lower() or '-' in age_text:
                    return int(match.group(1)), int(match.group(2))
                elif 'maximum' in age_text.lower():
                    return None, int(match.group(1))
                elif 'minimum' in age_text.lower():
                    return int(match.group(1)), None
                else:
                    return int(match.group(1)), int(match.group(1))
        
        return None, None
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills using NLP patterns"""
        if not text:
            return []
        
        skills = set()
        text_lower = text.lower()
        
        for pattern in self.skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.update(matches)
        
        # Additional keyword-based extraction
        skill_keywords = [
            'communication', 'leadership', 'teamwork', 'analytical',
            'computer', 'typing', 'internet', 'microsoft office',
            'problem solving', 'time management', 'project management'
        ]
        
        for keyword in skill_keywords:
            if keyword in text_lower:
                skills.add(keyword)
        
        return list(skills)
    
    def _extract_education(self, text: str) -> Optional[str]:
        """Extract education requirements"""
        if not text:
            return None
        
        education_info = []
        text_lower = text.lower()
        
        for pattern in self.education_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            education_info.extend(matches)
        
        if education_info:
            return ', '.join(set(education_info))
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date strings into datetime objects"""
        if not date_str:
            return None
        
        date_formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%B %d, %Y',
            '%d %B %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
