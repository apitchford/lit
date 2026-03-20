"""
Article extraction module with multi-tier paywall bypass
"""
import logging
import time
from typing import Optional, Dict, Any
from urllib.parse import quote

import requests
import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ArticleExtractor:
    """Extract article content with paywall bypass capabilities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article content using multi-tier approach
        
        Returns dict with: title, author, date, content, images
        """
        logger.info(f"Extracting article from: {url}")
        
        # Tier 1: Direct extraction with trafilatura
        result = self._extract_direct(url)
        if result and self._is_valid_content(result):
            logger.info("Tier 1 (direct) successful")
            return result
        
        # Tier 2: Archive.is
        result = self._extract_archive_is(url)
        if result and self._is_valid_content(result):
            logger.info("Tier 2 (archive.is) successful")
            return result
        
        # Tier 3: 12ft.io
        result = self._extract_12ft(url)
        if result and self._is_valid_content(result):
            logger.info("Tier 3 (12ft.io) successful")
            return result
        
        # Tier 4: Playwright with JS disabled
        result = self._extract_playwright(url)
        if result and self._is_valid_content(result):
            logger.info("Tier 4 (playwright) successful")
            return result
        
        logger.error("All extraction tiers failed")
        return None
    
    def _extract_direct(self, url: str) -> Optional[Dict[str, Any]]:
        """Tier 1: Direct extraction using trafilatura + BeautifulSoup"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            
            # Use BeautifulSoup to get better metadata
            soup = BeautifulSoup(downloaded, 'lxml')
            
            # Extract title from multiple sources
            title = None
            # Try og:title
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content')
            # Try title tag
            if not title and soup.title:
                title = soup.title.string
            # Try h1
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text().strip()
            
            # Extract author
            author = None
            author_meta = soup.find('meta', attrs={'name': 'author'}) or \
                         soup.find('meta', property='article:author')
            if author_meta:
                author = author_meta.get('content')
            
            # Extract date
            date = None
            date_meta = soup.find('meta', property='article:published_time')
            if date_meta:
                date = date_meta.get('content')
            
            # Extract main content with trafilatura (preserves structure better)
            content_html = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                include_images=True,
                include_links=False,
                output_format='html',
                favor_precision=True
            )

            if not content_html:
                # Fallback to text
                content_html = trafilatura.extract(
                    downloaded,
                    output_format='txt'
                )

            # Resolve relative image URLs so they match the processed image map
            if content_html:
                content_html = self._resolve_image_urls(content_html, url)

            # Extract images with better context
            images = self._extract_images_with_context(downloaded, url)
            
            logger.info(f"Extracted: title='{title}', author='{author}', images={len(images)}")
            
            return {
                'title': title or 'Untitled',
                'author': author,
                'date': date,
                'content': content_html or '',
                'images': images,
                'source_url': url
            }
            
        except Exception as e:
            logger.error(f"Direct extraction failed: {e}")
            return None
    
    def _extract_archive_is(self, url: str) -> Optional[Dict[str, Any]]:
        """Tier 2: Extract via archive.is"""
        try:
            # First check if archive exists
            archive_url = f"https://archive.is/newest/{url}"
            response = self.session.get(archive_url, timeout=10, allow_redirects=True)
            
            if response.status_code != 200:
                # Try to create new archive
                logger.info("Creating new archive.is snapshot...")
                submit_url = "https://archive.is/submit/"
                data = {'url': url}
                response = self.session.post(submit_url, data=data, timeout=30)
                
                if response.status_code != 200:
                    return None
                
                # Wait a bit for archive to be created
                time.sleep(3)
                response = self.session.get(archive_url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                # Use same extraction as direct
                return self._extract_from_html(response.text, url)
            
        except Exception as e:
            logger.error(f"Archive.is extraction failed: {e}")
        
        return None
    
    def _extract_12ft(self, url: str) -> Optional[Dict[str, Any]]:
        """Tier 3: Extract via 12ft.io"""
        try:
            proxy_url = f"https://12ft.io/{url}"
            response = self.session.get(proxy_url, timeout=15, verify=False)
            
            if response.status_code == 200:
                return self._extract_from_html(response.text, url)
            
        except Exception as e:
            logger.error(f"12ft.io extraction failed: {e}")
        
        return None
    
    def _extract_playwright(self, url: str) -> Optional[Dict[str, Any]]:
        """Tier 4: Extract using Playwright with JavaScript disabled"""
        try:
            from playwright.sync_api import sync_playwright
            executable_path = os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH')
            
            with sync_playwright() as p:
                launch_kwargs = {'headless': True}
                if executable_path:
                    launch_kwargs['executable_path'] = executable_path
                browser = p.chromium.launch(**launch_kwargs)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    java_script_enabled=False
                )
                page = context.new_page()
                
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    html = page.content()
                    
                    return self._extract_from_html(html, url)
                
                finally:
                    browser.close()
            
        except Exception as e:
            logger.error(f"Playwright extraction failed: {e}")
        
        return None
    
    def _extract_from_html(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Common extraction logic for HTML content"""
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract title
        title = None
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content')
        if not title and soup.title:
            title = soup.title.string
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
        
        # Extract author
        author = None
        author_meta = soup.find('meta', attrs={'name': 'author'}) or \
                     soup.find('meta', property='article:author')
        if author_meta:
            author = author_meta.get('content')
        
        # Extract date
        date = None
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta:
            date = date_meta.get('content')
        
        # Extract content
        content_html = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            include_images=True,
            output_format='html',
            favor_precision=True
        )

        if not content_html:
            content_html = trafilatura.extract(html, output_format='txt')

        # Resolve relative image URLs so they match the processed image map
        if content_html:
            content_html = self._resolve_image_urls(content_html, url)

        # Extract images
        images = self._extract_images_with_context(html, url)
        
        return {
            'title': title or 'Untitled',
            'author': author,
            'date': date,
            'content': content_html or '',
            'images': images,
            'source_url': url
        }
    
    def _extract_images_with_context(self, html: str, base_url: str) -> list:
        """Extract images with their context (position in article)"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            images = []
            
            # Find article body
            article_body = soup.find('article') or soup.find('main') or soup.find('body')
            
            if article_body:
                # Find images within article
                for idx, img in enumerate(article_body.find_all('img')):
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if not src:
                        continue
                    
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        from urllib.parse import urljoin
                        src = urljoin(base_url, src)
                    
                    # Filter out small icons and tracking pixels
                    if any(x in src.lower() for x in ['icon', 'logo', 'avatar', 'pixel', 'tracker', '1x1']):
                        continue
                    
                    # Skip very small images
                    width = img.get('width')
                    height = img.get('height')
                    if width and height:
                        try:
                            if int(width) < 100 or int(height) < 100:
                                continue
                        except:
                            pass
                    
                    images.append({
                        'src': src,
                        'alt': img.get('alt', ''),
                        'position': idx  # Track position in article
                    })
            
            return images
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return []
    
    def is_feed_url(self, url: str) -> bool:
        """Return True if the URL appears to be an RSS or Atom feed."""
        try:
            response = self.session.get(url, timeout=10)
            ct = response.headers.get('content-type', '').lower()
            if any(x in ct for x in ['rss', 'atom', 'xml']):
                return True
            snippet = response.text[:1000]
            return '<rss' in snippet or '<feed' in snippet
        except Exception:
            return False

    def extract_feed(self, url: str, max_articles: int = 10) -> list:
        """
        Extract article URLs and titles from an RSS 2.0 or Atom feed.

        Returns: list of {url, title, date}
        """
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'lxml-xml')
            articles = []

            # RSS 2.0
            items = soup.find_all('item')
            if items:
                for item in items[:max_articles]:
                    link = item.find('link')
                    title = item.find('title')
                    pub_date = item.find('pubDate')
                    link_text = link.get_text(strip=True) if link else ''
                    if link_text:
                        articles.append({
                            'url': link_text,
                            'title': title.get_text(strip=True) if title else link_text,
                            'date': pub_date.get_text(strip=True) if pub_date else ''
                        })
                return articles

            # Atom
            entries = soup.find_all('entry')
            for entry in entries[:max_articles]:
                link = entry.find('link')
                title = entry.find('title')
                published = entry.find('published') or entry.find('updated')
                href = link.get('href') or (link.get_text(strip=True) if link else '')
                if href:
                    articles.append({
                        'url': href,
                        'title': title.get_text(strip=True) if title else href,
                        'date': published.get_text(strip=True) if published else ''
                    })
            return articles

        except Exception as e:
            logger.error(f"Feed extraction failed: {e}")
            return []

    def _resolve_image_urls(self, content_html: str, base_url: str) -> str:
        """Make all img src URLs in content HTML absolute so they match the image map."""
        from urllib.parse import urljoin
        soup = BeautifulSoup(content_html, 'html.parser')
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if not src:
                continue
            if src.startswith('//'):
                img['src'] = 'https:' + src
            elif src.startswith('/'):
                img['src'] = urljoin(base_url, src)
        return str(soup)

    def _is_valid_content(self, result: Optional[Dict[str, Any]]) -> bool:
        """Check if extracted content is valid (not too short)"""
        if not result:
            return False
        
        content = result.get('content', '')
        # Consider valid if content is at least 200 characters
        return len(content.strip()) > 200
