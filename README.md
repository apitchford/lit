# Lit

Turn the web into your personal reading list. Paste any article URL and Lit sends it straight to your Kindle as a clean, well-formatted EPUB — images included, in their original positions. Compile multiple articles into a single digest with a table of contents, like building your own morning newspaper.

Built by [Art Pitchford](https://github.com/apitchford).

---

## What it does

- Sends any article to your Kindle in one click
- Compiles multiple articles into a single digest with a contents page
- Loads articles from RSS and Substack feeds
- Bypasses most paywalls automatically
- Preserves images in their original positions
- Works as a download too — grab the EPUB directly if you prefer

---

## Getting started

**You'll need:**
- Python 3.9+
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) set up
- Your Kindle's Send-to-Kindle email address (find it at Amazon → Manage Your Content and Devices → Preferences)

**Setup:**

```bash
git clone https://github.com/apitchford/lit.git
cd lit
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Open `.env` and fill in your details:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=you@gmail.com
KINDLE_EMAIL=your-kindle@kindle.com
SECRET_KEY=any-random-string
```

Then add your sending address to the approved senders list on Amazon (same Preferences page where you found your Kindle email).

**Run:**

```bash
./run.sh
```

Open [http://localhost:5000](http://localhost:5000).

---

## How it works

Paste a URL. Lit extracts the article content, processes and embeds the images, generates an EPUB formatted for e-ink, and sends it to your Kindle via email. Amazon handles the rest.

For paywalled articles, it tries a few approaches in sequence — direct extraction, archive.is, 12ft.io, and finally a headless browser — stopping as soon as one works.

For compilations, add as many URLs as you like. A title field and drag-to-reorder appear as you build your list. The resulting EPUB has a cover page and linked table of contents.

---

## Self-hosting

Lit runs fine on any small server or home machine. For a more permanent setup:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

A `Dockerfile`, `docker-compose.yml`, and `kindle-sender.service` systemd unit are included if you want to containerise or run it as a background service.

---

MIT License
