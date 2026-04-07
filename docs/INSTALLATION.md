# Installation Guide

## Requirements

- **Python:** 3.11+
- **Database:** PostgreSQL 12+ (recommended), MySQL 5.7+, or SQLite (development only)
- **Redis:** 7.0+ (required for Celery task queue)
- **Node.js:** Optional (for frontend asset building)
- **Docker:** Recommended for production deployments

## System Requirements

### Minimum (Development)
- RAM: 2 GB
- CPU: 2 cores
- Storage: 5 GB

### Recommended (Production)
- RAM: 8 GB
- CPU: 4 cores
- Storage: 50 GB+ (depends on backup frequency)

---

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/Varence-kiiru/Django_invoice_hub_master.git
cd Django_invoice_hub_master
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/invoicing
# OR for MySQL:
DATABASE_URL=mysql://user:password@localhost:3306/invoicing

# Redis (required for Celery)
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Payment Gateway (Optional)
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Application
APP_NAME=InvoiceHub
COMPANY_EMAIL=hernandezngash@gmail.com
```

### 5. Setup Database

```bash
# Create database (PostgreSQL example)
createdb invoicing

# Or use MySQL:
mysql -u root -p -e "CREATE DATABASE invoicing CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 6. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 7. Create Initial Organization (Optional)
```bash
python manage.py shell
```

```python
from invoicing_app.organizations.models import Organization
org = Organization.objects.create(
    name="Default Organization",
    email="admin@company.com",
    status="active"
)
print(org.id)
exit()
```

### 8. Start Services

**Terminal 1 - Django Development Server:**
```bash
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
celery -A invoicing_app worker -l info
```

**Terminal 3 - Celery Beat (Scheduler):**
```bash
celery -A invoicing_app beat -l info
```

Visit: `http://localhost:8000/admin`

---

## Production Setup

### Using Docker (Recommended)

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

### Using Gunicorn + NGINX

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Create systemd service (`/etc/systemd/system/invoicing.service`):
```ini
[Unit]
Description=InvoiceHub Django Application
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/invoicing
ExecStart=/var/www/invoicing/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/gunicorn.sock \
    invoicing_app.wsgi:application

[Install]
WantedBy=multi-user.target
```

3. Create Celery service:
```ini
[Unit]
Description=InvoiceHub Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
WorkingDirectory=/var/www/invoicing
ExecStart=/var/www/invoicing/venv/bin/celery -A invoicing_app worker -l info
```

4. Configure NGINX:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /var/www/invoicing/static/;
    }

    location /media/ {
        alias /var/www/invoicing/media/;
    }
}
```

---

## Post-Installation

### 1. Configure Email
- Set valid SMTP credentials in `.env`
- Test: `python manage.py shell` → `from django.core.mail import send_mail` → `send_mail(...)`

### 2. Configure Backups
- Set backup location permissions: `chmod 755 backups/`
- Enable automated backups via Celery Beat
- Configure backup retention policy

### 3. Security Setup
- Enable HTTPS/SSL (Let's Encrypt recommended)
- Configure CSRF and CORS settings
- Set `DEBUG=False` in production
- Rotate `DJANGO_SECRET_KEY`

### 4. Test Critical Paths
- Login and user management
- Create and send invoice
- Record payment
- Generate reports
- Test backup/restore

---

## Troubleshooting

### Database Connection Errors
```
Error: could not translate host name "localhost" to address
```
- Verify database is running: `psql -U user -d invoicing -c "SELECT 1"`
- Check DATABASE_URL format in `.env`

### Redis Connection Errors
```
Error connecting to Redis
```
- Verify Redis is running: `redis-cli ping`
- Check REDIS_URL in `.env`
- Default: `redis://localhost:6379/0`

### Migration Errors
```
python manage.py migrate --fake-initial
```

### Static Files 404
```bash
python manage.py collectstatic --clear --noinput
```

### Email Not Sending
- Check SMTP credentials in `.env`
- Verify EMAIL_USE_TLS setting
- Check firewall/port 587 access
- Review Django logs for errors

---

## Support

For issues or questions:
- Check [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for containerized deployment
- See [MAINTENANCE.md](MAINTENANCE.md) for operational guidance
- Review [SECURITY.md](SECURITY.md) for security best practices
- Consult [UPGRADE.md](UPGRADE.md) for version updates
