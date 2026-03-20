"""
EPUB generation with custom CSS styling for Kindle
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

from bs4 import BeautifulSoup
from ebooklib import epub

logger = logging.getLogger(__name__)


class EPUBGenerator:
    """Generate beautifully formatted EPUB files for Kindle"""

    DEFAULT_CSS = '''
@namespace epub "http://www.idpf.org/2007/ops";

body {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1em;
    line-height: 1.6;
    margin: 0;
    padding: 1em;
    text-align: justify;
    color: #000;
}

h1 {
    font-size: 2em;
    font-weight: bold;
    margin: 1em 0 0.5em 0;
    text-align: left;
    line-height: 1.2;
}

h2 {
    font-size: 1.5em;
    font-weight: bold;
    margin: 1em 0 0.5em 0;
    text-align: left;
    line-height: 1.3;
}

h3 {
    font-size: 1.2em;
    font-weight: bold;
    margin: 0.8em 0 0.4em 0;
}

p {
    margin: 0.5em 0;
    text-indent: 1.5em;
}

p:first-of-type,
h1 + p,
h2 + p,
h3 + p {
    text-indent: 0;
}

blockquote {
    margin: 1em 2em;
    font-style: italic;
    border-left: 3px solid #ccc;
    padding-left: 1em;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

.article-meta {
    font-size: 0.9em;
    color: #666;
    margin: 1em 0 2em 0;
    text-align: left;
}

.article-meta p {
    text-indent: 0;
    margin: 0.2em 0;
}

.author { font-weight: bold; }
.date   { font-style: italic; }

a {
    color: #000;
    text-decoration: underline;
}

ul, ol {
    margin: 0.5em 0;
    padding-left: 2em;
}

li { margin: 0.3em 0; }

hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 2em 0;
}

/* ── Cover page ── */
.cover-page {
    text-align: center;
}
.cover-content {
    margin: 5em auto;
    max-width: 90%;
}
.cover-label {
    font-size: 0.85em;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 1.5em;
}
.cover-title {
    font-size: 2.2em;
    font-weight: bold;
    line-height: 1.2;
    margin: 0 0 0.4em 0;
    text-indent: 0;
}
.cover-date {
    font-size: 1.05em;
    font-style: italic;
    color: #555;
    margin: 0.4em 0;
    text-indent: 0;
}
.cover-rule {
    border: none;
    border-top: 2px solid #333;
    width: 50%;
    margin: 1.5em auto;
}
.cover-stats {
    font-size: 0.9em;
    color: #666;
    text-indent: 0;
}

/* ── Table of contents page ── */
.toc-page h1 {
    font-size: 1.6em;
    margin-bottom: 0.3em;
}
.toc-date {
    font-size: 0.9em;
    color: #666;
    font-style: italic;
    margin-bottom: 2em;
    text-indent: 0;
}
.toc-list {
    list-style: none;
    padding: 0;
    margin: 0;
}
.toc-list li {
    border-bottom: 1px solid #ddd;
    padding: 0.9em 0;
}
.toc-list li a {
    text-decoration: none;
    color: #000;
    font-size: 1em;
    font-weight: bold;
}
.toc-reading-time {
    font-size: 0.82em;
    color: #888;
    font-style: italic;
    display: block;
    margin-top: 0.15em;
}
.toc-source {
    font-size: 0.8em;
    color: #aaa;
    display: block;
    margin-top: 0.1em;
}

/* ── Article number label ── */
.article-num {
    font-size: 0.8em;
    color: #aaa;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    text-indent: 0;
    margin-bottom: 0.3em;
}
'''

    def __init__(self, style_name: str = 'default'):
        self.style = self.DEFAULT_CSS

    # ── Public API ────────────────────────────────────────────────────

    def generate(
        self,
        article: Dict[str, Any],
        images: List[Tuple[bytes, str, str]],
        output_path: Path
    ) -> bool:
        """Generate EPUB for a single article."""
        try:
            book = epub.EpubBook()
            title = article.get('title', 'Untitled Article')
            book.set_identifier(f"article-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            book.set_title(title)
            book.set_language('en')

            author = article.get('author')
            if author:
                book.add_author(author)

            nav_css = self._make_css_item(book)

            image_items = self._add_images(book, images)
            content_html = self._format_content(article, image_items)

            chapter = epub.EpubHtml(title=title, file_name='chapter_1.xhtml', lang='en')
            chapter.set_content(content_html.encode('utf-8'))
            chapter.add_item(nav_css)
            book.add_item(chapter)

            book.toc = (chapter,)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = ['nav', chapter]

            epub.write_epub(output_path, book)
            logger.info(f"EPUB created successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate EPUB: {e}")
            return False

    def generate_compilation(
        self,
        articles_with_images: List[Tuple[Dict[str, Any], List[Tuple[bytes, str, str]]]],
        title: str,
        output_path: Path
    ) -> bool:
        """
        Generate a compiled EPUB from multiple articles with cover + table of contents.
        """
        try:
            book = epub.EpubBook()
            date_str = datetime.now().strftime('%B %d, %Y')
            book.set_identifier(f"compilation-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            book.set_title(title)
            book.set_language('en')

            nav_css = self._make_css_item(book)

            # Build article chapters
            chapters = []
            reading_times = []

            for idx, (article, images) in enumerate(articles_with_images):
                image_items = self._add_images(book, images, prefix=f"a{idx + 1}")

                article_html = self._format_content(article, image_items)
                num_label = f'<p class="article-num">Article {idx + 1} of {len(articles_with_images)}</p>'
                article_html = article_html.replace('<h1>', num_label + '\n    <h1>', 1)

                chapter = epub.EpubHtml(
                    title=article.get('title', f'Article {idx + 1}'),
                    file_name=f'article_{idx + 1}.xhtml',
                    lang='en'
                )
                chapter.set_content(article_html.encode('utf-8'))
                chapter.add_item(nav_css)
                book.add_item(chapter)
                chapters.append(chapter)

                minutes = self._reading_time_minutes(article.get('content', ''))
                reading_times.append(minutes)

            total_minutes = sum(reading_times)

            # Cover page
            cover = self._make_cover_page(title, date_str, len(chapters), total_minutes, nav_css)
            book.add_item(cover)

            # Table of contents page
            toc_page = self._make_toc_page(
                title, date_str, chapters, articles_with_images, reading_times, nav_css
            )
            book.add_item(toc_page)

            book.toc = tuple(chapters)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = ['nav', cover, toc_page] + chapters

            epub.write_epub(output_path, book)
            logger.info(f"Compilation EPUB created: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate compilation EPUB: {e}")
            return False

    # ── Private helpers ───────────────────────────────────────────────

    def _make_css_item(self, book: epub.EpubBook) -> epub.EpubItem:
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=self.style
        )
        book.add_item(nav_css)
        return nav_css

    def _add_images(
        self,
        book: epub.EpubBook,
        images: List[Tuple[bytes, str, str]],
        prefix: str = ''
    ) -> Dict[str, str]:
        """Add images to the book and return a url→epub_path map."""
        image_items = {}
        for i, (img_bytes, mime_type, url) in enumerate(images):
            ext = 'jpg' if 'jpeg' in mime_type else 'png'
            uid = f"{prefix}_img_{i + 1}" if prefix else f"image_{i + 1}"
            filename = f"images/{uid}.{ext}"
            img_item = epub.EpubItem(
                uid=uid, file_name=filename, media_type=mime_type, content=img_bytes
            )
            book.add_item(img_item)
            image_items[url] = filename
        return image_items

    def _make_cover_page(
        self,
        title: str,
        date_str: str,
        article_count: int,
        total_minutes: int,
        nav_css: epub.EpubItem
    ) -> epub.EpubHtml:
        reading_str = self._format_reading_time(total_minutes)
        art_word = 'article' if article_count == 1 else 'articles'
        html = f'''<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <link href="style/nav.css" rel="stylesheet" type="text/css"/>
</head>
<body class="cover-page">
    <div class="cover-content">
        <p class="cover-label">Daily Digest</p>
        <h1 class="cover-title">{title}</h1>
        <p class="cover-date">{date_str}</p>
        <hr class="cover-rule"/>
        <p class="cover-stats">{article_count} {art_word} &middot; {reading_str} reading time</p>
    </div>
</body>
</html>'''
        item = epub.EpubHtml(title='Cover', file_name='cover.xhtml', lang='en')
        item.set_content(html.encode('utf-8'))
        item.add_item(nav_css)
        return item

    def _make_toc_page(
        self,
        title: str,
        date_str: str,
        chapters: List[epub.EpubHtml],
        articles_with_images: List,
        reading_times: List[int],
        nav_css: epub.EpubItem
    ) -> epub.EpubHtml:
        items_html = '\n'.join(
            f'''        <li>
            <a href="{ch.file_name}">{ch.title}</a>
            <span class="toc-reading-time">{self._format_reading_time(reading_times[i])}</span>
            <span class="toc-source">{articles_with_images[i][0].get("source_url", "")}</span>
        </li>'''
            for i, ch in enumerate(chapters)
        )
        html = f'''<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Contents</title>
    <link href="style/nav.css" rel="stylesheet" type="text/css"/>
</head>
<body class="toc-page">
    <h1>Contents</h1>
    <p class="toc-date">{date_str}</p>
    <hr/>
    <ul class="toc-list">
{items_html}
    </ul>
</body>
</html>'''
        item = epub.EpubHtml(title='Contents', file_name='toc.xhtml', lang='en')
        item.set_content(html.encode('utf-8'))
        item.add_item(nav_css)
        return item

    def _reading_time_minutes(self, html_or_text: str) -> int:
        soup = BeautifulSoup(html_or_text, 'html.parser')
        words = len(soup.get_text().split())
        return max(1, round(words / 230))

    def _format_reading_time(self, minutes: int) -> str:
        if minutes < 60:
            return f"{minutes} min"
        hours, mins = divmod(minutes, 60)
        return f"{hours}h {mins}m" if mins else f"{hours}h"

    def _clean_html(self, html: str) -> str:
        """Remove empty tags and common trafilatura artifacts."""
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all(['p', 'div', 'figure', 'section']):
            if not tag.get_text(strip=True) and not tag.find('img'):
                tag.decompose()
        return str(soup)

    def _format_content(self, article: Dict[str, Any], image_map: Dict[str, str]) -> str:
        """Format article content as HTML with images in their original positions."""
        title = article.get('title', 'Untitled Article')
        author = article.get('author')
        date = article.get('date')
        content = article.get('content', '')
        raw_html = article.get('raw_html', '')
        source_url = article.get('source_url', '')

        logger.info(f"Content length: {len(content)}")

        if not content and raw_html:
            content = raw_html
            logger.info("Using raw_html instead of content")

        # Build metadata section
        meta_parts = []
        if author:
            meta_parts.append(f'<p class="author">By {author}</p>')
        if date:
            meta_parts.append(f'<p class="date">{date}</p>')
        if source_url:
            meta_parts.append(f'<p class="source">Source: <a href="{source_url}">{source_url}</a></p>')
        meta_html = f'<div class="article-meta">{"".join(meta_parts)}</div>' if meta_parts else ''

        # Convert plain text to paragraphs if needed
        if content and '<p>' not in content and '<h' not in content:
            paragraphs = content.split('\n\n')
            content_html = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
        elif content:
            content_html = content
        else:
            logger.error("Content is empty!")
            content_html = '<p>Content could not be extracted.</p>'

        # Clean up trafilatura artifacts (empty tags etc.)
        content_html = self._clean_html(content_html)

        # Replace image srcs in-place to preserve original article ordering
        if image_map:
            soup = BeautifulSoup(content_html, 'html.parser')
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if src in image_map:
                    img['src'] = image_map[src]
                    img['alt'] = img.get('alt', 'Article image')
                else:
                    img.decompose()
            content_html = str(soup)

        return f'''<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <link href="style/nav.css" rel="stylesheet" type="text/css"/>
</head>
<body>
    <h1>{title}</h1>
    {meta_html}
    <hr/>
    {content_html}
</body>
</html>'''
