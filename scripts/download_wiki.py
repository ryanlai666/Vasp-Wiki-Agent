#!/usr/bin/env python3
"""
Script to download VASP Wiki pages.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scraper.wiki_scraper import WikiScraper
from backend.utils.logger import logger


def main():
    """Download VASP Wiki pages."""
    logger.info("Starting VASP Wiki download...")
    
    scraper = WikiScraper(delay=1.0)  # 1 second delay between requests
    
    # Start from The_VASP_Manual page and follow links
    seed_pages = ["The_VASP_Manual"]
    
    print("\n" + "="*60)
    print("VASP Wiki Downloader")
    print("="*60)
    print("\nOptions:")
    print("1. Scrape from seed pages (The_VASP_Manual and linked pages)")
    print("2. Scrape all pages from the wiki")
    print("3. Continue from previous progress")
    
    choice = input("\nEnter choice (1-3, default=1): ").strip() or "1"
    
    if choice == "1":
        max_pages = input("Maximum pages to scrape (press Enter for unlimited): ").strip()
        max_pages = int(max_pages) if max_pages else None
        
        logger.info(f"Scraping from seed pages: {seed_pages}")
        scraped_data = scraper.scrape_from_seed(seed_pages, max_pages=max_pages)
        logger.info(f"Scraped {len(scraped_data)} pages")
        
    elif choice == "2":
        max_pages = input("Maximum pages to scrape (press Enter for unlimited): ").strip()
        max_pages = int(max_pages) if max_pages else None
        
        logger.info("Scraping all pages from wiki")
        scraped_data = scraper.scrape_all_pages(max_pages=max_pages)
        logger.info(f"Scraped {len(scraped_data)} pages")
        
    elif choice == "3":
        logger.info("Continuing from previous progress...")
        # The scraper will automatically skip already scraped pages
        scraped_data = scraper.scrape_from_seed(seed_pages)
        logger.info(f"Scraped {len(scraped_data)} new pages")
        
    else:
        logger.error("Invalid choice")
        return
    
    print(f"\n✓ Download complete! Scraped {len(scraped_data)} pages")
    print(f"  Raw HTML saved to: data/raw/")
    print(f"  Progress saved to: data/raw/scraping_progress.json")
    print("\nNext step: Run 'python scripts/build_index.py' to process and index the data")


if __name__ == "__main__":
    main()
