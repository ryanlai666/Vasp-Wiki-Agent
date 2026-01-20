"""MediaWiki scraper for VASP Wiki."""
import time
import json
import requests
from pathlib import Path
from typing import List, Set, Dict, Optional
from urllib.parse import urljoin, urlparse, unquote
import re

from backend.config import settings
from backend.utils.logger import logger


class WikiScraper:
    """Scraper for MediaWiki-based VASP Wiki."""
    
    def __init__(self, base_url: str = None, api_url: str = None, delay: float = 1.0):
        """
        Initialize the wiki scraper.
        
        Args:
            base_url: Base URL of the wiki
            api_url: MediaWiki API URL
            delay: Delay between requests in seconds
        """
        self.base_url = base_url or settings.wiki_base_url
        self.api_url = api_url or settings.wiki_api_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VASP-Wiki-RAG-Agent/1.0 (Educational Purpose)'
        })
        self.scraped_pages: Set[str] = set()
        self.failed_pages: Set[str] = set()
        self.progress_file = Path(settings.data_raw_path) / "scraping_progress.json"
        self._load_progress()
    
    def _load_progress(self):
        """Load scraping progress from file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    self.scraped_pages = set(progress.get('scraped_pages', []))
                    self.failed_pages = set(progress.get('failed_pages', []))
                    logger.info(f"Loaded progress: {len(self.scraped_pages)} pages scraped")
            except Exception as e:
                logger.warning(f"Could not load progress: {e}")
    
    def _save_progress(self):
        """Save scraping progress to file."""
        try:
            progress = {
                'scraped_pages': list(self.scraped_pages),
                'failed_pages': list(self.failed_pages)
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save progress: {e}")
    
    def _get_page_content(self, page_title: str) -> Optional[str]:
        """
        Get raw HTML content of a wiki page.
        
        Args:
            page_title: Title of the page to scrape
            
        Returns:
            HTML content or None if failed
        """
        # Use MediaWiki API to get page content
        params = {
            'action': 'parse',
            'page': page_title,
            'format': 'json',
            'prop': 'text',
            'disableeditsection': '1'
        }
        
        try:
            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'parse' in data and 'text' in data['parse']:
                return data['parse']['text']['*']
            else:
                logger.warning(f"No content found for page: {page_title}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {page_title}: {e}")
            return None
    
    def _extract_wiki_links(self, html_content: str) -> Set[str]:
        """
        Extract internal wiki links from HTML content.
        
        Args:
            html_content: HTML content of a page
            
        Returns:
            Set of page titles linked from this page
        """
        links = set()
        # Pattern to match wiki internal links: /wiki/Page_Title
        pattern = r'href=["\']/wiki/([^"\']+)["\']'
        matches = re.findall(pattern, html_content)
        
        for match in matches:
            # Remove URL fragments and query params
            page_title = unquote(match.split('#')[0].split('?')[0])
            # Skip special pages
            if not any(page_title.startswith(prefix) for prefix in ['Special:', 'Category:', 'File:', 'Template:', 'Help:']):
                links.add(page_title)
        
        return links
    
    def _get_all_pages_from_category(self, category: str = None) -> List[str]:
        """
        Get all page titles from MediaWiki API.
        
        Args:
            category: Optional category to filter pages
            
        Returns:
            List of page titles
        """
        all_pages = []
        continue_param = None
        
        params = {
            'action': 'query',
            'list': 'allpages',
            'aplimit': '500',  # Maximum allowed
            'format': 'json'
        }
        
        if category:
            params['list'] = 'categorymembers'
            params['cmtitle'] = f'Category:{category}'
            params['cmlimit'] = '500'
        
        logger.info(f"Fetching page list from API...")
        
        while True:
            if continue_param:
                params['apcontinue' if not category else 'cmcontinue'] = continue_param
            
            try:
                response = self.session.get(self.api_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'query' in data:
                    pages = data['query'].get('allpages' if not category else 'categorymembers', [])
                    for page in pages:
                        all_pages.append(page['title'])
                
                # Check for continuation
                if 'continue' in data:
                    continue_param = data['continue'].get('apcontinue' if not category else 'cmcontinue')
                else:
                    break
                    
                time.sleep(self.delay)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching page list: {e}")
                break
        
        logger.info(f"Found {len(all_pages)} pages")
        return all_pages
    
    def scrape_page(self, page_title: str) -> Optional[Dict]:
        """
        Scrape a single wiki page.
        
        Args:
            page_title: Title of the page to scrape
            
        Returns:
            Dictionary with page data or None if failed
        """
        if page_title in self.scraped_pages:
            logger.debug(f"Skipping already scraped page: {page_title}")
            return None
        
        logger.info(f"Scraping page: {page_title}")
        
        html_content = self._get_page_content(page_title)
        if html_content is None:
            self.failed_pages.add(page_title)
            self._save_progress()
            return None
        
        # Extract links
        links = self._extract_wiki_links(html_content)
        
        # Save raw HTML
        safe_title = page_title.replace('/', '_').replace('\\', '_')
        output_file = Path(settings.data_raw_path) / f"{safe_title}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        page_data = {
            'title': page_title,
            'url': f"{self.base_url}/{page_title.replace(' ', '_')}",
            'html_content': html_content,
            'links': list(links),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.scraped_pages.add(page_title)
        self._save_progress()
        
        time.sleep(self.delay)  # Rate limiting
        
        return page_data
    
    def scrape_from_seed(self, seed_pages: List[str], max_pages: int = None) -> List[Dict]:
        """
        Scrape wiki starting from seed pages, following internal links.
        
        Args:
            seed_pages: List of page titles to start from
            max_pages: Maximum number of pages to scrape (None for unlimited)
            
        Returns:
            List of scraped page data
        """
        queue = list(seed_pages)
        scraped_data = []
        
        while queue and (max_pages is None or len(scraped_data) < max_pages):
            page_title = queue.pop(0)
            
            if page_title in self.scraped_pages:
                continue
            
            page_data = self.scrape_page(page_title)
            if page_data:
                scraped_data.append(page_data)
                
                # Add linked pages to queue
                for link in page_data['links']:
                    if link not in self.scraped_pages and link not in queue:
                        queue.append(link)
                
                logger.info(f"Progress: {len(scraped_data)} pages scraped, {len(queue)} in queue")
        
        return scraped_data
    
    def scrape_all_pages(self, max_pages: int = None) -> List[Dict]:
        """
        Scrape all pages from the wiki.
        
        Args:
            max_pages: Maximum number of pages to scrape (None for unlimited)
            
        Returns:
            List of scraped page data
        """
        all_page_titles = self._get_all_pages_from_category()
        scraped_data = []
        
        for i, page_title in enumerate(all_page_titles):
            if max_pages and len(scraped_data) >= max_pages:
                break
            
            if page_title not in self.scraped_pages:
                page_data = self.scrape_page(page_title)
                if page_data:
                    scraped_data.append(page_data)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {len(scraped_data)} pages scraped out of {i + 1} processed")
        
        return scraped_data
