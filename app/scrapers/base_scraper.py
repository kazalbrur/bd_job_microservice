# =============================================================================
# 6. Base Scraper (app/scrapers/base_scraper.py)
# =============================================================================

import asyncio
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Browser, Page
import aiohttp
from typing import Dict, List, Optional
import random
import logging

from app.parsers.job_parser import JobParser
from app.config import settings

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, name: str):
        self.name = name
        self.browser: Optional[Browser] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.parser = JobParser()
        
    async def __aenter__(self):
        await self._setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup()
    
    async def _setup(self):
        """Setup browser and HTTP session"""
        # Try to start Playwright and launch a browser. If Playwright or the
        # browsers are not installed, log a warning and continue with only the
        # aiohttp session as a fallback. This allows running scripts in
        # environments where Playwright wasn't set up yet.
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
        except Exception as e:
            logger.warning(f"Playwright/browser startup failed, falling back to HTTP session: {e}")
            self.playwright = None
            self.browser = None

        # Always create an aiohttp session for HTTP based fallback scraping
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.SCRAPER_TIMEOUT),
            headers={'User-Agent': self._get_random_user_agent()}
        )
    
    async def _cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        return random.choice(user_agents)
    
    async def _delay(self):
        """Random delay between requests"""
        await asyncio.sleep(random.uniform(0.5, settings.SCRAPER_DELAY * 2))
    
    @abstractmethod
    async def scrape_jobs(self) -> List[Dict]:
        """Scrape jobs from the source"""
        pass
    
    async def scrape_with_retry(self, url: str, retries: int = None) -> Optional[Dict]:
        """Scrape with retry logic"""
        if retries is None:
            retries = settings.SCRAPER_RETRIES
        
        for attempt in range(retries):
            try:
                await self._delay()
                return await self._scrape_url(url)
            except Exception as e:
                logger.warning(f"Scrape attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to scrape {url} after {retries} attempts")
                    return None
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    @abstractmethod
    async def _scrape_url(self, url: str) -> Dict:
        """Scrape specific URL - to be implemented by subclasses"""
        pass
