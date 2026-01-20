"""Content processor for cleaning and extracting text from HTML."""
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import html2text
import re

from backend.config import settings
from backend.utils.logger import logger


class ContentProcessor:
    """Processes HTML content from wiki pages into clean text."""
    
    def __init__(self):
        """Initialize the content processor."""
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # Don't wrap lines
        self.html_converter.unicode_snob = True
    
    def clean_html(self, html_content: str) -> str:
        """
        Clean HTML content by removing navigation, sidebars, etc.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Cleaned HTML content
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove navigation elements
        for element in soup.find_all(['nav', 'aside', 'header', 'footer']):
            element.decompose()
        
        # Remove common MediaWiki navigation elements
        for element in soup.find_all(class_=re.compile(r'nav|sidebar|toc|mw-|vector-')):
            element.decompose()
        
        # Remove edit sections
        for element in soup.find_all(class_=re.compile(r'editsection|mw-editsection')):
            element.decompose()
        
        # Remove references/superscripts (but keep content)
        for element in soup.find_all('sup', class_=re.compile(r'reference')):
            element.decompose()
        
        # Get main content area
        content_div = soup.find('div', id='mw-content-text') or soup.find('div', class_='mw-parser-output')
        if content_div:
            return str(content_div)
        else:
            # Fallback to body
            return str(soup.find('body') or soup)
    
    def extract_sections(self, html_content: str) -> List[Dict]:
        """
        Extract sections from HTML content with headings.
        
        Args:
            html_content: HTML content
            
        Returns:
            List of sections with headings and content
        """
        soup = BeautifulSoup(html_content, 'lxml')
        sections = []
        current_section = None
        current_content = []
        
        # Find all headings and content
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'pre', 'code', 'blockquote']):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Save previous section
                if current_section and current_content:
                    sections.append({
                        'heading': current_section,
                        'content': '\n'.join(current_content),
                        'level': self._get_heading_level(current_section)
                    })
                
                # Start new section
                current_section = element.get_text(strip=True)
                current_content = []
            else:
                # Add content to current section
                text = element.get_text(separator=' ', strip=True)
                if text:
                    current_content.append(text)
        
        # Add last section
        if current_section and current_content:
            sections.append({
                'heading': current_section,
                'content': '\n'.join(current_content),
                'level': self._get_heading_level(current_section)
            })
        
        return sections
    
    def _get_heading_level(self, heading_text: str) -> int:
        """Extract heading level from heading text (if it contains level info)."""
        # This is a simple implementation; can be enhanced
        return 1
    
    def html_to_markdown(self, html_content: str) -> str:
        """
        Convert HTML to markdown.
        
        Args:
            html_content: HTML content
            
        Returns:
            Markdown content
        """
        cleaned_html = self.clean_html(html_content)
        markdown = self.html_converter.handle(cleaned_html)
        return markdown.strip()
    
    def html_to_text(self, html_content: str) -> str:
        """
        Convert HTML to plain text.
        
        Args:
            html_content: HTML content
            
        Returns:
            Plain text content
        """
        soup = BeautifulSoup(html_content, 'lxml')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text.strip()
    
    def process_page(self, page_data: Dict) -> Dict:
        """
        Process a scraped page into clean text with metadata.
        
        Args:
            page_data: Dictionary with page data from scraper
            
        Returns:
            Processed page data with clean text and sections
        """
        title = page_data['title']
        html_content = page_data['html_content']
        
        logger.info(f"Processing page: {title}")
        
        # Extract sections
        sections = self.extract_sections(html_content)
        
        # Convert to markdown and text
        markdown = self.html_to_markdown(html_content)
        plain_text = self.html_to_text(html_content)
        
        processed_data = {
            'title': title,
            'url': page_data['url'],
            'markdown': markdown,
            'plain_text': plain_text,
            'sections': sections,
            'metadata': {
                'num_sections': len(sections),
                'text_length': len(plain_text),
                'scraped_at': page_data.get('scraped_at', '')
            }
        }
        
        # Save processed content
        safe_title = title.replace('/', '_').replace('\\', '_')
        output_file = Path(settings.data_processed_path) / f"{safe_title}.json"
        
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        
        return processed_data
    
    def process_all_pages(self) -> List[Dict]:
        """
        Process all scraped pages from raw HTML files.
        
        Returns:
            List of processed page data
        """
        raw_dir = Path(settings.data_raw_path)
        processed_pages = []
        
        html_files = list(raw_dir.glob("*.html"))
        logger.info(f"Found {len(html_files)} HTML files to process")
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Extract title from filename
                title = html_file.stem.replace('_', ' ')
                
                page_data = {
                    'title': title,
                    'url': f"{settings.wiki_base_url}/{title.replace(' ', '_')}",
                    'html_content': html_content
                }
                
                processed_data = self.process_page(page_data)
                processed_pages.append(processed_data)
                
            except Exception as e:
                logger.error(f"Error processing {html_file}: {e}")
        
        logger.info(f"Processed {len(processed_pages)} pages")
        return processed_pages
