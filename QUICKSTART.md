# 🚀 Quick Start Guide

Get your Kindle Article Sender running in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.9 or higher installed
- [ ] Gmail account (or other SMTP provider)
- [ ] Kindle Send-to-Kindle email address
- [ ] Your sender email approved in Amazon Kindle settings

## Step-by-Step Setup

### 1. Install Dependencies (2 minutes)

```bash
# Run the setup script
./setup.sh
```

This will:
- Create a virtual environment
- Install all Python packages
- Install Playwright browsers
- Create `.env` from template

### 2. Configure Email & Kindle (2 minutes)

Edit the `.env` file:

```bash
nano .env
```

**For Gmail users**, you need an App Password:
1. Go to Google Account → Security → 2-Step Verification
2. At the bottom, click "App passwords"
3. Select "Mail" and "Other (Custom name)"
4. Copy the 16-character password

**Configure `.env`:**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Your app password
FROM_EMAIL=your-email@gmail.com
KINDLE_EMAIL=your-kindle@kindle.com
SECRET_KEY=any-random-string-here
```

**Find your Kindle email:**
- Go to Amazon.com → Account & Lists → Content & Devices
- Click Preferences → Personal Document Settings
- Your email looks like: `username_123@kindle.com`

**Approve your sender email:**
- Same page, scroll to "Approved Personal Document E-mail List"
- Click "Add a new approved e-mail address"
- Add the email from `FROM_EMAIL`

### 3. Test Installation (30 seconds)

```bash
source venv/bin/activate
python test_installation.py
```

All tests should pass ✓

### 4. Run the Application (30 seconds)

```bash
python app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

### 5. Use It! 🎉

1. Open browser to `http://localhost:5000`
2. Paste any article URL
3. Verify your Kindle email
4. Click "Send to Kindle"
5. Wait 30-60 seconds
6. Article appears on your Kindle!

## Test URLs

Try these free articles to test:

- **New York Times (free)**: Any article from https://www.nytimes.com/international/
- **Substack**: Any public Substack post
- **Medium**: Most Medium articles work
- **The Atlantic**: Many articles are accessible

## Troubleshooting

### "Failed to extract article"
- Try a different article first
- Some paywalls are very strong
- Check if the URL is correct

### "Failed to send email"
- Double-check SMTP credentials
- Verify app password is correct
- Make sure 2FA is enabled on Gmail

### "Article not appearing on Kindle"
- Check that sender email is approved on Amazon
- Check your Kindle email is correct
- Look in Amazon "Manage Your Content and Devices"
- It may take 1-2 minutes to appear

### Import errors
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

## Next Steps

### Access from Phone
1. Find your computer's local IP: `hostname -I`
2. On your phone, browse to: `http://YOUR-IP:5000`
3. Add to home screen for quick access

### Deploy to Server
See `DEPLOYMENT.md` for:
- Docker deployment
- Cloud hosting (Heroku, Railway, etc.)
- Systemd service setup
- Nginx reverse proxy

### Customize Styling
Edit `epub_generator.py` to change:
- Fonts
- Line spacing
- Text justification
- Image positioning

## Common Use Cases

### Daily Newsletter → Kindle
1. Copy newsletter URL
2. Paste in Kindle Sender
3. Read on your morning commute

### Long-form Articles → Kindle
Perfect for:
- Investigative journalism
- Technical blog posts
- Research papers
- Book reviews

### Substack Posts → Kindle
1. Find any Substack article
2. Send to Kindle
3. Read ad-free on e-ink

## Tips & Tricks

✨ **Bookmark the interface** on your phone for quick access

📱 **Add to home screen** on iOS/Android for app-like experience

🔖 **Browser extension idea**: Create a bookmarklet to send current page

⏰ **Batch processing**: Open multiple tabs, send several articles at once

📚 **Build your library**: Articles stay in "Manage Your Content and Devices"

## Support

- Check `README.md` for detailed documentation
- See `DEPLOYMENT.md` for production setup
- Review code comments for customization

---

**Enjoy ad-free, paywall-free reading on your Kindle! 📚**
