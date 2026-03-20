# System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Flask Web Application)                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  HTML Form: URL list + Kindle Email                     │  │
│  │  JavaScript: previews, RSS loading, status updates      │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Article Extraction                          │
│                   (Multi-Tier Approach)                         │
│                                                                 │
│  Tier 1: Direct Extraction                                     │
│  ┌──────────────────────────────────────────┐                 │
│  │  trafilatura → Parse HTML → Extract text │                 │
│  └──────────────────────────────────────────┘                 │
│                     │                                           │
│                     ▼ (if fails)                               │
│  Tier 2: Archive.is                                            │
│  ┌──────────────────────────────────────────┐                 │
│  │  Submit to archive.is → Fetch archived   │                 │
│  └──────────────────────────────────────────┘                 │
│                     │                                           │
│                     ▼ (if fails)                               │
│  Tier 3: 12ft.io Proxy                                         │
│  ┌──────────────────────────────────────────┐                 │
│  │  Proxy request → Bypass paywall          │                 │
│  └──────────────────────────────────────────┘                 │
│                     │                                           │
│                     ▼ (if fails)                               │
│  Tier 4: Playwright (JS Disabled)                              │
│  ┌──────────────────────────────────────────┐                 │
│  │  Launch browser → Disable JS → Fetch     │                 │
│  └──────────────────────────────────────────┘                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Image Processing                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  1. Extract image URLs from HTML                         │ │
│  │  2. Download each image (with timeout)                   │ │
│  │  3. Convert to RGB (if needed)                           │ │
│  │  4. Resize to max 800px width                            │ │
│  │  5. Compress as JPEG (80% quality)                       │ │
│  │  6. Optimize for Kindle display                          │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EPUB Generation                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  1. Create EPUB structure                                │ │
│  │  2. Add custom CSS (serif fonts, justified text)         │ │
│  │  3. Embed processed images                               │ │
│  │  4. Add metadata (title, author, date)                   │ │
│  │  5. Format content as XHTML                              │ │
│  │  6. Generate table of contents                           │ │
│  │  7. Package as .epub file                                │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Email Delivery                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  1. Create email message                                 │ │
│  │  2. Attach EPUB file                                     │ │
│  │  3. Connect to SMTP server (Gmail)                       │ │
│  │  4. Send to Kindle email address                         │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Amazon Kindle Service                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  1. Receive email with EPUB attachment                   │ │
│  │  2. Validate sender email (approved list)                │ │
│  │  3. Convert EPUB to Kindle format (.azw)                 │ │
│  │  4. Deliver to all associated Kindle devices             │ │
│  │  5. Add to "My Content" library                          │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    📱 Kindle Device 📱
                   (Article ready to read!)


Data Flow Summary:
==================

URL → Extract Content → Process Images → Generate EPUB → Email → Kindle

File Size Limits:
- Per image: 5MB max
- Total EPUB: 50MB max (Amazon limit)
- Typical article: 1-5MB
```

## Component Details

### 1. Article Extractor (`extractor.py`)
- **Purpose**: Extract article content with paywall bypass
- **Key Methods**:
  - `extract()`: Main extraction coordinator
  - `_extract_direct()`: Uses trafilatura
  - `_extract_archive_is()`: Uses archive.is
  - `_extract_12ft()`: Uses 12ft.io proxy
  - `_extract_playwright()`: Browser automation
- **Returns**: Dict with title, author, date, content, images

### 2. Image Processor (`image_processor.py`)
- **Purpose**: Download and optimize images for Kindle
- **Key Features**:
  - Resizes to 600-800px width
  - Converts to JPEG (80% quality)
  - Handles various image formats
  - Respects timeout limits
- **Optimization**: Reduces file size by 60-80%

### 3. EPUB Generator (`epub_generator.py`)
- **Purpose**: Create formatted EPUB files
- **Key Features**:
  - Custom CSS for e-ink readability
  - Embedded images
  - Proper metadata
  - Table of contents
- **Styling**: Serif fonts, justified text, proper spacing

### 4. Email Sender (`mailer.py`)
- **Purpose**: Send EPUB to Kindle via email
- **Key Features**:
  - SMTP connection handling
  - File size validation
  - Attachment encoding
  - Error handling

### 5. Web Application (`app.py`)
- **Purpose**: Flask web interface
- **Endpoints**:
  - `GET /`: Main interface
  - `POST /preview`: URL preview
  - `POST /fetch-feed`: RSS/Atom discovery
  - `POST /process`: Process article
  - `POST /compile`: Streaming multi-article compilation
  - `POST /download`: Direct EPUB download
  - `GET /health`: Health check
- **Features**: drag-to-reorder URL list, preview requests, feed loading, streaming progress, error handling

## Security Features

1. **Environment Variables**: Sensitive data in `.env`
2. **Request Guards**: Basic required-field checks and article-count limits
3. **File Size Limits**: Prevent oversized EPUBs
4. **Timeout Protection**: Network timeouts on external requests
5. **SMTP Security**: TLS encryption for email

## Scalability Considerations

### Current Limits
- Sequential processing (one article at a time)
- In-memory image processing
- No caching of extracted articles

### Potential Improvements
- Add Redis for caching
- Queue system (Celery) for async processing
- Database for user preferences
- CDN for static assets
- Multiple worker processes

## Error Handling

Each component has comprehensive error handling:
- Network errors: Retry with exponential backoff
- Parsing errors: Fall back to next tier
- File errors: Clean up temporary files
- Email errors: Log and report to user

## Monitoring Points

Recommended metrics to track:
- Extraction success rate by tier
- Average processing time
- Email delivery success rate
- Image processing success rate
- Error types and frequencies

## Nix Hosting

The repo now exports a Nix flake package and NixOS module named `art-domain`.

- The package contains the app sources and Python runtime.
- The module runs the app behind Gunicorn.
- On NAS, `nix-dotfiles` can import the repo flake and reverse proxy it on `art.bepis.lol`.
