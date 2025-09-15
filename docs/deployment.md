# MAZ ERP System Deployment Guide

This guide covers deploying the MAZ ERP System with both the React frontend and Flask backend.

## Architecture Overview

- **Frontend**: React + Vite + TypeScript + Tailwind CSS (served from `/var/www/maz`)
- **Backend**: Flask API (served from `localhost:5000`)
- **Database**: PostgreSQL 
- **Cache/Sessions**: Redis
- **Web Server**: Nginx (reverse proxy)

## Environment Variables

### Backend (.env)
```bash
# Flask Configuration
FLASK_ENV=production
FLASK_APP=wsgi.py

# Security Keys (CHANGE THESE!)
SECRET_KEY=your-super-secret-key-change-this-in-production-make-it-long-and-random
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production-also-long-and-random

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/erp_production

# Redis for caching and rate limiting
REDIS_URL=redis://localhost:6379/0

# CORS Settings
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting
RATE_LIMITS=60/minute

# Security Settings
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=https://yourdomain.com/api
```

## Nginx Configuration

Create `/etc/nginx/sites-available/maz-erp`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;

    # Security headers
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend (React SPA)
    location / {
        root /var/www/maz;
        index index.html;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/maz-erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Deployment Steps

### 1. Build Frontend

```bash
cd frontend
npm install
npm run build
```

This creates a `dist/` directory with the built React application.

### 2. Deploy Frontend Static Files

```bash
# Copy built files to web server directory
sudo mkdir -p /var/www/maz
sudo cp -r frontend/dist/* /var/www/maz/
sudo chown -R www-data:www-data /var/www/maz
sudo chmod -R 755 /var/www/maz
```

### 3. Deploy Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
```

### 4. Backend as a Service

Create `/etc/systemd/system/maz-erp.service`:

```ini
[Unit]
Description=MAZ ERP Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/ERP_Final
Environment=PATH=/path/to/ERP_Final/venv/bin
ExecStart=/path/to/ERP_Final/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable maz-erp
sudo systemctl start maz-erp
```

## Docker Deployment

### Using GitHub Container Registry (GHCR)

Pull and run the latest backend image:

```bash
# Pull the latest image
docker pull ghcr.io/ashour158/erp_final:latest

# Run with environment variables
docker run -d \
  --name maz-erp-backend \
  -p 5000:5000 \
  -e SECRET_KEY="your-secret-key" \
  -e JWT_SECRET_KEY="your-jwt-secret" \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e REDIS_URL="redis://localhost:6379/0" \
  ghcr.io/ashour158/erp_final:latest
```

### Frontend Container (Optional)

```bash
# Build frontend image
docker build -t maz-frontend ./frontend

# Run frontend container
docker run -d \
  --name maz-erp-frontend \
  -p 3000:80 \
  maz-frontend
```

## Database Setup

### PostgreSQL

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE erp_production;
CREATE USER erp_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE erp_production TO erp_user;
\q

# Run migrations
alembic upgrade head
```

### Redis

```bash
# Install Redis
sudo apt install redis-server

# Configure Redis (optional)
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

## SSL Certificate

### Using Let's Encrypt (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Monitoring and Logs

### Application Logs

```bash
# Backend logs
sudo journalctl -u maz-erp -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

- Backend: `https://yourdomain.com/health`
- Frontend: `https://yourdomain.com`

## Security Checklist

- [ ] Change all default passwords and secret keys
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall (only allow ports 22, 80, 443)
- [ ] Set up rate limiting with Redis
- [ ] Configure security headers in Nginx
- [ ] Enable fail2ban for SSH protection
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Backup database regularly
- [ ] Monitor application logs

## Backup Strategy

### Database Backup

```bash
# Create backup script
#!/bin/bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Add to crontab for daily backups
0 2 * * * /path/to/backup_script.sh
```

### Application Backup

```bash
# Backup uploaded files and configurations
tar -czf app_backup_$(date +%Y%m%d).tar.gz /path/to/ERP_Final/uploads /path/to/ERP_Final/.env
```

## Troubleshooting

### Common Issues

1. **Frontend not loading**: Check Nginx configuration and static file permissions
2. **API errors**: Check backend logs with `journalctl -u maz-erp`
3. **Database connection**: Verify DATABASE_URL and PostgreSQL service status
4. **Rate limiting issues**: Check Redis connection and REDIS_URL
5. **CORS errors**: Verify CORS_ORIGINS in backend .env

### Performance Tuning

- Adjust Gunicorn worker count based on CPU cores
- Configure Redis memory settings
- Optimize Nginx caching rules
- Use CDN for static assets in production
- Monitor database query performance

## Scaling Considerations

- Use load balancer for multiple backend instances
- Separate database server for high load
- Redis cluster for distributed caching
- CDN for global static asset delivery
- Container orchestration with Kubernetes