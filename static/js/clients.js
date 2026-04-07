/**
 * Client Management JavaScript
 * Handles form validation, interactions, and DOM manipulation for client pages
 */

// =========================================
// Form Validation
// =========================================

/**
 * Validate client form before submission
 */
function validateClientForm() {
    const name = document.getElementById('id_name');
    const email = document.getElementById('id_email');

    let isValid = true;

    // Clear previous errors
    clearFormErrors();

    // Validate name
    if (!name || !name.value.trim()) {
        showFieldError(name, 'Client name is required');
        isValid = false;
    }

    // Validate email
    if (!email || !email.value.trim()) {
        showFieldError(email, 'Email is required');
        isValid = false;
    } else if (!isValidEmail(email.value)) {
        showFieldError(email, 'Please enter a valid email address');
        isValid = false;
    }

    return isValid;
}

/**
 * Validate address form
 */
function validateAddressForm() {
    const streetAddress = document.getElementById('id_street_address');
    const city = document.getElementById('id_city');
    const state = document.getElementById('id_state');
    const postalCode = document.getElementById('id_postal_code');

    let isValid = true;
    clearFormErrors();

    if (!streetAddress || !streetAddress.value.trim()) {
        showFieldError(streetAddress, 'Street address is required');
        isValid = false;
    }

    if (!city || !city.value.trim()) {
        showFieldError(city, 'City is required');
        isValid = false;
    }

    if (!state || !state.value.trim()) {
        showFieldError(state, 'State is required');
        isValid = false;
    }

    if (!postalCode || !postalCode.value.trim()) {
        showFieldError(postalCode, 'Postal code is required');
        isValid = false;
    }

    return isValid;
}

/**
 * Validate contact form
 */
function validateContactForm() {
    const firstName = document.getElementById('id_first_name');
    const lastName = document.getElementById('id_last_name');
    const email = document.getElementById('id_email');

    let isValid = true;
    clearFormErrors();

    if (!firstName || !firstName.value.trim()) {
        showFieldError(firstName, 'First name is required');
        isValid = false;
    }

    if (!lastName || !lastName.value.trim()) {
        showFieldError(lastName, 'Last name is required');
        isValid = false;
    }

    if (email && email.value && !isValidEmail(email.value)) {
        showFieldError(email, 'Please enter a valid email address');
        isValid = false;
    }

    return isValid;
}

// =========================================
// Helper Functions
// =========================================

/**
 * Check if email is valid
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Show field error
 */
function showFieldError(fieldElement, message) {
    if (!fieldElement) return;

    fieldElement.classList.add('has-error');
    const formGroup = fieldElement.closest('.form-group');

    if (formGroup) {
        const existingError = formGroup.querySelector('.form-error');
        if (existingError) {
            existingError.textContent = message;
        } else {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'form-error';
            errorDiv.textContent = message;
            formGroup.appendChild(errorDiv);
        }
    }
}

/**
 * Clear all form errors
 */
function clearFormErrors() {
    document.querySelectorAll('.has-error').forEach(el => {
        el.classList.remove('has-error');
    });
    document.querySelectorAll('.form-error').forEach(el => {
        el.remove();
    });
}

// =========================================
// Client List Interactions
// =========================================

/**
 * Handle search and filter on client list
 */
document.addEventListener('DOMContentLoaded', function() {
    // Search clear button
    const clearBtn = document.querySelector('[onclick*="clearSearch"]');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            document.querySelector('input[name="search"]').value = '';
            this.closest('form').submit();
        });
    }

    // Status filter
    const statusFilter = document.querySelector('select[name="status"]');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            this.closest('form').submit();
        });
    }

    // Confirmation dialogs
    const deleteButtons = document.querySelectorAll('a[href*="delete"]');
    deleteButtons.forEach(btn => {
        if (!btn.closest('form')) { // Skip if already in form
            btn.addEventListener('click', function(e) {
                if (this.innerHTML.toLowerCase().includes('delete')) {
                    if (!confirm('Are you sure you want to delete this client?')) {
                        e.preventDefault();
                    }
                }
            });
        }
    });
});

// =========================================
// Edit Address Functionality
// =========================================

/**
 * Edit address - load into form
 */
function editAddress(addressId) {
    // In real implementation, this would load address data via AJAX
    // For now, scroll to form
    const form = document.getElementById('address-form');
    if (form) {
        form.scrollIntoView({ behavior: 'smooth' });
    }
}

// =========================================
// Edit Contact Functionality
// =========================================

/**
 * Edit contact - load into form
 */
function editContact(contactId) {
    // In real implementation, this would load contact data via AJAX
    // For now, scroll to form
    const form = document.getElementById('contact-form');
    if (form) {
        form.scrollIntoView({ behavior: 'smooth' });
    }
}

// =========================================
// Confirmation Dialogs
// =========================================

/**
 * Confirm delete client
 */
function confirmDeleteClient(clientName) {
    return confirm(`Are you sure you want to delete "${clientName}"? This action cannot be undone.`);
}

/**
 * Confirm delete address
 */
function confirmDeleteAddress() {
    return confirm('Are you sure you want to delete this address?');
}

/**
 * Confirm delete contact
 */
function confirmDeleteContact() {
    return confirm('Are you sure you want to delete this contact?');
}

// =========================================
// Export Functionality
// =========================================

/**
 * Export client statement to PDF
 */
function exportStatementPDF(clientId) {
    // This would trigger a server-side PDF generation
    window.location.href = `/clients/${clientId}/statement/pdf/`;
}

/**
 * Export client data to CSV
 */
function exportClientData(clientId) {
    // This would trigger a server-side CSV export
    window.location.href = `/clients/${clientId}/export/csv/`;
}

// =========================================
// Print Functionality
// =========================================

/**
 * Print client statement
 */
function printStatement() {
    window.print();
}

// =========================================
// Date Utilities
// =========================================

/**
 * Format date for display
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', options);
}

/**
 * Calculate days overdue
 */
function calculateDaysOverdue(dueDate) {
    const today = new Date();
    const due = new Date(dueDate);
    const diffTime = today - due;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
}

// =========================================
// Keyboard Shortcuts
// =========================================

document.addEventListener('keydown', function(e) {
    // Ctrl+S or Cmd+S to save form
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const form = document.querySelector('form');
        if (form) {
            form.submit();
        }
    }

    // Escape to cancel
    if (e.key === 'Escape') {
        const cancelBtn = document.querySelector('[href*="cancel"], a.btn-secondary');
        if (cancelBtn) {
            window.location.href = cancelBtn.href;
        }
    }
});

// =========================================
// Real-time Validation
// =========================================

// Email field real-time validation
document.addEventListener('DOMContentLoaded', function() {
    const emailFields = document.querySelectorAll('input[type="email"]');

    emailFields.forEach(field => {
        field.addEventListener('blur', function() {
            if (this.value && !isValidEmail(this.value)) {
                showFieldError(this, 'Please enter a valid email address');
            } else {
                clearFieldError(this);
            }
        });

        field.addEventListener('input', function() {
            if (this.classList.contains('has-error') && isValidEmail(this.value)) {
                clearFieldError(this);
            }
        });
    });
});

/**
 * Clear error from a single field
 */
function clearFieldError(fieldElement) {
    fieldElement.classList.remove('has-error');
    const formGroup = fieldElement.closest('.form-group');
    if (formGroup) {
        const errorDiv = formGroup.querySelector('.form-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
}

// =========================================
// Search Highlighting
// =========================================

/**
 * Highlight search terms in table
 */
function highlightSearchTerms(searchTerm) {
    if (!searchTerm) return;

    const rows = document.querySelectorAll('table tbody tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm.toLowerCase())) {
            row.classList.add('highlight');
        } else {
            row.classList.remove('highlight');
        }
    });
}

// Add highlight style to CSS
const style = document.createElement('style');
style.textContent = `
    tr.highlight {
        background-color: #fff3cd !important;
    }
`;
document.head.appendChild(style);
