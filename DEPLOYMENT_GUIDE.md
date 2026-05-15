# 🚀 Deployment Guide - FB Task Platform

## 📋 Prerequisites

- Git account
- Render.com account (recommended) or Heroku account
- Redis service (Render Redis, Redis Labs, etc.)
- Domain name (optional)
- Facebook Graph API access token (optional, for enhanced verification)

---

## 🛠️ Step 1: Prepare Your Code

### 1.1 Install Dependencies

```bash
pip install -r requirements.txt
playwright install  # Install browser binaries for Facebook verification
```

### 1.2 Run Migrations

```bash
python manage.py migrate
```

### 1.3 Create Superuser

```bash
python manage.py createsuperuser
```

### 1.4 Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 1.5 Test Facebook Verification

```bash
# Test basic functionality
python test_verification.py

# Test full Facebook verification (requires internet)
python test_verification.py --full
```

### 1.6 Test Locally

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
celery -A config worker --loglevel=info

# Terminal 3: Start Django
python manage.py runserver
```

Visit `http://127.0.0.1:8000` and test:
- User registration
- Task creation (as admin)
- Facebook group share task submission
- Verification process (should take 5-10 minutes)

---

## 🌐 Step 2: Deploy to Render.com

### 2.1 Create Render Services

#### Web Service (Django App)
1. Connect your GitHub repository
2. Set service name: `fb-task-platform`
3. Set runtime: `Python 3`
4. Build Command:
   ```bash
   pip install -r requirements.txt && playwright install
   ```
5. Start Command:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   ```

#### Redis Service
1. Create a new Redis service
2. Note the connection URL for environment variables

#### Background Worker (Celery)
1. Create another web service for Celery
2. Start Command:
   ```bash
   celery -A config worker --loglevel=info
   ```

### 2.2 Environment Variables

Set these in your Render dashboard:

```bash
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-app-name.onrender.com

# Database
DATABASE_URL=postgresql://your-render-postgres-url

# Redis (for Celery)
REDIS_URL=redis://your-render-redis-url

# Facebook (Optional)
FACEBOOK_GRAPH_ACCESS_TOKEN=your-facebook-access-token

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 2.3 Database Setup

1. Create a PostgreSQL database on Render
2. Run migrations after first deploy:
   ```bash
   render run python manage.py migrate
   ```
3. Create superuser:
   ```bash
   render run python manage.py createsuperuser
   ```

---

## 🔧 Step 3: Facebook Integration Setup

### 3.1 Facebook Graph API (Optional but Recommended)

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or use existing one
3. Get your App Access Token
4. Set `FACEBOOK_GRAPH_ACCESS_TOKEN` in environment variables

### 3.2 Testing Facebook Verification

After deployment, test with a real Facebook group post:

1. Create a test task with `task_type = 'share'`
2. Submit a Facebook group post URL
3. Monitor Celery logs for verification progress
4. Check if earnings are credited automatically

---

## 📊 Step 4: Monitoring & Maintenance

### 4.1 Logs

- **Render Logs**: Check service logs in Render dashboard
- **Celery Logs**: Monitor background task processing
- **Django Logs**: Application errors and verification results

### 4.2 Performance

- **Redis**: Monitor queue length and processing times
- **Database**: Check query performance and connection pooling
- **Browser Automation**: Facebook verification may be slow (5-10 min per task)

### 4.3 Scaling

For high traffic:
- Increase Render service instances
- Use Redis cluster for better performance
- Consider using Selenium Grid for parallel browser automation

---

## 🐛 Troubleshooting

### Common Issues

**Playwright Installation Fails**
```bash
# Manual installation
pip install playwright
playwright install chromium
```

**Celery Connection Issues**
- Check REDIS_URL format
- Ensure Redis service is running
- Verify network connectivity between services

**Facebook Verification Fails**
- Check if Facebook URLs are accessible
- Verify Playwright browser installation
- Test with different Facebook group posts
- Check for anti-bot measures (may need proxy rotation)

**Database Connection Issues**
- Verify DATABASE_URL format
- Check Render PostgreSQL credentials
- Run migrations after database changes

---

## 🔒 Security Considerations

- Keep `DEBUG=False` in production
- Use strong `SECRET_KEY`
- Regularly rotate Facebook access tokens
- Monitor for suspicious verification patterns
- Implement rate limiting for task submissions

---

## 📞 Support

For issues:
1. Check Render service logs
2. Test locally with `python test_verification.py`
3. Review Django admin for failed verifications
4. Check Celery worker status

Happy deploying! 🎉

## 🌐 Step 2: Deploy to Heroku

### 2.1 Install Heroku CLI

Download from: https://devcenter.heroku.com/articles/heroku-cli

### 2.2 Login to Heroku

```bash
heroku login
```

### 2.3 Create Heroku App

```bash
heroku create your-app-name
```

### 2.4 Set Environment Variables

```bash
heroku config:set SECRET_KEY=your-secret-key-here
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
heroku config:set FACEBOOK_GRAPH_ACCESS_TOKEN=your-facebook-token  # Optional
heroku config:set EMAIL_HOST_USER=your-email@gmail.com
heroku config:set EMAIL_HOST_PASSWORD=your-email-password
heroku config:set DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 2.5 Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:hobby-dev
```

This sets `DATABASE_URL` automatically.

### 2.6 Deploy Code

```bash
git add .
git commit -m "Ready for deployment"
git push heroku main
```

### 2.7 Run Migrations on Heroku

```bash
heroku run python manage.py migrate
```

### 2.8 Create Superuser on Heroku

```bash
heroku run python manage.py createsuperuser
```

### 2.9 Open Your App

```bash
heroku open
```

---

## 🔧 Step 3: Post-Deployment Configuration

### 3.1 Media Files Handling

For file uploads (screenshots), Heroku's filesystem is ephemeral. Use:

- **Cloudinary** (recommended for images)
- **AWS S3**
- **Google Cloud Storage**

Example with Cloudinary:

1. Sign up at cloudinary.com
2. Install: `pip install cloudinary`
3. Add to settings.py:

```python
import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
)

# Use Cloudinary for media
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
```

4. Set Heroku config vars for Cloudinary.

### 3.2 OCR Setup

For screenshot verification, install Tesseract on your system:

- **Heroku**: Use buildpack
- **Local**: Install system package

Add to your app:

```bash
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-apt
```

Create `Aptfile`:

```
tesseract-ocr
tesseract-ocr-eng
```

### 3.3 Background Tasks

For async verification, use:

- **Heroku Scheduler** (free)
- **Redis + Celery** (paid add-on)

Example with Heroku Scheduler:

```bash
heroku addons:create scheduler:standard
```

Then set up scheduled tasks in Heroku dashboard.

---

## 🔒 Step 4: Security Checklist

- [ ] Change SECRET_KEY to a strong random string
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use HTTPS (Heroku provides free SSL)
- [ ] Set secure session cookies
- [ ] Validate all user inputs
- [ ] Rate limit API endpoints
- [ ] Monitor for suspicious activity

---

## 📊 Step 5: Monitoring & Maintenance

### 5.1 Logs

```bash
heroku logs --tail
```

### 5.2 Database Backup

```bash
heroku pg:backups:capture
heroku pg:backups:download
```

### 5.3 Performance

- Use Heroku's metrics dashboard
- Monitor response times
- Scale dynos if needed

### 5.4 Updates

```bash
git add .
git commit -m "Update"
git push heroku main
heroku run python manage.py migrate
```

---

## 💰 Step 6: Going Live

### 6.1 Custom Domain (Optional)

```bash
heroku domains:add www.yourdomain.com
```

Then configure DNS at your domain registrar.

### 6.2 SSL Certificate

Heroku provides automatic SSL for custom domains.

### 6.3 Final Testing

- Test all user flows
- Verify payments/wallet system
- Check mobile responsiveness
- Test file uploads

---

## 🆘 Troubleshooting

### Common Issues

**App crashes on startup:**
- Check logs: `heroku logs`
- Verify environment variables
- Ensure all dependencies are in requirements.txt

**Database connection fails:**
- Check DATABASE_URL config
- Run migrations: `heroku run python manage.py migrate`

**Static files not loading:**
- Run `python manage.py collectstatic`
- Ensure STATIC_ROOT is set

**OCR not working:**
- Verify Tesseract installation
- Check Pillow version compatibility

---

## 📈 Scaling

### Free Tier Limits
- 550 hours/month
- 1GB RAM
- 10k row database

### Paid Upgrades
- Hobby: $7/month (unlimited hours)
- Standard: $25/month (more RAM)
- Performance: $250/month (high performance)

### Database Scaling
- Hobby Dev: 10k rows free
- Hobby Basic: $9/month (10M rows)
- Standard: $50/month (unlimited)

---

## 🎯 Success Metrics

- User registration rate
- Task completion rate
- Verification accuracy
- Fraud detection rate
- Server response time
- Uptime percentage

---

**Last Updated:** 2024
**Platform:** Heroku
**Status:** Ready for Deployment 🚀