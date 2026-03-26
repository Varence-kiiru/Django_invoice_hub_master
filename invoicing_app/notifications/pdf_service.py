"""
PDF generation service for invoices and other documents.
Handles generating and storing invoice PDFs.
"""
import logging
import os
import base64
import mimetypes
from io import BytesIO
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from invoicing_app.invoices.models import Invoice
from invoicing_app.core.models import CompanySettings

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDFs from templates."""
    
    @staticmethod
    def _get_logo_path():
        """
        Get the absolute file path to company logo for PDF generation.
        WeasyPrint needs absolute file paths, not URLs.
        
        Returns:
            Absolute file path if logo exists, None otherwise
        """
        try:
            company_settings = CompanySettings.get_settings()
            if company_settings.company_logo:
                # Get the file path from the ImageField
                logo_path = company_settings.company_logo.path
                
                # Check if file exists
                if os.path.exists(logo_path):
                    logger.info(f"Logo path resolved: {logo_path}")
                    return logo_path
                else:
                    logger.warning(f"Logo file not found at: {logo_path}")
                    return None
        except Exception as e:
            logger.warning(f"Error getting logo path: {str(e)}")
            return None
    
    @staticmethod
    def _get_logo_data_uri():
        """
        Get company logo as a base64 data URI for embedding in PDF.
        This is a more reliable method for PDF generation vs file:// URLs.
        
        Returns:
            Data URI string (e.g., 'data:image/jpeg;base64,...') or empty string if no logo
        """
        try:
            company_settings = CompanySettings.get_settings()
            if company_settings.company_logo:
                logo_path = company_settings.company_logo.path
                
                # Check if file exists
                if not os.path.exists(logo_path):
                    logger.warning(f"Logo file not found at: {logo_path}")
                    return ""
                
                # Read file and encode to base64
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                
                # Determine MIME type
                mime_type, _ = mimetypes.guess_type(logo_path)
                if not mime_type:
                    mime_type = 'image/jpeg'  # Default to JPEG
                
                # Create data URI
                base64_str = base64.b64encode(logo_data).decode('utf-8')
                data_uri = f"data:{mime_type};base64,{base64_str}"
                
                logger.info(f"Logo converted to data URI ({len(base64_str)} chars)")
                return data_uri
        except Exception as e:
            logger.warning(f"Error creating logo data URI: {str(e)}")
            return ""

    @staticmethod
    def _generate_invoice_qr_code(invoice):
        """
        Generate a QR code for invoice containing comprehensive invoice details.
        Returns QR code as base64 data URI for embedding in PDF.
        
        Args:
            invoice: Invoice object with all details
        
        Returns:
            Data URI string for QR code image or empty string if error
        """
        try:
            import qrcode
            from io import BytesIO
            
            # Create comprehensive QR code content with invoice details
            qr_content_lines = [
                f"Invoice: {invoice.invoice_number}",
                f"Date: {invoice.invoice_date.strftime('%d/%m/%Y')}",
                f"Due: {invoice.due_date.strftime('%d/%m/%Y')}",
                f"Billed To: {invoice.client.name}",
                f"Amount: KES {invoice.total_amount:.2f}",
                f"Tax: KES {invoice.vat_amount:.2f}",
                f"Total: KES {invoice.total_amount + invoice.vat_amount:.2f}",
            ]
            
            # Add tax number from company settings if available
            try:
                company_settings = CompanySettings.get_settings()
                if company_settings.tax_id:
                    qr_content_lines.append(f"Tax ID: {company_settings.tax_id}")
            except:
                pass
            
            qr_content = "\n".join(qr_content_lines)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=None,  # Auto-detect size based on data
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for more data
                box_size=10,
                border=2,
            )
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            data_uri = f"data:image/png;base64,{img_data}"
            logger.info(f"Generated comprehensive QR code for invoice {invoice.invoice_number}")
            return data_uri
        except Exception as e:
            logger.warning(f"Error generating QR code: {str(e)}")
            return ""

    @staticmethod
    def _generate_quote_qr_code(quote):
        """
        Generate a QR code for quotation containing comprehensive quotation details.
        Returns QR code as base64 data URI for embedding in PDF.
        
        Args:
            quote: Quote object with all details
        
        Returns:
            Data URI string for QR code image or empty string if error
        """
        try:
            import qrcode
            from io import BytesIO
            
            # Create comprehensive QR code content with quote details
            qr_content_lines = [
                f"Quote: {quote.quote_number}",
                f"Date: {quote.quote_date.strftime('%d/%m/%Y')}",
                f"Valid Until: {quote.valid_until.strftime('%d/%m/%Y')}",
                f"Quoted To: {quote.client.name}",
                f"Amount: KES {quote.total_amount:.2f}",
                f"Tax: KES {quote.vat_amount:.2f}",
                f"Total: KES {quote.total_amount + quote.vat_amount:.2f}",
            ]
            
            # Add tax number from company settings if available
            try:
                company_settings = CompanySettings.get_settings()
                if company_settings.tax_id:
                    qr_content_lines.append(f"Tax ID: {company_settings.tax_id}")
            except:
                pass
            
            qr_content = "\n".join(qr_content_lines)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=None,  # Auto-detect size based on data
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for more data
                box_size=10,
                border=2,
            )
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            data_uri = f"data:image/png;base64,{img_data}"
            logger.info(f"Generated comprehensive QR code for quote {quote.quote_number}")
            return data_uri
        except Exception as e:
            logger.warning(f"Error generating QR code: {str(e)}")
            return ""

    
    @staticmethod
    def generate_invoice_pdf(invoice_id, save=True):
        """
        Generate PDF for invoice using template rendering.
        Checks for existing cached PDF to avoid regeneration.
        
        Args:
            invoice_id: ID of invoice to generate PDF for
            save: Whether to save PDF to storage
        
        Returns:
            String path to PDF file (if save=True) or BytesIO object (if save=False)
        """
        try:
            invoice = Invoice.objects.select_related(
                'client'
            ).prefetch_related(
                'line_items'
            ).get(id=invoice_id)
            
            # Check if PDF already exists in database
            if save and invoice.invoice_pdf and default_storage.exists(invoice.invoice_pdf.name):
                logger.info(f"Using cached PDF for invoice {invoice.invoice_number}")
                return invoice.invoice_pdf.name
            
            # Get company settings
            company_settings = CompanySettings.get_settings()
            
            # Get logo as base64 data URI for embedding in PDF
            logo_data_uri = PDFService._get_logo_data_uri()
            
            # Generate QR code for invoice with comprehensive details
            qr_code_data_uri = PDFService._generate_invoice_qr_code(invoice)
            
            # Prepare context
            context = {
                'invoice': invoice,
                'line_items': invoice.line_items.all(),
                'company_name': company_settings.company_name,
                'company_address': company_settings.company_address,
                'company_phone': company_settings.company_phone,
                'company_email': company_settings.company_email,
                'company_logo': logo_data_uri if logo_data_uri else None,  # Use data URI for PDF
                'invoice_qr_code': qr_code_data_uri if qr_code_data_uri else None,  # Add QR code
                'company_tax_id': company_settings.tax_id,
                # Bank Details for payment display
                'bank_account_name': company_settings.bank_account_name,
                'bank_account_number': company_settings.bank_account_number,
                'bank_name': company_settings.bank_name,
                'bank_branch': company_settings.bank_branch,
                'bank_swift_code': company_settings.bank_swift_code,
                'bank_iban': company_settings.bank_iban,
                # M-Pesa Details for payment display
                'mpesa_paybill_number': company_settings.mpesa_paybill_number,
                'mpesa_account_name': company_settings.mpesa_account_name,
                'mpesa_phone': company_settings.mpesa_phone,
                # Payment Terms for display on unpaid/partially paid invoices
                'default_payment_terms': company_settings.default_payment_terms,
            }
            
            # Render HTML template
            html_string = render_to_string(
                'invoicing_app/invoices/invoice_pdf.html',
                context
            )
            
            # Generate PDF (using simple approach - in production use WeasyPrint or similar)
            pdf_content = PDFService._html_to_pdf(html_string)
            
            if save:
                # Save to storage and update model
                filename = f'invoices/pdfs/{invoice.invoice_number}.pdf'
                path = default_storage.save(filename, ContentFile(pdf_content))
                
                # Store path in database to avoid regeneration
                invoice.invoice_pdf = path
                invoice.save(update_fields=['invoice_pdf'])
                
                logger.info(f"Saved PDF for invoice {invoice.invoice_number} to {path}")
                return path
            else:
                # Return BytesIO object
                return BytesIO(pdf_content)
        
        except Invoice.DoesNotExist:
            logger.error(f"Invoice {invoice_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error generating PDF for invoice {invoice_id}: {str(e)}")
            raise
    
    @staticmethod
    def generate_quote_pdf(quote_id, save=True):
        """
        Generate PDF for quotation using template rendering.
        Checks for existing cached PDF to avoid regeneration.
        
        Args:
            quote_id: ID of quotation to generate PDF for
            save: Whether to save PDF to storage
        
        Returns:
            String path to PDF file (if save=True) or BytesIO object (if save=False)
        """
        try:
            from invoicing_app.quotations.models import Quote
            
            quote = Quote.objects.select_related(
                'client'
            ).prefetch_related(
                'line_items'
            ).get(id=quote_id)
            
            # Check if PDF already exists in database
            if save and quote.quote_pdf and default_storage.exists(quote.quote_pdf.name):
                logger.info(f"Using cached PDF for quotation {quote.quote_number}")
                return quote.quote_pdf.name
            
            # Get company settings
            company_settings = CompanySettings.get_settings()
            
            # Get logo as base64 data URI for embedding in PDF
            logo_data_uri = PDFService._get_logo_data_uri()
            
            # Generate QR code for quote with comprehensive details
            qr_code_data_uri = PDFService._generate_quote_qr_code(quote)
            
            # Prepare context
            context = {
                'quote': quote,
                'line_items': quote.line_items.all(),
                'company_settings': company_settings,
                'company_logo': logo_data_uri if logo_data_uri else None,  # Use data URI for PDF
                'quote_qr_code': qr_code_data_uri if qr_code_data_uri else None,  # Add QR code
                # Bank Details for payment display
                'bank_account_name': company_settings.bank_account_name,
                'bank_account_number': company_settings.bank_account_number,
                'bank_name': company_settings.bank_name,
                'bank_branch': company_settings.bank_branch,
                'bank_swift_code': company_settings.bank_swift_code,
                'bank_iban': company_settings.bank_iban,
                # M-Pesa Details for payment display
                'mpesa_paybill_number': company_settings.mpesa_paybill_number,
                'mpesa_account_name': company_settings.mpesa_account_name,
                'mpesa_phone': company_settings.mpesa_phone,
            }
            
            # Render HTML template
            html_string = render_to_string(
                '13_quotations/quote_pdf.html',
                context
            )
            
            # Generate PDF
            pdf_content = PDFService._html_to_pdf(html_string)
            
            if save:
                # Save to storage and update model
                filename = f'quotations/pdfs/{quote.quote_number}.pdf'
                path = default_storage.save(filename, ContentFile(pdf_content))
                
                # Store path in database to avoid regeneration
                quote.quote_pdf = path
                quote.save(update_fields=['quote_pdf'])
                
                logger.info(f"Saved PDF for quotation {quote.quote_number} to {path}")
                return path
            else:
                # Return BytesIO object
                return BytesIO(pdf_content)
        
        except Exception as e:
            logger.error(f"Error generating PDF for quotation {quote_id}: {str(e)}")
            raise
    
    @staticmethod
    def _html_to_pdf(html_string):
        """
        Convert HTML string to PDF bytes.
        
        This is a placeholder implementation.
        In production, use WeasyPrint or xhtml2pdf:
        
        from weasyprint import HTML, CSS
        doc = HTML(string=html_string)
        return doc.write_pdf()
        
        Returns:
            Bytes of PDF content
        """
        try:
            # Try to use WeasyPrint if installed
            from weasyprint import HTML
            doc = HTML(string=html_string)
            return doc.write_pdf()
        except ImportError:
            # Fallback: placeholder - in production, use proper library
            logger.warning("WeasyPrint not installed, returning mock PDF")
            return b"%PDF-1.4\n"  # Minimal valid PDF header
    
    @staticmethod
    def generate_invoice_batch_pdf(invoice_ids, save=True):
        """
        Generate merged PDF for multiple invoices.
        
        Args:
            invoice_ids: List of invoice IDs
            save: Whether to save to storage
        
        Returns:
            Path to merged PDF file
        """
        try:
            from datetime import datetime
            
            invoices = Invoice.objects.filter(
                id__in=invoice_ids
            ).select_related('client')
            
            # Get company settings
            company_settings = CompanySettings.get_settings()
            
            # Get logo as base64 data URI for embedding in PDF
            logo_data_uri = PDFService._get_logo_data_uri()
            
            # Render all invoices
            html_pages = []
            for invoice in invoices:
                context = {
                    'invoice': invoice,
                    'line_items': invoice.line_items.all(),
                    'company_name': company_settings.company_name,
                    'company_address': company_settings.company_address,
                    'company_phone': company_settings.company_phone,
                    'company_email': company_settings.company_email,
                    'company_logo': logo_data_uri if logo_data_uri else None,  # Use data URI for PDF
                    'company_tax_id': company_settings.tax_id,
                    'default_payment_terms': company_settings.default_payment_terms,
                }
                html = render_to_string(
                    'invoicing_app/invoices/invoice_pdf.html',
                    context
                )
                html_pages.append(html)
            
            # Merge and create PDF
            merged_html = '<div class="page-break">'.join(html_pages)
            pdf_content = PDFService._html_to_pdf(merged_html)
            
            if save:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'invoices/batch_{timestamp}_{len(invoice_ids)}_invoices.pdf'
                path = default_storage.save(filename, ContentFile(pdf_content))
                logger.info(f"Saved batch PDF with {len(invoice_ids)} invoices to {path}")
                return path
            else:
                return BytesIO(pdf_content)
        
        except Exception as e:
            logger.error(f"Error generating batch PDF: {str(e)}")
            raise
    
    @staticmethod
    def generate_payment_receipt_pdf(payment_id, save=True):
        """
        Generate PDF for payment receipt using template rendering.
        
        Args:
            payment_id: ID of payment to generate receipt for
            save: Whether to save PDF to storage
        
        Returns:
            String path to PDF file (if save=True) or bytes (if save=False)
        """
        try:
            from invoicing_app.payments.models import Payment
            from django.db.models import Sum
            
            payment = Payment.objects.select_related(
                'invoice',
                'invoice__client',
                'payment_method',
                'recorded_by'
            ).get(id=payment_id)
            
            # Check if PDF already exists (only when saving)
            if save and payment.receipt_pdf and default_storage.exists(payment.receipt_pdf.name):
                logger.info(f"PDF receipt already exists for payment {payment_id}: {payment.receipt_pdf.name}")
                return payment.receipt_pdf.name
            
            # Get company settings
            company_settings = CompanySettings.get_settings()
            
            # Get logo as base64 data URI for embedding in PDF
            logo_data_uri = PDFService._get_logo_data_uri()
            
            # Calculate previous payments
            previous_payments = payment.invoice.payments.exclude(id=payment.id).aggregate(total=Sum('amount'))['total'] or 0
            
            # Prepare context
            context = {
                'payment': payment,
                'previous_payments': previous_payments,
                'company_name': company_settings.company_name,
                'company_address': company_settings.company_address,
                'company_phone': company_settings.company_phone,
                'company_email': company_settings.company_email,
                'company_logo': logo_data_uri if logo_data_uri else None,  # Use data URI for PDF
                'company_tax_id': company_settings.tax_id,
            }
            
            # Render HTML template
            html_string = render_to_string(
                '7_payments/payment_receipt_pdf.html',
                context
            )
            
            # Generate PDF
            pdf_content = PDFService._html_to_pdf(html_string)
            
            if save:
                # Save to storage
                filename = f'payments/receipts/receipt_{payment.id}_{payment.invoice.invoice_number}.pdf'
                path = default_storage.save(filename, ContentFile(pdf_content))
                
                # Store reference in database
                payment.receipt_pdf = path
                payment.save(update_fields=['receipt_pdf'])
                
                logger.info(f"Saved PDF receipt for payment {payment.id} to {path}")
                return path  # Return path for file operations
            else:
                # Return bytes directly
                return pdf_content
        
        except Exception as e:
            logger.error(f"Error generating PDF for payment {payment_id}: {str(e)}")
            raise

    @staticmethod
    def generate_report_pdf(report_type, context, template_name, filename_prefix):
        """
        Generate PDF for a report using template rendering.
        
        Args:
            report_type: Type of report (e.g., 'invoices', 'vat', 'payments')
            context: Dictionary with report context data
            template_name: Name of the template to render
            filename_prefix: Prefix for the filename
        
        Returns:
            Bytes of PDF content (ready to serve as HTTP response)
        """
        try:
            from django.utils import timezone
            
            # Get company settings
            company_settings = CompanySettings.get_settings()
            
            # Get logo as base64 data URI for embedding in PDF
            logo_data_uri = PDFService._get_logo_data_uri()
            
            # Add company info to context
            context.update({
                'company_name': company_settings.company_name,
                'company_address': company_settings.company_address,
                'company_phone': company_settings.company_phone,
                'company_email': company_settings.company_email,
                'company_logo': logo_data_uri if logo_data_uri else None,
                'company_tax_id': company_settings.tax_id,
                'generated_date': timezone.now(),
            })
            
            # Render HTML template
            html_string = render_to_string(template_name, context)
            
            # Generate PDF
            pdf_content = PDFService._html_to_pdf(html_string)
            
            logger.info(f"Generated {report_type} report PDF ({len(pdf_content)} bytes)")
            return pdf_content
        
        except Exception as e:
            logger.error(f"Error generating {report_type} report PDF: {str(e)}")
            raise

    @staticmethod
    def generate_delivery_pdf(delivery_id, save=True):
        """
        Generate PDF for delivery challan using template rendering.
        Matches invoice PDF formatting.
        
        Args:
            delivery_id: ID of delivery to generate PDF for
            save: Whether to save PDF to storage
        
        Returns:
            String path to PDF file (if save=True) or BytesIO object (if save=False)
        """
        try:
            from invoicing_app.deliveries.models import Delivery
            
            delivery = Delivery.objects.select_related(
                'invoice',
                'invoice__client'
            ).prefetch_related(
                'line_items'
            ).get(id=delivery_id)
            
            # Check if PDF already exists in database
            if save and hasattr(delivery, 'delivery_pdf') and delivery.delivery_pdf and default_storage.exists(delivery.delivery_pdf.name):
                logger.info(f"Using cached PDF for delivery {delivery.delivery_number}")
                return delivery.delivery_pdf.name
            
            # Get company settings
            company_settings = CompanySettings.get_settings()
            
            # Get logo as base64 data URI for embedding in PDF
            logo_data_uri = PDFService._get_logo_data_uri()
            
            # Prepare context
            context = {
                'delivery': delivery,
                'invoice': delivery.invoice,
                'line_items': delivery.line_items.all(),
                'company_name': company_settings.company_name,
                'company_address': company_settings.company_address,
                'company_phone': company_settings.company_phone,
                'company_email': company_settings.company_email,
                'company_logo': logo_data_uri if logo_data_uri else None,  # Use data URI for PDF
                'company_tax_id': company_settings.tax_id,
            }
            
            # Render HTML template
            html_string = render_to_string(
                '14_deliveries/delivery_pdf.html',
                context
            )
            
            # Generate PDF
            pdf_content = PDFService._html_to_pdf(html_string)
            
            if save:
                # Save to storage
                filename = f'deliveries/pdfs/{delivery.delivery_number}.pdf'
                path = default_storage.save(filename, ContentFile(pdf_content))
                
                logger.info(f"Saved PDF for delivery {delivery.delivery_number} to {path}")
                return path
            else:
                # Return BytesIO object
                return BytesIO(pdf_content)
        
        except Delivery.DoesNotExist:
            logger.error(f"Delivery {delivery_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error generating PDF for delivery {delivery_id}: {str(e)}")
            raise


# Create singleton instance
pdf_service = PDFService()