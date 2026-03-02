/**
 * Product Management JavaScript
 * Handles form validation, CSV import, and interactions for product pages
 */

// =========================================
// Form Validation
// =========================================

/**
 * Validate product form before submission
 */
function validateProductForm() {
    const sku = document.getElementById('id_sku');
    const name = document.getElementById('id_name');
    const unitPrice = document.getElementById('id_unit_price');
    const unitOfMeasure = document.getElementById('id_unit_of_measure');
    
    let isValid = true;
    clearFormErrors();
    
    // Validate SKU
    if (!sku || !sku.value.trim()) {
        showFieldError(sku, 'SKU is required');
        isValid = false;
    }
    
    // Validate name
    if (!name || !name.value.trim()) {
        showFieldError(name, 'Product name is required');
        isValid = false;
    }
    
    // Validate unit price
    if (!unitPrice || !unitPrice.value) {
        showFieldError(unitPrice, 'Unit price is required');
        isValid = false;
    } else if (isNaN(parseFloat(unitPrice.value)) || parseFloat(unitPrice.value) < 0) {
        showFieldError(unitPrice, 'Please enter a valid price');
        isValid = false;
    }
    
    // Validate unit of measure
    if (!unitOfMeasure || !unitOfMeasure.value.trim()) {
        showFieldError(unitOfMeasure, 'Unit of measure is required');
        isValid = false;
    }
    
    return isValid;
}

/**
 * Validate CSV data
 */
function validateCSVData() {
    const csvData = document.querySelector('textarea[name="csv_data"]');
    const csvFile = document.getElementById('csv-file');
    
    clearFormErrors();
    
    if (!csvFile.files.length && !csvData.value.trim()) {
        alert('Please select a CSV file or paste CSV data');
        return false;
    }
    
    return true;
}

// =========================================
// Helper Functions
// =========================================

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
// Product List Interactions
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    // Search clear button
    const clearBtn = document.querySelector('[onclick*="clearSearch"]');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            document.querySelector('input[name="search"]').value = '';
            this.closest('form').submit();
        });
    }
    
    // Category filter
    const categoryFilter = document.querySelector('select[name="category"]');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            this.closest('form').submit();
        });
    }
    
    // Confirmation dialogs for delete buttons
    const deleteButtons = document.querySelectorAll('a[href*="delete"]');
    deleteButtons.forEach(btn => {
        if (!btn.closest('form') && btn.innerHTML.toLowerCase().includes('delete')) {
            btn.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to delete this product?')) {
                    e.preventDefault();
                }
            });
        }
    });
});

// =========================================
// CSV Import Functionality
// =========================================

/**
 * Handle file selection for CSV import
 */
function handleFileSelect(input) {
    const label = document.getElementById('file-label');
    const fileName = document.getElementById('file-name');
    
    if (input.files && input.files[0]) {
        const file = input.files[0];
        
        // Validate file type
        if (!file.name.endsWith('.csv')) {
            alert('Please select a CSV file');
            input.value = '';
            label.classList.remove('has-file');
            fileName.textContent = '';
            return;
        }
        
        label.classList.add('has-file');
        fileName.textContent = '✓ Selected: ' + file.name;
        document.getElementById('submit-btn').textContent = 'Import ' + file.name;
    } else {
        label.classList.remove('has-file');
        fileName.textContent = '';
        document.getElementById('submit-btn').textContent = 'Import Products';
    }
}

/**
 * Drag and drop file handling
 */
document.addEventListener('DOMContentLoaded', function() {
    const fileLabel = document.getElementById('file-label');
    const fileInput = document.getElementById('csv-file');
    
    if (fileLabel && fileInput) {
        fileLabel.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileLabel.style.backgroundColor = '#e8f4f8';
            fileLabel.style.borderColor = '#2980b9';
        });
        
        fileLabel.addEventListener('dragleave', () => {
            fileLabel.style.backgroundColor = '';
            fileLabel.style.borderColor = '';
        });
        
        fileLabel.addEventListener('drop', (e) => {
            e.preventDefault();
            fileLabel.style.backgroundColor = '';
            fileLabel.style.borderColor = '';
            
            if (e.dataTransfer.files) {
                fileInput.files = e.dataTransfer.files;
                handleFileSelect(fileInput);
            }
        });
    }
});

/**
 * Switch between import tabs
 */
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.classList.add('active');
        event.target.classList.add('active');
    }
}

/**
 * Parse and preview CSV data
 */
function previewCSVData() {
    const csvData = document.querySelector('textarea[name="csv_data"]').value;
    
    if (!csvData.trim()) {
        alert('Please paste CSV data first');
        return;
    }
    
    // Simple CSV parsing
    const lines = csvData.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    let previewHtml = '<table style="border-collapse: collapse; width: 100%; margin-top: 15px;">';
    previewHtml += '<thead><tr style="background: #f5f7fa;">';
    
    headers.forEach(header => {
        previewHtml += `<th style="padding: 10px; text-align: left; border: 1px solid #ddd;">${header}</th>`;
    });
    
    previewHtml += '</tr></thead><tbody>';
    
    // Show up to 5 rows preview
    for (let i = 1; i < Math.min(6, lines.length); i++) {
        const cells = lines[i].split(',').map(c => c.trim());
        previewHtml += '<tr style="background: ' + (i % 2 === 0 ? '#f9fafb' : 'white') + ';">';
        cells.forEach((cell, idx) => {
            if (idx < headers.length) {
                previewHtml += `<td style="padding: 10px; border: 1px solid #ddd;">${cell}</td>`;
            }
        });
        previewHtml += '</tr>';
    }
    
    previewHtml += '</tbody></table>';
    
    // Insert preview
    let previewDiv = document.getElementById('csv-preview');
    if (!previewDiv) {
        previewDiv = document.createElement('div');
        previewDiv.id = 'csv-preview';
        document.querySelector('textarea[name="csv_data"]').parentNode.insertAdjacentElement('afterend', previewDiv);
    }
    previewDiv.innerHTML = previewHtml;
}

// =========================================
// Price Calculation
// =========================================

/**
 * Calculate total on price change
 */
document.addEventListener('DOMContentLoaded', function() {
    const unitPrice = document.getElementById('id_unit_price');
    
    if (unitPrice) {
        unitPrice.addEventListener('input', function() {
            // Validate as number
            if (this.value && isNaN(parseFloat(this.value))) {
                this.classList.add('has-error');
            } else {
                this.classList.remove('has-error');
            }
        });
    }
});

/**
 * Format currency input
 */
function formatCurrency(value) {
    const num = parseFloat(value);
    return isNaN(num) ? '0.00' : num.toFixed(2);
}

// =========================================
// Category Management Functions
// =========================================

/**
 * Edit category - load into form
 */
function editCategory(id, name, description) {
    document.getElementById('form-title').textContent = 'Edit Category';
    document.getElementById('form-action').value = 'update';
    document.getElementById('submit-btn').textContent = 'Save Category';
    document.getElementById('category-id').value = id;
    
    // Pre-fill form
    document.getElementById('id_name').value = name;
    document.getElementById('id_description').value = description;
    
    // Scroll to form
    document.getElementById('category-form').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Reset category form
 */
function resetForm() {
    document.getElementById('form-title').textContent = 'Create New Category';
    document.getElementById('form-action').value = 'create';
    document.getElementById('submit-btn').textContent = 'Create Category';
    document.getElementById('category-id').value = '';
    
    document.getElementById('category-form').reset();
}

// =========================================
// Confirmation Dialogs
// =========================================

/**
 * Confirm delete product
 */
function confirmDeleteProduct(productName) {
    return confirm(`Are you sure you want to delete "${productName}"?`);
}

/**
 * Confirm bulk import
 */
function confirmImport(count) {
    return confirm(`This will import ${count} products. Continue?`);
}

// =========================================
// Export Functionality
// =========================================

/**
 * Export product list to CSV
 */
function exportProductList() {
    window.location.href = '/products/export/csv/';
}

/**
 * Export product inventory to CSV
 */
function exportInventory() {
    window.location.href = '/products/inventory/export/';
}

// =========================================
// Print Functionality
// =========================================

/**
 * Print product list
 */
function printProductList() {
    window.print();
}

// =========================================
// Real-time Validation
// =========================================

// Price field validation
document.addEventListener('DOMContentLoaded', function() {
    const priceFields = document.querySelectorAll('input[type="number"]');
    
    priceFields.forEach(field => {
        field.addEventListener('blur', function() {
            if (this.value) {
                const num = parseFloat(this.value);
                if (isNaN(num) || num < 0) {
                    showFieldError(this, 'Please enter a valid positive number');
                } else {
                    clearFieldError(this);
                }
            }
        });
        
        field.addEventListener('input', function() {
            if (this.classList.contains('has-error') && this.value && !isNaN(parseFloat(this.value))) {
                clearFieldError(this);
            }
        });
    });
});

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
