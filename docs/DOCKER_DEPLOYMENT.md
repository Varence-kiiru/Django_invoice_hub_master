# Docker Deployment Guide

## Overview

InvoiceHub is fully containerized and can be deployed using Docker and Docker Compose. This guide covers both development and production deployments.

---

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum for containers
- Internet connection for pulling images

---

## Quick Start (Development)

### 1. Clone Repository
```bash
git clone https://github.com/Varence-kiiru/Django_invoice_hub_master.git
cd Django_invoice_hub_master
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Run Migrations
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 5. Access Application
- Web: http://localhost:8000
- Admin: http://localhost:8000/admin
- API: http://localhost:8000/api/

---

## Docker Architecture

### Services

**Web Service (Django)**
```dockerfile
FROM python:3.11-slim
- Framework: Django 4.2.28
- Server: Gunicorn
- Port: 8000
- Environment: Production-ready
```

**Database (PostgreSQL)**
```yaml
- Version: 15
- Database: invoice
- Port: 5432 (internal)
- Volume: postgres_data (persistent)
```

**Redis Cache & Message Broker**
```yaml
- Version: 7
- Port: 6379 (internal)
- Usage: Celery jobs, caching
```

**Celery Worker**
```yaml
- Task Queue: Celery 5.4.0
- Broker: Redis
- Functions: Background jobs, email, backups
```

**Celery Beat (Optional)**
```yaml
- Scheduler: django-celery-beat
- Functions: Recurring tasks, automated backups
```

---

## Docker Compose Configuration

### Development Setup (docker-compose.yml)

```yaml
version: '3.9'

services:
  # Django Web Application
  web:
    build: .
    env_file:
      - .env
    ports:
      - '8000:8000'
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: python manage.py runserver 0.0.0.0:8000

  # PostgreSQL Database
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: invoice
      POSTGRES_USER: invoice
      POSTGRES_PASSWORD: invoice
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - '5432:5432'

  # Redis Cache & Broker
  redis:
    image: redis:7
    restart: always
    ports:
      - '6379:6379'

  # Celery Worker
  worker:
    build: .
    env_file:
      - .env
    depends_on:
      - db
      - redis
    command: celery -A invoicing_app worker -l info

  # Celery Beat Scheduler
  beat:
    build: .
    env_file:
      - .env
    depends_on:
      - db
      - redis
    command: celery -A invoicing_app beat -l info

volumes:
  postgres_data:
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Expose port
EXPOSE 8000

# Start application
CMD ["gunicorn", "invoicing_app.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

## Production Deployment

### 1. Production Environment (.env)

```ini
# Django
DJANGO_SECRET_KEY=your-very-secret-key-change-this
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_SETTINGS_MODULE=invoicing_app.settings.production

# Database (Use managed PostgreSQL for production)
DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/invoicing

# Redis (Use managed Redis for production)
REDIS_URL=redis://prod-redis.example.com:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.xxxxx
EMAIL_USE_TLS=True

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# Stripe (if using)
STRIPE_API_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

### 2. Production Docker Compose (docker-compose.prod.yml)

```yaml
version: '3.9'

services:
  web:
    build: .
    restart: always
    env_file:
      - .env
    ports:
      - '8000:8000'
    depends_on:
      - redis
    command: >
      gunicorn invoicing_app.wsgi:application
      --workers 4
      --bind 0.0.0.0:8000
      --timeout 120

  worker:
    build: .
    restart: always
    env_file:
      - .env
    depends_on:
      - redis
    command: celery -A invoicing_app worker -l info -c 2

  beat:
    build: .
    restart: always
    env_file:
      - .env
    depends_on:
      - redis
    command: celery -A invoicing_app beat -l info

  redis:
    image: redis:7-alpine
    restart: always
    ports:
      - '6379:6379'
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### 3. Reverse Proxy (NGINX)

```nginx
upstream invoicing {
    server web:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    client_max_body_size 50M;

    location / {
        proxy_pass http://invoicing;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/static/;
        expires 30d;
    }

    location /media/ {
        alias /app/media/;
        expires 7d;
    }
}
```

---

## Common Commands

### Start/Stop Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f beat
```

### Database Operations
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access database shell
docker-compose exec db psql -U invoice -d invoicing
```

### Backup & Restore
```bash
# Backup database
docker-compose exec db pg_dump -U invoice invoicing > backup.sql

# Restore database
docker-compose exec -T db psql -U invoice invoicing < backup.sql

# Backup media files
docker cp $(docker-compose ps -q web):/app/media ./media_backup
```

### Scaling
```bash
# Scale Celery workers
docker-compose up -d --scale worker=3

# Scale web servers (with load balancer)
docker-compose up -d --scale web=2
```

---

## Monitoring

### Health Checks
```bash
# Check web service health
curl http://localhost:8000/health/

# Check Redis connection
docker-compose exec redis redis-cli ping

# Check database connection
docker-compose exec db psql -U invoice -c "SELECT 1"
```

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f worker

# Export logs
docker-compose logs > all_logs.txt
```

---

## Troubleshooting

### Containers Won't Start
```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose build --no-cache

# Remove volumes and restart (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

### Database Connection Failed
```bash
# Verify database is ready
docker-compose exec db pg_isready -U invoice

# Check database URL in .env
# Format: postgresql://user:password@db:5432/invoicing
```

### Out of Memory
```bash
# Increase Docker resources
# Docker Desktop → Settings → Resources → Memory: 8GB
```

### Persistent Data Loss
```bash
# Always use named volumes for databases
volumes:
  - postgres_data:/var/lib/postgresql/data

# Backup volumes
docker run --rm -v postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz -C /data .
```

---

## Security Best Practices

1. **Secrets Management**
   - Never commit `.env` to version control
   - Use Docker secrets or external secret managers (AWS Secrets, HashiCorp Vault)

2. **Image Security**
   - Use specific version tags (not `latest`)
   - Scan images: `docker scan invoicing:latest`

3. **Network Security**
   - Use internal networks for inter-service communication
   - Only expose necessary ports

4. **Database Security**
   - Change default PostgreSQL credentials
   - Use strong passwords
   - Enable SSL for remote connections

5. **Backup Strategy**
   - Automate daily database backups
   - Store backups off-site
   - Test restore procedures regularly

---

## Support

- [INSTALLATION.md](INSTALLATION.md) - Manual installation
- [MAINTENANCE.md](MAINTENANCE.md) - Operational procedures
- [SECURITY.md](SECURITY.md) - Security guidelines
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate
CMD ["gunicorn", "invoicing_app.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## docker-compose.yml (root)
```yaml
version: '3.9'
services:
  web:
    build: .
    env_file:
      - .env
    ports:
      - '8000:8000'
    depends_on:
      - db
      - redis
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: invoice
      POSTGRES_USER: invoice
      POSTGRES_PASSWORD: invoice
    volumes:
      - postgres_data:/var/lib/postgresql/data
  redis:
    image: redis:7
  worker:
    build: .
    command: celery -A invoicing_app worker -l info
    env_file:
      - .env
    depends_on:
      - redis
      - db
volumes:
  postgres_data:
```

## Run
```
docker compose up -d --build
```

## Secrets + Environment
- Keep `.env` outside git
- Set `DJANGO_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `EMAIL_*`, `STRIPE_*`
