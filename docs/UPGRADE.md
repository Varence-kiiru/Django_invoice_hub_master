# Upgrade Guide

## Current Version Support

| Version | Release Date | Support Until | Status |
|---------|--------------|---------------|--------|
| 4.5.0   | 2026-04-07   | 2027-10-07    | **Current** |
| 4.x     | 2026-02-15   | 2027-08-15    | Supported |
| 3.x     | 2026-02-28   | 2026-08-28    | End of Life |
| 2.x     | 2026-02-15   | 2026-08-15    | End of Life |

---

## Upgrade Paths

### 3.0.0 → 4.5.0 (Recommended)

**Duration:** 30-60 minutes

**Breaking Changes:**
- Admin UI styling updated (no functional changes)
- Backup/restore system added (optional)
- API v2.1 fully compatible with v2.0

**Steps:**

1. **Backup Current System**
   ```bash
   # Database
   docker-compose exec db pg_dump -U invoice invoice > backup_3.0.0.sql

   # Media files
   tar -czf media_backup_3.0.0.tar.gz media/

   # Configuration
   cp .env .env.backup_3.0.0
   ```

2. **Pull Latest Code**
   ```bash
   git pull origin main
   git checkout v4.5.0  # Or use latest if continuous delivery
   ```

3. **Update Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Run Migrations**
   ```bash
   # List pending migrations
   python manage.py showmigrations

   # Apply migrations
   python manage.py migrate
   ```

5. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput --clear
   ```

6. **Restart Services**
   ```bash
   # Docker
   docker-compose up -d

   # or Systemd
   systemctl restart invoicing invoicing-worker
   ```

7. **Verify Upgrade**
   ```bash
   # Check admin interface loads
   curl http://localhost:8000/admin/ | head -20

   # Check API version
   curl http://localhost:8000/api/

   # Test invoice creation
   # Login at http://localhost:8000 and verify functionality
   ```

### 4.4.x → 4.5.0 (Minor Update)

**Duration:** 15-30 minutes

**What's New:**
- Backup & Restore system
- UI/UX styling improvements
- Performance optimizations
- Security enhancements

**Steps:**
```bash
# 1. Backup
docker-compose exec db pg_dump -U invoice invoice > backup_4.4.x.sql

# 2. Pull updates
git pull origin main

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Run migrations (usually none for patches)
python manage.py migrate

# 5. Restart
docker-compose restart
systemctl restart invoicing
```

---

## Pre-Upgrade Checklist

- [ ] Backup database and media files
- [ ] Backup `.env` configuration
- [ ] Test in staging environment first
- [ ] Schedule during low-traffic period
- [ ] Notify users of maintenance window
- [ ] Have rollback plan ready
- [ ] Verify disk space available (150% of DB size)
- [ ] Check database integrity: `python manage.py check`

---

## Database Migration Troubleshooting

### Migration Conflicts

**Error:** `Conflicting migrations detected`

**Solution:**
```bash
# Rollback to safe point
python manage.py migrate invoicing_app 0001_initial

# Then apply migrations
python manage.py migrate
```

### Timeout During Migration

**Error:** `Connection timeout during migration`

**Solution:**
```bash
# Increase timeout
python manage.py migrate --no-input --no-input

# Or migrate in batches
python manage.py migrate core
python manage.py migrate invoices
python manage.py migrate payments
```

### Out of Memory

**Error:** `MemoryError` during large migrations

**Solution:**
```bash
# Use batch processing
python manage.py migrate --batch-size 100

# Or run on larger machine temporarily
```

---

## Rollback Procedure

If upgrade fails or issues found:

### 1. Immediate Rollback (< 30 minutes)

```bash
# Restore database
docker-compose exec -T db psql -U invoice invoice < backup_3.0.0.sql

# Restore code
git checkout v3.0.0

# Restart services
docker-compose restart
```

### 2. Staged Rollback (> 30 minutes)

```bash
# 1. Revert code
git revert HEAD
git push origin main

# 2. Create database backup from corrupted state
pg_dump -U invoice invoice > corrupted_backup.sql

# 3. Restore from pre-upgrade backup
psql -U invoice invoice < backup_3.0.0.sql

# 4. Run migrations for original version
python manage.py migrate --app-label invoicing_app

# 5. Restart
systemctl restart invoicing invoicing-worker
```

### 3. Parallel Rollback (Zero Downtime)

```bash
# 1. Deploy v3.0.0 to new server
# 2. Update DNS/load balancer to point to v3.0.0
# 3. Monitor for errors
# 4. Decommission v4.5.0 server after stabilization
```

---

## Feature Migration Guide

### Backup & Restore System (v4.5.0 New)

**Enabled by Default**
- Access: Admin Dashboard → Backup & Restore
- Features: Automated daily backups, one-click restore
- Requirements: Redis running, Celery Beat active

**To Disable:**
```python
# settings.py
BACKUP_ENABLED = False
```

### Styling Updates (v4.5.0 New)

**Admin Pages Refreshed:**
- Consistent button styling
- Unified color scheme
- Dark mode support
- Mobile responsive

**What Changed:**
- Old: Custom inline styles
- New: CSS classes from bootstrap + variables
- Result: Cleaner, maintainable code (no functional changes)

**No Action Required** - changes are backward compatible

### API v2.1 Changes

**New Endpoints:**
- `GET /api/backup/` - List backups
- `POST /api/backup/` - Create backup
- `POST /api/backup/{id}/restore/` - Restore backup

**Deprecated (but still supported):**
- None in this release

**Subst:itutions:**
- Use new backup API instead of manual backups

---

## Version History

### v4.5.0 (2026-04-07)
- Backup & Restore system
- UI/UX improvements
- Security enhancements

### v4.4.0 (2026-03-15)
- Performance optimizations
- API improvements
- Bug fixes

### v4.0.0 (2026-03-01)
- Major UI redesign
- New dashboard
- Enhanced reporting

### v3.0.0 (2026-02-28)
- Analytics dashboard
- Data import tools
- Bulk operations

### v2.0.0 (2026-02-15)
- Initial production release

---

## Best Practices

### Upgrade Strategy

1. **Always Test in Staging First**
   ```bash
   # Create staging environment copy
   docker-compose -f docker-compose.staging.yml up -d
   git checkout latest
   python manage.py migrate
   # Test all features
   ```

2. **Schedule Maintenance Windows**
   - During low-traffic hours
   - Notify users in advance
   - Have support team on standby

3. **Monitor After Upgrade**
   ```bash
   tail -f logs/django.log
   tail -f logs/celery.log
   python manage.py check
   ```

4. **Document Changes**
   - Note version upgraded from/to
   - Record any modifications
   - Save rollback procedures

### Continuous Improvement

- Subscribe to security bulletins
- Apply patches as released
- Monitor GitHub issues for known problems
- Contribute feedback and improvements

---

## Automatic Upgrade (CI/CD)

For continuous deployment:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and push Docker image
        run: docker build -t invoicing:latest .
      - name: Deploy
        run: |
          docker-compose -f docker-compose.prod.yml up -d
          docker-compose exec web python manage.py migrate
          docker-compose exec web python manage.py collectstatic
```

---

## Support

- Database migration issues: See database documentation
- API compatibility questions: Check API docs
- Need help upgrading?: Contact hernandezngash@gmail.com

**Emergency Hotline:** Available for critical production issues
