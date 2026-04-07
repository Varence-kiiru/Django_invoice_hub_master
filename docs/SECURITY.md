# Security & Compliance Guide

## Overview

InvoiceHub is designed with security and compliance as core principles. This document outlines security practices, compliance standards, and threat mitigation strategies for v4.5.0.

---

## Security Standards & Compliance

### Standards & Regulations
- **GDPR:** European data protection regulation
- **PCI DSS:** Payment Card Industry Data Security Standard (when integrating payment gateways)
- **SOC 2:** System and Organization Controls framework
- **ISO 27001:** Information security management
- **OWASP:** Application security best practices

### Applicable Laws
- GDPR (EU/UK): Personal data handling
- HIPAA (US): Healthcare data (if applicable)
- CCPA (California): Privacy rights
- Local tax regulations: Invoice retention

---

## Application Security

### 1. Authentication & Authorization

**Password Policies:**
- Minimum 8 characters (14+ recommended)
- Complexity requirement: uppercase, lowercase, numbers, symbols
- No reuse of last 5 passwords
- Automatic expiration: 90 days
- Lock after 5 failed attempts: 30 minutes

**Multi-Factor Authentication (MFA):**
- TOTP support (Google Authenticator, Authy)
- SMS backup (optional)
- Recovery codes for account restoration

**Session Management:**
- Timeout: 60 minutes of inactivity
- HTTPS-only cookies
- CSRF token on all state-changing operations
- Session rotation on login

### 2. API Security

**Authentication:**
```python
# DRF Token Authentication
Authorization: Token abc123xyz789

# Or JWT (recommended for modern apps)
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Rate Limiting:**
```python
# 1000 requests per hour per user
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/hour'
    }
}
```

**CORS Configuration (.env):**
```ini
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CORS_ALLOW_CREDENTIALS=True
```

### 3. Data Protection

**Encryption at Rest:**
```python
# Sensitive fields encrypted using cryptography.fernet
from invoicing_app.core.models import EncryptedTextField

class Client(models.Model):
    tax_id = EncryptedTextField()  # Encrypted in database
    phone_number = EncryptedTextField()
```

**Encryption in Transit:**
- HTTPS/TLS 1.2+ required
- HSTS enabled: `Strict-Transport-Security: max-age=31536000`
- Certificate pinning (enterprise)

**Sensitive Data Handling:**
- Never log passwords, API keys, tokens
- Mask PII in logs
- Secure deletion: Overwrite disk 3 times
- No cleartext storage of payment info

### 4. CSRF Protection

**Enabled by Default:**
```html
<!-- Required in all POST forms -->
{% csrf_token %}
```

**API Endpoints:**
```python
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def process_payment(request):
    pass
```

### 5. XSS Prevention

**Template Auto-Escaping:**
```django
<!-- Auto-escaped -->
{{ user_input }}

<!-- Safe HTML only -->
{{ safe_html|safe }}
```

**Content Security Policy:**
```python
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "cdn.example.com"],
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", "data:", "https:"],
}
```

### 6. SQL Injection Prevention

**Django ORM Parameterized Queries:**
```python
# SAFE - parameterized
Invoice.objects.filter(invoice_number=user_input)

# UNSAFE - raw SQL (don't use!)
Invoice.objects.raw(f"SELECT * WHERE id = {user_id}")
```

### 7. File Upload Security

**Restrictions:**
```python
ALLOWED_UPLOAD_TYPES = ['image/jpeg', 'image/png', 'application/pdf']
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

# File type validation: Check MIME type, not extension
import magic
file_type = magic.from_buffer(file.read(), mime=True)
```

**Storage:**
- Files stored outside web root
- Randomized filenames (UUID)
- Virus scanning (optional)

---

## Infrastructure Security

### 1. Network Security

**Firewall Rules:**
- Allow: HTTPS (443), HTTP→HTTPS redirect (80)
- Allow: SSH (22) from office IPs only
- Allow: Database port (5432/3306) from app server only
- Block: All other inbound

**DDoS Protection:**
- Rate limiting at application level
- WAF (ModSecurity, CloudFlare)
- Load balancing with connection limits

### 2. Server Hardening

**SSH Configuration (/etc/ssh/sshd_config):**
```
Port 2222                          # Non-standard port
PermitRootLogin no                 # Disable root login
PasswordAuthentication no           # SSH keys only
X11Forwarding no                   # Disable X11
MaxAuthTries 3                     # Limit login attempts
MaxSessions 5                      # Limit concurrent sessions
```

**Fail2Ban (Intrusion Prevention):**
```bash
# Auto-ban after 5 failed logins
apt install fail2ban

[sshd]
enabled = true
maxretry = 5
findtime = 3600
bantime = 86400
```

### 3. Database Security

**PostgreSQL:**
```sql
-- Restrict user permissions
CREATE ROLE invoicing_user WITH LOGIN PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE invoicing TO invoicing_user;
GRANT CREATE ON SCHEMA public TO invoicing_user;

-- Audit sensitive operations
CREATE AUDIT TABLE for important records;
```

**Connection SSL:**
```
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/postgresql/server.crt'
ssl_key_file = '/etc/postgresql/server.key'
```

**Backups Encryption:**
```bash
# Encrypt database backup
gpg --encrypt --recipient your@email.com backup.sql

# Encrypt with password
gpg -c backup.sql
```

### 4. Secrets Management

**Never Commit Secrets:**
```bash
# .gitignore
.env
*.key
*.pem
secrets/
```

**Use Environment Variables:**
```python
import os
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
```

**Or External Secrets Manager:**
```bash
# HashiCorp Vault
vault kv get secret/invoicing/db

# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id invoicing/db
```

**Scan for Secrets:**
```bash
# Pre-commit hook
pip install detect-secrets
detect-secrets scan

# or git-secrets
brew install git-secrets
git secrets --install
```

### 5. Access Control

**Role-Based Access Control (RBAC):**
- Admin: Full system access
- Accountant: Invoices, payments, reports
- Manager: Clients, invoices (read-only)
- User: Own invoices only

**Audit Logging:**
```python
# All changes logged
from invoicing_app.audit.models import AuditLog

AuditLog.objects.create(
    user=request.user,
    action='DELETE_INVOICE',
    object_id=invoice.id,
    timestamp=timezone.now()
)
```

---

## Operational Security

### 1. Monitoring & Alerting

**Real-time Alerts for:**
- Failed login attempts (>5 per hour)
- Unauthorized API access
- Database query errors
- Out-of-memory conditions
- High CPU usage (>80%)
- Disk usage (>90%)

**Tools:**
- Sentry for error tracking
- New Relic/DataDog for APM
- ELK Stack for log aggregation
- Prometheus for metrics

### 2. Incident Response

**Incident Classification:**
- **Critical:** System down, data breach, payment processing down
- **High:** Unauthorized access, data loss
- **Medium:** Performance degradation
- **Low:** Minor bugs, cosmetic issues

**Response Timeline:**
- Critical: < 15 minutes
- High: < 1 hour
- Medium: < 4 hours
- Low: < 24 hours

**Incident Checklist:**
1. Identify and contain
2. Log incident details
3. Isolate affected systems
4. Notify stakeholders
5. Restore service
6. Post-mortem analysis

### 3. Patch Management

**Security Updates:**
- Monitor Django, DRF, dependencies for vulnerabilities
- Subscribe: https://pypi.org/project/pip-audit/
- Test patches in staging before production
- Apply critical patches within 24-48 hours

```bash
# Check for vulnerable dependencies
pip-audit

# Check Django security advisories
python manage.py check --deploy
```

### 4. Backup Security

**Backup Practices:**
- Encrypted backups: `gpg -c backup.sql`
- Off-site storage: AWS S3, Azure Blob (encrypted)
- Immutable backups: Object lock, WORM
- Regular restore tests
- Deletion protection enabled

**Backup Audit Trail:**
```sql
SELECT backup_date, file_name, size_mb, created_by
FROM backups_log
ORDER BY  backup_date DESC;
```

---

## GDPR Compliance

### Data Rights

**Right to Access:**
- Users can export their data
- API endpoint: `GET /api/users/me/data-export/`

**Right to be Forgotten:**
- Account deletion removes personal data
- Transaction data retained for 7 years (tax requirement)
- Endpoint: `DELETE /api/users/me/`

**Right to Rectification:**
- Users can update their profile
- Change history logged

**Right to Data Portability:**
- Export data in CSV/JSON format
- Endpoint:`GET /api/users/me/data-export/?format=json`

### Data Processing Agreement (if applicable)

- Processor agreement with cloud providers
- Sub-processor list maintained
- Data Processing Addendum (DPA) available

---

## PCI DSS Compliance (Payment Processing)

### Payment Card Restrictions

**Never Store:**
- Full card numbers
- Magnetic stripe data
- CVC/CVV codes
- PIN numbers

**Always Use:**
- Tokenized payments (Stripe, PayPal)
- PCI-compliant payment gateway
- 3D Secure (Verified by Visa, Mastercard SecureCode)

**Example - Stripe:**
```python
# Safe - never handle card data directly
import stripe
stripe.api_key = os.getenv('STRIPE_API_KEY')

payment_intent = stripe.PaymentIntent.create(
    amount=10000,
    currency='usd',
    payment_method=payment_method_id
)
```

---

## Security Checklist

**Before Production Deployment:**

```
Security
- [ ] HTTPS/TLS enabled
- [ ] SSL certificate valid (not self-signed)
- [ ] HSTS enabled
- [ ] DEBUG = False
- [ ] SECRET_KEY changed and strong
- [ ] ALLOWED_HOSTS configured

Authentication
- [ ] Password policy enforced
- [ ] MFA available (optional)
- [ ] Session timeout configured
- [ ] CSRF protection enabled

Database
- [ ] Database user has minimal permissions
- [ ] Connections encrypted (SSL)
- [ ] Backups encrypted
- [ ] Backup tested

API Security
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] API authentication required
- [ ] Request validation enabled

Monitoring
- [ ] Error tracking (Sentry) configured
- [ ] Logs centralized
- [ ] Alerts configured
- [ ] Health checks active

Compliance
- [ ] Privacy policy published
- [ ] Terms of service accepted
- [ ] Data retention policy defined
- [ ] Audit logging enabled
```

---

## Reporting Security Issues

**IMPORTANT:** Do NOT create public GitHub issues for security vulnerabilities.

**Report to:** security@invoicing-app.com

**Include:**
- Vulnerability description
- Affected component/version
- Steps to reproduce
- Impact assessment
- Suggested fix (if any)

**Response:**
- Acknowledgment within 24 hours
- Update within 72 hours
- Public disclosure after patch release

---

## Support

- See [MAINTENANCE.md](MAINTENANCE.md) for operational security
- Contact security team for compliance questions
- Review [INSTALLATION.md](INSTALLATION.md) for setup security
