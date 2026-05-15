# 🚀 Deployment Guide - FB Task Platform

## 📋 Prerequisites

- Git account
- Heroku account (free tier available)
- Domain name (optional)

---

## 🛠️ Step 1: Prepare Your Code

### 1.1 Install Dependencies

```bash
pip install -r requirements.txt
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

### 1.5 Test Locally

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` and test:
- User registration
- Task creation (as admin)
- Task submission
- Verification process

---

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