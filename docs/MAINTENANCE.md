# Maintenance & Operations Guide

## Overview

This guide covers operational procedures for running InvoiceHub v4.5.0 in production, including monitoring, backups, updates, and troubleshooting.

---

## Service Management

### Starting Services

**Docker:**
```bash
docker-compose up -d
```

**Manual (Linux/systemd):**
```bash
systemctl start invoicing
systemctl start invoicing-worker
systemctl start invoicing-beat
```

### Stopping Services
```bash
docker-compose down
# OR
systemctl stop invoicing invoicing-worker invoicing-beat
```

### Checking Service Status
```bash
# Docker
docker-compose ps

# Systemd
systemctl status invoicing
systemctl status invoicing-worker
systemctl status invoicing-beat
```

---

## Monitoring

### Application Health

**Health Check Endpoint:**
```bash
curl http://localhost:8000/health/
```

**Response:**
```json
{
  "status": "healthy",
  "version": "4.5.0",
  "database": "connected",
  "redis": "connected"
}
```

### Performance Monitoring

**Check Response Times:**
```bash
# Use New Relic, DataDog, or Sentry
# Configured via settings

# Quick check with curl
time curl http://localhost:8000/api/invoices/
```

### Error Tracking

**Sentry Configuration (.env):**
```ini
SENTRY_DSN=https://key@sentry.io/project-id
```

**View Errors:**
- Dashboard: http://your-domain:8000/admin/
- Sentry: https://sentry.io/organizations/...

### Log Monitoring

**Django Logs:**
```bash
tail -f logs/django.log
tail -f logs/celery.log
tail -f logs/nginx.log
```

**Filter by Level:**
```bash
tail -f logs/django.log | grep ERROR
tail -f logs/django.log | grep WARNING
```

---

## Backup & Restore

### Automated Backups (Recommended)

InvoiceHub includes automated backup system accessible via Admin Dashboard:

**Location:** `/admin/backup-restore/`

**Features:**
- Daily automated backups (default: 2:00 AM)
- Database-only or full system backups
- 30-day retention auto-cleanup
- One-click restore from Admin UI

**Configuration:**
1. Ensure Redis is running
2. Start Celery Beat: `celery -A invoicing_app beat`
3. Configure backup location (must be writable)
4. Backups stored in: `backups/`

### Manual Database Backup

**PostgreSQL:**
```bash
pg_dump -U invoice -h localhost invoice > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed
pg_dump -U invoice -h localhost invoice | gzip > backup_$(date +%Y%m%d).sql.gz
```

**MySQL:**
```bash
mysqldump -u root -p invoicing > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed
mysqldump -u root -p invoicing | gzip > backup_$(date +%Y%m%d).sql.gz
```

**Docker:**
```bash
docker-compose exec db pg_dump -U invoice invoice > backup.sql
```

### Media Files Backup

```bash
# Archive media folder
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Alternative: Rsync to remote
rsync -avr media/ user@backup-server:/backups/media/
```

### Full System Backup

```bash
# Backup both database and media
tar -czf full_backup_$(date +%Y%m%d).tar.gz \
  backup_latest.sql \
  media/ \
  .env

# Encrypt (optional)
gpg -c full_backup_*.tar.gz
```

### Restore Database

**From SQL file:**
```bash
# PostgreSQL
psql -U invoice -h localhost invoice < backup.sql

# MySQL
mysql -u root -p invoicing < backup.sql
```

**Docker:**
```bash
docker-compose exec -T db psql -U invoice invoice < backup.sql
```

**Using Admin Interface:**
1. Login: http://your-domain/admin/
2. Navigate: Backup & Restore
3. Click: Restore from File
4. Upload: backup.sql or .zip file
5. Confirm: Read warnings and proceed

### Restore Media Files

```bash
# Extract media backup
tar -xzf media_backup_*.tar.gz

# Or from Docker volume
docker cp media_backup.tar.gz container-id:/tmp/
docker-compose exec web tar -xzf /tmp/media_backup.tar.gz
```

---

## Database Maintenance

### Optimize Indexes

**PostgreSQL:**
```bash
VACUUM FULL;
REINDEX DATABASE invoice;
```

**MySQL:**
```sql
OPTIMIZE TABLE invoices, payments, clients, quotations;
ANALYZE TABLE invoices, payments, clients, quotations;
```

### Clear Old Data

**Delete Invoices Older Than 2 Years:**
```bash
python manage.py shell

from datetime import timedelta
from django.utils import timezone
from invoicing_app.invoices.models import Invoice

cutoff_date = timezone.now() - timedelta(days=730)
Invoice.objects.filter(created_at__lt=cutoff_date, status='archived').delete()
```

**Clear Celery Tasks:**
```bash
# Clear expired tasks
celery -A invoicing_app purge

# Clear Redis cache
redis-cli FLUSHDB
```

### Database Size

**PostgreSQL:**
```sql
SELECT datname, pg_size_pretty(pg_database_size(datname))
FROM pg_database WHERE datname = 'invoice';

SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables LIMIT 20;
```

**MySQL:**
```sql
SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.TABLES
WHERE table_schema = 'invoicing'
ORDER BY size_mb DESC;
```

---

## Performance Tuning

### Database Connection Pool

**settings.py:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### Cache Configuration

**Redis Cache:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50}
        }
    }
}
```

### Gunicorn Workers

**Recommended Formula:** (2 × CPU Cores) + 1

```bash
# Single CPU: 3 workers
gunicorn --workers 3 invoicing_app.wsgi:application

# Quad CPU: 9 workers
gunicorn --workers 9 invoicing_app.wsgi:application
```

### Celery Worker Concurrency

```bash
# Default: 1 process x (2 × CPU cores) threads
celery -A invoicing_app worker -c 4

# Or use multiprocessing
celery -A invoicing_app worker --pool=prefork -c 4
```

---

## Support & SLA

### Support Tiers

**Standard Support**
- Email response: 3 business days
- Bugfix SLA: 7 days for non-critical
- Updates: Monthly security patches

**Priority Support**
- Email response: 24 hours
- Bugfix SLA: 2 business days
- Updates: Weekly patches available

**Enterprise Support**
- Response: 4 hours
- On-call escalation available
- Dedicated support contact
- Custom SLA

### Reporting Issues

**Issue Template:**
```
Title: [BUG|FEATURE|QUESTION] Brief Description
Severity: [Critical|High|Medium|Low]
Version: 4.5.0
Environment: Docker/Manual/Other

Steps to reproduce:
1.
2.

Expected behavior:
Actual behavior:

Logs/Error messages:
```

**Channels:**
- GitHub Issues: https://github.com/your-org/invoicing/issues
- Email: hernandezngash@gmail.com
- Security Issues: security@invoicing-app.com

---

## Patch & Update Process

### Security Patches

**Critical (0-day):**
- Fixed within 24 hours
- Mandatory update recommended

**High Priority:**
- Fixed within 72 hours
- Update within 30 days recommended

**Normal:**
- Fixed in next release cycle
- Standard update timeline

### Applying Security Patches

```bash
# 1. Backup
docker-compose exec web python manage.py dumpdata > backup_pre_update.json

# 2. Pull latest
git pull origin main

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Run migrations
python manage.py migrate

# 5. Collect static
python manage.py collectstatic --noinput

# 6. Restart services
systemctl restart invoicing
systemctl restart invoicing-worker
```

### Update Timeline

**Recommended Update Windows:**
- Security patches: 24-48 hours
- Bug fixes: 1-2 weeks
- Features: 1-4 weeks
- Major versions: After testing in staging

---

## Disaster Recovery

### Recovery Time Objectives (RTO)

- Database failure: < 1 hour
- Application crash: < 15 minutes
- Backup corruption: < 4 hours

### Recovery Point Objectives (RPO)

- Automatic backups: < 24 hours
- Hourly snapshots: Optional (paid add-on)
- Real-time replication: Enterprise only

### Failover Procedure

1. **Detect Issue:**
   - Health check fails
   - Monitor alerts triggered

2. **Immediate Actions:**
   - Check logs for errors
   - Verify database connectivity
   - Check disk space

3. **Database Recovery:**
   - Restore from latest backup
   - Verify data integrity
   - Test write operations

4. **Application Recovery:**
   - Restart Django service
   - Verify worker processes
   - Test user login

5. **Restore Media Files:**
   - Restore from backup
   - Verify media links

---

## Capacity Planning

### Storage Estimation

**Monthly Growth:**
- Invoices: ~100 MB / 10,000 documents
- Media (PDFs, logos): ~50 GB / year
- Database backups: ~200 MB / backup × 30 days

**Year 1 Total:** ~50-100 GB

### RAM Requirements

- < 50,000 invoices: 4 GB
- < 500,000 invoices: 8 GB
- > 500,000 invoices: 16+ GB

### CPU Requirements

- Light usage: 2 cores
- Medium usage: 4 cores
- Heavy usage: 8+ cores

---

## Support

For operational support:
- Documentation: See related guides
- Troubleshooting: Check [SECURITY.md](SECURITY.md)
- Deployment: See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- Updates: See [UPGRADE.md](UPGRADE.md)
