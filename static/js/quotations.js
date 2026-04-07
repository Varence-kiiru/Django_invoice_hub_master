/**
 * Quotations JavaScript - Form handling, line items management, totals calculation
 */

(function() {
    'use strict';

    // ========== Line Items Formset Management ==========

    const QuoteFormset = {
        formPrefix: 'quotelineitem_set',

        init() {
            this.attachEventListeners();
            this.calculateTotals();
        },

        attachEventListeners() {
            // Add line item button
            const addBtn = document.getElementById('add-line-item');
            if (addBtn) {
                addBtn.addEventListener('click', () => this.addLineItem());
            }

            // Delete checkboxes
            this.attachDeleteHandlers();

            // Input change listeners for calculations
            const formset = document.getElementById('line-items-formset');
            if (formset) {
                formset.addEventListener('change', (e) => {
                    if (e.target.matches('input[type="number"], select')) {
                        this.calculateTotals();
                    }
                });

                formset.addEventListener('input', (e) => {
                    if (e.target.matches('input[type="number"]')) {
                        this.calculateTotals();
                    }
                });
            }
        },

        addLineItem() {
            const tbody = document.getElementById('line-items-tbody');
            if (!tbody) return;

            // Get current form count
            const forms = tbody.querySelectorAll('.line-item-row');
            const formCount = forms.length;

            // Get management form
            const mgmtForm = document.querySelector('[name="quotelineitem_set-TOTAL_FORMS"]');
            if (!mgmtForm) return;

            const currentCount = parseInt(mgmtForm.value);

            // Clone the last form
            const lastForm = forms[forms.length - 1];
            const newForm = lastForm.cloneNode(true);

            // Update form indices
            newForm.setAttribute('data-form-index', currentCount);
            newForm.querySelectorAll('input, select, textarea').forEach(field => {
                const name = field.getAttribute('name');
                if (name) {
                    const newName = name.replace(
                        new RegExp(`${this.formPrefix}-(\\d+)-`),
                        `${this.formPrefix}-${currentCount}-`
                    );
                    field.setAttribute('name', newName);
                    field.setAttribute('id', `id_${newName}`);

                    // Clear the value for new form
                    if (field.type === 'checkbox') {
                        field.checked = false;
                    } else {
                        field.value = '';
                    }
                }
            });

            // Clear delete checkbox if present
            const deleteCheckbox = newForm.querySelector('input[type="checkbox"]');
            if (deleteCheckbox && deleteCheckbox.getAttribute('name').includes('DELETE')) {
                deleteCheckbox.checked = false;
            }

            // Clear calculated fields
            newForm.querySelector('.line-total').textContent = '0.00';

            // Append to tbody
            tbody.appendChild(newForm);

            // Update management form
            mgmtForm.value = currentCount + 1;

            // Reattach event listeners
            this.attachDeleteHandlers();

            // Set focus to first input in new form
            const firstInput = newForm.querySelector('input:not([type="hidden"])');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }

            // Recalculate totals
            this.calculateTotals();
        },

        attachDeleteHandlers() {
            const deleteCheckboxes = document.querySelectorAll('input[type="checkbox"][name*="DELETE"]');
            deleteCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', () => {
                    const row = checkbox.closest('.line-item-row');
                    if (row) {
                        row.style.display = checkbox.checked ? 'none' : '';
                        this.calculateTotals();
                    }
                });
            });
        },

        calculateTotals() {
            let subtotal = 0;
            let totalTax = 0;

            const rows = document.querySelectorAll('.line-item-row');
            rows.forEach(row => {
                // Skip hidden/deleted rows
                if (row.style.display === 'none') return;

                // Get values
                const qtyInput = row.querySelector('input[name*="quantity"]');
                const priceInput = row.querySelector('input[name*="unit_price"]');
                const taxSelect = row.querySelector('select[name*="tax_rate"]');

                if (!qtyInput || !priceInput || !taxSelect) return;

                const qty = parseFloat(qtyInput.value) || 0;
                const price = parseFloat(priceInput.value) || 0;
                const taxOption = taxSelect.options[taxSelect.selectedIndex];
                const taxRate = taxOption ? parseFloat(taxOption.getAttribute('data-rate') || 0) : 0;

                // Calculate line total
                const lineSubtotal = qty * price;
                const lineTax = lineSubtotal * (taxRate / 100);
                const lineTotal = lineSubtotal + lineTax;

                // Update line total display
                const lineTotalSpan = row.querySelector('.line-total');
                if (lineTotalSpan) {
                    lineTotalSpan.textContent = lineTotal.toFixed(2);
                }

                // Accumulate
                subtotal += lineSubtotal;
                totalTax += lineTax;
            });

            // Update displayed totals
            const subtotalEl = document.getElementById('subtotal');
            const taxEl = document.getElementById('tax-total');
            const totalEl = document.getElementById('total');

            if (subtotalEl) subtotalEl.textContent = subtotal.toFixed(2);
            if (taxEl) taxEl.textContent = totalTax.toFixed(2);
            if (totalEl) totalEl.textContent = (subtotal + totalTax).toFixed(2);

            // Update form fields if they exist
            const subtotalField = document.querySelector('input[name="subtotal_amount"]');
            const taxField = document.querySelector('input[name="vat_amount"]');
            const totalField = document.querySelector('input[name="total_amount"]');

            if (subtotalField) subtotalField.value = subtotal.toFixed(2);
            if (taxField) taxField.value = totalTax.toFixed(2);
            if (totalField) totalField.value = (subtotal + totalTax).toFixed(2);
        }
    };

    // ========== Date Field Helpers ==========

    const DateHelper = {
        init() {
            this.setupDateValidation();
            this.setupDefaultDates();
        },

        setupDateValidation() {
            const quoteDate = document.getElementById('quote_date');
            const validUntil = document.getElementById('valid_until');

            if (quoteDate && validUntil) {
                quoteDate.addEventListener('change', () => {
                    // Ensure valid_until is not before quote_date
                    const quoteVal = quoteDate.value;
                    const validVal = validUntil.value;

                    if (quoteVal && validVal && quoteVal > validVal) {
                        validUntil.value = quoteVal;
                    }
                });

                validUntil.addEventListener('change', () => {
                    // Ensure valid_until is not before quote_date
                    const quoteVal = quoteDate.value;
                    const validVal = validUntil.value;

                    if (quoteVal && validVal && quoteVal > validVal) {
                        quoteDate.value = validVal;
                    }
                });
            }
        },

        setupDefaultDates() {
            const quoteDate = document.getElementById('quote_date');
            const validUntil = document.getElementById('valid_until');

            // If quote_date is auto-filled but valid_until is not, set default
            if (quoteDate && validUntil && quoteDate.value && !validUntil.value) {
                const quoteDateObj = new Date(quoteDate.value);
                const validUntilDate = new Date(quoteDateObj);
                validUntilDate.setDate(validUntilDate.getDate() + 30); // Default 30 days

                const year = validUntilDate.getFullYear();
                const month = String(validUntilDate.getMonth() + 1).padStart(2, '0');
                const day = String(validUntilDate.getDate()).padStart(2, '0');

                validUntil.value = `${year}-${month}-${day}`;
            }
        }
    };

    // ========== Invoice Date Defaults ==========

    const InvoiceDateHelper = {
        init() {
            this.setupInvoiceDateDefaults();
        },

        setupInvoiceDateDefaults() {
            const invoiceDate = document.getElementById('invoice_date');
            const dueDate = document.getElementById('due_date');

            if (invoiceDate && dueDate) {
                invoiceDate.addEventListener('change', () => {
                    if (!dueDate.value && invoiceDate.value) {
                        // Set due date to 30 days after invoice date
                        const invDateObj = new Date(invoiceDate.value);
                        const dueDateObj = new Date(invDateObj);
                        dueDateObj.setDate(dueDateObj.getDate() + 30);

                        const year = dueDateObj.getFullYear();
                        const month = String(dueDateObj.getMonth() + 1).padStart(2, '0');
                        const day = String(dueDateObj.getDate()).padStart(2, '0');

                        dueDate.value = `${year}-${month}-${day}`;
                    }
                });
            }
        }
    };

    // ========== Form Submission Handlers ==========

    const FormHandler = {
        init() {
            this.attachFormListeners();
        },

        attachFormListeners() {
            const quoteForm = document.getElementById('quote-create-form');
            if (quoteForm) {
                quoteForm.addEventListener('submit', (e) => {
                    if (!this.validateForm(e.target)) {
                        e.preventDefault();
                        return false;
                    }
                });
            }

            const convertForm = document.getElementById('convert-form');
            if (convertForm) {
                convertForm.addEventListener('submit', (e) => {
                    if (!this.validateConvertForm(e.target)) {
                        e.preventDefault();
                        return false;
                    }
                });
            }
        },

        validateForm(form) {
            // Check client selection
            const client = form.querySelector('[name="client"]');
            if (client && !client.value) {
                alert('Please select a client');
                client.focus();
                return false;
            }

            // Check dates
            const quoteDate = form.querySelector('[name="quote_date"]');
            const validUntil = form.querySelector('[name="valid_until"]');

            if (quoteDate && validUntil && quoteDate.value && validUntil.value) {
                if (quoteDate.value > validUntil.value) {
                    alert('Valid Until date must be after Quote Date');
                    validUntil.focus();
                    return false;
                }
            }

            // Check for at least one line item
            const lineItems = document.querySelectorAll('.line-item-row:not([style*="display: none"])');
            if (lineItems.length === 0) {
                alert('Please add at least one line item to the quotation');
                return false;
            }

            // Check all line items have required fields
            for (let item of lineItems) {
                const product = item.querySelector('[name*="product"]');
                const qty = item.querySelector('[name*="quantity"]');
                const price = item.querySelector('[name*="unit_price"]');

                if (product && !product.value) {
                    alert('Please select a product for all line items');
                    product.focus();
                    return false;
                }

                if (qty && (!qty.value || parseFloat(qty.value) <= 0)) {
                    alert('All quantities must be greater than 0');
                    qty.focus();
                    return false;
                }

                if (price && (!price.value || parseFloat(price.value) < 0)) {
                    alert('Unit prices cannot be negative');
                    price.focus();
                    return false;
                }
            }

            return true;
        },

        validateConvertForm(form) {
            const dueDate = form.querySelector('[name="due_date"]');

            if (!dueDate || !dueDate.value) {
                alert('Please enter a due date for the invoice');
                if (dueDate) dueDate.focus();
                return false;
            }

            return true;
        }
    };

    // ========== Initialization ==========

    document.addEventListener('DOMContentLoaded', function() {
        QuoteFormset.init();
        DateHelper.init();
        InvoiceDateHelper.init();
        FormHandler.init();
    });

    // Export for testing
    window.QuoteFormset = QuoteFormset;
    window.DateHelper = DateHelper;
    window.InvoiceDateHelper = InvoiceDateHelper;
    window.FormHandler = FormHandler;
})();
