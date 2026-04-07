# InvoiceHub User Guide

**Version:** 4.5.0 | **Last Updated:** April 7, 2026

Complete step-by-step guide to using InvoiceHub for managing invoices, clients, products, payments, and financial operations.

---

## 📑 Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Managing Clients](#managing-clients)
4. [Managing Products & Services](#managing-products--services)
5. [Tax Settings](#tax-settings)
6. [Creating Invoices](#creating-invoices)
7. [Quotations](#quotations)
8. [Deliveries](#deliveries)
9. [Recording Payments](#recording-payments)
10. [Managing Expenses](#managing-expenses)
11. [Financial Reports](#financial-reports)
12. [Analytics Dashboard](#analytics-dashboard)
13. [User Management](#user-management)
14. [System Settings](#system-settings)
15. [Backup & Restore](#backup--restore)

---

## Getting Started

### Registration & Account Setup

**Step 1: Access the Application**
1. Open your browser
2. Navigate to: `https://yourdomain.com` or `http://localhost:8000` (development)
3. You should see the login page

**Step 2: Create Your Account** (if not already created)
1. Click "Sign Up" or "Create Account"
2. Enter the following information:
   - **Email Address:** Your business email
   - **First Name:** Your first name
   - **Last Name:** Your last name
   - **Password:** Create a strong password (minimum 8 characters, including uppercase, lowercase, numbers, symbols)
   - **Confirm Password:** Repeat your password

3. Click "Create Account"
4. Check your email for a verification link
5. Click the verification link to activate your account

**Step 3: Initial Setup**
After logging in for the first time, you'll be guided through setup:

1. **Organization Name:** Enter your company/business name
   - Example: "Acme Corporation" or "John's Consulting"

2. **Organization Email:** Your business email address
   - This will be used on invoices and communications

3. **Phone Number:** Business contact number
   - Format: +1-234-567-8900 or similar

4. **Address:** Your business address
   - Street address
   - City
   - State/Province
   - ZIP/Postal Code
   - Country

5. **Currency:** Default currency for invoices
   - USD, EUR, GBP, INR, etc.
   - You can change this later

6. **Tax Configuration:** (Optional - can be set up later)
   - Tax ID/VAT Number
   - Tax rates used in your jurisdiction

7. **Logo Upload:** (Optional)
   - Upload your company logo (appears on invoices)
   - Recommended size: 200x100 pixels
   - Formats: PNG, JPG, JPEG

Click "Complete Setup" when finished.

### First Login

**Dashboard Welcome:**
- You'll see your dashboard with quick start guides
- Navigate using the main menu on the left side
- Typical workflow: Clients → Products → Tax Settings → Invoices → Payments

---

## Dashboard Overview

### Main Dashboard

**What You See:**
When you log in, the main dashboard shows:

1. **Quick Stats Cards:**
   - Total Invoices (this period)
   - Total Amount Pending
   - Total Paid Amount
   - Accounts Receivable Aging

2. **Financial Metrics:**
   - Revenue Overview (chart showing invoices over time)
   - Payment Timeline (incoming payments)
   - Top Clients (by invoice volume or amount)
   - Payment Method Breakdown

3. **Recent Activity:**
   - Recently created invoices
   - Recent payments received
   - Outstanding quotations

**Dashboard Features:**

- **Date Range Filter:** Click the date range selector to view:
  - Last 30 days
  - Last 90 days
  - Last 365 days
  - Custom range

- **Export Data:** Click "Export" to download dashboard data as CSV

- **Auto-Refresh:** Dashboard automatically updates every 5 minutes

- **Currency Display:** All amounts shown in your default currency

### Navigation Menu

**Left Sidebar Contains:**

**Main:**
- 📊 Dashboard
- 📈 Analytics

**Business Operations:**
- 👥 Clients
- 📦 Products
- 📄 Invoices
- 📋 Quotations
- 📦 Deliveries

**Finance & Accounting:**
- 💳 Payments
- 💰 Expenses
- 🏛️ Tax Settings
- 💰 Financials
- 📊 Reports

**⚙️ Settings**
- General Settings
- User Management
- Notifications
- Backup & Restore

**❓ Help & Support**

---

## Managing Clients

### Adding a New Client

**Navigate to Clients:**
1. Click "👥 Clients" in the main menu
2. Click "➕ Add Client" or "Add New Client" button

**Fill in Client Information:**

**Basic Information:**
- **Client Name:** (Required) Full company or person name
  - Example: "ABC Corporation" or "John Smith"

- **Email:** (Required) Primary contact email
  - Used for sending invoices

- **Phone:** (Optional) Contact phone number
  - Format: +1-234-567-8900

- **Website:** (Optional) Company website
  - Example: https://www.example.com

**Address Information:**
- **Street Address:** (Optional) Physical address line 1
- **City:** (Optional)
- **State/Province:** (Optional)
- **ZIP/Postal Code:** (Optional)
- **Country:** (Optional)

**Tax Information:**
- **Tax ID:** (Optional) Client's VAT/GST/Tax identification number
  - Used for B2B invoices

- **Tax Classification:** (Optional)
  - Domestic/International/Exempted

**Billing Details:**
- **Currency:** (Optional) Currency for this client
  - Defaults to your organization currency
  - Can override per-invoice

- **Payment Terms:** (Optional) Default payment terms
  - Net 30 (due in 30 days)
  - Net 60
  - Due upon receipt
  - Custom terms

- **Preferred Contact Method:** (Optional)
  - Email / Phone / WhatsApp / SMS

**Custom Fields:** (if enabled)
- Add any additional information specific to your business

**Click "Save Client"**

### Viewing & Editing Clients

**View All Clients:**
1. Go to Clients menu
2. See list of all clients with:
   - Client name
   - Email
   - Total invoices
   - Total amount due
   - Status (Active/Inactive)

**Search for a Client:**
1. Use the search box at the top
2. Type partial name or email
3. Results appear instantly

**Filter Clients:**
1. Click "Filters" button
2. Options:
   - Status: Active, Inactive
   - Has Outstanding Invoices
   - By Country
   - By Currency

**View Client Details:**
1. Click on client name in list
2. See complete client information:
   - Contact details
   - Invoice history
   - Total amount invoiced
   - Total paid
   - Amount due
   - Payment history
   - Recent activity

**Edit Client:**
1. Click "Edit" button on client detail page
2. Update any information
3. Click "Save Changes"

**Deactivate/Delete Client:**
1. Click "More Options" (⋯) button
2. Choose:
   - Deactivate (hides from future invoices)
   - Delete (removes client - only if no invoices)

### Client Portal Access

**Enable Client Portal:**
1. Go to client details
2. Click "Send Portal Access" button
3. Client receives email with login link
4. Clients can:
   - View their invoices
   - Download invoice PDFs
   - See payment history
   - Make payments online (if enabled)

---

## Managing Products & Services

### Adding Products/Services

**Navigate to Products:**
1. Click "📦 Products" in the main menu
2. Click "➕ Add Product" button

**Fill in Product Information:**

**Basic Information:**
- **Product/Service Name:** (Required)
  - Example: "Consulting Services" or "Software License"

- **Description:** (Optional) Detailed product description
  - Used on invoices
  - Example: "Project management consulting"

- **Category:** (Optional) Group similar products
  - Example: "Services", "Software", "Hardware"

**Pricing:**
- **Default Price:** (Required) Standard selling price
  - Example: $150.00

- **Unit:** (Required) Measurement unit
  - Hour / Day / Week / Month
  - Piece / Kilogram / Liter
  - Custom unit

- **Tax Class:** (Optional) Tax treatment for this product
  - Standard / Reduced / Exempt
  - See Tax Settings section for more

**Optional Information:**
- **SKU:** (Optional) Stock keeping unit code
  - Example: "PROD-001"

- **Quantity in Stock:** (Optional) Track inventory
  - Will warn when low

- **Reorder Level:** (Optional) Alert when stock drops below this

- **Supplier:** (Optional) Vendor information

**Click "Save Product"**

### Managing Your Product List

**View All Products:**
1. Go to Products menu
2. See list with:
   - Product name
   - Description
   - Default price
   - Tax class
   - Stock level (if tracked)

**Search Products:**
1. Use search box
2. Start typing product name
3. Results filter in real-time

**Filter Products:**
1. Click "Filters"
2. Options:
   - By Category
   - By Tax Class
   - In Stock / Out of Stock
   - By Price Range

**Edit Product:**
1. Click product name or "Edit" button
2. Modify information
3. Click "Save Changes"

**Delete Product:**
1. Click "More Options" (⋯)
2. Choose "Delete"
3. Note: Can't delete if used in invoices

**Bulk Actions:**
1. Check multiple products
2. Click "Bulk Actions"
3. Options:
   - Change Price
   - Change Tax Class
   - Add to Category
   - Archive Multiple

---

## Tax Settings

### Configuring Tax Classes

**Navigate to Tax Settings:**
1. Click "🏛️ Tax Settings" in the main menu

**View Current Tax Configuration:**
You'll see:
- Your organization tax ID
- Default tax class
- List of configured tax rates

### Creating Tax Classes

**Add New Tax Class:**
1. Click "➕ Add Tax Class" button
2. Enter information:
   - **Tax Class Name:** (Required)
     - Example: "Standard", "Reduced", "Exempt", "Zero-rated"

   - **Description:** (Optional)
     - Example: "Standard rate for most goods and services"

   - **Tax Rate (%):** (Required) Percentage to apply
     - Example: 10 for 10%, 0 for tax-exempt

   - **Tax Type:** (Optional)
     - VAT (Value Added Tax)
     - GST (Goods & Services Tax)
     - Sales Tax
     - Service Tax
     - Other

3. Click "Save Tax Class"

### Managing Tax Classes

**View All Tax Classes:**
- See name, rate, and type
- Sort by rate (ascending/descending)

**Edit Tax Class:**
1. Click on tax class row
2. Update rate or description
3. Click "Save"
4. Note: Changes apply to future invoices only

**Set Default Tax Class:**
1. Find desired tax class
2. Click "Set as Default" button
3. This will be used automatically on new invoices

**Delete Tax Class:**
1. Click "More Options" (⋯)
2. Choose "Delete"
3. Note: Can't delete if used in invoices

### Tax Exemption

**Mark Clients as Tax-Exempt:**
1. Go to client details
2. Check "Tax Exempt" checkbox
3. Save
4. Invoices to this client won't include tax

**Mark Products as Tax-Exempt:**
1. When editing product
2. Set Tax Class to "Exempt" or "Zero-rated"

---

## Creating Invoices

### Starting an Invoice

**Navigate to Invoices:**
1. Click "📄 Invoices" in the main menu
2. Click "➕ Create Invoice" button

**Basic Invoice Information:**

**Client Selection:**
- Click "Select Client" dropdown
- Search and select client from list
- Creates dropdown showing client details
- Billing address auto-fills from client record

**Invoice Details:**
- **Invoice Number:** (Auto-generated)
  - Format: INV-2026-001
  - Can be manually overridden (if enabled)

- **Invoice Date:** (Auto-set to today)
  - Click to change date
  - Cannot be future-dated

- **Due Date:** (Set by default to Invoice Date + Payment Terms)
  - Click to change
  - Used for invoice aging calculations

- **Invoice Reference:** (Optional)
  - Purchase order number or your reference
  - Example: "PO-12345"

- **Notes:** (Optional)
  - Additional terms or special instructions
  - Appears at bottom of printed invoice

### Adding Line Items

**Add First Item:**
1. Click "➕ Add Line Item" button

**For Each Line Item:**
- **Product/Service:** (Required)
  - Click dropdown to select predefined product
  - Or type custom description
  - Autocomplete shows your products

- **Quantity:** (Required)
  - Number of units
  - Default: 1

- **Unit Price:** (Required)
  - Price per unit
  - Auto-fills if product selected
  - Can override

- **Tax Class:** (Optional)
  - Defaults to product tax class
  - Can override per-line item

- **Discount:** (Optional)
  - Percentage or fixed amount
  - Example: 10% or $50

**Line Item Calculations:**
Automatically calculated:
- Subtotal = Quantity × Unit Price - Discount
- Tax = Subtotal × (1 + Tax Rate)
- Total = Subtotal + Tax

**Adding More Items:**
1. Click "➕ Add Line Item" again
2. Repeat process

**Removing Items:**
1. Click "🗑️ Delete" on that line item

### Invoice Totals

**Automatic Calculation:**
- **Subtotal:** Sum of all line items
- **Discounts:** Applied discounts
- **Tax:** Calculated on subtotal (if applicable)
- **Total Amount Due:** Subtotal + Tax - Discounts

**Add Global Discount:** (Optional)
1. Click "Add Discount" section
2. Enter percentage or fixed amount
3. Updates total automatically

**Add Invoice Notes:**
1. In Notes section
2. Example: "Thank you for your business"
3. Appears on invoice PDF

### Saving & Managing Invoice

**Save as Draft:**
1. Click "Save as Draft"
2. Invoice stays in draft status
3. Can edit anytime before issuing

**Issue Invoice:**
1. Click "Issue Invoice"
2. Status changes to "Issued"
3. Invoice number becomes permanent
4. Can mark as sent

**Send Invoice to Client:**
1. Click "Send Invoice" button
2. Choose delivery method:
   - Email (sent to client email)
   - Download PDF (save locally)
   - Print
   - Send Link

3. Custom message (optional):
   - Add personal note
   - Example: "Please find your invoice attached"

4. Click "Send"

**View Invoice PDF:**
1. Click "View PDF" button
2. Shows professional formatted invoice
3. Includes:
   - Your company details
   - Client details
   - Line items with total
   - Payment instructions (if configured)
   - Notes and terms

### Invoice Status Flow

**Draft:**
- Initial state
- Can edit all fields
- Not yet official

**Issued:**
- Converted to official invoice
- Invoice number assigned
- Can be sent to client
- Cannot edit (must create credit note)

**Sent:**
- Invoice has been sent to client
- Status updates when client views

**Viewed:**
- Client has viewed the invoice
- (Tracked via email link or portal)

**Partially Paid:**
- Payment received but amount < total
- Shows amount outstanding

**Paid:**
- Full payment received
- Status set automatically when payment recorded

**Overdue:**
- Past due date with unpaid balance
- Highlighted in red

**Cancelled:**
- Marked as void/cancelled
- Shown but not counted in reports

### Invoice Actions

**Edit Draft Invoice:**
1. Open draft invoice
2. Click "Edit"
3. Modify any fields
4. Click "Save"

**Reissue Invoice:**
1. Go to issued invoice
2. Click "Reissue" to create new version
3. Original archived
4. New invoice issued

**Send Reminder:**
1. Open unpaid invoice
2. Click "Send Reminder"
3. Automated email sent to client
4. Payment link included

**Record Payment:**
1. Click "Record Payment"
2. See "Recording Payments" section below
3. Amount, date, method

**Download PDF:**
1. Click "Download" button
2. Saves invoice as PDF file

**Print:**
1. Click "Print" button
2. Opens print dialog
3. Print to physical printer or PDF

**Delete (Draft Only):**
1. Open draft invoice
2. Click "Delete"
3. Permanently removes

---

## Quotations

### Creating a Quotation

**Navigate to Quotations:**
1. Click "📋 Quotations" in main menu
2. Click "➕ Create Quotation" button

**Quotation Information:**

**Similar to Invoices:**
- Select client
- Add line items (products/services)
- Set quantity and price
- Apply taxes
- Add notes

**Quotation-Specific Fields:**
- **Valid Until Date:** (Required)
  - When quote expires
  - Shown on quotation
  - Example: 30 days from today

- **Quote Reference:** (Optional)
  - Your internal reference

**PDF Actions:**
- Download PDF
- Print
- Email to client

### Converting Quote to Invoice

**Option 1: From Quotation List:**
1. Click quotation
2. Click "Convert to Invoice"
3. Creates invoice with same line items
4. Review and issue

**Option 2: Create Manual Invoice:**
1. When creating invoice
2. Can reference quotation number in invoice reference field
3. Manually add same items

### Managing Quotations

**View Quotation Status:**
- New / Sent / Viewed / Accepted / Declined / Expired

**Send Quotation:**
1. Click quotation
2. Click "Send"
3. Email to client or download

**Track Quotation:**
- See when sent
- See when viewed (if via email link)
- See if converted to invoice

**Expire Quotation:**
1. Quotation becomes "Expired" after due date
2. Can't convert to invoice

**Delete Quotation:**
1. Click "More Options"
2. Choose "Delete" (if not sent)

---

## Deliveries

### Creating a Delivery Note

**Navigate to Deliveries:**
1. Click "📦 Deliveries" in main menu
2. Click "➕ Create Delivery" button

**Delivery Information:**

**Client:**
- Select client
- Address auto-fills from client record

**Items:**
- Add items being delivered
- Specify quantity
- Optional: Serial numbers, batch codes

**Driver/Carrier Info:** (Optional)
- Drive name
- Delivery date/time
- Vehicle information

**Special Instructions:** (Optional)
- Handling notes
- Delivery instructions
- Example: "Fragile - Handle with care"

**Recipient Signature:** (Optional)
- Track who received delivery

### Delivery Workflow

**Create Delivery:**
1. Click "Create Delivery"
2. Enter information
3. Save as "Pending"

**Confirm Delivery:**
1. Use mobile app or portal
2. Confirm items delivered
3. Status changes to "Delivered"

**Receive Signature:**
1. Client/recipient signs
2. Proof of delivery saved

**Link to Invoice:**
1. Delivery can be linked to invoice
2. Shows delivery status on invoice
3. Useful for delivery-on-invoice workflows

### View Delivery History

1. Go to Deliveries list
2. See all deliveries with status
3. Click to view details
4. See delivery date, items, recipient

---

## Recording Payments

### Adding a Payment

**Navigate to Payments:**
1. Click "💳 Payments" in main menu
2. Click "➕ Record Payment" button

**Or from Invoice:**
1. Open unpaid invoice
2. Click "Record Payment"
3. Pre-fills invoice details

**Payment Information:**

**Client Selection:**
- Select client receiving payment
- Shows outstanding invoices

**Invoice Selection:**
- Click invoice(s) to apply payment to
- Can apply to single or multiple invoices

**Payment Details:**
- **Amount Received:** (Required)
  - Amount in client's currency
  - Validate against invoice total

- **Payment Date:** (Required)
  - When payment was received
  - Defaults to today

- **Payment Method:** (Required)
  - Bank Transfer / Cheque
  - Credit Card / Debit Card
  - Cash
  - Digital Wallet
  - Check

- **Reference:** (Optional)
  - Cheque number
  - Bank transaction ID
  - Reference from client

- **Notes:** (Optional)
  - Additional payment notes

### Recording Partial Payments

**If Amount < Invoice Total:**
1. Select invoice
2. Enter amount received
3. Click "Record Partial Payment"
4. Invoice shows as "Partially Paid"
5. Remainder due

**Reconciliation:**
- Shows amount still outstanding
- Original due date maintained

### Payment Reconciliation

**View Payment Status:**
1. Go to Payments menu
2. See all recorded payments
3. Search by client, date, amount

**Match Payments to Invoices:**
1. System can auto-match
2. Or manually connect payment to invoice
3. Shows unmatched payments

**Report Discrepancies:**
1. Look for unmatched payments
2. Click to investigate
3. Contact client if needed

### Payment Receipts

**Generate Receipt:**
1. Click recorded payment
2. Click "Generate Receipt"
3. Creates receipt PDF

**Email Receipt:**
1. Click "Send Receipt"
2. Emailed to client
3. Includes payment confirmation

---

## Managing Expenses

### Recording an Expense

**Navigate to Expenses:**
1. Click "💰 Expenses" in main menu
2. Click "➕ Add Expense" button

**Expense Information:**

**Basic Details:**
- **Expense Category:** (Required)
  - Supplies / Travel / Meals / Utilities
  - Rent / Insurance / Equipment
  - Other

- **Description:** (Required)
  - What was purchased
  - Example: "Office Stationery"

- **Amount:** (Required)
  - Total expense amount
  - In your default currency

- **Date:** (Required)
  - When expense was incurred
  - For tax deduction purposes

**Additional Information:**
- **Vendor/Supplier:** (Optional)
  - Who you bought from
  - Example: "Office Depot"

- **Receipt:** (Optional)
  - Upload receipt image/PDF
  - Proof for tax purposes

- **Tax Treatment:** (Optional)
  - Deductible / Non-deductible
  - Tax category for accounting

- **Project/Client:** (Optional)
  - Assign to client if billable
  - Optional cost code

**Click "Save Expense"**

### Managing Expenses

**View All Expenses:**
1. Go to Expenses list
2. See all recorded expenses
3. Sort by date, category, amount

**Filter Expenses:**
1. Click Filters
2. By date range
3. By category
4. By vendor
5. Deductible vs. non-deductible

**Edit Expense:**
1. Click expense
2. Click "Edit"
3. Modify details
4. Save

**Delete Expense:**
1. Click "More Options"
2. Choose "Delete"

### Expense Reports

**Generate Report:**
1. Click "Generate Report" button
2. Choose period (month, quarter, year)
3. Select categories
4. System creates expense summary

**Export Expenses:**
1. Click "Export"
2. Format: CSV, Excel, PDF
3. Use for accounting software

---

## Financial Reports

### Available Reports

**Navigate to Reports:**
1. Click "📊 Reports" in main menu

**Report Types:**

### 1. Income Statement

**Shows:**
- Total revenue (from invoices)
- Total expenses (by category)
- Net income (profit/loss)

**For Period:**
- Click date range
- Month / Quarter / Year

**Export:**
- Download as PDF or Excel
- Use for accounting/banking

### 2. Accounts Receivable (AR) Report

**Shows:**
- Invoices sent but not paid
- By customer
- Aging: 0-30, 30-60, 60-90, 90+ days

**Action Items:**
- Identify overdue invoices
- Prioritize collection follow-ups

**Export Data:**
- Send to accountant
- Use for financing discussions

### 3. Payment Received Report

**Shows:**
- All payments received by date
- By customer
- By payment method

**For Period:**
- Select date range
- Detailed list or summary

### 4. Expense Summary

**Shows:**
- Total expenses
- By category (pie chart)
- Top expense categories

**Analysis:**
- Compare month-to-month
- Identify saving opportunities

### 5. Tax Report

**Shows:**
- Invoices by tax class
- Tax amount collected
- Tax liabilities

**For Filing:**
- Export for tax authorities
- Track tax remittance due

### 6. Client Summary

**Shows:**
- Revenue per client
- Number of invoices per client
- Average invoice value
- Payment status per client

**Analysis:**
- Identify top clients
- See who owes money
- Client profitability

### Creating Custom Reports

**Add Custom Report:**
1. Click "Create Custom Report"
2. Select:
   - Date range
   - Data fields
   - Grouping (by date, client, category)
   - Charts (if desired)

3. Preview and save
4. Can rerun with different parameters

### Exporting Reports

**Choose Format:**
- PDF (for printing/sharing)
- Excel (for analysis)
- CSV (for other software)

**Email Report:**
1. Click "Email"
2. Recipient email
3. Message (optional)
4. Send

---

## Analytics Dashboard

### Dashboard Components

**Navigate to Analytics:**
1. Click "📈 Analytics" in main menu

### Real-Time Metrics

**Financial Overview:**
- Total Revenue (selected period)
- Total Expenses
- Net Profit/Loss
- Profit Margin (%)

**Invoice Metrics:**
- Total Invoices Issued
- Average Invoice Value
- Invoices Outstanding
- Overdue Invoice Count

**Payment Status:**
- On-time Payments (%)
- Payment Days (average)
- Collected vs. Due

### Charts & Visualizations

**Revenue Timeline:**
- Line chart showing revenue trend
- Daily/Weekly/Monthly breakdown
- Click to zoom in/out

**Top Clients:**
- Table showing:
  - Client name
  - Revenue from client
  - Number of invoices
  - Payment status

**Payment Method Distribution:**
- Pie chart showing:
  - Cash
  - Bank Transfer
  - Card
  - Other

**Aging Report:**
- Invoices by age:
  - 0-30 days
  - 30-60 days
  - 60-90 days
  - 90+ days (overdue)

### Dashboard Customization

**Change Date Range:**
- Last 30 days (default)
- Last 90 days
- Last 365 days
- Custom date range
- Invoice period

**Refresh Data:**
- Auto-refreshes every 5 minutes
- Click "Refresh" for immediate update

**Download Dashboard:**
1. Click "Export"
2. Format: PDF or Excel
3. Includes all metrics and charts

**Print Dashboard:**
1. Click "Print"
2. Shows printable version
3. Send to printer

---

## User Management

### Managing Users in Your Organization

**Navigate to Team:**
1. Click "⚙️ Settings"
2. Click "Team Members"

**Current Team:**
- See list of all users
- Name, email, role, status
- Join date

### Adding New Users

**Invite Team Member:**
1. Click "➕ Invite Team Member"
2. Enter:
   - Email address
   - First name
   - Last name
   - Role (see below)

3. Click "Send Invite"
4. User receives email with login link
5. They create password and join

### User Roles & Permissions

**Admin:**
- Full system access
- Can add/remove users
- Can access all financial reports
- Can change settings
- Can manage backup & restore

**Accountant:**
- Can view invoices, payments
- Can create reports
- Can access analytics
- Cannot delete records
- Cannot manage users

**Manager:**
- Can create invoices
- Can view clients and products
- Can see own reports
- Cannot view financial data
- Cannot manage users

**User:**
- Can view basic information
- Limited to assigned clients/invoices
- Cannot create new records
- Cannot access reports

**Viewer (Read-only):**
- Can view all data
- Cannot create or modify
- Cannot delete
- Good for stakeholders

### Changing User Role

**Update User Permission:**
1. Go to Team Members
2. Click on user
3. Click "Edit"
4. Change "Role" dropdown
5. Click "Save"
6. Changes take effect immediately

### Removing Users

**Remove from Organization:**
1. Click user
2. Click "More Options" (⋯)
3. Click "Remove"
4. Confirm action
5. User loses access

**Note:** User account isn't deleted, just access revoked

### Personal Account Settings

**Your Profile:**
1. Click your name/avatar (top right)
2. Click "My Profile"

**Update Profile:**
- Change first/last name
- Update email
- Can change password
- Upload profile picture

**Notification Preferences:**
1. Go to Settings
2. Click "Notifications"
3. Choose what to receive:
   - Payment received alerts
   - Invoice due reminders
   - Invoice overdue alerts
   - Summary emails (weekly/monthly)

4. Select frequency and methods

---

## System Settings

### Organization Settings

**Navigate to Settings:**
1. Click "⚙️ Settings" in main menu
2. Click "General Settings"

**Basic Organization Info:**
- Organization name
- Organization email
- Phone number
- Website (optional)
- Address

**Currency & Format:**
- Default currency
- Date format (MM/DD/YYYY, DD/MM/YYYY, etc.)
- Number format (decimal separator)
- Timezone

**Tax Settings:**
- Your tax ID
- Default tax rate
- Tax invoice format

**Communication:**
- Default payment terms
- Invoice reminder schedule
- Overdue reminder schedule

### Invoice Settings

**Invoice Configuration:**
1. Click "Invoice Settings"

**Number Format:**
- Prefix (example: "INV-")
- Number format (sequential, yearly reset, etc.)
- Starting number

**Invoice Terms:**
- Default payment terms
- Invoice footer text
- Payment instructions
- Thank you message

**Email Settings:**
- From address
- Email template
- Signature

### Payment Settings

**Payment Methods:**
1. Click "Payment Methods"
2. Configure:
   - Bank transfer details
   - Check/cheque information
   - Accepted cards
   - Digital wallet info

**Display on Invoices:**
- What payment info appears
- Where clients should send payment

**Online Payments:** (if enabled)
- Stripe or PayPal integration
- Payment gateway credentials
- Fee calculation

### Notification Settings

**Email Configuration:**
1. Click "Email Settings"
2. Configure SMTP:
   - Email provider
   - Sender address
   - Email templates

**Notification Types:**
- Invoice sent notifications
- Payment confirmations
- Overdue reminders
- Monthly summaries

### Backup Settings

**Automated Backups:**
1. Go to "Backup & Restore"
2. Backup configuration:
   - Schedule (daily, weekly, etc.)
   - Backup type (database, full system)
   - Retention policy (how long to keep)

**Manual Backup:**
1. Click "Create Backup"
2. Choose type:
   - Database only
   - Full system (includes media files)

3. Click "Create"
4. Download when complete

---

## Backup & Restore

### Regular Backups

**Importance:**
- Protects against data loss
- Allows recovery if something goes wrong
- Required for business continuity

**Automatic Daily Backups:**
- Scheduled for 2:00 AM daily
- Kept for 30 days
- Automatically cleaned up
- Requires Celery service running

### Creating Manual Backup

**Step 1: Access Backup Page:**
1. Click "⚙️ Settings"
2. Click "Backup & Restore"

**Step 2: Create Backup:**
1. Click "💾 Create Backup"
2. Choose backup type:
   - Database Only (~0.02 MB typical)
     - Just your invoice/payment data
   - Full System
     - Database + uploaded files (logos, invoices, etc.)

3. Click "Create Backup Now"
4. Status shows "Processing..."

**Step 3: Download Backup:**
1. Wait for backup to complete
2. Click "⬇️ Download"
3. Backup downloads to your computer
4. File size shown (typically 0.5-10 MB depending on data)

### Viewing Backup History

**Backup History Table:**
- Lists all backups with:
  - Date created
  - File name
  - Size
  - Type
  - Status (Complete, Processing, Failed)

**Actions:**
- ⬇️ Download - Download to your computer
- 🗑️ Delete - Remove from server
- 🔄 Restore - Restore from this backup

### Restoring from Backup

**Important:** Read warnings before restoring!

**Step 1: Choose Backup File:**
1. Click "Upload Backup File"
2. Click "Choose File"
3. Select backup file from your computer
4. Supported formats:
   - .sql (database only)
   - .sql.gz (compressed database)
   - .zip (full system backup)

**Step 2: Review & Confirm:**
1. See file preview:
   - File name
   - Size
   - Type

2. Read warning checklist:
   - ✓ I have backed up current database
   - ✓ I have verified backup is valid
   - ✓ I understand all current data will be overwritten
   - ✓ System will be temporarily unavailable

3. Check all boxes to confirm

**Step 3: Restore:**
1. Click "Upload & Restore"
2. Status shows "Restoring..."
3. Wait for completion
4. Application automatically restarts
5. Log in again when complete

**For .zip Backups:**
- Database restored
- Media files (logos, invoices) restored
- Everything returns to backup state

### Backup Schedule

**Best Practices:**
- Create manual backup before major changes
- Download backups to secure location
- Keep backups off-site (send to other computer)
- Test restore procedure occasionally
- Document backup schedule

**Recommended Schedule:**
- Daily: Automated backups (system handles)
- Weekly: Manual full backup (user creates)
- Monthly: Off-site backup (store separately)

### If Restore Fails

**What to do:**
1. Check file format (must be .sql or .zip)
2. Verify file is not corrupted
3. Try manually uploading backup
4. Contact support if issues persist

---

## Tips & Best Practices

### Invoice Management

1. **Send Invoices Promptly:**
   - Issue and send immediately after service
   - Improves payment timeline

2. **Track Overdue Invoices:**
   - Review dashboard daily
   - Send reminders at 10, 20, 30 days overdue

3. **Use Line Item Descriptions:**
   - Be specific about what was delivered
   - Reduces payment delays

4. **Set Clear Payment Terms:**
   - Consistent terms reduce confusion
   - Consider your cash flow needs

5. **Keep Detailed Records:**
   - Document all communications
   - Save emails and confirmations

### Client Management

1. **Complete Client Information:**
   - Get all details upfront
   - Include tax ID if B2B

2. **Maintain Current Contact Info:**
   - Update email if changed
   - Verify phone numbers

3. **Monitor Client Balance:**
   - Check outstanding amounts regularly
   - Follow up on overdue invoices

4. **Use Client Portal:**
   - Improves communication
   - Clients can access own invoices

### Financial Health

1. **Review Reports Monthly:**
   - Analyze revenue trends
   - Monitor expenses
   - Calculate profit margins

2. **Track Accounts Receivable:**
   - Know total money owed
   - Aging report essential
   - Prioritize collection

3. **Monitor Cash Flow:**
   - Compare revenue vs. expenses
   - Plan for seasonal changes
   - Maintain emergency fund

4. **Reconcile Regularly:**
   - Match invoices to payments
   - Identify discrepancies
   - Keep records clean

5. **Plan Taxes:**
   - Use tax reports for estimates
   - Set aside tax payments
   - Organize for filing

### Backup & Security

1. **Regular Backups:**
   - Create weekly manual backups
   - Store copies off-site
   - Test restore procedure

2. **Strong Passwords:**
   - Use 12+ characters
   - Mix uppercase, lowercase, numbers, symbols
   - Unique per account

3. **Secure Access:**
   - Enable MFA (Multi-Factor Authentication) if available
   - Share login info securely
   - Use team roles appropriately

---

## Troubleshooting

### Common Issues

**Issue: Can't find a client**
- Solution: Use search box, check if inactive, verify spelling

**Issue: Invoice won't send by email**
- Solutions:
  - Check email settings configured
  - Verify client email correct
  - Check internet connection
  - Wait 5 minutes and retry

**Issue: Payment not showing on invoice**
- Solutions:
  - Confirm payment was recorded
  - Check if applied to correct invoice
  - Verify amount is correct
  - Check system time is correct

**Issue: Reports showing no data**
- Solutions:
  - Verify date range includes your data
  - Check if invoices are marked as "Issued"
  - Ensure filters aren't excluding data

**Issue: Can't download PDF**
- Solutions:
  - Try different browser
  - Disable browser ad blocker
  - Check file size (if large, may need download manager)
  - Try again in few minutes

### Getting Help

**In-Application Help:**
- Click "❓ Help & Support" in menu
- Browse common questions
- Video tutorials
- Contact links

**Email Support:**
- hernandezngash@gmail.com
- Include:
  - What you were trying to do
  - What went wrong
  - Error message (if any)
  - Browser/device info

---

## Glossary

**AR (Accounts Receivable):** Money owed by clients for invoices

**Invoice:** Bill sent to client for goods/services provided

**Quotation (Quote):** Price proposal sent before invoice

**Line Item:** Individual product/service line on invoice

**Payment Terms:** When invoice is due (e.g., Net 30)

**Tax Class:** Categories of items with different tax rates

**Vendor:** Supplier or company you purchase from

**SKU:** Stock Keeping Unit (product identifier)

**HMRC:** Her Majesty's Revenue and Customs (UK tax)

**VAT:** Value Added Tax

**GST:** Goods and Services Tax

**Deduction:** Allowable business expense for taxes

**Profit Margin:** Percentage of revenue remaining as profit

---

## FAQs

**Q: Can I bulk import clients?**
A: Via CSV import in Data Management section (contact support for template)

**Q: Can I use multiple currencies?**
A: Yes, set per-client in client settings

**Q: How do I handle partial payments?**
A: Record amount received; system tracks as "Partially Paid"

**Q: Can I customize invoice template?**
A: Limited customization in settings; contact for premium designs

**Q: How do I contact support?**
A: Email bernandezngash@gmail.com or visit https://github.com/Varence-kiiru for the source code and issue tracker

**Q: Can clients make payments online?**
A: Yes, if Stripe/PayPal configured by admin

**Q: How long is data retained?**
A: Indefinitely unless you delete; backups kept 30 days

**Q: Can I export financial data?**
A: Yes, all reports exportable as PDF/Excel/CSV

---

## Contact & Support

**Developer Support:** hernandezngash@gmail.com
**Developer GitHub:** https://github.com/Varence-kiiru
**Documentation:** In-app help widget
**Source Code:** https://github.com/Varence-kiiru/invoice-system

For queries, bug reports, or system support, please reach out to the developer via email or check the GitHub repository for updates and discussions.

---

**Happy invoicing! 🎉**
