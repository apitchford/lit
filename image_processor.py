"""
Image processing for Kindle optimization
"""
import io
import logging
import time
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Download and optimize images for Kindle"""

    # Kindle Paperwhite optimal settings
    MAX_WIDTH = 800
    MAX_HEIGHT = 1200
    JPEG_QUALITY = 80
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB per image

    def __init__(self, target_width: int = MAX_WIDTH, jpeg_quality: int = JPEG_QUALITY):
        self.target_width = target_width
        self.jpeg_quality = jpeg_quality
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def download_and_process(self, url: str) -> Optional[Tuple[bytes, str]]:
        """
        Download and optimize image for Kindle.
        Retries up to 2 times with a Referer header to bypass CDN restrictions.

        Returns: (image_bytes, mime_type) or None
        """
        parsed = urlparse(url)
        referer = f"{parsed.scheme}://{parsed.netloc}/"

        for attempt in range(3):
            try:
                response = self.session.get(
                    url,
                    timeout=10,
                    stream=True,
                    headers={'Referer': referer}
                )
                response.raise_for_status()

                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type:
                    logger.warning(f"Not an image: {url}")
                    return None

                # Load image
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))

                # Convert to RGB if necessary (handles PNG, RGBA, etc.)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                # Resize if needed
                if img.width > self.target_width:
                    ratio = self.target_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((self.target_width, new_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized image to {self.target_width}x{new_height}")

                # Optimize and save to bytes
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=self.jpeg_quality, optimize=True)
                img_bytes = output.getvalue()

                # Check file size
                if len(img_bytes) > self.MAX_FILE_SIZE:
                    logger.warning(f"Image too large ({len(img_bytes)} bytes), reducing quality")
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=self.jpeg_quality - 20, optimize=True)
                    img_bytes = output.getvalue()

                logger.info(f"Processed image: {len(img_bytes)} bytes")
                return (img_bytes, 'image/jpeg')

            except Exception as e:
                if attempt < 2:
                    logger.warning(f"Image attempt {attempt + 1} failed for {url}: {e}, retrying...")
                    time.sleep(1)
                else:
                    logger.error(f"Failed to process image {url} after 3 attempts: {e}")
                    return None

    def batch_process(self, image_urls: list, max_images: int = 20) -> list:
        """
        Process multiple images

        Returns: list of (image_bytes, mime_type, original_url)
        """
        results = []

        for i, url in enumerate(image_urls[:max_images]):
            logger.info(f"Processing image {i+1}/{min(len(image_urls), max_images)}: {url}")
            result = self.download_and_process(url)

            if result:
                img_bytes, mime_type = result
                results.append((img_bytes, mime_type, url))

        return results
