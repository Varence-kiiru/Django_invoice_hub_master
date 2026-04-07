# InvoiceHub - Professional Invoice Management System

A comprehensive, enterprise-grade Django-based invoicing application with advanced features for managing invoices, payments, clients, quotations, and multi-tenant organizations. Built for scale with comprehensive API, data analytics, and automation capabilities.

**Version:** 4.5.0 | **Status:** Production Ready ✅ | **Last Updated:** April 7, 2026 | **API:** v2.1

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Project Status](#project-status)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
- [Environment Setup](#environment-setup)
- [Database Configuration](#database-configuration)
- [Deployment Guide](#deployment-guide)
- [Project Structure](#project-structure)
- [Core Modules](#core-modules)
- [Features by Priority](#features-by-priority)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Multi-Tenancy & Organizations](#multi-tenancy--organizations)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security & Compliance](#security--compliance)
- [Support & Contributing](#support--contributing)

---

## 🎯 Overview

InvoiceHub is a modern, feature-rich invoicing and invoice management system designed for businesses of all sizes. It provides a complete solution for managing the complete invoicing lifecycle:

- **Invoice Management**: Create, edit, send, track, and archive invoices with full audit trail
- **Payment Tracking**: Record and manage client payments with multiple payment methods and reconciliation
- **Client Management**: Maintain comprehensive client databases with contact information and payment history
- **Quotations**: Generate and manage price quotations with conversion tracking and templates
- **Advanced Filtering**: Powerful search and filter capabilities with saved presets across all modules
- **Bulk Operations**: Batch actions for status updates, email sending, and data management
- **Email Automation**: Automated email reminders, scheduling, and document distribution
- **Reporting & Analytics**: Comprehensive financial reports, dashboards, and business intelligence
- **Multi-Tenancy**: Support for multiple organizations/companies in single deployment
- **Data Import/Export**: Bulk data import with validation and error handling
- **API-First Design**: RESTful API for all operations, suitable for integrations

**Target Users:**
- Freelancers and small business owners
- Accounting departments in medium-sized companies
- Multi-branch enterprises requiring centralized invoice management
- SaaS platforms needing white-label invoicing

---

## ✨ Key Features

### Core Features ✅
- ✅ Complete invoice lifecycle management (create → send → track → paid → archive)
- ✅ Multi-currency support with automatic conversion
- ✅ Tax calculation with configurable tax classes
- ✅ Recurring invoices and quotations
- ✅ Payment reconciliation with partial payment support
- ✅ Client portal for invoice viewing and payment
- ✅ Email reminders with customizable templates
- ✅ Expense tracking and management
- ✅ Delivery notes and quotation management

### Advanced Features ✅
- ✅ Advanced filtering with saved presets and full-text search
- ✅ Bulk operations (status updates, email, delete)
- ✅ CSV/Excel data import with validation
- ✅ Real-time dashboard with financial metrics
- ✅ Comprehensive reporting (aging, financial, tax)
- ✅ Audit trail and activity logging
- ✅ Role-based access control (RBAC)
- ✅ Multi-tenancy with organization isolation
- ✅ Payment method tracking and analysis
- ✅ API for third-party integrations

### Premium Features
- 🔒 Advanced role-based access control (RBAC)
- 📊 Financial forecasting and analytics
- 💰 Automated payment gateway integration
- 📱 Mobile app support (API-ready)
- 📧 Email template customization
- 🔔 Smart notifications and alerts

---

## 📊 Project Status

**Current Version:** 4.5.0
**Release Date:** April 7, 2026
**Status:** Production Ready ✅
**Python Version:** 3.11+
**Django Version:** 4.2.28+
**Database:** PostgreSQL (Prod) / MySQL (Supported) / SQLite (Dev)
**API Version:** v2.1
**Task Queue:** Celery 5.4.0 with Redis 7

## 📚 Documentation & Policies

- `README.md` (this file)
- `docs/INSTALLATION.md`
- `docs/UPGRADE.md`
- `docs/DOCKER_DEPLOYMENT.md`
- `docs/PRICING_TIERS.md`
- `docs/MARKETING_COPY.md`
- `docs/SECURITY.md`
- `TERMS_OF_SERVICE.md`
- `PRIVACY_POLICY.md`
- `EULA.md`

### Completed Modules

| Module | Status | Features | API |
|--------|--------|----------|-----|
| Invoices | ✅ Complete | CRUD, Status Tracking, Templates, PDF Export | ✅ |
| Payments | ✅ Complete | Payment Recording, Reconciliation, Methods | ✅ |
| Clients | ✅ Complete | Client Management, Contact Info, History | ✅ |
| Quotations | ✅ Complete | Quote Generation, Conversion Tracking | ✅ |
| Email/Notifications | ✅ Complete | Reminders, Templates, Scheduling | ✅ |
| Advanced Filtering | ✅ Complete | Multi-criteria, Presets, Full-text Search | ✅ |
| Bulk Operations | ✅ Complete | Status Update, Email, Delete | ✅ |
| Data Import | ✅ Complete | CSV/Excel, Validation, Duplicate Detection | ✅ |
| Dashboard Analytics | ✅ Complete | Metrics, Charts, Aging Report | ✅ |
| Expenses | ✅ Complete | Expense Tracking, Categories, Reports | ✅ |
| Deliveries | ✅ Complete | Delivery Notes, Tracking | ✅ |
| Multi-Tenancy | ✅ Complete | Organization Isolation, User Management | ✅ |
| Audit & Logging | ✅ Complete | Activity Tracking, Audit Trail | ✅ |
| RBAC | ✅ Complete | Role-based Access Control | ✅ |

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│              Frontend Layer                          │
│  (HTML5, CSS3, Vanilla JavaScript, Service Worker)  │
└────────────┬────────────────────────────┬───────────┘
             │                            │
    ┌────────▼──────────┐        ┌───────▼─────────┐
    │   REST API Layer  │        │  HTML Views     │
    │  (Django REST     │        │  (Django        │
    │   Framework)      │        │   Templates)    │
    └────────┬──────────┘        └───────┬─────────┘
             │                            │
    ┌────────▼────────────────────────────▼─────────┐
    │         Application Layer                      │
    │  (Django Apps: Core, Invoices, Payments, etc) │
    └────────┬────────────────────────────┬──────────┘
             │                            │
    ┌────────▼────────────────────────────▼─────────┐
    │         Service Layer                         │
    │  (Email, Search, Filtering, Analytics)        │
    └────────┬────────────────────────────┬──────────┘
             │                            │
    ┌────────▼────────────────────────────▼─────────┐
    │         Data Access Layer                     │
    │  (ORM: Django Models, Migrations)             │
    └────────┬────────────────────────────┬──────────┘
             │                            │
    ┌────────▼─────────────────────────────────────┐
    │      Database Layer                          │
    │  (PostgreSQL / MySQL / SQLite)               │
    └──────────────────────────────────────────────┘

    ┌──────────────────────────────────┐
    │   Background Processing          │
    │  (Celery + Redis)                │
    │  - Email Scheduling              │
    │  - Report Generation             │
    │  - Data Import Processing        │
    └──────────────────────────────────┘
```

### Technology Stack

**Backend:**
- **Framework:** Django 4.2+ (Python web framework)
- **Python:** 3.13+ (Programming language)
- **API:** Django REST Framework 3.14+ (API development)
- **Task Queue:** Celery 5.3+ (Asynchronous tasks)
- **Cache/Broker:** Redis (Caching & Celery broker)
- **Database:** PostgreSQL 14+ (Production) / SQLite 3 (Development)
- **ORM:** SQLAlchemy via Django ORM (Database abstraction)

**Frontend:**
- **HTML5** (Markup)
- **CSS3** (Styling with responsive design)
- **Vanilla JavaScript ES6+** (Client-side logic)
- **Chart.js 3.9.1** (Data visualization)
- **Service Worker** (Offline support)

**Infrastructure & DevOps:**
- **Development:** XAMPP/Apache, Django dev server
- **Production:** Gunicorn/uWSGI, Nginx reverse proxy
- **Version Control:** Git/GitHub
- **Deployment:** Docker-ready (Dockerfile included)
- **Static Files:** WhiteNoise/Nginx
- **Media Processing:** Django media files, file storage

**Key Dependencies:**
- Django extensions (admin customization)
- Pillow (Image processing)
- openpyxl/xlrd (Excel support)
- python-dateutil (Date handling)
- requests (HTTP client)
- celery-beat (Scheduled tasks)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.13+** (Download from python.org)
- **Git** (Version control)
- **PostgreSQL** (Production) OR **MySQL** (Development/XAMPP)
- **pip** (Python package manager)
- **Virtual environment** (venv)

### Installation (5 minutes)

1. **Clone the repository:**
   ```bash
   cd c:\xampp\htdocs\invoice
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\Activate.ps1

   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (database, email, etc.)
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (admin account):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Load demo/seed data (optional):**
   ```bash
   python manage.py demo_filters
   python manage.py seed_demo_data  # Creates sample invoices, clients, etc.
   ```

8. **Collect static files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

9. **Start development server:**
   ```bash
   python manage.py runserver
   ```

10. **Access the application:**
    - **Web UI:** http://localhost:8000
    - **Admin Panel:** http://localhost:8000/admin
    - **API Docs:** http://localhost:8000/api/docs
    - **Login** with your superuser credentials

---

## 🔧 Environment Setup

### Environment Variables (.env file)

Create a `.env` file in the project root with the following variables:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database Configuration
DATABASE_ENGINE=django.db.backends.postgresql  # postgresql, mysql, sqlite3
DATABASE_NAME=invoice_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-db-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Use app-specific password for Gmail
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Services Webhook URL
WEBHOOK_URL=https://yourdomain.com/webhooks/

# Timezone
TIME_ZONE=UTC  # or your timezone: America/New_York, Europe/London, etc.

# Security (Production)
SECURE_SSL_REDIRECT=False  # Set to True in production
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# AWS/Storage (if using S3)
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
```

### Development vs Production Configuration

**Development (.env.development):**
```bash
DEBUG=True
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Production (.env.production):**
```bash
DEBUG=False
DATABASE_ENGINE=django.db.backends.postgresql
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## 🗄️ Database Configuration

### Supported Databases

**SQLite (Development - Default)**
```bash
# Uses db.sqlite3 (file-based)
DATABASE_ENGINE=django.db.backends.sqlite3
```

**PostgreSQL (Recommended Production)**
```bash
# Install: pip install psycopg2-binary
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=invoice_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
```

**MySQL (XAMPP Development)**
```bash
# Install: pip install mysqlclient
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=invoice_db
DATABASE_USER=root
DATABASE_PASSWORD=
```

### Database Initialization

```bash
# Create migrations for changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# View migration status
python manage.py showmigrations

# Backup database
python manage.py dumpdata > backup.json

# Restore database
python manage.py loaddata backup.json
```

### Database Schema

The system uses 13+ core models:
- **User & Organization:** User, Organization, Team, Permission
- **Invoice:** Invoice, InvoiceLineItem, InvoiceTemplate
- **Payment:** Payment, PaymentMethod, PaymentReconciliation
- **Client:** Client, ClientContact, ClientPaymentHistory
- **Quotation:** Quotation, QuoteLineItem
- **Product:** Product, ProductCategory
- **Tax:** TaxClass, TaxRate
- **Notification:** EmailTemplate, Reminder, EmailLog
- **Audit:** AuditLog, ActivityLog
- **Settings:** CompanySettings, SystemSettings

---

## 🌐 Deployment Guide

### Deploying to Production

#### 1. Server Requirements

- **OS:** Linux (Ubuntu 20.04+ recommended), Windows Server, or macOS
- **Python:** 3.13+
- **Database:** PostgreSQL 14+ (recommended)
- **Memory:** Minimum 2GB RAM, 4GB+ recommended
- **Storage:** Minimum 20GB free space
- **CPU:** 2+ cores recommended

#### 2. Deployment Steps

**Step 1: Prepare Server**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.13 python3.13-venv postgresql postgresql-contrib nginx

# Create application user
sudo useradd -m -s /bin/bash invoice_user
sudo su - invoice_user
```

**Step 2: Clone and Setup Application**
```bash
cd /home/invoice_user
git clone <your-repo-url> invoice
cd invoice

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Step 3: Configure Environment**
```bash
# Copy and configure .env
cp .env.example .env
nano .env
# Update: DEBUG=False, DATABASE config, EMAIL config, SECRET_KEY
```

**Step 4: Database Setup**
```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE invoice_db;
CREATE USER invoice_user WITH PASSWORD 'strong_password';
ALTER ROLE invoice_user SET client_encoding TO 'utf8';
ALTER ROLE invoice_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE invoice_user SET default_transaction_deferrable TO on;
ALTER ROLE invoice_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE invoice_db TO invoice_user;
\q

# Run migrations
python manage.py migrate
python manage.py collectstatic --noinput
```

**Step 5: Create Superuser & Demo Data**
```bash
python manage.py createsuperuser
python manage.py seed_demo_data  # Optional
```

**Step 6: Configure Gunicorn**
```bash
# Create systemd service file
sudo nano /etc/systemd/system/invoice.service
```

Add content:
```ini
[Unit]
Description=Invoice Application
After=network.target postgresql.service

[Service]
User=invoice_user
WorkingDirectory=/home/invoice_user/invoice
ExecStart=/home/invoice_user/invoice/venv/bin/gunicorn invoicing_app.wsgi:application --bind 127.0.0.1:8000 --workers 4 --timeout 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable invoice
sudo systemctl start invoice
sudo systemctl status invoice
```

**Step 7: Configure Nginx Reverse Proxy**
```bash
sudo nano /etc/nginx/sites-available/invoice
```

Add content:
```nginx
upstream invoice_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location / {
        proxy_pass http://invoice_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/invoice_user/invoice/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/invoice_user/invoice/media/;
        expires 30d;
    }
}
```

Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/invoice /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Step 8: Setup SSL Certificate (Let's Encrypt)**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

**Step 9: Configure Celery for Background Tasks** (Optional but recommended)
```bash
# Install Redis
sudo apt install redis-server

# Create Celery service
sudo nano /etc/systemd/system/invoice-celery.service
```

Add content:
```ini
[Unit]
Description=Invoice Celery Worker
After=network.target redis-server.service

[Service]
User=invoice_user
WorkingDirectory=/home/invoice_user/invoice
ExecStart=/home/invoice_user/invoice/venv/bin/celery -A invoicing_app worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker Deployment

**Dockerfile Example:**
```dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "invoicing_app.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**Docker Compose Configuration:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: invoice_db
      POSTGRES_PASSWORD: your-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn invoicing_app.wsgi:application --bind 0.0.0.0:8000"
    environment:
      DATABASE_ENGINE: django.db.backends.postgresql
      DATABASE_NAME: invoice_db
      DATABASE_USER: postgres
      DATABASE_PASSWORD: your-password
      DATABASE_HOST: db
    ports:
      - "8000:8000"
    depends_on:
      - db

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - web

volumes:
  postgres_data:
```

---

## 📁 Core Modules

### Core Application Modules

**Core Module** (`invoicing_app/core/`)
- Central authentication and user management
- Dashboard and system analytics
- Advanced filtering and search infrastructure
- Bulk operations API
- Email service and configuration
- Audit logging and activity tracking
- System settings and configuration

**Invoice Module** (`invoicing_app/invoices/`)
- Invoice creation and management
- Invoice templates and numbering
- Line items and tax calculations
- Status tracking (draft, sent, issued, paid, overdue, archived)
- PDF generation and export
- Invoice reminders and follow-up

**Payment Module** (`invoicing_app/payments/`)
- Payment recording
- Multiple payment method support
- Payment reconciliation
- Partial payment tracking
- Payment history and aging
- Payment method analysis

**Client Module** (`invoicing_app/clients/`)
- Client database management
- Contact information and communication history
- Payment history and outstanding balance
- Client portal access
- Tax ID management
- Client segmentation

**Quotation Module** (`invoicing_app/quotations/`)
- Quotation creation and management
- Quote-to-invoice conversion
- Template management
- Expiration tracking
- Quotation status tracking
- Historical records

**Expense Module** (`invoicing_app/expenses/`)
- Expense tracking and categorization
- Receipt management
- Expense reports
- Budget tracking
- Reimbursement workflow

**Delivery Module** (`invoicing_app/deliveries/`)
- Delivery note generation
- Delivery tracking
- Goods received status
- Return management
- Proof of delivery

**Notification Module** (`invoicing_app/notifications/`)
- Email template management
- Reminder scheduling
- Email log tracking
- Failed email handling
- Notification preferences

**Audit Module** (`invoicing_app/audit/`)
- Activity logging
- Change tracking
- User action history
- Data modification audit trail
- Compliance reporting

**Organization Module** (`invoicing_app/organizations/`)
- Multi-organization/multi-tenant support
- Organization settings
- Team management
- User-organization relationships
- Data isolation

**Tax Module** (`invoicing_app/taxes/`)
- Tax class definitions
- Tax rate management
- Tax calculations
- Tax compliance reporting
- Multi-country tax support

**Settings Module** (`invoicing_app/settings/`)
- Company profile and branding
- Payment terms configuration
- Email configuration
- API keys management
- System preferences

---

### Full Project Structure

```
invoice/
├── invoicing_app/                       # Main Django application
│   ├── __init__.py
│   ├── asgi.py                          # ASGI (async server gateway)
│   ├── celery.py                        # Celery task configuration
│   ├── wsgi.py                          # WSGI (web server gateway)
│   ├── urls.py                          # Root URL routing
│   ├── settings.py                      # Django configuration
│   │
│   ├── core/                            # Core module
│   │   ├── admin.py                     # Django admin customization
│   │   ├── apps.py                      # App configuration
│   │   ├── models.py                    # Core models
│   │   ├── views.py                     # API views
│   │   ├── views_html.py                # HTML views
│   │   ├── serializers.py               # API serializers
│   │   ├── urls.py                      # Module URLs
│   │   ├── permissions.py               # Custom permissions
│   │   ├── api_filters.py               # Advanced filtering
│   │   ├── api_bulk_operations.py       # Bulk operation APIs
│   │   ├── analytics_dashboard.py       # Dashboard analytics
│   │   ├── email_backend.py             # Email functionality
│   │   ├── validators.py                # Data validators
│   │   ├── decorators.py                # Custom decorators
│   │   ├── exception_handlers.py        # Error handling
│   │   ├── context_processors.py        # Template context
│   │   ├── data_import.py               # Data import logic
│   │   └── migrations/                  # Database migrations
│   │
│   ├── invoices/                        # Invoice module
│   │   ├── models.py                    # Invoice, LineItem models
│   │   ├── views.py / views_html.py     # Invoice views
│   │   ├── serializers.py               # API serializers
│   │   ├── forms.py                     # Django forms
│   │   ├── urls.py                      # Module routes
│   │   ├── admin.py                     # Admin interface
│   │   └── migrations/
│   │
│   ├── payments/                        # Payment module
│   │   ├── models.py                    # Payment models
│   │   ├── views.py / views_html.py
│   │   ├── serializers.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── clients/                         # Client module
│   │   ├── models.py
│   │   ├── views.py / views_html.py
│   │   ├── serializers.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── quotations/                      # Quotation module
│   │   ├── models.py
│   │   ├── views.py / views_html.py
│   │   ├── serializers.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── expenses/                        # Expense module
│   ├── deliveries/                      # Delivery module
│   ├── payments/                        # Payment module
│   ├── products/                        # Product catalog
│   ├── notifications/                   # Email & notifications
│   ├── organizations/                   # Multi-tenancy
│   ├── taxes/                           # Tax management
│   ├── audit/                           # Audit logging
│   ├── user_management/                 # User/role management
│   ├── settings/                        # System settings
│   ├── tests/                           # Test suite
│   └── management/                      # Management commands
│
├── templates/                           # HTML templates
│   ├── 1_base/
│   │   └── base.html                    # Master template
│   ├── 2_auth/                          # Authentication pages
│   ├── 3_dashboard/                     # Dashboard pages
│   ├── 4_clients/                       # Client pages
│   ├── 5_products/                      # Product pages
│   ├── 6_invoices/                      # Invoice pages
│   ├── 7_payments/                      # Payment pages
│   ├── 8_reports/                       # Report pages
│   ├── 9_admin/                         # Admin pages
│   ├── 10_modals/                       # Modal components
│   ├── 11_expenses/                     # Expense pages
│   ├── 12_errors/                       # Error pages
│   ├── 13_quotations/                   # Quotation pages
│   ├── 14_deliveries/                   # Delivery pages
│   ├── layouts/                         # Reusable layouts
│   ├── components/                      # Reusable components
│   ├── invoicing_app/                   # App-level templates
│   ├── settings/                        # Settings pages
│   └── emails/                          # Email templates
│
├── static/                              # Static assets
│   ├── js/
│   │   ├── app.js                       # Main app JavaScript
│   │   ├── filter_system.js             # Advanced filtering
│   │   ├── bulk_operations.js           # Bulk operations handler
│   │   ├── analytics.js                 # Dashboard analytics
│   │   ├── data_import.js               # Data import wizard
│   │   ├── form_validation.js           # Form validation
│   │   ├── api_client.js                # API communication
│   │   └── pages/                       # Page-specific scripts
│   ├── css/
│   │   ├── style.css                    # Main stylesheet
│   │   ├── responsive.css               # Mobile responsive
│   │   ├── components.css               # Component styles
│   │   └── pages/                       # Page-specific styles
│   ├── images/                          # Image assets
│   └── offline.html                     # Offline page
│
├── media/                               # User-uploaded files
│   ├── company/                         # Company logos
│   ├── invoices/                        # Invoice exports
│   ├── payments/                        # Payment receipts
│   ├── quotations/                      # Quote PDFs
│   ├── deliveries/                      # Delivery docs
│   └── receipts/
│
├── manage.py                            # Django management
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Docker configuration
├── docker-compose.yml                   # Docker Compose config
├── .env.example                         # Environment template
├── README.md                            # This file
├── LICENSE                              # MIT License
├── QUICK_START.md                       # Quick start guide
├── SECURITY.md                          # Security information
├── PRIVACY_POLICY.md                    # Privacy policy
├── TERMS_OF_SERVICE.md                  # Terms of service
├── CONTRIBUTING.md                      # Contributing guide
├── MULTITENANCY_USER_MANAGEMENT.md      # Multi-tenant docs
└── INDEX.md                             # Document index
```

---

## 🎁 Features by Priority

### Priority 1A: Email Reminders ✅

**What it does:**
- Automatically sends payment reminders to clients
- Schedules reminder emails based on invoice due dates
- Tracks reminder history and client responses
- Customizable email templates per reminder type

**How to use:**
1. Navigate to Settings → Email → Email Templates
2. Configure reminder email templates
3. Set reminders on invoices (automatic by default)
4. System sends emails automatically on schedule

**API Endpoints:**
- `POST /api/reminders/schedule/` - Schedule reminder
- `GET /api/reminders/history/` - View reminder history
- `POST /api/reminders/send-test/` - Test email sending

---

### Priority 1B: Advanced Filtering & Search ✅

**What it does:**
- Filter invoices, payments, clients, quotations by multiple criteria
- Save filter presets for quick access
- Full-text search with real-time suggestions
- Smart autocomplete on all fields

**Filterable Fields:**

**Invoices:**
- Status (draft, sent, issued, paid, overdue, etc.)
- Date range
- Amount range
- Client
- Invoice number

**Payments:**
- Status (pending, confirmed, failed)
- Payment method
- Date range
- Amount range
- Invoice/Client

**Clients:**
- Status (active, inactive)
- Client type (individual, company)
- Outstanding amount
- Contact info

**Quotations:**
- Status (draft, sent, accepted, rejected, expired, etc.)
- Validity date range
- Amount range
- Client

**How to use:**
1. Click filter icon on any list page
2. Select filter criteria
3. Results update in real-time
4. Click "Save Filter" to create preset
5. Load saved filters from dropdown

**API Endpoints:**
- `POST /api/filters/` - Apply filters
- `POST /api/filters/<id>/` - Save/update filter
- `DELETE /api/filters/<id>/` - Delete filter
- `GET /api/search/suggestions/` - Get search suggestions

---

### Priority 2A: Bulk Operations ✅

**What it does:**
- Select multiple items at once
- Perform batch actions without opening each item
- Efficient database operations with error handling
- Real-time selection feedback

**Available Bulk Actions:**

**Update Status** (Invoices, Payments, Quotations)
- Select items → Choose new status → Apply to all
- Single click instead of individual edits
- Automatic page reload after update

**Send Email** (All entity types)
- Send invoices to multiple clients
- Send quotations in batch
- Send payment reminders
- Custom email with custom subject/message

**Delete** (All entity types)
- Delete multiple items with confirmation
- Error handling for protected items
- Success/failure count reporting

**How to use:**

1. **Navigate to list page:**
   - Invoices: http://localhost:8000/invoices
   - Payments: http://localhost:8000/payments
   - Clients: http://localhost:8000/clients
   - Quotations: http://localhost:8000/quotations

2. **Select items:**
   - Check individual checkboxes
   - Use "Select All" checkbox in header
   - Toolbar appears with action buttons

3. **Perform action:**
   - Click desired action button
   - Complete modal dialog
   - Confirm action
   - Page reloads with confirmation

**API Endpoints:**
- `POST /api/bulk/status-update/` - Update status for multiple items
- `POST /api/bulk/send-email/` - Send emails to multiple recipients
- `POST /api/bulk/delete/` - Delete multiple items
- `POST /api/bulk/options/` - Get available actions per entity

---

### Priority 2B: Data Import Tools ✅ **NEW**

**What it does:**
- Import bulk data from CSV or Excel files
- Comprehensive validation and error reporting
- Automatic duplicate detection
- Support for all entity types (invoices, payments, clients, quotations)
- Atomic transactions ensure data integrity

**Supported File Formats:**
- CSV (.csv) - Comma-separated values
- Excel (.xlsx, .xls) - Microsoft Excel workbooks

**Supported Entity Types:**
- Invoices: invoice_number, invoice_date, client_name, total_amount, currency
- Payments: payment_number, payment_date, client_name, amount, currency
- Clients: name, email, phone, company, address
- Quotations: quotation_number, quote_date, client_name, total_amount, currency

**Validation Features:**
- Required field checking
- Data type validation (amounts, dates, emails)
- Status validation against allowed values
- Duplicate detection with customizable keys
- Per-row error reporting

**How to use:**

1. **Prepare CSV/Excel file:**
   - Download template from import page
   - Fill in data matching required fields
   - Ensure dates are in YYYY-MM-DD format
   - Ensure amounts are valid numbers

2. **Navigate to import:**
   - Click "Import Data" button
   - Or: http://localhost:8000/import/

3. **Upload file:**
   - Select file (CSV or Excel)
   - Choose entity type
   - Select duplicate handling:
     - Skip duplicates (default)
     - Update existing records
   - Click "Preview"

4. **Review results:**
   - View rows that will be imported
   - See any validation errors
   - Fix errors in file and re-upload if needed
   - Click "Import" to confirm

5. **Check results:**
   - Summary shows imported count
   - Link to detailed error report
   - Successfully imported records appear in lists

**Example CSV Format - Invoices:**
```
invoice_number,invoice_date,client_name,total_amount,currency,status,description
INV-2024-001,2024-01-15,Acme Corp,1500.00,USD,sent,Consulting services
INV-2024-002,2024-01-16,TechCorp LLC,2300.50,USD,draft,Software development
INV-2024-003,2024-01-17,Global Solutions,5200.00,EUR,paid,Annual license
```

**API Endpoints:**
- `POST /api/import/data/` - Import data file
- `GET /api/import/template/` - Get import template with field definitions

---

### Priority 3: Dashboard Analytics ✅ **NEW**

**What it does:**
- Real-time dashboard with comprehensive business metrics
- Financial analysis and KPI tracking
- Visual charts and trends
- Aging report for accounts receivable
- Payment method analysis
- Top clients ranking

**Dashboard Metrics:**

**Summary Metrics:**
- Total invoices, payments, clients, quotations
- Active clients vs. inactive
- Overdue invoices count

**Financial Metrics:**
- Total invoiced amount
- Total paid amount
- Outstanding (accounts receivable)
- Collection rate percentage
- Average invoice value
- Revenue trend (month-over-month)

**Timeline Charts:**
- Daily invoice creation count and amounts
- Daily payment received count and amounts
- 30/60/90/365 day views
- Compare trends over periods

**Aging Report:**
- Current (0-30 days) outstanding
- 31-60 days overdue
- 61-90 days overdue
- Over 90 days overdue
- Percentage breakdown for action planning

**Top Clients:**
- Ranked by invoice value
- Shows paid, outstanding, and transaction history
- Quick link to client details

**Payment Method Breakdown:**
- Cash, bank transfer, credit card, check, other
- Amount and percentage for each method
- Identify payment method preferences

**How to use:**

1. **View dashboard:**
   - Navigate to Dashboard
   - All metrics auto-refresh every 30 seconds

2. **Analyze financials:**
   - Review collection rate
   - Monitor outstanding A/R
   - Track revenue trends

3. **Check aging:**
   - Review aging report section
   - Identify overdue amounts
   - Create collection strategy

4. **Manage clients:**
   - See top performing clients
   - Track client payment methods
   - Prioritize follow-ups

5. **Export analytics:**
   - All charts support export
   - Generate reports for stakeholders
   - Use data for business planning

**API Endpoints:**
- `GET /api/dashboard/` - Complete dashboard data
- `GET /api/metrics/financial/` - Financial metrics only
- `GET /api/chart/timeline/` - Timeline data for custom charts
- `GET /api/report/aging/` - Aging report details
- `GET /api/metrics/payment-methods/` - Payment method breakdown

---

## ⚙️ Configuration

### Email Configuration

**Location:** `invoicing_app/settings.py`

```python
# SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

### Celery Configuration (Task Scheduling)

```python
# Enable Celery for email reminders
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'

# Reminder schedule (adjust as needed)
CELERY_BEAT_SCHEDULE = {
    'send-payment-reminders': {
        'task': 'invoicing_app.notifications.tasks.send_due_payment_reminders',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
}
```

### Company Settings

**Navigation:** Settings → Company

Configure:
- Company name & logo
- Tax identification
- Default currency
- Invoice numbering format
- Payment terms

---

## 📡 API Documentation

### Bulk Operations API

#### Update Status
```json
POST /api/bulk/status-update/

Request:
{
  "entity_type": "invoices",
  "ids": [1, 2, 3],
  "status": "sent"
}

Response:
{
  "success": true,
  "updated_count": 3,
  "errors": []
}
```

#### Send Email
```json
POST /api/bulk/send-email/

Request:
{
  "entity_type": "invoices",
  "ids": [1, 2, 3],
  "email_type": "invoice"
}

Response:
{
  "success": true,
  "sent_count": 3,
  "errors": []
}
```

#### Bulk Delete
```json
POST /api/bulk/delete/

Request:
{
  "entity_type": "invoices",
  "ids": [1, 2, 3]
}

Response:
{
  "success": true,
  "deleted_count": 3,
  "errors": []
}
```

#### Get Available Options
```json
POST /api/bulk/options/

Request:
{
  "entity_type": "invoices"
}

Response:
{
  "success": true,
  "options": {
    "status_options": ["draft", "sent", "issued", "paid", ...],
    "email_types": ["invoice", "reminder", "custom"],
    "can_delete": true
  }
}
```

### Advanced Filtering API

#### Apply Filters
```json
POST /api/filters/

Request:
{
  "entity_type": "invoices",
  "filters": {
    "status": ["sent", "paid"],
    "date_from": "2026-01-01",
    "date_to": "2026-01-31",
    "amount_min": 1000,
    "amount_max": 50000
  },
  "page": 1
}

Response:
{
  "success": true,
  "results": [...],
  "total_count": 42,
  "page_count": 5
}
```

#### Save Filter Preset
```json
POST /api/filters/

Request:
{
  "entity_type": "invoices",
  "name": "Unpaid Over 30 Days",
  "filters": {...}
}

Response:
{
  "success": true,
  "filter_id": 123
}
```

---

## 🏢 Multi-Tenancy & Organizations

### Multi-Tenant Architecture

InvoiceHub supports multiple organizations in a single deployment with complete data isolation:

**Key Concepts:**
- **Tenant:** An independent organization/company with its own data
- **User:** Can belong to one or multiple organizations
- **Data Isolation:** Each organization's data is completely separate
- **Scalability:** Single deployment can support unlimited organizations

### Organization Setup

**Creating an Organization:**

1. **Admin Panel:**
   - Navigate to Admin → Organizations
   - Click "Add Organization"
   - Fill in organization details (name, domain, logo, etc.)

2. **Programmatically:**
   ```python
   from invoicing_app.organizations.models import Organization

   org = Organization.objects.create(
       name="Acme Corporation",
       slug="acme-corp",
       domain="acme.yourdomain.com",
       email="admin@acme.corp"
   )
   ```

### User & Organization Relationship

**User Assignment:**
```python
from invoicing_app.organizations.models import OrganizationMember

# Add user to organization
member = OrganizationMember.objects.create(
    user=user,
    organization=org,
    role='admin'  # admin, manager, accountant, viewer
)
```

**Role-Based Access:**
- **Admin:** Full system access, can manage users and settings
- **Manager:** Can manage all financial records
- **Accountant:** Read-only access to financial data
- **Viewer:** View-only access to assigned records

### Data Isolation

All queries are automatically filtered by organization:

```python
# Automatically filtered by current organization
invoices = Invoice.objects.filter(organization=request.organization)

# OR using context manager
with request.organization:
    invoices = Invoice.objects.all()  # Already isolated
```

**How It Works:**
1. Middleware sets `request.organization` from subdomain or header
2. Querysets automatically filtered by organization
3. Each model has `organization` ForeignKey
4. No cross-organization data leakage possible

### Subdomain-Based Organization

Configure nginx/apache to support `*.yourdomain.com`:

```nginx
# Nginx configuration
server {
    server_name ~^(?<subdomain>.+)\.yourdomain\.com$ yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Organization-Subdomain $subdomain;
    }
}
```

Then in Django:
```python
# middleware.py
class OrganizationMiddleware:
    def __call__(self, request):
        subdomain = request.META.get('HTTP_X_ORGANIZATION_SUBDOMAIN', '')
        if subdomain:
            request.organization = Organization.objects.get(slug=subdomain)
        return self.get_response(request)
```

### Organization Settings

Each organization has isolated settings:

```python
from invoicing_app.settings.models import CompanySettings

settings = CompanySettings.objects.get(organization=org)
settings.company_name = "Acme Corp"
settings.invoice_prefix = "ACM"
settings.currency = "USD"
settings.timezone = "America/New_York"
settings.save()
```

### Multi-Tenant API

Prefix API calls with organization identifier:

```bash
# Organization-specific API
curl https://api.yourdomain.com/api/invoices/ \
  -H "X-Organization: acme-corp" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test invoicing_app.invoices

# Run specific test class
python manage.py test invoicing_app.invoices.tests.InvoiceTestCase

# Run with verbose output
python manage.py test --verbosity=2
```

### Testing Bulk Operations

1. **Navigate to invoices list:**
   ```
   http://localhost:8000/invoices
   ```

2. **Test checkbox selection:**
   - Click individual checkbox → select item
   - Click "Select All" → select all visible items
   - Bulk actions toolbar appears

3. **Test status update:**
   - Select 2-3 invoices
   - Click "Update Status"
   - Choose new status from dropdown
   - Click confirm
   - Verify page reloads with new status

4. **Test email sending:**
   - Select 2-3 invoices
   - Click "Send Email"
   - Choose email type
   - Click confirm
   - Check email logs

5. **Test delete:**
   - Select 1 invoice
   - Click "Delete"
   - Confirm deletion
   - Verify item removed from list

### Testing Filters

1. **Navigate to invoices list**
2. **Click filter icon**
3. **Add filter criteria:**
   - Status: Select "Sent"
   - Amount: Set min $1000, max $50000
   - Date: Last 30 days
4. **Verify results update in real-time**
5. **Save filter** as "Large Recent Invoices"
6. **Clear filters** and reload
7. **Load saved filter** from dropdown

---

## 🔧 Troubleshooting

### "Select All" Checkbox Not Working

**Symptoms:** Checkboxes don't check when clicking "Select All"

**Solution:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+F5)
3. Check browser console (F12) for errors
4. Ensure `bulk_operations.js` is loading (Network tab)

### API Returning 400 Bad Request

**Symptoms:** Bulk actions fail with 400 error

**Solution:**
1. Verify `entity_type` is correct:
   - Use singular: `invoice` not plural `invoices` (usually handled automatically)
   - Check API response for error message
2. Ensure CSRF token is present in headers
3. Check server logs: `python manage.py runserver`

### Emails Not Sending

**Symptoms:** "Send Email" action succeeds but no emails received

**Solution:**
1. Verify email configuration in settings
2. Check email logs: Admin → Logs → Email Logs
3. Test email: Settings → Email → Test Email
4. Verify SMTP credentials
5. Check spam/junk folder

### Filter Results Empty

**Symptoms:** Filters return no results when they should

**Solution:**
1. Clear all filters and try again
2. Verify filter criteria match data
3. Check browser console for JS errors
4. Ensure data exists: View raw table without filters
5. Check SELECT statement in server logs

### Database Connection Error

**Symptoms:** "No database available" or connection timeout

**Solution:**
1. Verify XAMPP MySQL is running: XAMPP Control Panel
2. Check DATABASE setting in settings.py
3. Run: `python manage.py migrate`
4. Restart Django server

---

## � Security & Compliance

### Security Features

**Authentication & Authorization**
- ✅ Django built-in authentication system
- ✅ Password hashing with PBKDF2 (configurable)
- ✅ Session-based authentication
- ✅ Token-based API authentication (Token or JWT)
- ✅ CSRF protection on all forms
- ✅ SQL injection prevention via ORM

**Data Protection**
- ✅ HTTPS/SSL encryption in production
- ✅ Secure password reset workflow
- ✅ Sensitive data encryption at rest (optional)
- ✅ Rate limiting on API endpoints
- ✅ Input validation and sanitization

**Access Control**
- ✅ Role-Based Access Control (RBAC)
- ✅ Organization-level data isolation
- ✅ User permission granularity
- ✅ Audit logging of all actions

### GDPR Compliance

**Data Protection:**
- ✅ User data deletion (right to be forgotten)
- ✅ Data export functionality
- ✅ Privacy policy template
- ✅ Consent management
- ✅ Activity logging and audit trail

**Implementations:**
```python
# Export user data
from invoicing_app.core.models import User

user_data = user.get_export_data()  # JSON export

# Delete user (anonymize data)
user.anonymize_data()
```

### Security Best Practices

**Production Deployment Checklist:**
- [ ] Set `DEBUG=False` in production
- [ ] Generate strong `SECRET_KEY` (not the default)
- [ ] Enable `SECURE_SSL_REDIRECT=True`
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Set `CSRF_COOKIE_SECURE=True`
- [ ] Use strong database passwords
- [ ] Enable database backups
- [ ] Set up monitoring and alerting
- [ ] Keep dependencies updated
- [ ] Configure logging for audit trail
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting on public APIs

**Environment Variables to Never Commit:**
```bash
# .gitignore
.env
.env.local
*.key
*.pem
db.sqlite3
__pycache__/
*.pyc
media/
```

### Compliance & Standards

**Standards Supported:**
- ISO 27001 (Information Security)
- PCI DSS (Payment Card Industry) - when processing payments
- HIPAA (Health Insurance Portability) - if handling health data
- SOC 2 (Service Organization Control)

**Audit & Compliance Reports:**
- User activity logs
- Data modification audit trail
- Login/logout history
- Permission changes log
- Data export audit

---

## 📞 Support & Contributing

### Getting Help

**Documentation:**
- Primary documentation: [README.md](README.md) (this file)
- Quick start guide: [QUICK_START.md](QUICK_START.md)
- Multi-tenancy guide: [MULTITENANCY_USER_MANAGEMENT.md](MULTITENANCY_USER_MANAGEMENT.md)
- Contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security information: [SECURITY.md](SECURITY.md)

**Online Resources:**
- Django Documentation: https://docs.djangoproject.com
- Django REST Framework: https://www.django-rest-framework.org
- PostgreSQL Docs: https://www.postgresql.org/docs/
- Mozilla JavaScript Guide: https://developer.mozilla.org/en-US/docs/Web/JavaScript
- Bootstrap CSS Framework: https://getbootstrap.com

**Bug Reports and Issues:**
1. Check existing issues: https://github.com/yourusername/invoice/issues
2. Create new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs. actual behavior
   - Django version: `python manage.py version`
   - Python version: `python --version`
   - Browser/OS information
   - Error traceback if applicable

**Feature Requests:**
1. Create discussion: https://github.com/Varence-kiiru/Django_invoice_hub_master/discussions
2. Describe use case and benefits
3. Suggest implementation approach if possible

### Contributing Guidelines

**Development Setup:**
```bash
# Clone repository
git clone https://github.com/Varence-kiiru/Django_invoice_hub_master.git
cd Django_invoice_hub_master

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1

# Install development dependencies
pip install -r requirements.txt
pip install django-debug-toolbar flake8 black pytest

# Create local database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

**Code Standards:**

**Python (PEP 8):**
```bash
# Check code style
flake8 invoicing_app/

# Auto-format code
black invoicing_app/

# Run type checking
mypy invoicing_app/
```

**JavaScript (ESLint):**
```bash
# Lint JavaScript files
npm run lint

# Auto-fix issues
npm run lint:fix
```

**Commit Message Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:
- `feat(invoices): add recurring invoice support`
- `fix(payments): correct payment reconciliation logic`
- `docs(readme): update installation instructions`
- `refactor(filters): simplify filter query builder`
- `test(clients): add comprehensive client model tests`

**Types:** feat, fix, docs, style, refactor, test, chore, ci, perf

**Creating Pull Requests:**

1. Create feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make changes with meaningful commits:
   ```bash
   git add .
   git commit -m "feat(module): description"
   ```

3. Push to GitHub:
   ```bash
   git push origin feature/my-feature
   ```

4. Create Pull Request with:
   - Clear title and description
   - Link to related issues
   - Checklist:
     - [ ] Tests added/updated
     - [ ] Documentation updated
     - [ ] Code follows style guidelines
     - [ ] No breaking changes

5. Code Review:
   - Address feedback
   - Discuss concerns or suggestions
   - Update PR as needed

6. Merge:
   - Squash commits if needed
   - Delete branch after merge

---

## 📊 Version History

| Version | Date | Status | Key Features |
|---------|------|--------|--------------|
| 3.0.0 | Feb 28, 2026 | Stable | Multi-tenancy, Analytics, Data Import |
| 2.5.0 | Jan 15, 2026 | Legacy | Dashboard refactor, Performance improvements |
| 2.0.0 | Dec 1, 2025 | Legacy | Bulk operations, Advanced filtering |
| 1.5.0 | Sep 1, 2025 | Legacy | Core features, Authentication |

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

**Permissions:**
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

**Conditions:**
- 📝 License and copyright notice required

**Limitations:**
- ❌ Liability
- ❌ Warranty

---

## 🎓 Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| Start dev server | `python manage.py runserver` |
| Run migrations | `python manage.py migrate` |
| Create migrations | `python manage.py makemigrations` |
| Create superuser | `python manage.py createsuperuser` |
| Run tests | `python manage.py test` |
| Load demo data | `python manage.py seed_demo_data` |
| Collect static files | `python manage.py collectstatic` |
| Database backup | `python manage.py dumpdata > backup.json` |
| Database restore | `python manage.py loaddata backup.json` |
| Shell (interactive) | `python manage.py shell` |

### URL Endpoints Reference

| Page | URL |
|------|-----|
| Dashboard | `/` or `/dashboard/` |
| Invoices | `/invoices/` |
| Payments | `/payments/` |
| Clients | `/clients/` |
| Quotations | `/quotations/` |
| Expenses | `/expenses/` |
| Analytics | `/analytics/` |
| Data Import | `/import/` |
| Settings | `/settings/` |
| Admin Panel | `/admin/` |
| API Root | `/api/` |

### API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/invoices/` | GET, POST | List/Create invoices |
| `/api/invoices/<id>/` | GET, PUT, DELETE | Retrieve/Update/Delete |
| `/api/payments/` | GET, POST | List/Create payments |
| `/api/clients/` | GET, POST | List/Create clients |
| `/api/quotations/` | GET, POST | List/Create quotes |
| `/api/filters/` | GET, POST | Filtering |
| `/api/bulk/` | POST | Bulk operations |
| `/api/import/data/` | POST | Data import |
| `/api/dashboard/` | GET | Dashboard data |
| `/api/reports/` | GET | Reports |

### File Locations Quick Reference

| Type | Location |
|------|----------|
| Models | `invoicing_app/*/models.py` |
| Views | `invoicing_app/*/views.py` |
| Templates | `templates/*/` |
| Static JS | `static/js/` |
| Static CSS | `static/css/` |
| Settings | `invoicing_app/settings.py` |
| URLs | `invoicing_app/urls.py` |
| Tests | `invoicing_app/tests/` |

---

## 🚀 Roadmap

**Planned Features (Q2 2026):**
- [ ] Mobile app (React Native)
- [ ] Payment gateway integration (Stripe, PayPal)
- [ ] Accounting software integration (QuickBooks, Xero)
- [ ] Advanced reporting with drill-down analysis
- [ ] Machine learning for invoice categorization
- [ ] Real-time collaboration features

**Under Consideration:**
- [ ] Multi-language support (i18n)
- [ ] Advanced permission system (granular permissions)
- [ ] White-label solution
- [ ] Blockchain for invoice verification
- [ ] Voice-based data entry

---

## 💡 Tips & Tricks

**Performance Optimization:**
```python
# Use select_related for foreign keys
invoices = Invoice.objects.select_related('client').all()

# Use prefetch_related for reverse foreign keys
clients = Client.objects.prefetch_related('invoices').all()

# Use only() to select specific fields
invoices = Invoice.objects.only('invoice_number', 'total').all()
```

**Development Productivity:**
```bash
# Django shell with IPython
pip install ipython django-extensions
python manage.py shell_plus

# Auto-reload on file changes
python manage.py runserver --reload

# Print SQL queries (development only)
# Add to settings: LOGGING configuration
```

**Database Optimization:**
```python
# Add database indexes on frequently queried fields
class Invoice(models.Model):
    invoice_number = models.CharField(max_length=50, db_index=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, db_index=True)
    created_date = models.DateField(db_index=True)
```

---

## 📧 Contact & Support

**Developer:** Varence-kiiru
**Email:** hernandezngash@gmail.com
**GitHub:** https://github.com/Varence-kiiru
**Repository:** https://github.com/Varence-kiiru/invoice
**Issue Tracker:** https://github.com/Varence-kiiru/invoice/issues
**Discussions:** https://github.com/Varence-kiiru/invoice/discussions

---

**Last Updated:** April 7, 2026
**InvoiceHub v4.5.0** - Professional Invoice Management System
