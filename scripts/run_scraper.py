# =============================================================================
# 24. Standalone Scraper Runner (scripts/run_scraper.py)
# =============================================================================

import asyncio
import sys
import os
import argparse
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scrapers.scraper_manager import ScraperManager
from app.utils.logger import setup_logging
from app.config import settings
import logging

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

async def run_scraper(save_to_db: bool = True, max_jobs: int = None):
    # Run the scraper and optionally save to database
    start_time = datetime.now()
    logger.info(f"Starting scraper run at {start_time}")
    
    try:
        manager = ScraperManager()
        
        # Scrape jobs
        jobs = await manager.scrape_all_sources()
        
        if max_jobs:
            jobs = jobs[:max_jobs]
        
        logger.info(f"Scraped {len(jobs)} jobs")
        
        # Save to database if requested
        if save_to_db and jobs:
            await manager.save_jobs_to_db(jobs)
            logger.info("Jobs saved to database")
        
        # Print summary
        if jobs:
            print(f"\\nScraper Summary:")
            print(f"Total jobs scraped: {len(jobs)}")
            print(f"Execution time: {datetime.now() - start_time}")
            print(f"\\nSample jobs:")
            
            for i, job in enumerate(jobs[:3], 1):
                print(f"{i}. {job.title} - {job.department} ({job.location})")
        else:
            print("No jobs scraped")
            
    except Exception as e:
        logger.error(f"Scraper run failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run BD Government Jobs Scraper")
    parser.add_argument("--no-save", action="store_true", help="Don't save to database")
    parser.add_argument("--max-jobs", type=int, help="Maximum number of jobs to process")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Update log level if specified
    if args.log_level:
        setup_logging(args.log_level)
    
    # Run scraper
    asyncio.run(run_scraper(
        save_to_db=not args.no_save,
        max_jobs=args.max_jobs
    ))

if __name__ == "__main__":
    main()