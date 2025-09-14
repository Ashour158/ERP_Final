# DigitalOcean App Platform Deployment Guide

## 🚀 Quick Deployment Steps

### 1. Prepare Your Repository
The repository is now ready for deployment with all necessary files:
- ✅ `app.py` - Main application with environment-driven config
- ✅ `config.py` - Environment-specific configurations  
- ✅ `wsgi.py` - WSGI entry point with auto-initialization
- ✅ `Dockerfile` - Container configuration with health checks
- ✅ `requirements.txt` - Python dependencies
- ✅ `.env.example` - Environment variable template

### 2. DigitalOcean App Platform Setup

#### Create New App
1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Connect your GitHub repository `Ashour158/ERP_Final`
4. Select the branch you want to deploy

#### Configure Build Settings
```yaml
# App Platform will auto-detect these from Dockerfile
name: erp-system
services:
- name: web
  source_dir: /
  github:
    repo: Ashour158/ERP_Final
    branch: main
  run_command: gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 wsgi:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
  health_check:
    http_path: /
```

### 3. Required Environment Variables

Set these in the App Platform environment variables section:

#### Core Settings (REQUIRED)
```bash
FLASK_ENV=production
SECRET_KEY=generate-a-long-random-string-here-32chars-minimum
JWT_SECRET_KEY=generate-another-long-random-string-here-32chars-minimum
```

#### Database (REQUIRED for Production)
```bash
# For DigitalOcean Managed Database
DATABASE_URL=postgresql://username:password@hostname:port/database

# Or for development/testing
DEV_DATABASE_URL=sqlite:///erp_development.db
```

#### Optional Settings
```bash
# CORS for multiple domains
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Company initialization
DEFAULT_COMPANY_NAME=Your Company Name
DEFAULT_COMPANY_CODE=YOURCO
DEFAULT_COMPANY_EMAIL=admin@yourcompany.com

# Admin user setup
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-secure-password
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_FIRST_NAME=System
ADMIN_LAST_NAME=Administrator
```

### 4. Database Setup (Recommended)

#### Option A: DigitalOcean Managed Database (Recommended)
1. Create a PostgreSQL database in DigitalOcean
2. Copy the connection string to `DATABASE_URL`
3. The app will automatically create tables and initialize data

#### Option B: SQLite (Development Only)
- Set `DEV_DATABASE_URL=sqlite:///erp_development.db`
- Suitable for testing but not recommended for production

### 5. Deploy and Verify

#### Deploy
1. Click "Create Resources" in App Platform
2. Wait for build and deployment to complete
3. App Platform will provide a URL like `https://your-app-name.ondigitalocean.app`

#### Verify Deployment
1. **Health Check**: Visit `https://your-app.ondigitalocean.app/`
   - Should return JSON with `{"status": "ok", "env": "production", ...}`
2. **Admin Login**: Visit the app URL
   - Login with admin credentials you set in environment variables
3. **Profile Test**: Check if authentication profile loads correctly

### 6. Post-Deployment Configuration

#### Custom Domain (Optional)
1. In App Platform, go to Settings > Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Update `CORS_ORIGINS` environment variable

#### Scaling (Optional)
1. Monitor app performance in App Platform dashboard
2. Scale up instance size or count as needed
3. Consider adding a load balancer for high traffic

### 7. Monitoring and Maintenance

#### Health Monitoring
- App Platform automatically monitors the `/` health endpoint
- Check logs in App Platform dashboard for any issues
- Set up alerts for downtime or errors

#### Database Backups
- DigitalOcean Managed Database includes automatic backups
- Consider setting up additional backup strategies for critical data

#### Updates
- Push changes to your GitHub repository
- App Platform will automatically redeploy
- Monitor deployment logs for any issues

### 8. Security Considerations

#### Environment Variables
- Never commit `.env` files to your repository
- Use strong, unique values for `SECRET_KEY` and `JWT_SECRET_KEY`
- Regularly rotate secrets

#### HTTPS
- App Platform provides free SSL certificates
- Ensure `CORS_ORIGINS` uses HTTPS URLs
- Set `SESSION_COOKIE_SECURE=true` in production

#### Database Security
- Use DigitalOcean Managed Database for automatic security updates
- Restrict database access to your app only
- Monitor database logs for unusual activity

### 9. Troubleshooting

#### Common Issues

**Build Failures**
- Check that all files are committed to your repository
- Verify `requirements.txt` includes all dependencies
- Check build logs in App Platform dashboard

**Database Connection Issues**  
- Verify `DATABASE_URL` is correctly formatted
- Ensure database is accessible from your app
- Check firewall settings on managed database

**Health Check Failures**
- Verify the `/` endpoint is accessible
- Check application logs for startup errors
- Ensure all required environment variables are set

**Authentication Issues**
- Verify JWT secrets are set and consistent
- Check that admin user was created successfully
- Review authentication logs

#### Log Access
- Access logs through App Platform dashboard
- Use `docker logs` commands for local debugging
- Enable debug logging by setting `LOG_LEVEL=DEBUG`

### 10. Performance Optimization

#### App Platform Settings
- Start with `basic-xxs` instance and scale up as needed
- Monitor CPU and memory usage
- Consider enabling CDN for static assets

#### Database Optimization
- Use connection pooling (included in SQLAlchemy)
- Monitor query performance
- Consider read replicas for high-read workloads

#### Application Optimization
- Enable Redis for session storage (optional)
- Implement caching for frequently accessed data
- Monitor API response times

---

## 📞 Support

If you encounter issues during deployment:

1. **Check the logs** in App Platform dashboard
2. **Verify environment variables** are correctly set
3. **Test locally** with the same environment configuration
4. **Review the implementation summary** for detailed technical information

The application includes comprehensive error handling and logging to help diagnose issues quickly.