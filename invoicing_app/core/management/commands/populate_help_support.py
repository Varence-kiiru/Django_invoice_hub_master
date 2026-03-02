"""Management command to populate sample Help & Support data."""
from django.core.management.base import BaseCommand
from invoicing_app.core.models import FAQ, HelpArticle
from django.utils.text import slugify


class Command(BaseCommand):
    """Populate sample Help & Support data."""
    
    help = 'Populate sample FAQs and Help Articles for demonstration'

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Starting to populate Help & Support data...'))
        
        # Sample FAQs
        faqs_data = [
            {
                'category': 'invoicing',
                'question': 'How do I create a new invoice?',
                'answer': 'To create a new invoice:\n1. Navigate to Invoices in the sidebar\n2. Click "New Invoice"\n3. Select a client\n4. Add line items\n5. Set payment terms\n6. Click Save\n\nYour invoice will be automatically numbered based on your settings.',
                'order': 1,
            },
            {
                'category': 'invoicing',
                'question': 'Can I customize invoice templates?',
                'answer': 'Yes! You can customize invoice templates in Settings > Invoice. You can add your company logo, change colors, adjust the layout, and add custom notes or terms and conditions.',
                'order': 2,
            },
            {
                'category': 'payments',
                'question': 'How do I record a payment?',
                'answer': 'To record a payment:\n1. Go to Invoices\n2. Find the invoice that was paid\n3. Click "Record Payment"\n4. Enter the payment amount and date\n5. Select payment method\n6. Add any reference notes\n7. Click Save\n\nThe invoice status will update automatically.',
                'order': 1,
            },
            {
                'category': 'payments',
                'question': 'What payment methods are supported?',
                'answer': 'You can record payments for any method including:\n- Bank Transfer\n- Credit Card\n- Cheque\n- Cash\n- PayPal\n- Stripe\n- Custom payment methods\n\nSet your default payment methods in Settings > Payment Methods.',
                'order': 2,
            },
            {
                'category': 'clients',
                'question': 'How do I add a new client?',
                'answer': 'To add a new client:\n1. Go to Clients in the sidebar\n2. Click "New Client"\n3. Fill in their details (name, email, address, phone)\n4. Set default payment terms\n5. Click Save\n\nYou can then create invoices for this client.',
                'order': 1,
            },
            {
                'category': 'reports',
                'question': 'Can I export reports?',
                'answer': 'Yes! All reports can be exported in multiple formats:\n- PDF: For sharing or printing\n- CSV: For use in Excel or other tools\n- Print: Direct printing to your printer\n\nLook for the export buttons above any report.',
                'order': 1,
            },
            {
                'category': 'technical',
                'question': 'What should I do if the system is running slowly?',
                'answer': 'If the system is running slowly:\n1. Try clearing your browser cache\n2. Go to System > System Status and click \"Clear Cache\"\n3. Try \"Optimize Database\" to improve performance\n4. Check that you have a stable internet connection\n5. If problems persist, contact support',
                'order': 1,
            },
            {
                'category': 'settings',
                'question': 'How do I set up email notifications?',
                'answer': 'To set up email:\n1. Go to Settings > Email Configuration\n2. Select your email provider (Gmail, Outlook, Custom SMTP)\n3. Enter your email credentials\n4. Click \"Test Email\" to verify\n5. Check the box to enable notifications\n\nEmails will be sent for invoice reminders, payments, and other events.',
                'order': 1,
            },
        ]
        
        # Create FAQs
        for faq_data in faqs_data:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Created FAQ: {faq_data["question"][:50]}...'
                ))
            else:
                self.stdout.write(f'  Already exists: {faq_data["question"][:50]}...')
        
        # Sample Help Articles
        articles_data = [
            {
                'title': 'Getting Started with Invoice System',
                'slug': 'getting-started-invoice-system',
                'category': 'getting-started',
                'excerpt': 'Learn the basics of setting up and using the invoice system for your business.',
                'content': """<h2>Welcome to Invoice System</h2>
<p>This comprehensive guide will help you get started with our invoice management system.</p>

<h3>Initial Setup</h3>
<p>Before creating your first invoice, complete these setup steps:</p>
<ul>
<li>Configure your company details in Settings</li>
<li>Set up your invoice numbering scheme</li>
<li>Create your invoice template with your logo</li>
<li>Add your products/services</li>
</ul>

<h3>Key Features</h3>
<p>The system provides:</p>
<ul>
<li>Professional invoice creation and management</li>
<li>Automated payment tracking</li>
<li>Comprehensive reporting and analytics</li>
<li>Client management</li>
<li>Tax and VAT calculation</li>
</ul>

<h3>Next Steps</h3>
<p>Start by reading our detailed guides on invoicing, payments, and reporting.</p>""",
                'author': 'Support Team',
                'featured': True,
                'order': 1,
                'tags': 'setup, getting-started, tutorial'
            },
            {
                'title': 'Creating and Managing Invoices',
                'slug': 'creating-managing-invoices',
                'category': 'invoicing',
                'excerpt': 'Complete guide to creating professional invoices and managing your invoicing workflow.',
                'content': """<h2>Creating and Managing Invoices</h2>
<p>Learn how to create, send, and manage invoices effectively.</p>

<h3>Creating an Invoice</h3>
<ol>
<li>Click on "Invoices" in the main menu</li>
<li>Click "New Invoice"</li>
<li>Select a client from your list</li>
<li>Add line items with descriptions and amounts</li>
<li>Set payment terms</li>
<li>Review and save</li>
</ol>

<h3>Invoice Status</h3>
<p>Invoices go through these statuses:</p>
<ul>
<li><strong>Draft:</strong> Not yet sent to client</li>
<li><strong>Sent:</strong> Email sent to client</li>
<li><strong>Viewed:</strong> Client has opened the email</li>
<li><strong>Paid:</strong> Payment received</li>
<li><strong>Overdue:</strong> Payment not received by due date</li>
</ul>

<h3>Sending Invoices</h3>
<p>To send an invoice to your client:</p>
<ol>
<li>Open the invoice</li>
<li>Click "Send Invoice"</li>
<li>Optionally add a custom message</li>
<li>Click "Send"</li>
</ol>

<h3>Templates</h3>
<p>Customize your invoice appearance in Settings to match your brand.""",
                'author': 'Support Team',
                'featured': True,
                'order': 2,
                'tags': 'invoicing, tutorial, workflow'
            },
            {
                'title': 'Understanding Payment Processing',
                'slug': 'understanding-payment-processing',
                'category': 'payments',
                'excerpt': 'Learn how to record and track payments, and understand payment methods.',
                'content': """<h2>Payment Processing Guide</h2>
<p>Manage your payments efficiently with our streamlined payment system.</p>

<h3>Recording Payments</h3>
<p>When you receive a payment:</p>
<ol>
<li>Navigate to the invoice</li>
<li>Click "Record Payment"</li>
<li>Enter the amount received</li>
<li>Select the payment date</li>
<li>Choose the payment method</li>
<li>Save</li>
</ol>

<h3>Payment Methods</h3>
<p>The system supports multiple payment methods:</p>
<ul>
<li>Bank Transfer / Wire</li>
<li>Credit Card</li>
<li>Debit Card</li>
<li>Check</li>
<li>Cash</li>
<li>PayPal</li>
<li>Stripe</li>
<li>Custom methods</li>
</ul>

<h3>Partial Payments</h3>
<p>For partial payments:</p>
<ol>
<li>Record the payment as normal</li>
<li>The system will show remaining balance</li>
<li>The invoice remains open until fully paid</li>
</ol>

<h3>Payment Reminders</h3>
<p>Set up automatic payment reminders to encourage timely payment.""",
                'author': 'Support Team',
                'featured': False,
                'order': 1,
                'tags': 'payments, tutorial, methods'
            },
            {
                'title': 'Reports and Analytics',
                'slug': 'reports-analytics-guide',
                'category': 'reports',
                'excerpt': 'Master comprehensive reporting and analytics to understand your business performance.',
                'content': """<h2>Reports and Analytics</h2>
<p>Gain insights into your business with comprehensive reports and analytics.</p>

<h3>Available Reports</h3>
<p>The system provides multiple reports:</p>
<ul>
<li><strong>Invoice Register:</strong> All invoices with status and amounts</li>
<li><strong>Payment Register:</strong> All payments received</li>
<li><strong>Aging Report:</strong> Outstanding invoices by age</li>
<li><strong>Client Analysis:</strong> Performance by client</li>
<li><strong>Product Sales:</strong> Sales by product/service</li>
<li><strong>Tax Report:</strong> VAT and tax calculations</li>
</ul>

<h3>Filtering and Searching</h3>
<p>Most reports allow you to:</p>
<ul>
<li>Filter by date range</li>
<li>Search by client, invoice, or product</li>
<li>Filter by status or payment method</li>
</ul>

<h3>Exporting Reports</h3>
<p>Export your reports in:</p>
<ul>
<li>PDF - for sharing and printing</li>
<li>CSV - for use in Excel</li>
<li>Print directly</li>
</ul>""",
                'author': 'Support Team',
                'featured': True,
                'order': 3,
                'tags': 'reports, analytics, business-intelligence'
            },
            {
                'title': 'System Settings and Configuration',
                'slug': 'system-settings-configuration',
                'category': 'settings',
                'excerpt': 'Configure your system settings for optimal performance and customization.',
                'content': """<h2>System Settings and Configuration</h2>
<p>Configure all aspects of your system to match your business needs.</p>

<h3>Company Settings</h3>
<p>Set up your company information:</p>
<ul>
<li>Company name and contact details</li>
<li>Address and registration information</li>
<li>Logo and branding</li>
<li>Tax ID and registration numbers</li>
</ul>

<h3>Invoice Settings</h3>
<p>Configure invoice behavior:</p>
<ul>
<li>Invoice number prefix (INV-, etc.)</li>
<li>Starting invoice number</li>
<li>Default payment terms</li>
<li>Invoice notes and terms & conditions</li>
</ul>

<h3>Tax Configuration</h3>
<p>Set up your tax rules:</p>
<ul>
<li>Configure VAT rates</li>
<li>Set tax rules by product or client</li>
<li>Enable/disable tax calculations</li>
</ul>

<h3>Email Configuration</h3>
<p>Set up email notifications for:</p>
<ul>
<li>Invoice delivery</li>
<li>Payment notifications</li>
<li>Reminders</li>
<li>System alerts</li>
</ul>

<h3>User Preferences</h3>
<p>Customize your personal preferences in your account settings.""",
                'author': 'Support Team',
                'featured': False,
                'order': 2,
                'tags': 'settings, configuration, admin'
            },
        ]
        
        # Create Help Articles
        for article_data in articles_data:
            article, created = HelpArticle.objects.get_or_create(
                slug=article_data['slug'],
                defaults=article_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Created Article: {article_data["title"]}'
                ))
            else:
                self.stdout.write(f'  Already exists: {article_data["title"]}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Help & Support data population complete!'))
        self.stdout.write(self.style.WARNING(
            '\nVisit http://localhost:8000/help/ to see the Help & Support center'
        ))
