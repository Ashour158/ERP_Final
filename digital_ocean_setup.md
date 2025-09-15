# Digital Ocean Deployment Guide
## Complete ERP System V2.0

### 🌊 Digital Ocean App Platform Deployment (Recommended)

This is the easiest way to deploy your Complete ERP System on Digital Ocean.

#### **Step 1: Prepare Your Repository**

1. **Upload Files** to GitHub, GitLab, or directly to Digital Ocean
2. **Ensure all files** from this package are included
3. **Verify** the following files are present:
   - `app.py` (main application)
   - `wsgi.py` (WSGI entry point)
   - `requirements.txt` (dependencies)
   - `Dockerfile` (containerization)
   - `index.html` (frontend)
   - All other files in this package

#### **Step 2: Create Digital Ocean App**

1. **Login** to Digital Ocean Console
2. **Navigate** to App Platform
3. **Click** "Create App"
4. **Choose** your source (GitHub/GitLab/Docker Hub)
5. **Select** your repository or upload files

#### **Step 3: Configure Build Settings**

```yaml
# App Spec Configuration
name: complete-erp-system
services:
- name: web
  source_dir: /
  github:
    repo: your-username/complete-erp-system
    branch: main
  run_command: gunicorn --bind 0.0.0.0:$PORT --workers 4 wsgi:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
  routes:
  - path: /
  health_check:
    http_path: /
  envs:
  - key: FLASK_ENV
    value: production
  - key: SECRET_KEY
    value: your-secret-key-change-in-production
  - key: JWT_SECRET_KEY
    value: your-jwt-secret-key-change-in-production

# Celery Worker Component for Background Tasks
workers:
- name: celery-worker
  source_dir: /
  github:
    repo: your-username/complete-erp-system
    branch: main
  run_command: celery -A app.celery worker --loglevel=info
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: FLASK_ENV
    value: production
  - key: SECRET_KEY
    value: your-secret-key-change-in-production
  - key: JWT_SECRET_KEY
    value: your-jwt-secret-key-change-in-production
```

#### **Step 4: Add Database**

1. **In App Platform**, go to "Database" tab
2. **Add** PostgreSQL database
3. **Choose** appropriate size (Basic $15/month recommended)
4. **Note** the connection details

#### **Step 5: Configure Environment Variables**

Add these environment variables in App Platform:

```bash
# Required Variables
DATABASE_URL=${db.DATABASE_URL}  # Auto-populated by DO
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this
FLASK_ENV=production

# Optional Variables
REDIS_URL=redis://your-redis-instance
MAIL_SERVER=smtp.your-provider.com
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-password
CORS_ORIGINS=https://your-app-name.ondigitalocean.app

# DigitalOcean Spaces Storage (Optional)
DO_SPACES_KEY=your-spaces-access-key
DO_SPACES_SECRET=your-spaces-secret-key
DO_SPACES_BUCKET=your-bucket-name
DO_SPACES_REGION=nyc3
```

#### **Step 6: Background Tasks with Celery Worker (Optional)**

The ERP system includes Celery worker support for background tasks. The worker component is already included in the App Spec above.

**Benefits of Celery Worker:**
- Asynchronous email sending
- Background report generation
- Automated data processing
- Scheduled maintenance tasks

**Configuration:**
1. **Redis** is required for Celery (set REDIS_URL environment variable)
2. **Worker automatically starts** with the web service deployment
3. **Scales independently** from web service
4. **Logs available** in App Platform dashboard

**Monitoring Worker Health:**
```bash
# Check worker status via app logs
celery -A app.celery inspect active
celery -A app.celery inspect stats
```

#### **Step 7: File Storage with DigitalOcean Spaces (Optional)**

The ERP system supports pluggable storage backends. By default, it uses local file storage, but you can configure DigitalOcean Spaces for cloud storage.

**To Enable DigitalOcean Spaces:**
1. **Create Spaces bucket** in DO console
2. **Generate API keys** (Spaces access key/secret)
3. **Set environment variables** (see Step 5 above)
4. **Storage automatically switches** to Spaces when credentials are detected

**Storage Backend Features:**
- Automatic backend detection based on environment variables
- Local filesystem fallback when Spaces not configured
- Secure file uploads with conflict resolution
- Public URL generation for file access

#### **Step 8: Deploy**

1. **Click** "Create Resources"
2. **Wait** for deployment (5-10 minutes)
3. **Access** your app at the provided URL
4. **Login** with admin/admin123

---

### 🖥️ Digital Ocean Droplet Deployment

For more control and customization, deploy on a Droplet.

#### **Step 1: Create Droplet**

1. **Create** new Droplet in Digital Ocean
2. **Choose** Ubuntu 22.04 LTS
3. **Select** size (2GB RAM minimum recommended)
4. **Add** SSH key for secure access
5. **Create** Droplet

#### **Step 2: Connect and Setup**

```bash
# Connect to your Droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install required packages
apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git -y

# Create application user
adduser erp
usermod -aG sudo erp
su - erp
```

#### **Step 3: Deploy Application**

```bash
# Clone or upload your ERP system files
git clone https://github.com/your-username/complete-erp-system.git
cd complete-erp-system

# Run the deployment script
./deploy.sh
```

#### **Step 4: Configure Domain (Optional)**

1. **Point** your domain to Droplet IP
2. **Update** Nginx configuration with your domain
3. **Install** SSL certificate:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

### 🗄️ Digital Ocean Managed Database Setup

#### **PostgreSQL Database**

1. **Create** Managed PostgreSQL Database
2. **Choose** appropriate size:
   - **Basic ($15/month)**: Small businesses
   - **Professional ($60/month)**: Growing businesses
   - **Business ($240/month)**: Large enterprises

3. **Configure** connection:
```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

#### **Redis Cache (Optional)**

1. **Create** Managed Redis Database
2. **Configure** connection:
```bash
REDIS_URL=redis://username:password@host:port/0
```

---

### 📁 Digital Ocean Spaces (File Storage)

For file uploads and document storage:

1. **Create** Spaces bucket
2. **Generate** API keys
3. **Configure** in environment:

```bash
DO_SPACES_KEY=your-spaces-access-key
DO_SPACES_SECRET=your-spaces-secret-key
DO_SPACES_BUCKET=your-bucket-name
DO_SPACES_REGION=nyc3
```

---

### 🔧 Performance Optimization

#### **App Platform Scaling**

```yaml
# Auto-scaling configuration
services:
- name: web
  instance_count: 2  # Start with 2 instances
  instance_size_slug: professional-xs  # Upgrade for better performance
  autoscaling:
    min_instance_count: 1
    max_instance_count: 5
    metrics:
    - cpu:
        percent: 70
    - memory:
        percent: 80
```

#### **Database Optimization**

1. **Enable** connection pooling
2. **Configure** read replicas for high traffic
3. **Set up** automated backups
4. **Monitor** performance metrics

#### **CDN Setup**

1. **Enable** Digital Ocean CDN
2. **Configure** for static assets
3. **Set** appropriate cache headers

---

### 📊 Monitoring and Alerts

#### **Digital Ocean Monitoring**

1. **Enable** monitoring for your resources
2. **Set up** alerts for:
   - High CPU usage (>80%)
   - High memory usage (>80%)
   - Disk space (>80%)
   - Application downtime

#### **Application Monitoring**

```bash
# Built-in vigilance system provides:
- Real-time system monitoring
- Performance alerts
- Business rule violations
- Security incident detection
```

---

### 💾 Backup Strategy

#### **Automated Backups**

1. **Database**: Automatic daily backups (Digital Ocean)
2. **Files**: Spaces backup with versioning
3. **Application**: Git repository backup

#### **Manual Backup**

```bash
# Run backup script
./backup.sh

# Backup includes:
- Database dump
- Application files
- Configuration files
- Upload directory
```

---

### 🔒 Security Best Practices

#### **Firewall Configuration**

```bash
# Configure UFW firewall
ufw allow ssh
ufw allow 'Nginx Full'
ufw enable
```

#### **SSL/TLS Setup**

```bash
# Let's Encrypt SSL (Free)
certbot --nginx -d yourdomain.com

# Or use Digital Ocean Load Balancer with SSL termination
```

#### **Security Headers**

Already configured in Nginx:
- X-Frame-Options
- X-XSS-Protection
- X-Content-Type-Options
- Content-Security-Policy

---

### 💰 Cost Estimation

#### **App Platform Deployment**

| Component | Cost/Month | Description |
|-----------|------------|-------------|
| **App Platform** | $12 | Basic tier (512MB RAM) |
| **PostgreSQL** | $15 | Basic managed database |
| **Redis** | $15 | Basic managed cache |
| **Spaces** | $5 | 250GB storage + CDN |
| **Domain** | $12 | .com domain registration |
| ****Total**** | **$59** | **Complete setup** |

#### **Droplet Deployment**

| Component | Cost/Month | Description |
|-----------|------------|-------------|
| **Droplet** | $24 | 2GB RAM, 50GB SSD |
| **Managed DB** | $15 | PostgreSQL database |
| **Spaces** | $5 | File storage |
| **Load Balancer** | $12 | SSL termination |
| ****Total**** | **$56** | **Self-managed setup** |

---

### 🚀 Quick Start Commands

#### **App Platform Deployment**

```bash
# 1. Upload files to repository
git add .
git commit -m "Complete ERP System"
git push origin main

# 2. Create app in Digital Ocean console
# 3. Connect repository
# 4. Deploy automatically
```

#### **Droplet Deployment**

```bash
# 1. Create and connect to Droplet
ssh root@your-droplet-ip

# 2. Download and run deployment
wget https://your-repo/deploy.sh
chmod +x deploy.sh
./deploy.sh

# 3. Configure domain and SSL
certbot --nginx -d yourdomain.com
```

---

### 🆘 Troubleshooting

#### **Common Issues**

1. **Application won't start**
   ```bash
   # Check logs
   sudo journalctl -u complete-erp -f
   
   # Check configuration
   python3 -c "from app import app; print('Config OK')"
   ```

2. **Database connection failed**
   ```bash
   # Test database connection
   psql $DATABASE_URL -c "SELECT version();"
   ```

3. **High memory usage**
   ```bash
   # Restart application
   sudo systemctl restart complete-erp
   
   # Check memory usage
   free -h
   ```

#### **Performance Issues**

1. **Slow response times**
   - Upgrade instance size
   - Enable Redis caching
   - Optimize database queries

2. **High CPU usage**
   - Scale to multiple instances
   - Enable auto-scaling
   - Optimize application code

---

### 📞 Support Resources

#### **Digital Ocean Documentation**
- [App Platform Guide](https://docs.digitalocean.com/products/app-platform/)
- [Managed Databases](https://docs.digitalocean.com/products/databases/)
- [Spaces Object Storage](https://docs.digitalocean.com/products/spaces/)

#### **Application Support**
- Built-in monitoring and alerts
- Comprehensive logging system
- Automated backup and recovery
- Performance optimization tools

---

**🎉 Your Complete ERP System is now ready to deploy on Digital Ocean!**

**Choose App Platform for simplicity or Droplet for full control. Both options provide enterprise-grade performance at a fraction of the cost of traditional ERP systems.**

