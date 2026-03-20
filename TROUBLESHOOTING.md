# Troubleshooting Guide

Common issues and their solutions.

## Installation Issues

### "Python version too old"

**Error**: `Python 3.9+ required. Found: 3.7`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11

# macOS
brew install python@3.11

# Verify
python3.11 --version
```

### "pip install failed"

**Error**: Package installation errors

**Solution**:
```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# If specific package fails, install individually
pip install flask trafilatura ebooklib Pillow
```

### "playwright install failed"

**Error**: Browser download failed

**Solution**:
```bash
# Install system dependencies first (Ubuntu)
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1

# Then install browsers
playwright install chromium

# Alternative: Skip Playwright (Tier 4 won't work)
# Comment out playwright in requirements.txt
```

## Configuration Issues

### "SMTP authentication failed"

**Error**: `SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')`

**Solutions**:

1. **Using Gmail**:
   - Enable 2FA on your Google account
   - Generate App Password (not your regular password)
   - Use the 16-character app password in `.env`

2. **Check credentials**:
   ```bash
   # Test SMTP connection
   python3 << EOF
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   print("Success!")
   server.quit()
   EOF
   ```

3. **Gmail security**:
   - Check https://myaccount.google.com/lesssecureapps
   - Disable "Less secure app access" (use app passwords instead)

### "Kindle email not configured"

**Error**: `Kindle email is required`

**Solution**:
1. Find your Kindle email:
   - Go to amazon.com → Account → Content & Devices
   - Click Preferences tab
   - Look for "Send-to-Kindle Email Settings"
   - Your email: `username_123@kindle.com`

2. Update `.env`:
   ```env
   KINDLE_EMAIL=username_123@kindle.com
   ```

### "Sender email not approved"

**Error**: Article sent but not appearing on Kindle

**Solution**:
1. Go to Amazon → Content & Devices → Preferences
2. Scroll to "Approved Personal Document E-mail List"
3. Add your `FROM_EMAIL` to approved list
4. Wait 5 minutes for Amazon to update
5. Try sending again

## Extraction Issues

### "Failed to extract article"

**Common causes**:

1. **Very strong paywall**:
   - Some sites can't be bypassed (e.g., WSJ, FT with strict paywalls)
   - Try accessing article in incognito mode first
   - If you can't read it manually, the tool can't either

2. **URL issues**:
   ```bash
   # Wrong: relative URL
   example.com/article
   
   # Correct: full URL with https://
   https://www.example.com/article
   ```

3. **Site blocking automation**:
   - Some sites detect and block automated tools
   - Try a different tier manually:
   ```python
   # In Python shell
   from extractor import ArticleExtractor
   ext = ArticleExtractor()
   result = ext._extract_12ft("https://example.com/article")
   ```

### "Content too short"

**Error**: Extracted content less than 200 characters

**Solutions**:
- Article might be behind a paywall the tool can't bypass
- Page might be a landing page, not the actual article
- Try the direct article URL (not the homepage)

### "Images not extracted"

**Possible causes**:
- Images loaded via JavaScript (Playwright tier should help)
- Images are SVG or other unsupported formats
- Images behind authentication

**Solution**:
```python
# Check what was extracted
from extractor import ArticleExtractor
ext = ArticleExtractor()
article = ext.extract("URL")
print(article.get('images', []))
```

## Processing Issues

### "Image download failed"

**Error**: Failed to process images

**Solutions**:

1. **Network timeout**:
   ```python
   # In image_processor.py, increase timeout
   response = self.session.get(url, timeout=30)  # was 10
   ```

2. **SSL certificate errors**:
   ```python
   # Add to session
   self.session.verify = False  # Not recommended for production
   ```

3. **Skip problematic images**:
   - The tool continues even if some images fail
   - Check logs to see which images failed

### "EPUB generation failed"

**Error**: Failed to generate EPUB

**Solutions**:

1. **Check content**:
   ```python
   # Verify article data
   print(article.get('title'))
   print(len(article.get('content', '')))
   ```

2. **Check images**:
   ```python
   # Verify processed images
   print(f"Processed {len(images)} images")
   for img_bytes, mime, url in images:
       print(f"{len(img_bytes)} bytes - {url}")
   ```

3. **Missing dependencies**:
   ```bash
   pip install --upgrade ebooklib lxml
   ```

### "EPUB too large"

**Error**: `EPUB too large (55MB). Amazon limit is 50MB.`

**Solutions**:

1. **Reduce image quality**:
   ```python
   # In image_processor.py
   JPEG_QUALITY = 60  # was 80
   ```

2. **Reduce image count**:
   ```python
   # In app.py
   images = image_processor.batch_process(image_urls, max_images=10)  # was 20
   ```

3. **Reduce image size**:
   ```python
   # In image_processor.py
   MAX_WIDTH = 600  # was 800
   ```

## Email Issues

### "Failed to send email"

**Common causes**:

1. **SMTP connection timeout**:
   ```python
   # Check firewall
   sudo ufw allow out 587/tcp
   
   # Test connection
   telnet smtp.gmail.com 587
   ```

2. **Wrong SMTP settings**:
   ```env
   # Gmail
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   
   # Outlook
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587
   
   # Yahoo
   SMTP_SERVER=smtp.mail.yahoo.com
   SMTP_PORT=587
   ```

3. **Attachment too large**:
   - Amazon limit: 50MB
   - Check file size before sending

### "Email sent but not appearing on Kindle"

**Checklist**:

1. ✓ Sender email approved on Amazon?
2. ✓ Correct Kindle email address?
3. ✓ Wait 2-5 minutes for delivery
4. ✓ Check Amazon "Manage Your Content and Devices"
5. ✓ Check Kindle's WiFi connection
6. ✓ Sync Kindle manually (Settings → Sync)

## Runtime Issues

### "Port 5000 already in use"

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
python app.py  # Edit app.py to change port
# Change: app.run(port=5001)
```

### "Permission denied"

**Error**: Permission errors when running

**Solution**:
```bash
# Fix file permissions
chmod +x setup.sh test_installation.py

# Fix ownership (for systemd)
sudo chown -R www-data:www-data /opt/kindle-article-sender
```

### "Module not found"

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
# Activate virtual environment first
source venv/bin/activate

# Then run
python app.py

# Verify you're in venv
which python  # Should show venv/bin/python
```

## Performance Issues

### "Processing taking too long"

**Normal times**:
- Fast articles: 10-20 seconds
- With paywall bypass: 30-60 seconds
- With Playwright: 45-90 seconds

**If slower**:

1. **Check network speed**:
   ```bash
   ping google.com
   speedtest-cli
   ```

2. **Check system resources**:
   ```bash
   top
   htop
   ```

3. **Disable unnecessary tiers**:
   ```python
   # In extractor.py, comment out slow tiers
   # Skip archive.is if slow:
   # result = self._extract_archive_is(url)
   ```

### "High memory usage"

**Solutions**:

1. **Limit image processing**:
   ```python
   # Process fewer images
   max_images=10  # instead of 20
   ```

2. **Process images sequentially** (already implemented)

3. **Add memory limits** (Docker):
   ```yaml
   # docker-compose.yml
   services:
     kindle-sender:
       mem_limit: 512m
   ```

## Browser/UI Issues

### "Form not submitting"

**Solutions**:
- Check browser console for JavaScript errors (F12)
- Try different browser
- Disable browser extensions
- Clear browser cache

### "Progress stuck"

**Solutions**:
- Check backend logs for errors
- Refresh page and try again
- Check network tab in browser dev tools

## Debugging Tips

### Enable debug mode

```python
# In app.py
app.run(debug=True)
```

Or in `.env`:
```env
DEBUG=True
```

### Check logs

```bash
# View Flask logs
python app.py

# View systemd logs
sudo journalctl -u kindle-sender -f

# View Docker logs
docker-compose logs -f
```

### Test components individually

```python
# Test extractor
from extractor import ArticleExtractor
ext = ArticleExtractor()
article = ext.extract("https://example.com/article")
print(article)

# Test image processor
from image_processor import ImageProcessor
proc = ImageProcessor()
images = proc.batch_process(["https://example.com/image.jpg"])
print(images)

# Test EPUB generator
from epub_generator import EPUBGenerator
from pathlib import Path
gen = EPUBGenerator()
success = gen.generate(article, images, Path("test.epub"))
print(success)
```

### Verbose error output

```python
# Add to app.py
import traceback

try:
    # code
except Exception as e:
    logger.error(f"Error: {e}")
    logger.error(traceback.format_exc())
```

## Getting Help

Still stuck? Here's what to include when asking for help:

1. **Error message** (full text)
2. **Logs** (last 50 lines)
3. **Configuration** (sanitized `.env`)
4. **System info**:
   ```bash
   python --version
   pip list
   uname -a
   ```
5. **Steps to reproduce**
6. **What you've tried**

## Common Workflows

### "I want to test if it's working"

```bash
# 1. Run test script
python test_installation.py

# 2. Try with a known-good URL
# Test URL: https://www.nytimes.com/international/
# (Most articles here are free)

# 3. Check each component
python -c "from extractor import ArticleExtractor; print('OK')"
python -c "from image_processor import ImageProcessor; print('OK')"
python -c "from epub_generator import EPUBGenerator; print('OK')"
python -c "from mailer import KindleMailer; print('OK')"
```

### "I want to see what's happening"

```bash
# Enable verbose logging
# In app.py, change logging level:
logging.basicConfig(level=logging.DEBUG)

# Then run and watch output
python app.py
```

### "I want to bypass a specific paywall"

```python
# Test different tiers manually
from extractor import ArticleExtractor

ext = ArticleExtractor()
url = "https://paywalled-site.com/article"

# Try each tier
print("Tier 1:", ext._extract_direct(url))
print("Tier 2:", ext._extract_archive_is(url))
print("Tier 3:", ext._extract_12ft(url))
print("Tier 4:", ext._extract_playwright(url))
```

---

If you can't find your issue here, check the main README.md or open an issue on the project repository.
