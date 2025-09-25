# =============================================================================
# 8. Scraper Manager (app/scrapers/scraper_manager.py)
# =============================================================================

class ScraperManager:
    def __init__(self):
        self.scrapers = [
            GovBDScraper,
            # Add more scrapers here
        ]
        self.parser = JobParser()
    
    async def scrape_all_sources(self) -> List[ParsedJob]:
        """Scrape all job sources and return parsed jobs"""
        all_jobs = []
        
        for scraper_class in self.scrapers:
            try:
                async with scraper_class() as scraper:
                    logger.info(f"Starting scraper: {scraper.name}")
                    raw_jobs = await scraper.scrape_jobs()
                    
                    # Parse jobs
                    for raw_job in raw_jobs:
                        try:
                            parsed_job = self.parser.parse_job(raw_job)
                            all_jobs.append(parsed_job)
                        except Exception as e:
                            logger.error(f"Job parsing failed: {e}")
                    
                    logger.info(f"Scraped {len(raw_jobs)} jobs from {scraper.name}")
                    
            except Exception as e:
                logger.error(f"Scraper {scraper_class.__name__} failed: {e}")
        
        # Deduplicate jobs
        unique_jobs = self._deduplicate_jobs(all_jobs)
        logger.info(f"Total unique jobs after deduplication: {len(unique_jobs)}")
        
        return unique_jobs
    
    def _deduplicate_jobs(self, jobs: List[ParsedJob]) -> List[ParsedJob]:
        """Remove duplicate jobs based on job_id"""
        seen_ids = set()
        unique_jobs = []
        
        for job in jobs:
            if job.job_id not in seen_ids:
                seen_ids.add(job.job_id)
                unique_jobs.append(job)
        
        return unique_jobs
    
    async def save_jobs_to_db(self, jobs: List[ParsedJob]):
        """Save parsed jobs to database"""
        with db_manager.get_session() as session:
            saved_count = 0
            
            for job in jobs:
                try:
                    # Check if job already exists
                    existing = session.query(Job).filter(Job.job_id == job.job_id).first()
                    
                    if not existing:
                        db_job = Job(
                            job_id=job.job_id,
                            title=job.title,
                            department=job.department,
                            location=job.location,
                            grade=job.grade,
                            salary=job.salary,
                            vacancies=job.vacancies,
                            education=job.education,
                            experience=job.experience,
                            age_min=job.age_min,
                            age_max=job.age_max,
                            skills=job.skills,
                            description=job.description,
                            posting_date=job.posting_date,
                            deadline_date=job.deadline_date,
                            application_link=job.application_link,
                            source_url=job.source_url,
                            source_site=job.source_site
                        )
                        session.add(db_job)
                        saved_count += 1
                
                except Exception as e:
                    logger.error(f"Failed to save job {job.job_id}: {e}")
            
            session.commit()
            logger.info(f"Saved {saved_count} new jobs to database")

