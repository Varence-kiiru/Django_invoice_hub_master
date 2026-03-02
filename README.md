# InvoiceHub - Professional Invoice Management System

A comprehensive, Django-based invoicing application with advanced features for managing invoices, payments, clients, and quotations.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Project Status](#project-status)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Features by Priority](#features-by-priority)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

---

## 🎯 Overview

InvoiceHub is a modern, feature-rich invoicing and invoice management system designed for businesses of all sizes. It provides:

- **Invoice Management**: Create, edit, send, and track invoices
- **Payment Tracking**: Record and manage client payments with multiple payment methods
- **Client Management**: Maintain comprehensive client databases with contact information
- **Quotations**: Generate and manage price quotations with conversion tracking
- **Advanced Filtering**: Powerful search and filter capabilities across all modules
- **Bulk Operations**: Batch actions for status updates, email sending, and data management
- **Email Automation**: Automated email reminders and document distribution
- **Reporting**: Comprehensive reports on sales, payments, taxes, and aging

---

## ✨ Key Features

### Priority 1: Core Infrastructure ✅
- ✅ Email Reminders system with scheduling
- ✅ Advanced Search & Filtering with saved presets
- ✅ Full-text search with autocomplete suggestions
- ✅ Real-time filter suggestions for all entities

### Priority 2: Bulk Operations ✅
- ✅ Batch status updates for invoices, payments, quotations
- ✅ Bulk email sending (invoices, quotations, reminders, custom)
- ✅ Batch deletion with error handling
- ✅ Checkbox-based item selection with "Select All"
- ✅ Modal dialogs for bulk actions

### Priority 3: Data Import & Analytics ✅ **NEW**
- ✅ CSV/Excel data import with validation
- ✅ Duplicate detection and handling
- ✅ Multi-entity support (invoices, payments, clients, quotations)
- ✅ Real-time dashboard analytics
- ✅ Financial metrics and KPIs
- ✅ Aging report and payment analysis
- ✅ Timeline charts and trends
- ✅ Top clients and payment method breakdown

### Premium Features
- 🔒 Role-based access control (RBAC)
- 📊 Advanced financial reporting
- 💰 Partial payment tracking
- 📱 Mobile-responsive design
- 📧 Email template management
- 🔔 Smart notifications

---

## 📊 Project Status

| Component | Status | Priority | UI | Backend |
|-----------|--------|---|----|----|
| Email Reminders | ✅ Complete | 1A | ✅ | ✅ |
| Advanced Filtering | ✅ Complete | 1B | ✅ | ✅ |
| Bulk Operations | ✅ Complete | 2A | ✅ | ✅ |
| Data Import Tools | ✅ Complete | 2B | ✅ Phase 4 | ✅ Phase 3 |
| Dashboard Analytics | ✅ Complete | 3 | ✅ Phase 4 | ✅ Phase 3 |

**Version:** 3.0.0  
**Last Updated:** February 28, 2026  
**Status:** Production Ready ✅

---

## 🎯 Phase 4 - UI Implementation (Complete ✅)

### Component 1: Data Import Modal (Complete ✅)
- 4-step import workflow with progress tracking
- CSV/Excel file upload with validation
- Real-time data preview
- Detailed error reporting
- Integrated at `/import/` 

### Component 2: Analytics Dashboard (Complete ✅)
- 6 dashboard widgets displaying real-time metrics
- Financial summary cards (revenue, A/R, avg transaction, payment rate)
- Invoice timeline chart (line graph)
- Payment timeline chart (line graph)
- Aging report widget (A/R breakdown by days)
- Top clients table (top 10 by revenue)
- Payment methods distribution (pie/doughnut chart)
- Responsive mobile design
- Auto-refresh (5-minute intervals)
- Dynamic currency formatting from system settings
- Accessible at `/analytics/`

### Technology
- **UI**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Charts**: Chart.js 3.9.1
- **Features**: Responsive design, error handling, loading states, mobile-optimized
- **Code Quality**: 2800+ lines of production-ready code

---

## 🛠 Technology Stack

**Backend:**
- Python 3.13+
- Django 4.2+
- PostgreSQL (production) / SQLite (development)
- Celery (task scheduling)
- Django REST Framework (API)

**Frontend:**
- HTML5 / CSS3
- Vanilla JavaScript (ES6+)
- Responsive design patterns
- Service Worker support

**Infrastructure:**
- XAMPP (local development)
- GitHub version control
- Email backends (SMTP, Sendgrid)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- pip (Python package manager)
- Git
- XAMPP (for local MySQL)

### Installation

1. **Clone the repository:**
   ```bash
   cd c:\xampp\htdocs\invoice
   ```

2. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\Activate.ps1
   
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Load demo data (optional):**
   ```bash
   python manage.py demo_filters
   ```

7. **Start development server:**
   ```bash
   python manage.py runserver
   ```

8. **Access the application:**
   - Open http://localhost:8000 in your browser
   - Login with your superuser credentials

---

## 📁 Project Structure

```
invoice/
├── invoicing_app/
│   ├── core/                      # Core app (auth, dashboard, reports)
│   │   ├── models.py              # Core models (User, Company, Settings)
│   │   ├── views_html.py          # HTML views
│   │   ├── api_filters.py         # Advanced filtering API
│   │   ├── api_bulk_operations.py # Bulk operations API
│   │   ├── urls.py                # URL routing
│   │   └── email_service.py       # Email operations
│   │
│   ├── invoices/                  # Invoice module
│   │   ├── models.py              # Invoice, InvoiceLineItem
│   │   ├── views_html.py          # Invoice views
│   │   ├── forms.py               # Invoice forms
│   │   └── urls.py
│   │
│   ├── payments/                  # Payment module
│   │   ├── models.py              # Payment, PaymentMethod
│   │   ├── views_html.py          # Payment views
│   │   └── forms.py
│   │
│   ├── clients/                   # Client module
│   │   ├── models.py              # Client model
│   │   ├── views_html.py          # Client views
│   │   └── forms.py
│   │
│   ├── quotations/                # Quotation module
│   │   ├── models.py              # Quote, QuoteLineItem
│   │   ├── views_html.py          # Quote views
│   │   └── forms.py
│   │
│   ├── notifications/             # Email & reminders
│   │   ├── models.py              # EmailTemplate, Reminder
│   │   ├── email_service.py       # Email handling
│   │   ├── reminder_service.py    # Reminder scheduling
│   │   └── tasks.py               # Celery tasks
│   │
│   └── settings.py                # Django settings
│
├── templates/
│   ├── layouts/                   # Base layouts
│   │   └── base.html              # Master template
│   ├── 2_auth/                    # Authentication pages
│   ├── 4_clients/                 # Client pages
│   ├── 6_invoices/                # Invoice pages
│   ├── 7_payments/                # Payment pages
│   ├── 10_modals/                 # Modal components
│   ├── 13_quotations/             # Quotation pages
│   └── 99_dashboard/              # Dashboard pages
│
├── static/
│   ├── js/
│   │   ├── app.js                 # Main application
│   │   ├── filter_system.js       # Advanced filtering
│   │   ├── bulk_operations.js     # Bulk actions handler
│   │   └── pages/                 # Page-specific scripts
│   ├── css/
│   │   ├── style.css              # Main stylesheet
│   │   └── pages/                 # Page-specific styles
│   └── images/
│
├── manage.py                      # Django management
├── requirements.txt               # Python dependencies
└── README.md                      # This file
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

## 📞 Support

### Getting Help

**For Bug Reports:**
1. Open GitHub Issues
2. Include:
   - Django version: `python manage.py version`
   - Steps to reproduce
   - Error message and traceback
   - Browser and OS information

**For Feature Requests:**
1. Create discussion in GitHub Discussions
2. Describe use case and benefits
3. Link related issues if applicable

**Common Resources:**
- Django Documentation: https://docs.djangoproject.com
- Django REST Framework: https://www.django-rest-framework.org
- Mozilla JavaScript Guide: https://developer.mozilla.org/en-US/docs/Web/JavaScript

---

## 📝 Version History

**Current Version:** 2.0.0 (February 28, 2026)

### 2.0.0 - Major Release
- ✅ Email reminders system
- ✅ Advanced filtering with presets
- ✅ Bulk operations (status, email, delete)
- ✅ Fixed entity type normalization

### 1.5.0 - Previous Release
- Core invoice/payment/client management
- Basic reporting
- User authentication

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🤝 Contributing

### Development Workflow

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes:**
   ```bash
   # Edit files
   # Test changes
   # Commit regularly
   git commit -m "Descriptive message"
   ```

3. **Push and create pull request:**
   ```bash
   git push origin feature/my-feature
   ```

4. **Code review and merge**

### Code Standards
- PEP 8 for Python code
- ESLint for JavaScript
- Meaningful commit messages
- Comprehensive docstrings
- Unit tests for new features

---

## 🎓 Quick Reference

| Task | Command |
|------|---------|
| Start server | `python manage.py runserver` |
| Run migrations | `python manage.py migrate` |
| Create user | `python manage.py createsuperuser` |
| Load demo data | `python manage.py demo_filters` |
| Run tests | `python manage.py test` |
| Collect static files | `python manage.py collectstatic` |
| Check configuration | `python manage.py check` |

---

## 🚀 Getting Started with Features

### First Time Setup Checklist

- [ ] Create superuser account
- [ ] Configure company settings (Settings → Company)
- [ ] Add payment methods (Settings → Payment Methods)
- [ ] Create 2-3 test clients (Clients → New)
- [ ] Create test invoices (Invoices → New)
- [ ] Test email by sending to yourself
- [ ] Try bulk operations on test invoices
- [ ] Test filtering and saved filters
- [ ] Review dashboard and reports

### Next Steps

1. **Load real data:**
   - Import clients from CSV/Excel
   - Create recurring invoices for products
   - Set up invoice templates

2. **Customize:**
   - Adjust invoice numbering format
   - Create custom email templates
   - Set payment terms and conditions

3. **Integrate:**
   - Connect accounting software
   - Set up payment gateway integration
   - Enable automated recurring invoices

---

**Last Updated:** February 28, 2026
