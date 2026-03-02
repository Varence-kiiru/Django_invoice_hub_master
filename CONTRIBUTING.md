# Contributing to InvoiceHub

Thank you for your interest in contributing to InvoiceHub! This document provides guidelines and instructions for contributing to this production-ready invoicing system.

## Code of Conduct

Please be respectful and professional in all interactions. We're committed to providing a welcoming and inclusive environment for all contributors.

## Current Project Status

**Version:** 3.0.0 (Production Ready)  
**Last Update:** February 28, 2026  

### Completed Features
- ✅ Email Reminders system with Celery scheduling
- ✅ Advanced search and filtering with saved presets
- ✅ Bulk operations (status updates, email sending, deletion)
- ✅ Data import tools (CSV/Excel with validation)
- ✅ Analytics dashboard with real-time metrics

### Active Development Areas
- Payment gateway integration
- Mobile app companion
- Advanced forecasting and predictions
- Custom reporting builder

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check the issue list to avoid duplicates.

When reporting a bug, include:
- Clear, descriptive title
- Exact steps to reproduce the issue
- Expected behavior vs actual behavior
- Screenshots or error messages if applicable
- Your environment (OS, Python version, Django version)
- Browser and console errors (if frontend issue)

**Example:**
```
Title: Dashboard analytics API returns 500 error for payment methods
Steps:
1. Navigate to /analytics/
2. Wait for dashboard to load
3. Check browser console

Error: GET /api/analytics/payment-methods/ 500 Internal Server Error
Environment: Windows 11, Python 3.13, Django 4.2.28
```

### Suggesting Features

Feature requests are welcome! Please provide:
- Clear, descriptive title
- Detailed description of the feature
- Why this feature would be useful
- Possible implementation approaches
- Any relevant examples or mockups
- Which phase/component it relates to

### Code Standards

Before submitting, ensure:
- **Python Code**
  - Follows PEP 8 style guide
  - Includes docstrings for functions/classes
  - Type hints for function signatures
  - Django ORM best practices (no raw SQL when possible)
  
- **JavaScript Code**
  - ES6+ syntax (no legacy IE support)
  - Comments for complex logic
  - Proper error handling
  - No console.log() in production code
  
- **HTML/CSS**
  - Semantic HTML5 structure
  - Comments for complex selectors
  - Mobile-first responsive design
  - WCAG AA accessibility standards

### Pull Requests

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/invoice.git
   cd invoice
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or for bug fixes
   git checkout -b bugfix/issue-description
   ```

3. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

4. **Make your changes**
   - Write clean, readable code
   - Add/update tests if applicable
   - Update documentation if needed
   - Test locally with sample data

5. **Test your changes**
   ```bash
   # Run Django system checks
   python manage.py check
   
   # Run tests (if available)
   python manage.py test
   
   # Check code style
   flake8 invoicing_app/ --max-line-length=120
   ```

6. **Commit with clear messages**
   ```bash
   # Follow conventional commits
   git commit -m "feat: add new feature description"
   git commit -m "fix: resolve issue with payment calculation"
   git commit -m "docs: update API documentation"
   ```

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request**
   - Provide a clear title and description
   - Link any related issues with #123
   - Upload screenshots for UI changes
   - Explain the implementation approach
   - List any breaking changes

## Development Setup

### Prerequisites
- Python 3.13+
- Git
- Virtual environment (venv or virtualenv)
- XAMPP or MySQL server (for production)

### Quick Start
```bash
# Clone and setup
git clone https://github.com/yourusername/invoice.git
cd invoice
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
export DJANGO_SETTINGS_MODULE=invoicing_app.settings.development
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver
# Access at http://localhost:8000
```

### Project Structure
```
invoice/
├── invoicing_app/
│   ├── core/              # Core functionality (auth, settings, analytics)
│   ├── clients/           # Client management
│   ├── invoices/          # Invoice handling
│   ├── payments/          # Payment tracking
│   ├── quotations/        # Quote management
│   ├── expenses/          # Expense tracking
│   ├── taxes/             # Tax calculations
│   └── settings/          # Django settings
├── templates/             # HTML templates
├── static/                # CSS, JavaScript, images
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Testing Guidelines

### What to Test
- ✅ Core functionality (CRUD operations)
- ✅ API endpoints (request/response format)
- ✅ Error handling (invalid inputs, edge cases)
- ✅ Permissions (authentication, authorization)
- ✅ Frontend validation (form inputs, data types)
- ✅ Mobile responsiveness (tablets, phones)

### Test Documentation
Include tests for:
- New API endpoints
- Data validation logic
- Calculation formulas
- Error scenarios

## Documentation Updates

When contributing, update relevant documentation:
- **README.md**: For major features or setup changes
- **CHANGELOG.md**: All code changes
- **Code comments**: Complex logic or non-obvious implementations
- **Docstrings**: All functions and classes

## Questions or Need Help?

- Check existing issues for similar problems
- Review SECURITY.md for security guidelines
- Check README.md for API documentation
- Create a discussion for general questions

Thank you for contributing to InvoiceHub! 🙏

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/invoice.git
cd invoice

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## Code Standards

### Python
- Follow PEP 8
- Maximum line length: 100 characters
- Use meaningful variable names
- Add docstrings to functions and classes

Example:
```python
def calculate_invoice_total(invoice):
    """
    Calculate total amount for an invoice including taxes.
    
    Args:
        invoice: Invoice instance
        
    Returns:
        Decimal: Total amount with tax
    """
    subtotal = invoice.get_subtotal()
    tax = subtotal * invoice.tax_rate
    return subtotal + tax
```

### JavaScript
- Use ES6+ syntax
- Use meaningful variable names
- Add comments for complex logic
- No external dependencies (vanilla JS preferred)

Example:
```javascript
/**
 * Handle bulk checkbox selection
 * @param {Event} event - The change event
 */
function handleSelectAll(event) {
    const isChecked = event.target.checked;
    // Implementation...
}
```

### HTML/CSS
- Use semantic HTML
- Follow responsive design principles
- Use CSS classes for styling
- Avoid inline styles

## Commit Messages

Use clear, descriptive commit messages:

```
Good:
- "Add bulk email sending feature"
- "Fix select all checkbox not checking items"
- "Update invoice filter styling"

Avoid:
- "fix bug"
- "update stuff"
- "work in progress"
```

## Testing

### Running Tests

```bash
# All tests
python manage.py test

# Specific app
python manage.py test invoicing_app.invoices

# Specific test case
python manage.py test invoicing_app.invoices.tests.InvoiceTestCase

# With verbosity
python manage.py test --verbosity=2
```

### Writing Tests

```python
from django.test import TestCase
from invoicing_app.invoices.models import Invoice

class InvoiceTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.invoice = Invoice.objects.create(
            invoice_number="INV-001",
            status="draft"
        )
    
    def test_invoice_creation(self):
        """Test that invoice is created properly"""
        self.assertEqual(self.invoice.status, "draft")
        self.assertTrue(self.invoice.id)
```

## Documentation

When adding features, please update documentation:

1. **README.md** - Add feature description and usage
2. **API Documentation** - Document new endpoints
3. **Code Comments** - Explain complex logic
4. **Docstrings** - Document all functions/classes

## Issues & Discussions

- Use **Issues** for bug reports and feature requests
- Use **Discussions** for questions and general topics
- Search existing issues before creating new ones
- Provide as much context as possible

## Review Process

All pull requests will be reviewed for:
- Code quality and style
- Test coverage
- Documentation
- Security implications
- Performance impact

Feedback will be provided promptly, and revisions may be requested before merging.

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Release checklist:
- [ ] Update version in `__init__.py`
- [ ] Update CHANGELOG
- [ ] Tag release on GitHub
- [ ] Create release notes

## Questions?

- 📖 Check [README.md](README.md) for documentation
- 💬 Start a discussion for questions
- 🐛 Open an issue for bugs

Thank you for contributing to InvoiceHub! 🎉
