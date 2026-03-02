# Security Policy

## Reporting Security Vulnerabilities

**Please do not open public issues for security vulnerabilities.**

If you discover a security vulnerability in InvoiceHub, please email security@yourdomain.com with:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Your name and contact information (optional)

We will:
- Acknowledge receipt within 48 hours
- Work on a fix immediately
- Keep you informed of progress
- Credit you in the security advisory (if desired)

## Current Security Status

**Version:** 3.0.0  
**Last Security Audit:** February 28, 2026  
**Status:** Production Ready ✅

### Security Features Implemented
- ✅ CSRF protection on all forms and API endpoints
- ✅ Password hashing using Django's PBKDF2 algorithm
- ✅ SQL injection prevention via Django ORM
- ✅ XSS protection through template auto-escaping
- ✅ Authentication required for all protected endpoints
- ✅ Input validation on forms and API endpoints
- ✅ File upload validation (CSV/Excel import)
- ✅ Secure session handling with HTTPS support
- ✅ Environment variable management for secrets
- ✅ Service worker for offline support (no sensitive data cached)

## Security Best Practices

### For Developers

1. **Never commit sensitive data:**
   - API keys and secrets → use environment variables
   - Database credentials → .env files
   - Authentication tokens → .env / .gitignore
   - Private keys → .env / .gitignore

2. **Keep dependencies updated:**
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

3. **Use Django security features:**
   - ✅ CSRF protection (enabled by default)
   - ✅ SQL injection prevention (use Django ORM)
   - ✅ XSS protection (template escaping)
   - ✅ Secure password hashing (PBKDF2)
   - ✅ Secure cookies (HttpOnly, Secure flags)
   - ✅ Content Security Policy (CSP) headers
   - ✅ X-Frame-Options for clickjacking protection

4. **Input validation:**
   - Validate all user inputs on backend
   - Use Django forms for built-in validation
   - Sanitize data before display
   - Validate file uploads (type, size)
   - Validate API request parameters

5. **Code Review Before Commit:**
   - Check for hardcoded secrets
   - Review API authentication
   - Verify input validation logic
   - Test error handling

### For API Development

- All endpoints require authentication (@login_required)
- Use JSON responses for consistency
- Include status codes in responses
- Log security-relevant events
- Rate limit sensitive endpoints
- Validate request parameters
- Use appropriate HTTP methods (GET, POST, etc.)
- Return minimal information in error messages

### For Database Security

- Use Django ORM to prevent SQL injection
- Never use string interpolation in queries
- Use parameterized queries
- Restrict database user permissions
- Encrypt sensitive data at rest (consider for future)
- Use prepared statements (Django ORM does this)
- Regular database backups
- Audit logs for sensitive operations

### Testing Security

Before deployment:
1. **Run security check:**
   ```bash
   python manage.py check --deploy
   ```

2. **Check for common vulnerabilities:**
   - Test SQL injection attempts
   - Test XSS with script tags in inputs
   - Test CSRF by omitting token
   - Test authentication bypass
   - Test authorization (access control)
   - Test file upload with malicious files

3. **Security Headers Checklist**
   - ✅ SECURE_HSTS_SECONDS set (production)
   - ✅ SECURE_SSL_REDIRECT enabled (production)
   - ✅ SESSION_COOKIE_SECURE enabled (production)
   - ✅ CSRF_COOKIE_SECURE enabled (production)
   - ✅ X-Content-Type-Options set to nosniff
   - ✅ X-Frame-Options set to DENY/SAMEORIGIN

### For Administrators

1. **Environment Setup:**
   ```bash
   # Create .env file (never commit this)
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DATABASE_URL=postgresql://user:password@localhost/invoicedb
   ```

2. **Production Deployment:**
   - ✅ Set DEBUG = False
   - ✅ Configure ALLOWED_HOSTS
   - ✅ Use HTTPS/SSL certificates
   - ✅ Run admin commands from secure location
   - ✅ Use strong database passwords
   - ✅ Enable database encryption
   - ✅ Regular security updates

3. **Access Control:**
   - Use Django admin for user management
   - Assign permissions based on roles
   - Audit admin access logs
   - Disable accounts as needed
   - Require strong passwords
   - Monitor for suspicious activity

4. **Monitoring & Logging:**
   - Monitor error logs for attacks
   - Log authentication attempts
   - Alert on repeated failed logins
   - Track database queries in logs
   - Monitor system resources
   - Set up automated backups

5. **Regular Maintenance:**
   ```bash
   # Weekly
   - Review error logs
   - Check failed login attempts
   - Verify backup integrity
   - Update system packages
   
   # Monthly
   - Review user access
   - Audit permission assignments
   - Test backup restoration
   - Review security settings
   
   # Quarterly
   - Security audit
   - Dependency updates
   - Performance review
   - Disaster recovery drill
   ```

## Data Protection

### User Data
- Passwords: PBKDF2 hashing with salt
- Sensitive fields: Marked sensitive in Django admin
- PII (Personally Identifiable Information): Access controlled
- Export/Delete: Available to users (GDPR compliance)

### Financial Data
- Transactions: Immutable audit trail
- Payments: Status tracked and verified
- Invoices: Archive when closed
- Reports: Timestamped for audit

### Import Data
- File validation on upload
- Duplicate detection and handling
- Transaction integrity checks
- Error logging for all failures
- Data retention: Configurable

## Incident Response

### If a vulnerability is discovered:

1. **Immediate Actions:**
   - Isolate affected systems if needed
   - Gather technical details
   - Document timeline

2. **Assessment:**
   - Determine severity
   - Identify affected data
   - Estimate impact scope

3. **Response:**
   - Develop and test fix
   - Deploy fix to production
   - Notify users if necessary
   - Document lessons learned

4. **Follow-up:**
   - Monitor for similar issues
   - Update security documentation
   - Review code for related issues
   - Implement preventive measures

## Security Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/4.2/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Django REST Framework Security](https://www.django-rest-framework.org/api-guide/authentication/)

## Version Control Security

### Before Each Commit
```bash
# Check for committed secrets
git diff --cached | grep -i "password\|secret\|key\|token"

# Run security checks
python manage.py check

# Remove sensitive files from staging
git reset HEAD sensitive_file.py
```

### .gitignore Protection
Ensure these are in .gitignore:
```
.env
.env.local
*.key
*.pem
secrets.json
db.sqlite3
__pycache__/
*.pyc
.vscode/
.idea/
node_modules/
```

## Contact & Support

For security questions or vulnerability reports:
- Email: security@yourdomain.com
- Response time: 48 hours
- Confidential: Yes

---

**Last Updated:** February 28, 2026  
**Maintained by:** Security Team  
**Questions?** See CONTRIBUTING.md for support contacts
   # Use production settings
   export DJANGO_SETTINGS_MODULE=invoicing_app.settings.production
   
   # Set SECRET_KEY from environment variable
   export SECRET_KEY='your-secret-key-here'
   ```

2. **Database Security:**
   - Use strong passwords
   - Regular backups
   - Restrict database access
   - Enable encryption at rest

3. **Email Configuration:**
   - Use TLS/SSL for SMTP
   - Don't store passwords in code
   - Use app-specific passwords
   - Monitor email logs

4. **User Access:**
   - Use strong passwords (require in settings)
   - Enable 2FA when available
   - Regular access reviews
   - Audit login history

5. **Updates:**
   - Keep Django updated
   - Monitor security advisories
   - Update dependencies regularly
   - Test updates in staging

## Supported Versions

| Version | Status | Supported Until |
|---------|--------|-----------------|
| 2.0.x   | Active | Feb 2028 |
| 1.5.x   | EOL    | Feb 2027 |

## Security Checklist

Before deploying to production:

- [ ] `DEBUG = False` in settings
- [ ] `ALLOWED_HOSTS` configured properly
- [ ] `SECRET_KEY` is secure and hidden
- [ ] CSRF protection enabled
- [ ] XSS protection enabled
- [ ] Email credentials secure
- [ ] Database backed up
- [ ] HTTPS enabled
- [ ] Security headers configured
- [ ] Dependencies up to date
- [ ] Audit logging enabled
- [ ] User roles and permissions configured

## Compliance

InvoiceHub helps meet compliance requirements:

- **GDPR:** User data protection, data export/deletion
- **SOC 2:** Audit logging, access controls, backups
- **PCI DSS:** Payment data handling (integrate securely)

For specific compliance needs, contact your organization's security team.

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
- [CVE - Common Vulnerabilities and Exposures](https://www.cve.org/)

## Questions?

For security questions, email: security@yourdomain.com
