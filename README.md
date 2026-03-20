# Lit / Art Domain

This repository currently serves Lit: a Flask app that turns article URLs into Kindle-friendly EPUBs, with preview, feed loading, download, and multi-article compilation support.

It now also exports a Nix flake and NixOS module under the service name `art-domain`, so the same repo can be hosted on `art.bepis.lol` through `nix-dotfiles` while the repo itself remains named `lit`.

Built by [Art Pitchford](https://github.com/apitchford).

---

## What it does

- Sends any article to your Kindle in one click
- Compiles multiple articles into a single digest with a contents page
- Loads articles from RSS and Substack feeds
- Shows inline article previews before sending
- Lets you download the generated EPUB without emailing it
- Stores the chosen Kindle email and theme in browser local storage
- Tries several extraction strategies, including a Playwright fallback for harder sites
- Preserves images in their original positions

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

Open `.env` and fill in your SMTP details:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=you@gmail.com
SECRET_KEY=any-random-string
```

`KINDLE_EMAIL` is optional: the UI lets the user enter a Kindle email directly and stores it in browser local storage after a successful send.

Then add your sending address to the approved senders list on Amazon.

**Run:**

```bash
./run.sh
```

Open [http://localhost:5000](http://localhost:5000).

---

## How it works

Paste one or more URLs. Lit can preview each article, extract the content, process and embed images, generate an EPUB formatted for e-ink, and either send it to Kindle or download it directly.

For harder sites, extraction falls back through direct parsing, archive.is, 12ft.io, and finally Playwright with JavaScript disabled.

For compilations, add as many as 20 URLs, drag to reorder them, optionally pull items from an RSS/Atom feed, and generate a digest with a cover page and linked table of contents.

## Current HTTP Surface

- `GET /` — main UI
- `POST /preview` — title/snippet/reading-time preview
- `POST /process` — single-article send to Kindle
- `POST /fetch-feed` — RSS/Atom article discovery
- `POST /compile` — multi-article compile with streamed progress
- `POST /download` — generate EPUB for direct download
- `GET /health` — health check

---

## Self-hosting

Lit runs fine on any small server or home machine. For a more permanent setup:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

A `Dockerfile`, `docker-compose.yml`, and `kindle-sender.service` systemd unit are included if you want to containerise or run it as a background service.

### Nix / NixOS

This repo exports:

- `packages.default` / `packages.art-domain`
- `nixosModules.default`

The NixOS module is configured under `services.art-domain` and is intended to be reverse proxied from `art.bepis.lol`.

---

MIT License
