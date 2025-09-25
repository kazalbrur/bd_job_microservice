# =============================================================================
# 7. Government Jobs Scraper (app/scrapers/govbd_scraper.py)
# =============================================================================

from typing import List, Dict, Optional
from datetime import datetime
from playwright.async_api import Page
import logging
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GovBDScraper(BaseScraper):
    def __init__(self):
        super().__init__("GovBD")
        self.base_url = "https://www.bcsconfidence.online"
        self.jobs_url = "https://www.bcsconfidence.online/job-news"
    
    async def scrape_jobs(self) -> List[Dict]:
        """Scrape jobs from government portal, with an HTTP fallback when Playwright isn't available."""
        jobs = []
        
        try:
            # If browser is available, use the JS-powered approach
            if self.browser:
                page = await self.browser.new_page()
                await page.goto(self.jobs_url, wait_until="networkidle")
                
                # Extract job links (from client-side rendered pages)
                job_links = await page.evaluate("""
                    () => {
                        const links = [];
                        document.querySelectorAll('a[href*="job"]').forEach(link => {
                            if (link.href && link.textContent.trim()) {
                                links.push({
                                    url: link.href,
                                    title: link.textContent.trim()
                                });
                            }
                        });
                        return links;
                    }
                """)
                
                for job_link in job_links[:20]:  # Limit for safety
                    job_data = await self._scrape_job_detail(page, job_link)
                    if job_data:
                        jobs.append(job_data)

                await page.close()

            else:
                # HTTP fallback using BeautifulSoup; this is JS-free but works for
                # simple server-rendered pages. It returns basic metadata so the
                # rest of the pipeline can run during development.
                try:
                    async with self.session.get(self.jobs_url) as resp:
                        if resp.status != 200:
                            logger.warning(f"GovBD listing endpoint returned {resp.status}")
                            return jobs
                        body = await resp.text()
                except Exception as e:
                    logger.error(f"GovBD HTTP listing request failed: {e}")
                    return jobs

                soup = BeautifulSoup(body, "lxml")
                anchors = soup.find_all("a", href=True)
                seen = set()

                for a in anchors:
                    href = a.get("href")
                    text = (a.get_text(strip=True) or "").strip()
                    if not text:
                        continue
                    lowered = (href + " " + text).lower()
                    if "job" in lowered or "vacancy" in lowered or "circular" in lowered:
                        full = href if href.startswith("http") else (self.base_url.rstrip("/") + "/" + href.lstrip("/"))
                        if full in seen:
                            continue
                        seen.add(full)
                        jobs.append({
                            "title": text,
                            "source_url": full,
                            "source_site": "gov.bd",
                            "posting_date": datetime.now().isoformat(),
                            "description": "",
                        })

                # Limit results for demo/runtime sanity
                jobs = jobs[:20]

        except Exception as e:
            logger.error(f"GovBD scraping error: {e}")
        
        return jobs
    
    async def _scrape_job_detail(self, page: Page, job_link: Dict) -> Optional[Dict]:
        """Scrape individual job details (browser-driven)."""
        try:
            await page.goto(job_link['url'], wait_until="networkidle")
            
            # Extract job data using page evaluation
            job_data = await page.evaluate("""
                    () => {
                        const data = {};
                        
                        // Title
                        const titleEl = document.querySelector('h1, .job-title, .title');
                        data.title = titleEl ? titleEl.textContent.trim() : '';
                        
                        // Department
                        const deptEl = document.querySelector('.department, .organization');
                        data.department = deptEl ? deptEl.textContent.trim() : '';
                        
                        // Location
                        const locEl = document.querySelector('.location, .workplace');
                        data.location = locEl ? locEl.textContent.trim() : '';
                        
                        // Description
                        const descEl = document.querySelector('.description, .job-description, .details');
                        data.description = descEl ? descEl.textContent.trim() : '';
                        
                        // Deadline
                        const deadlineEl = document.querySelector('.deadline, .last-date');
                        data.deadline_date = deadlineEl ? deadlineEl.textContent.trim() : '';
                        
                        // Application link
                        const applyEl = document.querySelector('a[href*="apply"], .apply-link');
                        data.application_link = applyEl ? applyEl.href : window.location.href;
                        
                        return data;
                    }
                """)
            
            # Add metadata
            job_data.update({
                'source_url': job_link['url'],
                'source_site': 'gov.bd',
                'posting_date': datetime.now().isoformat()
            })
            
            return job_data
            
        except Exception as e:
            logger.error(f"Job detail scraping error: {e}")
            return None
    
    async def _scrape_url(self, url: str) -> Dict:
        """Scrape specific URL implementation (browser-driven)."""
        page = await self.browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            # Implementation specific to URL structure
            return {}
        finally:
            await page.close()
