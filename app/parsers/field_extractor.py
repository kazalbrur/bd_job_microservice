# =============================================================================
# Field Extractor with NLP (app/parsers/field_extractor.py)
# =============================================================================

import re
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FieldExtractor:
    def __init__(self):
        # Skill patterns for extraction
        self.skill_patterns = {
            'programming': [
                r'\b(python|java|javascript|php|c\+\+|c#|sql|html|css|react|angular|vue|node\.?js)\b',
                r'\b(django|flask|spring|laravel|bootstrap|jquery)\b',
                r'\b(mysql|postgresql|mongodb|oracle|sqlite)\b'
            ],
            'office': [
                r'\b(microsoft\s+office|ms\s+office|excel|word|powerpoint|outlook)\b',
                r'\b(google\s+workspace|google\s+docs|sheets|slides)\b',
                r'\b(pdf|spreadsheet|presentation)\b'
            ],
            'technical': [
                r'\b(autocad|solidworks|matlab|photoshop|illustrator)\b',
                r'\b(linux|windows|unix|ubuntu|centos)\b',
                r'\b(git|github|gitlab|svn|version\s+control)\b'
            ],
            'soft_skills': [
                r'\b(communication|leadership|teamwork|problem\s+solving|analytical)\b',
                r'\b(project\s+management|time\s+management|critical\s+thinking)\b',
                r'\b(presentation|negotiation|interpersonal|organizational)\b'
            ]
        }
        
        # Education patterns
        self.education_patterns = [
            r'\b(bachelor|masters?|phd|doctorate|diploma|certificate)\b',
            r'\b(b\.?sc|m\.?sc|ba|ma|bba|mba|llb|mbbs|phd)\b',
            r'\b(engineering|medicine|arts|science|commerce|law|business)\b',
            r'\b(computer\s+science|civil\s+engineering|electrical\s+engineering)\b',
            r'\b(mechanical\s+engineering|software\s+engineering)\b',
            r'\b(university|college|institute|polytechnic)\b'
        ]
        
        # Experience patterns
        self.experience_patterns = [
            r'(\d+)[\+\-\s]*(?:to|-)?\s*(\d+)?\s*years?\s+(?:of\s+)?experience',
            r'minimum\s+(\d+)\s+years?\s+experience',
            r'at\s+least\s+(\d+)\s+years?\s+experience',
            r'(\d+)\s*\+\s*years?\s+experience',
            r'fresh\s+graduate|fresher|entry\s+level|no\s+experience'
        ]
        
        # Salary patterns
        self.salary_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*(?:to|-)?\s*(\d{1,3}(?:,\d{3})*)?\s*(?:taka|tk|bdt)',
            r'grade\s*(\d+)',
            r'pay\s+scale[:\s]+(\d+(?:,\d+)*)\s*-\s*(\d+(?:,\d+)*)',
            r'salary[:\s]+(\d+(?:,\d+)*)\s*(?:to|-)?\s*(\d+(?:,\d+)*)?'
        ]
        
        # Age patterns
        self.age_patterns = [
            r'age\s+limit[:\s]+(\d+)\s*(?:to|-)?\s*(\d+)?\s*years?',
            r'(\d+)\s*(?:to|-)?\s*(\d+)?\s*years?\s+(?:of\s+)?age',
            r'maximum\s+age[:\s]+(\d+)\s*years?',
            r'minimum\s+age[:\s]+(\d+)\s*years?'
        ]
        
        # Location mapping for Bangladesh
        self.location_mapping = {
            'dhaka': 'Dhaka',
            'chittagong': 'Chittagong', 
            'chattogram': 'Chittagong',
            'sylhet': 'Sylhet',
            'rajshahi': 'Rajshahi',
            'khulna': 'Khulna',
            'barisal': 'Barisal',
            'barishal': 'Barisal',
            'rangpur': 'Rangpur',
            'mymensingh': 'Mymensingh',
            'comilla': 'Comilla',
            'cox\'s bazar': 'Cox\'s Bazar',
            'jessore': 'Jessore',
            'bogra': 'Bogra',
            'faridpur': 'Faridpur',
            'pabna': 'Pabna'
        }
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from job description using pattern matching"""
        if not text:
            return []
        
        skills = set()
        text_lower = text.lower()
        
        # Extract using patterns
        for category, patterns in self.skill_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if isinstance(matches[0], tuple) if matches else False:
                    skills.update([m for match in matches for m in match if m])
                else:
                    skills.update(matches)
        
        # Additional keyword-based extraction
        skill_keywords = [
            'typing', 'internet', 'email', 'database', 'networking',
            'troubleshooting', 'documentation', 'reporting', 'analysis',
            'research', 'planning', 'coordination', 'supervision'
        ]
        
        for keyword in skill_keywords:
            if keyword in text_lower:
                skills.add(keyword)
        
        # Clean and format skills
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip().lower()
            if len(skill) > 2:  # Minimum length check
                cleaned_skills.append(skill.title())
        
        return list(set(cleaned_skills))  # Remove duplicates
    
    def extract_education(self, text: str) -> Optional[str]:
        """Extract education requirements"""
        if not text:
            return None
        
        education_info = []
        text_lower = text.lower()
        
        for pattern in self.education_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            education_info.extend(matches)
        
        if education_info:
            # Clean and deduplicate
            unique_education = list(set([edu.title() for edu in education_info]))
            return ', '.join(unique_education)
        
        return None
    
    def extract_experience(self, text: str) -> Optional[str]:
        """Extract experience requirements"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Check for fresh graduate first
        if re.search(r'fresh\s+graduate|fresher|entry\s+level|no\s+experience', text_lower):
            return "Fresh Graduate"
        
        # Extract years of experience
        for pattern in self.experience_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                if len(groups) >= 2 and groups[1]:
                    return f"{groups[0]}-{groups[1]} years"
                elif groups[0]:
                    return f"{groups[0]}+ years"
        
        return None
    
    def extract_salary_info(self, text: str) -> Optional[str]:
        """Extract salary information"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        for pattern in self.salary_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0).strip()
        
        return None
    
    def extract_age_range(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract age range"""
        if not text:
            return None, None
        
        text_lower = text.lower()
        
        for pattern in self.age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                if len(groups) >= 2 and groups[1]:
                    # Range found
                    return int(groups[0]), int(groups[1])
                elif 'maximum' in match.group(0):
                    return None, int(groups[0])
                elif 'minimum' in match.group(0):
                    return int(groups[0]), None
                elif groups[0]:
                    return int(groups[0]), int(groups[0])
        
        return None, None
    
    def extract_vacancies(self, text: str) -> Optional[int]:
        """Extract number of vacancies"""
        if not text:
            return None
        
        # Patterns for vacancy extraction
        patterns = [
            r'(\d+)\s*(?:posts?|positions?|vacancies|openings?)',
            r'vacancies?[:\s]+(\d+)',
            r'posts?[:\s]+(\d+)',
            r'(\d+)\s*(?:জন|persons?)'  # Bengali and English
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1))
        
        # Fallback: extract any number if context suggests vacancies
        if 'vacancy' in text_lower or 'post' in text_lower:
            numbers = re.findall(r'\b(\d+)\b', text_lower)
            if numbers:
                # Take the first reasonable number (not too large)
                for num in numbers:
                    val = int(num)
                    if 1 <= val <= 1000:  # Reasonable range for job vacancies
                        return val
        
        return None
    
    def normalize_location(self, location: str) -> str:
        """Normalize location names"""
        if not location:
            return ""
        
        location_clean = re.sub(r'[^\w\s\']', '', location.lower().strip())
        
        # Check mapping
        for key, value in self.location_mapping.items():
            if key in location_clean:
                return value
        
        # Default formatting
        return ' '.join(word.capitalize() for word in location_clean.split())
    
    def extract_grade_scale(self, text: str) -> Optional[str]:
        """Extract government job grade/scale"""
        if not text:
            return None
        
        patterns = [
            r'grade[:\s]+(\d+)',
            r'pay\s+scale[:\s]+(\d+)',
            r'class[:\s]+([ivxl]+)',
            r'category[:\s]+([abc])'
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0).title()
        
        return None
    
    def extract_application_deadline(self, text: str) -> Optional[datetime]:
        """Extract application deadline"""
        if not text:
            return None
        
        # Date patterns
        date_patterns = [
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # DD-MM-YYYY or DD/MM/YYYY
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
            r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})'
        ]
        
        text_lower = text.lower()
        
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    groups = match.groups()
                    
                    if pattern == date_patterns[0]:  # DD-MM-YYYY
                        day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        return datetime(year, month, day)
                    elif pattern == date_patterns[1]:  # YYYY-MM-DD
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        return datetime(year, month, day)
                    elif pattern == date_patterns[2]:  # DD Month YYYY
                        day, month_name, year = int(groups[0]), groups[1], int(groups[2])
                        month = self._month_name_to_number(month_name)
                        return datetime(year, month, day)
                    elif pattern == date_patterns[3]:  # Month DD, YYYY
                        month_name, day, year = groups[0], int(groups[1]), int(groups[2])
                        month = self._month_name_to_number(month_name)
                        return datetime(year, month, day)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _month_name_to_number(self, month_name: str) -> int:
        """Convert month name to number"""
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        return months.get(month_name.lower(), 1)
    
    def extract_department_clean(self, department: str) -> str:
        """Clean and normalize department names"""
        if not department:
            return ""
        
        # Remove extra text and normalize
        department = re.sub(r'\s+', ' ', department.strip())
        
        # Common department mappings
        dept_mappings = {
            'ict': 'Information and Communication Technology',
            'rhd': 'Roads and Highways Department',
            'lged': 'Local Government Engineering Department',
            'doe': 'Department of Environment',
            'dae': 'Department of Agricultural Extension',
            'health': 'Ministry of Health and Family Welfare'
        }
        
        dept_lower = department.lower()
        for abbrev, full_name in dept_mappings.items():
            if abbrev in dept_lower:
                return full_name
        
        return department.title()
    
    def extract_comprehensive_info(self, text: str) -> Dict:
        """Extract all information from a job description"""
        if not text:
            return {}
        
        return {
            'skills': self.extract_skills(text),
            'education': self.extract_education(text),
            'experience': self.extract_experience(text),
            'salary': self.extract_salary_info(text),
            'age_min': self.extract_age_range(text)[0],
            'age_max': self.extract_age_range(text)[1],
            'vacancies': self.extract_vacancies(text),
            'grade': self.extract_grade_scale(text),
            'deadline': self.extract_application_deadline(text)
        }