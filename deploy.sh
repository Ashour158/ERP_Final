#!/bin/bash

# Complete ERP System - Digital Ocean Deployment Script
# This script automates the deployment process for Digital Ocean

set -e  # Exit on any error

echo "🚀 Starting Complete ERP System Deployment..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check for required commands
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is required but not installed."
        exit 1
    fi
}

print_status "Checking required dependencies..."
check_command "python3"
check_command "pip3"
check_command "git"

# Create application directory
APP_DIR="/opt/complete-erp"
print_status "Setting up application directory: $APP_DIR"

if [ ! -d "$APP_DIR" ]; then
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
fi

# Copy application files
print_status "Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p uploads
mkdir -p logs
mkdir -p backups

# Set proper permissions
chmod 755 uploads
chmod 755 logs
chmod 755 backups

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating environment file from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your actual configuration values"
fi

# Database setup
print_status "Setting up database..."
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"

# Create systemd service file
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/complete-erp.service > /dev/null <<EOF
[Unit]
Description=Complete ERP System
After=network.target

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
print_status "Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/complete-erp > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # File upload size
    client_max_body_size 500M;

    # Static files
    location /static {
        alias $APP_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Uploads
    location /uploads {
        alias $APP_DIR/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Enable Nginx site
if [ -f "/etc/nginx/sites-available/complete-erp" ]; then
    sudo ln -sf /etc/nginx/sites-available/complete-erp /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
fi

# Create backup script
print_status "Creating backup script..."
tee backup.sh > /dev/null <<EOF
#!/bin/bash
# Complete ERP System Backup Script

BACKUP_DIR="$APP_DIR/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="erp_backup_\$DATE.tar.gz"

echo "Creating backup: \$BACKUP_FILE"

# Create database dump
pg_dump \$DATABASE_URL > \$BACKUP_DIR/database_\$DATE.sql

# Create full backup
tar -czf \$BACKUP_DIR/\$BACKUP_FILE \\
    --exclude='venv' \\
    --exclude='__pycache__' \\
    --exclude='*.pyc' \\
    --exclude='logs/*.log' \\
    --exclude='backups/*.tar.gz' \\
    .

echo "Backup completed: \$BACKUP_FILE"

# Clean old backups (keep last 30 days)
find \$BACKUP_DIR -name "erp_backup_*.tar.gz" -mtime +30 -delete
find \$BACKUP_DIR -name "database_*.sql" -mtime +30 -delete
EOF

chmod +x backup.sh

# Create log rotation configuration
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/complete-erp > /dev/null <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload complete-erp
    endscript
}
EOF

# Install and configure fail2ban (optional security)
if command -v fail2ban-server &> /dev/null; then
    print_status "Configuring fail2ban for additional security..."
    sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF
fi

# Create monitoring script
print_status "Creating monitoring script..."
tee monitor.sh > /dev/null <<EOF
#!/bin/bash
# Complete ERP System Monitoring Script

APP_URL="http://localhost:8080"
LOG_FILE="$APP_DIR/logs/monitor.log"

# Check if application is responding
if curl -f -s \$APP_URL > /dev/null; then
    echo "\$(date): Application is running" >> \$LOG_FILE
else
    echo "\$(date): Application is down - restarting" >> \$LOG_FILE
    sudo systemctl restart complete-erp
fi

# Check disk space
DISK_USAGE=\$(df $APP_DIR | tail -1 | awk '{print \$5}' | sed 's/%//')
if [ \$DISK_USAGE -gt 80 ]; then
    echo "\$(date): Disk usage is \$DISK_USAGE% - cleanup needed" >> \$LOG_FILE
fi

# Check memory usage
MEMORY_USAGE=\$(free | grep Mem | awk '{printf("%.0f", \$3/\$2 * 100.0)}')
if [ \$MEMORY_USAGE -gt 80 ]; then
    echo "\$(date): Memory usage is \$MEMORY_USAGE%" >> \$LOG_FILE
fi
EOF

chmod +x monitor.sh

# Add monitoring to crontab
print_status "Setting up monitoring cron job..."
(crontab -l 2>/dev/null; echo "*/5 * * * * $APP_DIR/monitor.sh") | crontab -

# Add backup to crontab
print_status "Setting up backup cron job..."
(crontab -l 2>/dev/null; echo "0 2 * * * $APP_DIR/backup.sh") | crontab -

# Start and enable services
print_status "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable complete-erp
sudo systemctl start complete-erp

# Check if Nginx is installed and configure
if command -v nginx &> /dev/null; then
    sudo systemctl enable nginx
    sudo nginx -t && sudo systemctl restart nginx
    print_success "Nginx configured and restarted"
else
    print_warning "Nginx not found. Please install and configure manually."
fi

# Final status check
print_status "Checking application status..."
sleep 5

if systemctl is-active --quiet complete-erp; then
    print_success "Complete ERP System is running!"
else
    print_error "Failed to start Complete ERP System"
    print_status "Checking logs..."
    sudo journalctl -u complete-erp --no-pager -n 20
    exit 1
fi

# Display final information
echo ""
echo "================================================"
print_success "🎉 Complete ERP System Deployment Completed!"
echo "================================================"
echo ""
print_status "Application Details:"
echo "  📁 Installation Directory: $APP_DIR"
echo "  🌐 Local URL: http://localhost:8080"
echo "  📊 Service Status: $(systemctl is-active complete-erp)"
echo "  📝 Logs: sudo journalctl -u complete-erp -f"
echo ""
print_status "Next Steps:"
echo "  1. Edit $APP_DIR/.env with your configuration"
echo "  2. Update Nginx server_name with your domain"
echo "  3. Set up SSL certificate (Let's Encrypt recommended)"
echo "  4. Configure your database connection"
echo "  5. Set up DNS to point to your server"
echo ""
print_status "Useful Commands:"
echo "  🔄 Restart: sudo systemctl restart complete-erp"
echo "  📊 Status: sudo systemctl status complete-erp"
echo "  📝 Logs: sudo journalctl -u complete-erp -f"
echo "  💾 Backup: $APP_DIR/backup.sh"
echo "  📈 Monitor: $APP_DIR/monitor.sh"
echo ""
print_warning "Remember to:"
echo "  - Change default passwords"
echo "  - Configure firewall rules"
echo "  - Set up regular backups"
echo "  - Monitor system resources"
echo "  - Keep system updated"
echo ""
print_success "Your Complete ERP System is ready to revolutionize your business!"
echo "🚀 Access it at your domain and start with admin/admin123"
echo ""

