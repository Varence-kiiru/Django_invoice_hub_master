"""
Data import functionality for CSV and Excel files.
Supports importing invoices, payments, clients, and quotations with validation.
"""

import csv
import json
import logging
from io import StringIO, BytesIO
from datetime import datetime
from decimal import Decimal

import openpyxl
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction

from invoicing_app.invoices.models import Invoice
from invoicing_app.payments.models import Payment
from invoicing_app.clients.models import Client
from invoicing_app.quotations.models import Quote

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates imported data before saving to database"""
    
    REQUIRED_FIELDS = {
        'invoice': ['invoice_number', 'client_id', 'total_amount'],
        'payment': ['invoice_id', 'amount', 'payment_date'],
        'client': ['name', 'email'],
        'quotation': ['quote_number', 'client_id', 'total_amount'],
    }
    
    OPTIONAL_FIELDS = {
        'invoice': ['status', 'due_date', 'description'],
        'payment': ['payment_method_id', 'status'],
        'client': ['phone', 'status', 'tax_id'],
        'quotation': ['status', 'valid_until'],
    }

    def __init__(self, entity_type):
        self.entity_type = entity_type
        self.errors = []
        self.warnings = []

    def validate_row(self, row, row_number):
        """Validate a single row of data"""
        row_errors = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS.get(self.entity_type, []):
            if field not in row or not row[field]:
                row_errors.append(f"Missing required field: {field}")
        
        # Validate data types
        if self.entity_type == 'invoice':
            row_errors.extend(self._validate_invoice_row(row))
        elif self.entity_type == 'payment':
            row_errors.extend(self._validate_payment_row(row))
        elif self.entity_type == 'client':
            row_errors.extend(self._validate_client_row(row))
        elif self.entity_type == 'quotation':
            row_errors.extend(self._validate_quotation_row(row))
        
        return row_errors

    def _validate_invoice_row(self, row):
        """Validate invoice-specific fields"""
        errors = []
        
        try:
            Decimal(str(row.get('total_amount', 0)))
        except:
            errors.append("Invalid amount format")
        
        if 'due_date' in row and row['due_date']:
            if not self._is_valid_date(row['due_date']):
                errors.append("Invalid due_date format (use YYYY-MM-DD)")
        
        status = row.get('status', 'draft')
        valid_statuses = ['draft', 'sent', 'issued', 'paid', 'partially_paid', 'overdue', 'cancelled']
        if status not in valid_statuses:
            errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        return errors

    def _validate_payment_row(self, row):
        """Validate payment-specific fields"""
        errors = []
        
        try:
            Decimal(str(row.get('amount', 0)))
        except:
            errors.append("Invalid amount format")
        
        if not self._is_valid_date(row.get('payment_date')):
            errors.append("Invalid payment_date format (use YYYY-MM-DD)")
        
        return errors

    def _validate_client_row(self, row):
        """Validate client-specific fields"""
        errors = []
        
        email = row.get('email', '')
        if email and '@' not in email:
            errors.append("Invalid email format")
        
        return errors

    def _validate_quotation_row(self, row):
        """Validate quotation-specific fields"""
        errors = []
        
        try:
            Decimal(str(row.get('total_amount', 0)))
        except:
            errors.append("Invalid amount format")
        
        if 'valid_until' in row and row['valid_until']:
            if not self._is_valid_date(row['valid_until']):
                errors.append("Invalid valid_until format (use YYYY-MM-DD)")
        
        return errors

    @staticmethod
    def _is_valid_date(date_string):
        """Check if string is valid date (YYYY-MM-DD)"""
        if not date_string:
            return True
        try:
            datetime.strptime(str(date_string).strip(), '%Y-%m-%d')
            return True
        except:
            return False


class DuplicateDetector:
    """Detects duplicate entries in imported data"""
    
    def __init__(self, entity_type):
        self.entity_type = entity_type
    
    def find_duplicates(self, data):
        """Find duplicate entries in data"""
        duplicates = []
        seen = set()
        
        for idx, row in enumerate(data):
            key = self._get_unique_key(row)
            if key in seen:
                duplicates.append({
                    'row': idx + 2,  # +2 for header and 0-indexing
                    'key': key,
                    'data': row
                })
            else:
                seen.add(key)
        
        return duplicates

    def _get_unique_key(self, row):
        """Get unique identifier for row based on entity type"""
        if self.entity_type == 'invoice':
            return row.get('invoice_number', '')
        elif self.entity_type == 'payment':
            return f"{row.get('invoice_id')}-{row.get('payment_date')}"
        elif self.entity_type == 'client':
            return row.get('name', '') + row.get('email', '')
        elif self.entity_type == 'quotation':
            return row.get('quote_number', '')
        return str(row)


class DataImporter:
    """Main data importer handling CSV and Excel files"""
    
    def __init__(self, entity_type, file_content, file_type='csv'):
        self.entity_type = entity_type
        self.file_content = file_content
        self.file_type = file_type
        self.validator = DataValidator(entity_type)
        self.detector = DuplicateDetector(entity_type)
        self.data = []
        self.results = {
            'imported': 0,
            'failed': 0,
            'duplicates': 0,
            'errors': [],
            'warnings': [],
        }

    def parse(self):
        """Parse CSV or Excel file"""
        try:
            if self.file_type == 'csv':
                self.data = self._parse_csv()
            elif self.file_type == 'xlsx':
                self.data = self._parse_excel()
            return True
        except Exception as e:
            self.results['errors'].append(f"Parse error: {str(e)}")
            return False

    def _parse_csv(self):
        """Parse CSV file"""
        data = []
        content = self.file_content.decode('utf-8') if isinstance(self.file_content, bytes) else self.file_content
        
        reader = csv.DictReader(StringIO(content))
        for row in reader:
            data.append(row)
        
        return data

    def _parse_excel(self):
        """Parse Excel file"""
        data = []
        workbook = openpyxl.load_workbook(BytesIO(self.file_content))
        worksheet = workbook.active
        
        # Get headers from first row
        headers = [cell.value for cell in worksheet[1]]
        
        # Parse data rows
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            row_dict = {headers[i]: row[i] for i in range(len(headers)) if i < len(row)}
            data.append(row_dict)
        
        return data

    def validate(self):
        """Validate all data before import"""
        for idx, row in enumerate(self.data):
            errors = self.validator.validate_row(row, idx + 2)
            if errors:
                self.results['errors'].append({
                    'row': idx + 2,
                    'errors': errors
                })

    def check_duplicates(self):
        """Check for duplicates in data"""
        duplicates = self.detector.find_duplicates(self.data)
        self.results['duplicates'] = len(duplicates)
        
        if duplicates:
            self.results['warnings'].append({
                'type': 'duplicate',
                'count': len(duplicates),
                'samples': duplicates[:5]
            })

    @transaction.atomic
    def import_data(self):
        """Import validated data into database"""
        if self.results['errors']:
            return False
        
        for idx, row in enumerate(self.data):
            try:
                if self.entity_type == 'invoice':
                    self._import_invoice(row)
                elif self.entity_type == 'payment':
                    self._import_payment(row)
                elif self.entity_type == 'client':
                    self._import_client(row)
                elif self.entity_type == 'quotation':
                    self._import_quotation(row)
                
                self.results['imported'] += 1
            except Exception as e:
                self.results['failed'] += 1
                self.results['errors'].append({
                    'row': idx + 2,
                    'error': str(e)
                })
                logger.error(f"Import error at row {idx + 2}: {str(e)}")

    def _import_invoice(self, row):
        """Import invoice row"""
        Invoice.objects.create(
            invoice_number=row['invoice_number'],
            client_id=int(row['client_id']),
            total_amount=Decimal(str(row['total_amount'])),
            status=row.get('status', 'draft'),
            due_date=self._parse_date(row.get('due_date')),
            description=row.get('description', ''),
        )

    def _import_payment(self, row):
        """Import payment row"""
        Payment.objects.create(
            invoice_id=int(row['invoice_id']),
            amount=Decimal(str(row['amount'])),
            payment_date=self._parse_date(row['payment_date']),
            payment_method_id=int(row.get('payment_method_id')) if row.get('payment_method_id') else None,
            status=row.get('status', 'confirmed'),
        )

    def _import_client(self, row):
        """Import client row"""
        Client.objects.create(
            name=row['name'],
            email=row['email'],
            phone=row.get('phone', ''),
            status=row.get('status', 'active'),
            tax_id=row.get('tax_id', ''),
        )

    def _import_quotation(self, row):
        """Import quotation row"""
        Quote.objects.create(
            quote_number=row['quote_number'],
            client_id=int(row['client_id']),
            total_amount=Decimal(str(row['total_amount'])),
            status=row.get('status', 'draft'),
            valid_until=self._parse_date(row.get('valid_until')),
        )

    @staticmethod
    def _parse_date(date_string):
        """Parse date string"""
        if not date_string:
            return None
        try:
            return datetime.strptime(str(date_string).strip(), '%Y-%m-%d').date()
        except:
            return None

    def get_results(self):
        """Get import results"""
        return {
            'success': len(self.results['errors']) == 0,
            'imported_count': self.results['imported'],
            'failed_count': self.results['failed'],
            'duplicate_count': self.results['duplicates'],
            'errors': self.results['errors'][:10],  # Limit to first 10
            'warnings': self.results['warnings'],
            'total_rows': len(self.data),
        }


@login_required
@require_http_methods(["POST"])
def import_data(request):
    """API endpoint for data import"""
    try:
        entity_type = request.POST.get('entity_type')
        file = request.FILES.get('file')
        
        if not entity_type or not file:
            return JsonResponse({
                'success': False,
                'error': 'Missing entity_type or file'
            }, status=400)
        
        # Determine file type
        file_type = 'xlsx' if file.name.endswith('.xlsx') else 'csv'
        
        # Read file content
        file_content = file.read()
        
        # Create importer
        importer = DataImporter(entity_type, file_content, file_type)
        
        # Parse file
        if not importer.parse():
            return JsonResponse({
                'success': False,
                'error': importer.results['errors'][0]
            }, status=400)
        
        # Validate data
        importer.validate()
        
        # Check duplicates
        importer.check_duplicates()
        
        # If no validation errors, import data
        if not importer.results['errors']:
            importer.import_data()
        
        return JsonResponse(importer.get_results())
    
    except Exception as e:
        logger.error(f"Import error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_import_template(request):
    """Get CSV/Excel template for data import"""
    entity_type = request.GET.get('entity_type', 'invoice')
    
    templates = {
        'invoice': {
            'headers': ['invoice_number', 'client_id', 'total_amount', 'status', 'due_date', 'description'],
            'example': {
                'invoice_number': 'INV-001',
                'client_id': '1',
                'total_amount': '1500.00',
                'status': 'draft',
                'due_date': '2026-03-31',
                'description': 'Invoice description'
            }
        },
        'payment': {
            'headers': ['invoice_id', 'amount', 'payment_date', 'payment_method_id', 'status'],
            'example': {
                'invoice_id': '1',
                'amount': '1500.00',
                'payment_date': '2026-02-28',
                'payment_method_id': '1',
                'status': 'confirmed'
            }
        },
        'client': {
            'headers': ['name', 'email', 'phone', 'status', 'tax_id'],
            'example': {
                'name': 'Acme Corporation',
                'email': 'contact@acme.com',
                'phone': '+1-555-0100',
                'status': 'active',
                'tax_id': 'TAX123456'
            }
        },
        'quotation': {
            'headers': ['quote_number', 'client_id', 'total_amount', 'status', 'valid_until'],
            'example': {
                'quote_number': 'QT-001',
                'client_id': '1',
                'total_amount': '2500.00',
                'status': 'draft',
                'valid_until': '2026-03-31'
            }
        }
    }
    
    template = templates.get(entity_type, templates['invoice'])
    
    return JsonResponse({
        'success': True,
        'entity_type': entity_type,
        'headers': template['headers'],
        'example': template['example'],
        'notes': [
            'Required fields: ' + ', '.join(DataValidator.REQUIRED_FIELDS.get(entity_type, [])),
            'Dates should be in YYYY-MM-DD format',
            'Decimals should use . as separator (e.g., 1500.00)',
            'IDs should be valid references to existing records'
        ]
    })

@login_required
@require_http_methods(["GET"])
def get_import_history(request):
    """API endpoint for import history"""
    # Return empty history for now - can be expanded with audit log integration
    return JsonResponse({
        'success': True,
        'data': []
    })