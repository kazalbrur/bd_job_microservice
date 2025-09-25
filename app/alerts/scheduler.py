# =============================================================================
# 13. Scheduler (app/alerts/scheduler.py)
# =============================================================================

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

class JobScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scraper_manager = ScraperManager()
        self.alert_service = AlertService()
    
    def start(self):
        """Start the scheduler"""
        
        # Schedule scraping every 6 hours
        self.scheduler.add_job(
            self._run_scraper,
            IntervalTrigger(hours=6),
            id='scraper_job',
            name='Run job scraper',
            replace_existing=True
        )
        
        # Schedule alert checking every hour
        self.scheduler.add_job(
            self._check_alerts,
            IntervalTrigger(hours=1),
            id='alert_job',
            name='Check and send alerts',
            replace_existing=True
        )
        
        # Schedule cleanup at 2 AM daily
        self.scheduler.add_job(
            self._cleanup_old_jobs,
            CronTrigger(hour=2, minute=0),
            id='cleanup_job',
            name='Cleanup old jobs',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Job scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Job scheduler stopped")
    
    async def _run_scraper(self):
        """Scheduled scraper task"""
        try:
            logger.info("Starting scheduled scraping...")
            jobs = await self.scraper_manager.scrape_all_sources()
            await self.scraper_manager.save_jobs_to_db(jobs)
            logger.info(f"Scheduled scraping completed: {len(jobs)} jobs processed")
        except Exception as e:
            logger.error(f"Scheduled scraping failed: {e}")
    
    async def _check_alerts(self):
        """Scheduled alert checking"""
        try:
            with db_manager.get_session() as db:
                await self.alert_service.check_and_send_alerts(db)
        except Exception as e:
            logger.error(f"Alert checking failed: {e}")
    
    async def _cleanup_old_jobs(self):
        """Cleanup old jobs"""
        try:
            with db_manager.get_session() as db:
                # Deactivate jobs older than 6 months
                cutoff_date = datetime.utcnow() - timedelta(days=180)
                updated = db.query(Job).filter(
                    Job.created_at < cutoff_date
                ).update({'is_active': False})
                
                db.commit()
                logger.info(f"Deactivated {updated} old jobs")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Initialize scheduler
scheduler = JobScheduler()