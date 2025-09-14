# Complete ERP System - GitHub Copilot Instructions

**ALWAYS follow these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## System Overview

Complete ERP System is a comprehensive Flask-based Enterprise Resource Planning application with 14 integrated modules including CRM, Finance, HR, Supply Chain, and more. The application is designed for Digital Ocean deployment with Docker support and can run on various cloud platforms.

## Working Effectively

### Bootstrap and Setup Commands (NEVER CANCEL - Set 60+ minute timeouts)
Run these commands in sequence to set up the development environment:

1. **Install System Dependencies:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-pip python3-venv python3-dev
   sudo apt install -y python3-flask python3-flask-cors python3-flask-sqlalchemy
   sudo apt install -y python3-sqlalchemy python3-gunicorn postgresql postgresql-contrib
   sudo apt install -y redis-server nginx git docker.io docker-compose
   ```
   - Takes 5-10 minutes. NEVER CANCEL. Set timeout to 15+ minutes.

2. **Create Virtual Environment:**
   ```bash
   python3 -m venv erp_env
   source erp_env/bin/activate
   ```
   - Takes 30 seconds. Always activate before working.

3. **Install Python Dependencies (CRITICAL - FIREWALL LIMITATIONS):**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   - **WARNING: pip install often fails due to firewall/SSL limitations in CI environments**
   - Alternative approach if pip fails:
     ```bash
     sudo apt install -y python3-flask python3-flask-cors python3-flask-sqlalchemy
     sudo apt install -y python3-jwt python3-werkzeug python3-gunicorn
     sudo apt install -y python3-psycopg2 python3-redis python3-celery
     sudo apt install -y python3-requests python3-pillow python3-pandas
     ```
   - Takes 10-15 minutes. NEVER CANCEL. Set timeout to 30+ minutes.

### Build and Test Commands

4. **Test Application Loading:**
   ```bash
   python3 -c "from app import app; print('App loaded successfully')"
   ```
   - Takes 5 seconds. Should complete without errors.

5. **Initialize Database:**
   ```bash
   python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"
   ```
   - Takes 2-3 seconds. Creates SQLite database by default.

6. **Test Flask Application (Development Mode):**
   ```bash
   export FLASK_APP=wsgi.py
   export FLASK_ENV=development
   python3 -m flask run --host=0.0.0.0 --port=8080
   ```
   - Takes 5 seconds to start. Application runs on http://localhost:8080
   - **NEVER CANCEL** - Application runs continuously until stopped

### Docker Deployment (Production-like Testing)

7. **Build Docker Image (NEVER CANCEL - Set 60+ minute timeout):**
   ```bash
   docker build -t complete-erp .
   ```
   - Takes 20-30 minutes. NEVER CANCEL. Set timeout to 60+ minutes.
   - **WARNING: May fail due to pip install limitations in Docker build**

8. **Run with Docker Compose (NEVER CANCEL - Set 30+ minute timeout):**
   ```bash
   docker-compose up -d
   ```
   - Takes 5-15 minutes. NEVER CANCEL. Set timeout to 30+ minutes.
   - Starts PostgreSQL, Redis, and Flask application

9. **Check Docker Application Status:**
   ```bash
   docker-compose ps
   docker-compose logs web
   ```
   - Takes 5 seconds. Check if all services are running.

### Validation Scenarios (ALWAYS PERFORM THESE TESTS)

10. **Manual End-to-End Testing:**
    - Access application at http://localhost:8080
    - **Login Test:** Use admin/admin123 credentials
    - **Navigation Test:** Click through all 14 module sections
    - **Form Test:** Create a test customer in CRM module
    - **Database Test:** Verify data persistence after restart
    - **GPS Test:** Test location services if available
    - Take screenshots of working application interface

11. **API Testing:**
    ```bash
    curl -X POST http://localhost:8080/api/auth/login \
         -H "Content-Type: application/json" \
         -d '{"username":"admin","password":"admin123"}'
    ```
    - Takes 5 seconds. Should return JWT token.

### Linting and Code Quality

12. **Run Code Quality Checks:**
    ```bash
    python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    python3 -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    ```
    - Takes 30 seconds. Always run before committing.

## Repository Structure and Navigation

### Key Files and Directories
- **`app.py`** - Main Flask application with all 14 modules (107KB - comprehensive)
- **`wsgi.py`** - WSGI entry point for production deployment
- **`config.py`** - Configuration management for dev/prod/test environments
- **`requirements.txt`** - Python dependencies (33 packages including ML libraries)
- **`Dockerfile`** - Container definition for deployment
- **`docker-compose.yml`** - Multi-service setup with PostgreSQL and Redis
- **`deploy.sh`** - Automated deployment script for Digital Ocean
- **`index.html`** - Frontend interface (51KB - complete UI)
- **`.env.example`** - Environment variables template
- **`.github/workflows/`** - CI/CD pipeline definitions

### Module Structure (All in app.py)
1. **Digital Signature Module** - OCR and certificate management
2. **Internal Communication** - Teams-like messaging
3. **Operations Management** - Workflow automation
4. **Marketing Module** - E-commerce and lead scoring
5. **Supply Chain Management** - Logistics and courier integration
6. **Contract Management** - AI-powered analysis
7. **Survey Module** - Multi-channel insights
8. **HR & People Management** - Complete HR solution
9. **Internal Community** - Social platform features
10. **Enhanced CRM** - Customer relationship management
11. **Advanced Finance** - Financial management
12. **Business Analysis** - Intelligence and analytics
13. **Compliance & Quality** - ISO 9001 implementation
14. **Enhanced Desk Module** - Support ticketing

## Known Issues and Workarounds

### Network and Installation Issues
- **pip install failures:** Common in CI environments due to SSL/firewall issues
  - Workaround: Use system packages via apt install
  - Alternative: Pre-built Docker images
- **Docker build failures:** Due to pip install limitations
  - Workaround: Test with system packages first
- **Package version conflicts:** requirements.txt uses specific versions
  - Workaround: Use latest compatible versions from system packages

### Database Configuration
- **Default:** SQLite for development (file: complete_erp.db)
- **Production:** PostgreSQL (requires DATABASE_URL environment variable)
- **Testing:** In-memory SQLite (automatically configured)

### Environment Variables Required for Production
```bash
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-change-in-production
DATABASE_URL=postgresql://user:pass@host:port/database
REDIS_URL=redis://host:port/0
FLASK_ENV=production
```

## Testing Strategy

### Unit Testing
```bash
python3 -m pytest
```
- **WARNING:** No pytest configuration found - tests may not exist
- Takes 1-5 minutes if tests exist. NEVER CANCEL. Set timeout to 10+ minutes.

### Integration Testing
```bash
python3 -c "from app import app; app.test_client().get('/')"
```
- Takes 5 seconds. Tests basic Flask routing.

### Load Testing (Optional)
```bash
# If testing tools are available
ab -n 100 -c 10 http://localhost:8080/
```
- Takes 30 seconds. Stress test application.

## Deployment Options

### 1. Digital Ocean App Platform (Recommended)
- Use `deploy.sh` script for automated setup
- Deployment time: 10-15 minutes
- **NEVER CANCEL** during deployment process

### 2. Digital Ocean Droplet
- Manual server setup with Nginx reverse proxy
- Deployment time: 20-30 minutes
- **NEVER CANCEL** during configuration

### 3. Docker Deployment
- Use `docker-compose.yml` for multi-service setup
- Deployment time: 15-25 minutes including image builds
- **NEVER CANCEL** during docker build process

## Performance Expectations

### Build Times (CRITICAL - Set Appropriate Timeouts)
- **pip install:** 10-15 minutes (may fail due to network issues)
- **Docker build:** 20-30 minutes. NEVER CANCEL. Set timeout to 60+ minutes.
- **System package install:** 5-10 minutes
- **Database initialization:** 5-10 seconds
- **Application startup:** 5-15 seconds

### Test Times
- **Flask application test:** 5-10 seconds
- **API endpoint tests:** 5-30 seconds per test
- **End-to-end validation:** 5-10 minutes for complete workflow testing

## Common Validation Commands

Always run these commands to verify the system is working:

```bash
# Quick system check
python3 --version
docker --version
python3 -c "import flask; print('Flask available')"

# Application health check
curl -s http://localhost:8080/health || echo "Application not running"

# Database connectivity check
python3 -c "from app import app, db; app.app_context().push(); print('Database connection:', 'OK' if db.engine.table_names() else 'Failed')"

# Service status check (if using systemd)
sudo systemctl status complete-erp || echo "Service not installed"
```

## Development Workflow

### Making Changes
1. **Always activate virtual environment:** `source erp_env/bin/activate`
2. **Test changes locally:** Run Flask development server
3. **Validate database changes:** Check model migrations
4. **Run linting:** flake8 before committing
5. **Test Docker build:** If deployment-related changes
6. **Manual validation:** Always test user workflows

### Key Areas to Check After Changes
- **Database models:** Located in app.py (lines 40-200+)
- **API routes:** All modules have dedicated route sections
- **Configuration:** config.py for environment settings
- **Frontend:** index.html for UI changes
- **Deployment:** Dockerfile and docker-compose.yml

## Security Considerations

- **Default credentials:** admin/admin123 (CHANGE IN PRODUCTION)
- **Secret keys:** Must be changed from defaults in production
- **Database:** Multi-company data isolation implemented
- **CORS:** Configured for cross-origin requests
- **JWT:** Token-based authentication with 24-hour expiry

## Important Notes

1. **NEVER CANCEL long-running builds** - Docker builds can take 30+ minutes
2. **Always use appropriate timeouts** - Set 60+ minutes for builds, 30+ for tests
3. **Test multiple scenarios** - Login, navigation, data entry, persistence
4. **Check logs** - Use `docker-compose logs` or `sudo journalctl -u complete-erp`
5. **Validate deployment** - Always test the deployed application manually
6. **Network limitations** - CI environments may have firewall restrictions
7. **Documentation first** - These instructions should handle 90% of development needs

## Troubleshooting

### Application Won't Start
```bash
# Check Python path and modules
python3 -c "import sys; print(sys.path)"
python3 -c "from app import app"

# Check database
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Docker Issues
```bash
# Check container status
docker ps -a
docker logs complete-erp_web_1

# Restart services
docker-compose down && docker-compose up -d
```

### Performance Issues
```bash
# Check system resources
free -h
df -h
top

# Check application logs
tail -f logs/complete-erp.log
```

**Remember: Always validate your changes with real user scenarios. The system is complex with 14 integrated modules - thorough testing is essential.**