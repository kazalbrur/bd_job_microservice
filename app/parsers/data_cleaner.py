# =============================================================================
# Data Cleaner and Normalizer (app/parsers/data_cleaner.py)
# =============================================================================

import re
import unicodedata
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self):
        # Common abbreviations and their full forms
        self.department_mappings = {
            'ict division': 'Information and Communication Technology Division',
            'rhd': 'Roads and Highways Department',
            'lged': 'Local Government Engineering Department', 
            'bsti': 'Bangladesh Standards and Testing Institution',
            'btrc': 'Bangladesh Telecommunication Regulatory Commission',
            'doe': 'Department of Environment',
            'dae': 'Department of Agricultural Extension',
            'dghs': 'Directorate General of Health Services',
            'bcs': 'Bangladesh Civil Service',
            'ntrca': 'Non-Government Teachers Registration and Certification Authority'
        }
        
        # Title standardization
        self.title_mappings = {
            'asst': 'Assistant',
            'sr': 'Senior',
            'jr': 'Junior',
            'mgr': 'Manager',
            'exec': 'Executive',
            'tech': 'Technical',
            'admin': 'Administrative'
        }
        
        # Grade standardization
        self.grade_patterns = [
            (r'grade[:\s]*(\d+)', r'Grade \1'),
            (r'class[:\s]*([ivxl]+)', lambda m: f'Class {m.group(1).upper()}'),
            (r'pay\s+scale[:\s]*(\d+)', r'Pay Scale \1')
        ]
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep Bengali characters
        text = re.sub(r'[^\w\s\u0980-\u09FF.,()-]', '', text)
        
        return text.strip()
    
    def clean_title(self, title: str) -> str:
        """Clean and standardize job titles"""
        if not title:
            return ""
        
        title = self.clean_text(title)
        
        # Apply title mappings
        for abbrev, full in self.title_mappings.items():
            title = re.sub(rf'\b{abbrev}\b', full, title, flags=re.IGNORECASE)
        
        # Remove redundant words
        redundant_patterns = [
            r'\b(post\s+of|position\s+of|job\s+of)\b',
            r'\b(recruitment|hiring|vacancy)\b',
            r'\b(advertisement|circular)\b'
        ]
        
        for pattern in redundant_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        # Clean up spacing and capitalization
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Proper case formatting
        return ' '.join(word.capitalize() if word.lower() not in ['of', 'and', 'in', 'for', 'at'] 
                       else word.lower() for word in title.split())
    
    def normalize_department(self, department: str) -> str:
        """Normalize department names"""
        if not department:
            return ""
        
        department = self.clean_text(department.lower())
        
        # Apply department mappings
        for abbrev, full in self.department_mappings.items():
            if abbrev in department:
                return full
        
        # Remove common prefixes/suffixes
        department = re.sub(r'\b(ministry\s+of\s+the?|department\s+of\s+the?)\b', '', department)
        department = re.sub(r'\b(government\s+of\s+bangladesh|bangladesh\s+government)\b', '', department)
        
        # Proper case
        words = department.split()
        normalized = []
        for word in words:
            if word in ['of', 'and', 'the', 'in', 'for']:
                normalized.append(word.lower())
            else:
                normalized.append(word.capitalize())
        
        return ' '.join(normalized).strip()
    
    def normalize_location(self, location: str) -> str:
        """Normalize location names"""
        if not location:
            return ""
        
        location = self.clean_text(location.lower())
        
        # Location mappings
        location_mappings = {
            'chittagong': 'Chittagong',
            'chattogram': 'Chittagong',
            'dhaka': 'Dhaka',
            'sylhet': 'Sylhet',
            'rajshahi': 'Rajshahi',
            'khulna': 'Khulna',
            'barisal': 'Barisal',
            'barishal': 'Barisal',
            'rangpur': 'Rangpur',
            'mymensingh': 'Mymensingh'
        }
        
        for key, value in location_mappings.items():
            if key in location:
                return value
        
        # Remove common location indicators
        location = re.sub(r'\b(district|division|upazila|thana|area)\b', '', location)
        location = re.sub(r'\bbangladesh\b', '', location)
        
        return ' '.join(word.capitalize() for word in location.split() if word).strip()
    
    def clean_salary(self, salary: str) -> Optional[str]:
        """Clean and normalize salary information"""
        if not salary:
            return None
        
        salary = self.clean_text(salary.lower())
        
        # Remove currency symbols and normalize
        salary = re.sub(r'[৳$€£]', '', salary)
        salary = re.sub(r'\b(taka|tk|bdt|rupees?)\b', 'BDT', salary, flags=re.IGNORECASE)
        
        # Standardize number format
        salary = re.sub(r'(\d+),(\d+)', r'\1\2', salary)  # Remove commas in numbers
        
        # Extract and format salary ranges
        patterns = [
            r'(\d+)\s*(?:to|-)?\s*(\d+)?\s*(?:bdt|per\s+month)?',
            r'grade\s*(\d+)',
            r'pay\s+scale[:\s]+(\d+(?:,\d+)*)\s*-\s*(\d+(?:,\d+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, salary)
            if match:
                groups = match.groups()
                if len(groups) >= 2 and groups[1]:
                    return f"{groups[0]}-{groups[1]} BDT"
                else:
                    return f"{groups[0]} BDT"
        
        return salary.strip().title() if salary.strip() else None
    
    def clean_skills(self, skills: List[str]) -> List[str]:
        """Clean and deduplicate skills"""
        if not skills:
            return []
        
        cleaned_skills = set()
        
        for skill in skills:
            if not skill:
                continue
                
            skill = self.clean_text(skill.lower())
            
            # Skip very short or generic skills
            if len(skill) <= 2 or skill in ['a', 'an', 'the', 'is', 'are']:
                continue
            
            # Normalize common skill names
            skill_mappings = {
                'ms office': 'Microsoft Office',
                'ms word': 'Microsoft Word',
                'ms excel': 'Microsoft Excel',
                'powerpoint': 'Microsoft PowerPoint',
                'js': 'JavaScript',
                'html5': 'HTML',
                'css3': 'CSS',
                'mysql': 'MySQL',
                'postgresql': 'PostgreSQL'
            }
            
            normalized_skill = skill_mappings.get(skill, skill.title())
            cleaned_skills.add(normalized_skill)
        
        return sorted(list(cleaned_skills))
    
    def validate_date(self, date_obj: Optional[datetime]) -> Optional[datetime]:
        """Validate and clean date objects"""
        if not date_obj:
            return None
        
        current_date = datetime.now()
        
        # Check if date is reasonable (not too far in past or future)
        min_date = current_date - timedelta(days=365)  # 1 year ago
        max_date = current_date + timedelta(days=730)  # 2 years in future
        
        if min_date <= date_obj <= max_date:
            return date_obj
        
        logger.warning(f"Date {date_obj} is outside reasonable range")
        return None
    
    def clean_description(self, description: str) -> str:
        """Clean job description"""
        if not description:
            return ""
        
        description = self.clean_text(description)
        
        # Remove repeated phrases
        description = re.sub(r'\b(\w+)\b\s+\1\b', r'\1', description)
        
        # Remove excessive repetition of common words
        common_words = ['job', 'position', 'role', 'responsibility', 'requirement']
        for word in common_words:
            pattern = rf'\b{word}\b'
            if len(re.findall(pattern, description, re.IGNORECASE)) > 3:
                # Keep only first 2 occurrences
                matches = list(re.finditer(pattern, description, re.IGNORECASE))
                if len(matches) > 2:
                    for match in matches[2:]:
                        start, end = match.span()
                        description = description[:start] + description[end:]
        
        return description.strip()
    
    def validate_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean complete job data"""
        if not isinstance(job_data, dict):
            return {}
        
        cleaned = {}
        
        # Required fields
        required_fields = ['title', 'department', 'location']
        for field in required_fields:
            value = job_data.get(field, '')
            if not value or not str(value).strip():
                logger.warning(f"Missing required field: {field}")
                return {}  # Invalid job if required fields are missing
        
        # Clean individual fields
        cleaned['title'] = self.clean_title(job_data.get('title', ''))
        cleaned['department'] = self.normalize_department(job_data.get('department', ''))
        cleaned['location'] = self.normalize_location(job_data.get('location', ''))
        
        # Optional fields
        cleaned['grade'] = self.clean_grade(job_data.get('grade', ''))
        cleaned['salary'] = self.clean_salary(job_data.get('salary', ''))
        cleaned['description'] = self.clean_description(job_data.get('description', ''))
        
        # Numeric fields
        cleaned['vacancies'] = self.clean_numeric_field(job_data.get('vacancies'), 'vacancies')
        cleaned['age_min'] = self.clean_numeric_field(job_data.get('age_min'), 'age')
        cleaned['age_max'] = self.clean_numeric_field(job_data.get('age_max'), 'age')
        
        # List fields
        cleaned['skills'] = self.clean_skills(job_data.get('skills', []))
        
        # Date fields
        cleaned['posting_date'] = self.validate_date(job_data.get('posting_date'))
        cleaned['deadline_date'] = self.validate_date(job_data.get('deadline_date'))
        
        # Text fields
        cleaned['education'] = self.clean_text(job_data.get('education', ''))
        cleaned['experience'] = self.clean_text(job_data.get('experience', ''))
        
        # URL fields
        cleaned['application_link'] = self.clean_url(job_data.get('application_link', ''))
        cleaned['source_url'] = self.clean_url(job_data.get('source_url', ''))
        
        return cleaned
    
    def clean_grade(self, grade: str) -> Optional[str]:
        """Clean and standardize job grades"""
        if not grade:
            return None
        
        grade = self.clean_text(grade.lower())
        
        for pattern, replacement in self.grade_patterns:
            if isinstance(replacement, str):
                grade = re.sub(pattern, replacement, grade, flags=re.IGNORECASE)
            else:
                match = re.search(pattern, grade, re.IGNORECASE)
                if match:
                    grade = replacement(match)
        
        return grade.strip().title() if grade.strip() else None
    
    def clean_numeric_field(self, value: Any, field_type: str) -> Optional[int]:
        """Clean numeric fields with validation"""
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                # Extract numbers from string
                numbers = re.findall(r'\d+', value)
                if not numbers:
                    return None
                value = int(numbers[0])
            else:
                value = int(value)
            
            # Validate ranges
            if field_type == 'vacancies':
                return value if 1 <= value <= 10000 else None
            elif field_type == 'age':
                return value if 15 <= value <= 70 else None
            else:
                return value if value > 0 else None
                
        except (ValueError, TypeError):
            return None
    
    def clean_url(self, url: str) -> Optional[str]:
        """Clean and validate URLs"""
        if not url:
            return None
        
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if re.match(url_pattern, url):
            return url
        
        return None
    
    def deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on title, department, and location"""
        if not jobs:
            return []
        
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create unique key
            key_parts = [
                self.clean_title(job.get('title', '')),
                self.normalize_department(job.get('department', '')),
                self.normalize_location(job.get('location', ''))
            ]
            key = '|'.join(part.lower().strip() for part in key_parts if part)
            
            if key not in seen and key:
                seen.add(key)
                unique_jobs.append(job)
            else:
                logger.debug(f"Duplicate job found: {job.get('title', 'Unknown')}")
        
        logger.info(f"Removed {len(jobs) - len(unique_jobs)} duplicate jobs")
        return unique_jobs
    
    def calculate_data_quality_score(self, job_data: Dict[str, Any]) -> float:
        """Calculate data quality score for a job (0-100)"""
        if not job_data:
            return 0.0
        
        score = 0.0
        max_score = 100.0
        
        # Required fields (40 points)
        required_fields = ['title', 'department', 'location']
        for field in required_fields:
            if job_data.get(field) and str(job_data[field]).strip():
                score += 40 / len(required_fields)
        
        # Important optional fields (30 points)
        important_fields = ['description', 'application_link', 'deadline_date']
        for field in important_fields:
            if job_data.get(field) and str(job_data[field]).strip():
                score += 30 / len(important_fields)
        
        # Additional fields (20 points)
        additional_fields = ['salary', 'vacancies', 'skills', 'education']
        for field in additional_fields:
            value = job_data.get(field)
            if value and (isinstance(value, list) and len(value) > 0 or str(value).strip()):
                score += 20 / len(additional_fields)
        
        # Data completeness bonus (10 points)
        filled_fields = sum(1 for v in job_data.values() if v and str(v).strip())
        total_fields = len(job_data)
        if total_fields > 0:
            completeness = filled_fields / total_fields
            score += 10 * completeness
        
        return min(score, max_score)
    
    def clean_batch(self, jobs: List[Dict[str, Any]], 
                   min_quality_score: float = 50.0) -> List[Dict[str, Any]]:
        """Clean a batch of jobs with quality filtering"""
        if not jobs:
            return []
        
        logger.info(f"Cleaning batch of {len(jobs)} jobs")
        
        # Clean individual jobs
        cleaned_jobs = []
        for job in jobs:
            try:
                cleaned_job = self.validate_job_data(job)
                if cleaned_job:  # Only add if validation passed
                    quality_score = self.calculate_data_quality_score(cleaned_job)
                    cleaned_job['_quality_score'] = quality_score
                    
                    if quality_score >= min_quality_score:
                        cleaned_jobs.append(cleaned_job)
                    else:
                        logger.debug(f"Job rejected due to low quality score: {quality_score}")
            except Exception as e:
                logger.error(f"Error cleaning job: {e}")
                continue
        
        # Remove duplicates
        unique_jobs = self.deduplicate_jobs(cleaned_jobs)
        
        # Remove quality score field before returning
        for job in unique_jobs:
            job.pop('_quality_score', None)
        
        logger.info(f"Batch cleaning completed: {len(unique_jobs)} valid jobs from {len(jobs)} input")
        
        return unique_jobs
    
    def generate_cleaning_report(self, original_jobs: List[Dict], 
                               cleaned_jobs: List[Dict]) -> Dict[str, Any]:
        """Generate a report on the cleaning process"""
        if not original_jobs:
            return {}
        
        original_count = len(original_jobs)
        cleaned_count = len(cleaned_jobs)
        
        # Calculate field completeness
        field_completeness = {}
        if cleaned_jobs:
            for field in cleaned_jobs[0].keys():
                filled_count = sum(1 for job in cleaned_jobs 
                                 if job.get(field) and str(job[field]).strip())
                field_completeness[field] = (filled_count / cleaned_count) * 100
        
        # Calculate average quality score
        quality_scores = []
        for job in cleaned_jobs:
            score = self.calculate_data_quality_score(job)
            quality_scores.append(score)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        report = {
            'original_count': original_count,
            'cleaned_count': cleaned_count,
            'removed_count': original_count - cleaned_count,
            'removal_rate': ((original_count - cleaned_count) / original_count) * 100,
            'average_quality_score': round(avg_quality, 2),
            'field_completeness': field_completeness,
            'quality_distribution': {
                'excellent (90-100)': len([s for s in quality_scores if s >= 90]),
                'good (70-89)': len([s for s in quality_scores if 70 <= s < 90]),
                'fair (50-69)': len([s for s in quality_scores if 50 <= s < 70]),
                'poor (0-49)': len([s for s in quality_scores if s < 50])
            }
        }
        
        return report