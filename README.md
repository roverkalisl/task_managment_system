# 🔥 FB Task Platform

An AI-powered, automated social media task verification platform built with Django.

## 🚀 Features

- **Multi-Level AI Verification**: 3-tier verification system with OCR and fraud detection
- **Smart Fraud Detection**: User trust scoring and pattern analysis
- **Automated Approval**: High-confidence submissions approved instantly
- **Admin Dashboard**: Full management interface for tasks and users
- **Wallet System**: Built-in earning and withdrawal management
- **Facebook Integration**: Graph API validation for posts and shares

## 🛠️ Tech Stack

- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL (production), SQLite (development)
- **AI/ML**: OCR (Tesseract), Image Recognition
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Deployment**: Heroku-ready with Docker support

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL (optional, SQLite for dev)
- Tesseract OCR (for screenshot verification)

## 🏃‍♂️ Quick Start

1. **Clone & Setup**
   ```bash
   git clone <your-repo>
   cd fbtask_platform
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

4. **Access**
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