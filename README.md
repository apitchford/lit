# 📚 Kindle Article Sender

A self-hosted web application that converts newspaper articles and Substack posts into beautifully formatted EPUBs and sends them directly to your Kindle.

## ✨ Features

- **Multi-tier Paywall Bypass**: Automatically bypasses most paywalls using a cascading approach
  1. Direct extraction with trafilatura
  2. Archive.is fallback
  3. 12ft.io proxy
  4. Playwright with JavaScript disabled
  
- **Beautiful Formatting**: Custom CSS optimized for e-ink displays
  - Serif fonts (Georgia)
  - Proper line spacing and justification
  - Optimized for Kindle Paperwhite
  
- **Image Processing**: 
  - Downloads and embeds article images
  - Resizes to 600-800px width
  - JPEG optimization (75-85% quality)
  - Keeps total EPUB under 50MB
  
- **Direct Kindle Delivery**: Sends EPUB via email to your Send-to-Kindle address

- **Support for Multiple Sources**: Works with most news sites, blogs, and Substack posts

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip
- Gmail account (or other SMTP server)
- Kindle Send-to-Kindle email address

### Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers (for Tier 4 paywall bypass):
```bash
playwright install chromium
```

4. Create `.env` file from template:
```bash
cp .env.example .env
```

5. Configure your `.env` file:
```env
# SMTP Configuration (for Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # See setup guide below
FROM_EMAIL=your-email@gmail.com

# Kindle Configuration
KINDLE_EMAIL=your-kindle@kindle.com

# Application Configuration
SECRET_KEY=your-random-secret-key
DEBUG=False
```

### Gmail Setup

To send emails via Gmail, you need to create an **App Password**:

1. Go to your Google Account settings
2. Security → 2-Step Verification (must be enabled)
3. App passwords → Select app: "Mail" → Select device: "Other"
4. Copy the 16-character password to `SMTP_PASSWORD` in `.env`

**Important**: Your Gmail account must have 2FA enabled to use app passwords.

### Kindle Setup

1. Find your Send-to-Kindle email address:
   - Go to Amazon → Manage Your Content and Devices → Preferences
   - Look for "Send-to-Kindle Email Settings"
   - Your address looks like: `username@kindle.com`

2. Add your sender email to approved list:
   - In the same settings page, scroll to "Approved Personal Document E-mail List"
   - Add the email address you're using in `FROM_EMAIL`

### Running the Application

Start the Flask server:
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## 📖 Usage

1. Open the web interface in your browser
2. Paste the URL of any article
3. Verify your Kindle email address
4. Click "Send to Kindle"
5. Wait 30-60 seconds for processing
6. Article appears on your Kindle!

## 🎨 Customization

### Custom CSS Styles

Edit `epub_generator.py` to customize the CSS:

```python
DEFAULT_CSS = '''
body {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1em;
    line-height: 1.6;
    /* Add your customizations */
}
'''
```

### Image Settings

Adjust in `image_processor.py`:

```python
MAX_WIDTH = 800  # Maximum image width
JPEG_QUALITY = 80  # JPEG quality (0-100)
```

### Paywall Bypass Order

Modify the extraction order in `extractor.py`:

```python
def extract(self, url: str):
    # Change order or add new tiers
    result = self._extract_direct(url)
    # ...
```

## 🔧 Advanced Configuration

### Using Different SMTP Providers

For non-Gmail providers, update `.env`:

**Outlook/Hotmail:**
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

**Yahoo:**
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

**Custom SMTP:**
```env
SMTP_SERVER=mail.example.com
SMTP_PORT=587  # or 465 for SSL
```

### Production Deployment

For production use, consider:

1. **Use a production WSGI server** (Gunicorn/uWSGI):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **Set up reverse proxy** (Nginx):
```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

3. **Enable HTTPS** with Let's Encrypt

4. **Use systemd service** for auto-restart:
```ini
[Unit]
Description=Kindle Article Sender
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/kindle-article-sender
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

## 📝 How It Works

1. **URL Submission**: User submits article URL through web interface

2. **Article Extraction**: 
   - Tries direct extraction first (fast)
   - Falls back to archive.is if blocked
   - Uses 12ft.io as secondary fallback
   - Final attempt with Playwright + JS disabled

3. **Image Processing**:
   - Downloads all article images
   - Resizes to Kindle-optimal dimensions (600-800px)
   - Compresses as JPEG with 75-85% quality
   - Limits total images to prevent oversized EPUBs

4. **EPUB Generation**:
   - Creates EPUB with custom CSS
   - Embeds processed images
   - Includes metadata (title, author, date)
   - Optimized for e-ink displays

5. **Email Delivery**:
   - Attaches EPUB to email
   - Sends via SMTP to Kindle address
   - Amazon automatically converts and delivers to device

## 🐛 Troubleshooting

### "Failed to extract article"
- The paywall may be very strong
- Try accessing the URL manually first
- Some sites require login and can't be bypassed

### "Failed to send email"
- Check SMTP credentials in `.env`
- Verify 2FA and app password for Gmail
- Check that sender email is approved on Amazon

### "EPUB too large"
- Reduce image quality in `image_processor.py`
- Reduce `max_images` parameter
- Some articles have very large images

### Images not showing
- Check image URLs are accessible
- Some sites block image hotlinking
- Try opening images in browser

## 🔒 Privacy & Security

- All processing happens on your server
- No data is sent to third parties (except archive.is/12ft.io when needed)
- Article content is not stored permanently
- Temporary files are cleaned up after sending

## 📄 License

MIT License - Feel free to modify and use as needed!

## 🙏 Credits

Built with:
- [trafilatura](https://github.com/adbar/trafilatura) - Article extraction
- [ebooklib](https://github.com/aerkalov/ebooklib) - EPUB generation
- [Playwright](https://playwright.dev/) - Browser automation
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Pillow](https://python-pillow.org/) - Image processing

## 🎯 Future Enhancements

Potential improvements:
- [ ] Multiple style templates (light/dark, different fonts)
- [ ] Cover image generation with article title
- [ ] Batch processing multiple URLs
- [ ] Schedule articles for later sending
- [ ] Browser extension for one-click sending
- [ ] Support for PDF output
- [ ] Reading time estimation
- [ ] Article archiving/library

## 💡 Tips

- **Bookmark the web interface** on your phone for easy access
- **Add to Home Screen** on iOS/Android for app-like experience
- **Test with free articles** first to verify setup
- **Check Kindle's special offers** - some articles may already be available
- **Use for newsletters** - great for converting Substack to Kindle format

## 🤝 Contributing

Issues and pull requests welcome! This is a personal project but happy to accept improvements.

---

**Note**: This tool is for personal use only. Please respect copyright and publisher's terms of service. Support journalism by subscribing to publications you read regularly.
