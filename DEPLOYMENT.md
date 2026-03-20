# Deployment Guide

This guide covers different deployment options for the Kindle Article Sender.

## Option 1: Local Development

Perfect for testing and personal use on your local machine.

```bash
# 1. Run setup script
./setup.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Edit .env with your credentials
nano .env

# 4. Test installation
python test_installation.py

# 5. Run the application
python app.py
```

Access at: `http://localhost:5000`

## Option 2: Docker Deployment

Easiest way to deploy on a server.

### Prerequisites
- Docker
- Docker Compose

### Steps

```bash
# 1. Create .env file
cp .env.example .env
nano .env  # Add your credentials

# 2. Build and run
docker-compose up -d

# 3. Check logs
docker-compose logs -f

# 4. Stop
docker-compose down
```

Access at: `http://your-server-ip:5000`

### Docker with Nginx Reverse Proxy

1. Create nginx configuration:

```nginx
# /etc/nginx/sites-available/kindle-sender
server {
    listen 80;
    server_name kindle.yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long-running requests
        proxy_read_timeout 120s;
    }
}
```

2. Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/kindle-sender /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

3. Add HTTPS with Let's Encrypt:

```bash
sudo certbot --nginx -d kindle.yourdomain.com
```

## Option 3: Systemd Service (Production)

For running on a Linux server without Docker.

### Prerequisites
- Ubuntu/Debian server
- Python 3.9+
- Nginx (optional but recommended)

### Steps

```bash
# 1. Clone to /opt
sudo mkdir -p /opt/kindle-article-sender
sudo cp -r . /opt/kindle-article-sender
cd /opt/kindle-article-sender

# 2. Run setup
sudo ./setup.sh

# 3. Create log directory
sudo mkdir -p /var/log/kindle-sender
sudo chown www-data:www-data /var/log/kindle-sender

# 4. Install gunicorn
source venv/bin/activate
pip install gunicorn

# 5. Copy service file
sudo cp kindle-sender.service /etc/systemd/system/

# 6. Edit service file if needed
sudo nano /etc/systemd/system/kindle-sender.service

# 7. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable kindle-sender
sudo systemctl start kindle-sender

# 8. Check status
sudo systemctl status kindle-sender

# 9. View logs
sudo journalctl -u kindle-sender -f
```

### Systemd Commands

```bash
# Start service
sudo systemctl start kindle-sender

# Stop service
sudo systemctl stop kindle-sender

# Restart service
sudo systemctl restart kindle-sender

# View status
sudo systemctl status kindle-sender

# View logs
sudo journalctl -u kindle-sender -f

# Disable auto-start
sudo systemctl disable kindle-sender
```

## Option 4: Cloud Platforms

### Heroku

```bash
# 1. Create Procfile
echo "web: gunicorn app:app" > Procfile

# 2. Create heroku.yml
cat > heroku.yml << EOF
build:
  docker:
    web: Dockerfile
EOF

# 3. Deploy
heroku create your-kindle-sender
heroku stack:set container
git push heroku main

# 4. Set environment variables
heroku config:set SMTP_USERNAME=your-email@gmail.com
heroku config:set SMTP_PASSWORD=your-app-password
heroku config:set KINDLE_EMAIL=your-kindle@kindle.com
```

### Railway

1. Connect your GitHub repository
2. Add environment variables in Railway dashboard
3. Deploy automatically on push

### DigitalOcean App Platform

1. Create new app from GitHub
2. Configure environment variables
3. Deploy

## Security Considerations

### 1. Firewall

```bash
# Allow only necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 2. Environment Variables

Never commit `.env` file to version control:
```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore
```

### 3. SSL/TLS

Always use HTTPS in production:
```bash
# With Certbot (Let's Encrypt)
sudo certbot --nginx -d your-domain.com
```

### 4. Rate Limiting

Add rate limiting in Nginx:
```nginx
limit_req_zone $binary_remote_addr zone=kindle:10m rate=10r/m;

location / {
    limit_req zone=kindle burst=5;
    proxy_pass http://localhost:5000;
}
```

## Monitoring

### Health Check Endpoint

The app includes a health check at `/health`:

```bash
curl http://localhost:5000/health
```

### Log Monitoring

With systemd:
```bash
sudo journalctl -u kindle-sender -f
```

With Docker:
```bash
docker-compose logs -f
```

### Uptime Monitoring

Use services like:
- UptimeRobot
- Pingdom
- StatusCake

Configure to check: `https://your-domain.com/health`

## Backup

### Important Files to Backup

1. `.env` file (credentials)
2. Any custom CSS modifications
3. Configuration files

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backups/kindle-sender"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp .env $BACKUP_DIR/env_$DATE
cp -r styles/ $BACKUP_DIR/styles_$DATE/
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>
```

### Permission Denied

```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/kindle-article-sender

# Fix permissions
sudo chmod -R 755 /opt/kindle-article-sender
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u kindle-sender -n 50

# Test manually
cd /opt/kindle-article-sender
source venv/bin/activate
python app.py
```

### Playwright Issues

```bash
# Reinstall browsers
source venv/bin/activate
playwright install --with-deps chromium
```

## Updating

### Git-based Deployment

```bash
# Pull latest changes
git pull origin main

# Restart service
sudo systemctl restart kindle-sender
```

### Docker Deployment

```bash
# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Performance Tuning

### Gunicorn Workers

Adjust based on CPU cores:
```
workers = (2 × CPU cores) + 1
```

Edit in `kindle-sender.service`:
```
--workers 9  # For 4-core server
```

### Nginx Caching

Add caching for static assets:
```nginx
location /static {
    alias /opt/kindle-article-sender/static;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Multi-User Setup

To support multiple users with different Kindle addresses:

1. Remove default `KINDLE_EMAIL` from `.env`
2. Users enter their Kindle email in the web interface
3. Optional: Add user authentication with Flask-Login

---

For questions or issues, refer to the main README.md or open an issue on GitHub.
