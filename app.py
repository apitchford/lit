"""
Flask web application for Kindle Article Sender
"""
import io
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, Response, send_file, stream_with_context
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from extractor import ArticleExtractor
from image_processor import ImageProcessor
from epub_generator import EPUBGenerator
from mailer import KindleMailer

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

extractor = ArticleExtractor()
image_processor = ImageProcessor()
epub_generator = EPUBGenerator()

mailer = KindleMailer(
    smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    smtp_port=int(os.getenv('SMTP_PORT', 587)),
    username=os.getenv('SMTP_USERNAME', ''),
    password=os.getenv('SMTP_PASSWORD', ''),
    from_email=os.getenv('FROM_EMAIL', '')
)

KINDLE_EMAIL = os.getenv('KINDLE_EMAIL', '')


# ── Helpers ───────────────────────────────────────────────────────────

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _safe_filename(title: str) -> str:
    return "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]


def _extract_snippet(content: str, length: int = 220) -> str:
    """Return plain-text snippet from HTML content."""
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text(separator=' ').strip()
    text = ' '.join(text.split())
    return text[:length] + '…' if len(text) > length else text


def _reading_time_str(content: str) -> str:
    soup = BeautifulSoup(content, 'html.parser')
    words = len(soup.get_text().split())
    minutes = max(1, round(words / 230))
    return f"{minutes} min read"


# ── Routes ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', kindle_email=KINDLE_EMAIL)


@app.route('/process', methods=['POST'])
def process_article():
    """Extract a single article and send to Kindle."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        custom_kindle_email = data.get('kindle_email', KINDLE_EMAIL).strip()

        if not url:
            return jsonify({'error': 'URL is required'}), 400
        if not custom_kindle_email:
            return jsonify({'error': 'Kindle email is required'}), 400

        logger.info(f"Processing URL: {url}")

        article = extractor.extract(url)
        if not article:
            return jsonify({'error': 'Failed to extract article. The paywall may be too strong.'}), 400

        images = []
        if article.get('images'):
            image_urls = [img['src'] for img in article['images']]
            images = image_processor.batch_process(image_urls, max_images=20)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        epub_filename = f"{_safe_filename(article['title'])}_{timestamp}.epub"

        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = Path(tmpdir) / epub_filename
            if not epub_generator.generate(article, images, epub_path):
                return jsonify({'error': 'Failed to generate EPUB'}), 500

            file_size_mb = epub_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 50:
                return jsonify({'error': f'EPUB too large ({file_size_mb:.2f}MB).'}), 400

            if not mailer.send_to_kindle(custom_kindle_email, epub_path, article['title']):
                return jsonify({'error': 'Failed to send email to Kindle'}), 500

        return jsonify({
            'success': True,
            'title': article['title'],
            'author': article.get('author'),
            'images_count': len(images),
            'file_size_mb': round(file_size_mb, 2),
            'kindle_email': custom_kindle_email
        })

    except Exception as e:
        logger.error(f"Error processing article: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/preview', methods=['POST'])
def preview_article():
    """Extract title, snippet, and reading time for a URL without sending."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        article = extractor.extract(url)
        if not article:
            return jsonify({'error': 'Could not extract article'}), 400

        content = article.get('content', '')
        return jsonify({
            'title': article['title'],
            'author': article.get('author', ''),
            'snippet': _extract_snippet(content),
            'reading_time': _reading_time_str(content),
        })

    except Exception as e:
        logger.error(f"Preview error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/fetch-feed', methods=['POST'])
def fetch_feed():
    """Fetch article list from an RSS or Atom feed URL."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'error': 'Feed URL is required'}), 400

        if not extractor.is_feed_url(url):
            return jsonify({'error': 'URL does not appear to be an RSS or Atom feed'}), 400

        articles = extractor.extract_feed(url, max_articles=10)
        if not articles:
            return jsonify({'error': 'No articles found in feed'}), 400

        return jsonify({'articles': articles})

    except Exception as e:
        logger.error(f"Feed fetch error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/compile', methods=['POST'])
def compile_articles():
    """
    Extract multiple articles and stream progress via SSE,
    then send the compiled EPUB to Kindle.
    """
    data = request.get_json()
    urls = [u.strip() for u in data.get('urls', []) if u.strip()]
    title = data.get('title', '').strip() or f"Daily Digest – {datetime.now().strftime('%B %d, %Y')}"
    custom_kindle_email = data.get('kindle_email', KINDLE_EMAIL).strip()

    if not urls:
        return jsonify({'error': 'At least one URL is required'}), 400
    if len(urls) > 20:
        return jsonify({'error': 'Maximum 20 URLs per compilation'}), 400
    if not custom_kindle_email:
        return jsonify({'error': 'Kindle email is required'}), 400

    def generate():
        tmpdir = tempfile.mkdtemp()
        try:
            articles_with_images = []
            failed_urls = []

            for i, url in enumerate(urls):
                yield _sse({'type': 'progress', 'step': 'extracting',
                            'index': i, 'total': len(urls), 'url': url})
                try:
                    article = extractor.extract(url)
                    if not article:
                        failed_urls.append({'url': url, 'reason': 'Could not extract content'})
                        yield _sse({'type': 'progress', 'step': 'failed',
                                    'index': i, 'url': url, 'reason': 'Could not extract content'})
                        continue

                    yield _sse({'type': 'progress', 'step': 'images',
                                'index': i, 'title': article['title']})

                    images = []
                    if article.get('images'):
                        image_urls = [img['src'] for img in article['images']]
                        images = image_processor.batch_process(image_urls, max_images=10)

                    articles_with_images.append((article, images))
                    yield _sse({'type': 'progress', 'step': 'done',
                                'index': i, 'url': url, 'title': article['title']})

                except Exception as e:
                    logger.warning(f"Failed to extract {url}: {e}")
                    failed_urls.append({'url': url, 'reason': str(e)})
                    yield _sse({'type': 'progress', 'step': 'failed',
                                'index': i, 'url': url, 'reason': str(e)})

            if not articles_with_images:
                yield _sse({'type': 'error', 'message': 'Failed to extract any articles.'})
                return

            yield _sse({'type': 'progress', 'step': 'generating', 'message': 'Generating EPUB…'})

            epub_filename = f"{_safe_filename(title)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.epub"
            epub_path = Path(tmpdir) / epub_filename

            if not epub_generator.generate_compilation(articles_with_images, title, epub_path):
                yield _sse({'type': 'error', 'message': 'Failed to generate EPUB'})
                return

            file_size_mb = epub_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 50:
                yield _sse({'type': 'error',
                            'message': f'EPUB too large ({file_size_mb:.2f}MB). Try fewer articles.'})
                return

            yield _sse({'type': 'progress', 'step': 'sending', 'message': 'Sending to Kindle…'})

            if not mailer.send_to_kindle(custom_kindle_email, epub_path, title):
                yield _sse({'type': 'error', 'message': 'Failed to send email to Kindle'})
                return

            yield _sse({
                'type': 'complete',
                'title': title,
                'articles_compiled': len(articles_with_images),
                'articles_failed': len(failed_urls),
                'failed_urls': failed_urls,
                'file_size_mb': round(file_size_mb, 2),
                'kindle_email': custom_kindle_email
            })

        except Exception as e:
            logger.error(f"Streaming compile error: {e}", exc_info=True)
            yield _sse({'type': 'error', 'message': str(e)})
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/download', methods=['POST'])
def download_epub():
    """
    Generate and download an EPUB without sending to Kindle.
    Accepts {urls: [...], title: ''} — single article or compilation.
    """
    try:
        data = request.get_json()
        urls = [u.strip() for u in data.get('urls', []) if u.strip()]
        title = data.get('title', '').strip()

        if not urls:
            return jsonify({'error': 'At least one URL is required'}), 400
        if len(urls) > 20:
            return jsonify({'error': 'Maximum 20 URLs'}), 400

        tmpdir = tempfile.mkdtemp()
        try:
            if len(urls) == 1:
                # Single article
                article = extractor.extract(urls[0])
                if not article:
                    return jsonify({'error': 'Could not extract article'}), 400
                if not title:
                    title = article['title']
                images = []
                if article.get('images'):
                    images = image_processor.batch_process(
                        [img['src'] for img in article['images']], max_images=20
                    )
                epub_filename = f"{_safe_filename(title)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.epub"
                epub_path = Path(tmpdir) / epub_filename
                if not epub_generator.generate(article, images, epub_path):
                    return jsonify({'error': 'Failed to generate EPUB'}), 500
            else:
                # Compilation
                if not title:
                    title = f"Daily Digest – {datetime.now().strftime('%B %d, %Y')}"
                articles_with_images = []
                for url in urls:
                    article = extractor.extract(url)
                    if not article:
                        continue
                    images = []
                    if article.get('images'):
                        images = image_processor.batch_process(
                            [img['src'] for img in article['images']], max_images=10
                        )
                    articles_with_images.append((article, images))
                if not articles_with_images:
                    return jsonify({'error': 'Could not extract any articles'}), 400
                epub_filename = f"{_safe_filename(title)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.epub"
                epub_path = Path(tmpdir) / epub_filename
                if not epub_generator.generate_compilation(articles_with_images, title, epub_path):
                    return jsonify({'error': 'Failed to generate EPUB'}), 500

            with open(epub_path, 'rb') as f:
                epub_bytes = f.read()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        return send_file(
            io.BytesIO(epub_bytes),
            mimetype='application/epub+zip',
            as_attachment=True,
            download_name=epub_filename
        )

    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    if not os.getenv('SMTP_USERNAME') or not os.getenv('SMTP_PASSWORD'):
        logger.warning("SMTP credentials not configured.")
    if not KINDLE_EMAIL:
        logger.warning("Default Kindle email not configured.")

    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
