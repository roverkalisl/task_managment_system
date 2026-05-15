# 🔥 FB Task Platform

An AI-powered, automated social media task verification platform built with Django.

## 🚀 Features

- **Facebook Group Share Verification**: Automated verification of Facebook group posts using browser automation
- **Multi-Level AI Verification**: 3-tier verification system with OCR and fraud detection
- **Smart Fraud Detection**: User trust scoring, duplicate detection, and pattern analysis
- **Automated Approval**: High-confidence submissions approved instantly with earnings credited
- **Background Processing**: Celery + Redis for asynchronous verification (5-10 min processing)
- **Admin Dashboard**: Full management interface for tasks and users
- **Wallet System**: Built-in earning and withdrawal management
- **Facebook Integration**: Graph API validation with Playwright browser automation

## 🛠️ Tech Stack

- **Backend**: Django 5.2, Django REST Framework
- **Database**: PostgreSQL (production), SQLite (development)
- **AI/ML**: OCR (Tesseract), Image Recognition, Browser Automation
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Task Queue**: Celery + Redis
- **Browser Automation**: Playwright
- **Deployment**: Render/Heroku-ready with Docker support

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL (optional, SQLite for dev)
- Redis (for background tasks)
- Tesseract OCR (for screenshot verification)
- Playwright browsers (installed automatically)

## 🏃‍♂️ Quick Start

1. **Clone & Setup**
   ```bash
   git clone <your-repo>
   cd fbtask_platform
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   playwright install  # Install browser binaries
   ```

2. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Environment Variables**
   ```bash
   # Create .env file
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
   REDIS_URL=redis://localhost:6379/0
   FACEBOOK_GRAPH_ACCESS_TOKEN=your-facebook-token  # Optional
   ```

4. **Run Services**
   ```bash
   # Terminal 1: Redis server
   redis-server

   # Terminal 2: Celery worker
   celery -A config worker --loglevel=info

   # Terminal 3: Django server
   python manage.py runserver
   ```

5. **Access**
   - **Platform**: http://localhost:8000
   - **Admin**: http://localhost:8000/admin

## 🔧 Facebook Verification System

### How It Works

1. **User Flow**:
   - User selects Facebook share task
   - Shares post to Facebook group
   - Submits group post URL
   - System verifies automatically (5-10 minutes)

2. **Verification Checks**:
   - ✅ Valid Facebook group post URL
   - ✅ Posted to Facebook Group (not profile/page)
   - ✅ Original task content included in share
   - ✅ Post exists and is accessible
   - ✅ No duplicate submissions
   - ✅ No fake/manipulated links

3. **Auto Actions**:
   - **Approved**: Credit earnings, mark task complete
   - **Rejected**: Clear rejection reason
   - **Manual Review**: Suspicious cases for admin review

### Testing

```bash
# Run verification tests
python test_verification.py

# Run full Facebook verification test (requires internet)
python test_verification.py --full
```

## 🚀 Deployment

### Render.com Deployment

1. **Connect Repository**
   - Link your GitHub repo to Render
   - Set build command: `pip install -r requirements.txt && playwright install`
   - Set start command: `gunicorn config.wsgi:application`

2. **Environment Variables**
   ```bash
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-app-name.onrender.com
   REDIS_URL=redis://your-redis-url
   DATABASE_URL=postgresql://your-db-url
   FACEBOOK_GRAPH_ACCESS_TOKEN=your-token
   ```

3. **Redis Setup**
   - Use Render Redis or external Redis service
   - Set REDIS_URL in environment

4. **Background Workers**
   - Use Render Cron Jobs or separate service for Celery
   - Command: `celery -A config worker --loglevel=info`

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
playwright install

# Setup database
python manage.py migrate

# Run Redis (if not installed, use Docker)
docker run -d -p 6379:6379 redis:alpine

# Run Celery worker
celery -A config worker --loglevel=info

# Run Django
python manage.py runserver
```

## 📊 API Endpoints

- `GET /api/tasks/` - List available tasks
- `POST /api/submit/` - Submit task completion
- `GET /wallet/balance/` - Check earnings balance
- `POST /wallet/withdraw/` - Request withdrawal

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## 📝 License

MIT License - see LICENSE file for details
   - App: http://127.0.0.1:8000
   - Admin: http://127.0.0.1:8000/admin/

## 📁 Project Structure

```
fbtask_platform/
├── accounts/          # User management & trust scoring
├── task/             # Task creation & submission
├── wallet/           # Payment & transaction system
├── verification/     # AI verification engine
├── api/              # REST API endpoints
├── templates/        # HTML templates
├── static/           # CSS, JS, images
├── config/           # Django settings & URLs
└── media/            # User uploaded files
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Key variables:
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `FACEBOOK_GRAPH_ACCESS_TOKEN`: For Facebook API validation
- `EMAIL_*`: SMTP configuration

### Facebook Graph API (Optional)

1. Create Facebook App at https://developers.facebook.com
2. Get Page Access Token
3. Set `FACEBOOK_GRAPH_ACCESS_TOKEN` environment variable

## 🚀 Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

### Quick Heroku Deploy

```bash
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

## 📚 Documentation

- [System Architecture](VERIFICATION_SYSTEM_ARCHITECTURE.md)
- [Implementation Guide](IMPLEMENTATION_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)

## 🔐 Security

- Custom user model with unique phone/member_id
- CSRF protection on all forms
- Secure session management
- Input validation and sanitization
- Rate limiting on sensitive endpoints

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or issues:
- Check the documentation
- Open an issue on GitHub
- Contact the development team

---

**Built with ❤️ for automated social media task verification**