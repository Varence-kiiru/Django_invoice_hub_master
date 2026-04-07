/**
 * Invoice Management JavaScript
 * Handles form interactions, calculations, and API calls
 */

// ━━━━━ UTILITIES ━━━━━

function showLoadingIndicator(message = 'Loading...') {
  const loader = document.getElementById('loading-indicator');
  if (loader) {
    loader.style.display = 'flex';
  }
}

function hideLoadingIndicator() {
  const loader = document.getElementById('loading-indicator');
  if (loader) {
    loader.style.display = 'none';
  }
}

function showAlert(message, type = 'info') {
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible`;
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
      <span aria-hidden="true">&times;</span>
    </button>
  `;

  const container = document.querySelector('.admin-container');
  if (container) {
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      alertDiv.style.opacity = '0';
      setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
  }
}

// ━━━━━ LINE ITEM CALCULATIONS ━━━━━

function calculateLineTotal() {
  const qty = parseFloat(document.getElementById('quantity')?.value) || 0;
  const price = parseFloat(document.getElementById('unit-price')?.value) || 0;
  const taxRate = parseFloat(document.getElementById('tax-rate')?.value) || 0;

  const subtotal = qty * price;
  const tax = subtotal * (taxRate / 100);
  const total = subtotal + tax;

  const totalElement = document.getElementById('line-total');
  if (totalElement) {
    totalElement.value = total.toFixed(2);
    // Also update any display elements
    const displayElement = document.getElementById('line-total-display') ||
                          document.querySelector('.line-total-display') ||
                          document.querySelector('[data-line-total]');
    if (displayElement) {
      displayElement.textContent = total.toFixed(2);
    }
  }

  return { subtotal, tax, total };
}

function updateProductInfo() {
  const select = document.getElementById('product');
  if (!select) return;

  const option = select.options[select.selectedIndex];

  // Clear if no selection
  if (!option.value) {
    document.getElementById('description').value = '';
    document.getElementById('unit-price').value = '0';
    document.getElementById('tax_rate').value = '0';
    calculateLineTotal();
    return;
  }

  // Get product data from option attributes
  const description = option.getAttribute('data-description');
  const price = option.getAttribute('data-price');
  const taxRateType = option.getAttribute('data-tax-rate-type');

  console.log('[updateProductInfo] Selected product:', {
    description: description,
    price: price,
    taxRateType: taxRateType
  });

  // Auto-populate description
  if (description) {
    const descInput = document.getElementById('description');
    if (descInput) {
      descInput.value = description;
      console.log('[updateProductInfo] Description set to:', description);
    }
  }

  // Auto-populate unit price
  if (price) {
    const priceInput = document.getElementById('unit-price');
    if (priceInput) {
      priceInput.value = parseFloat(price).toFixed(2);
      console.log('[updateProductInfo] Price set to:', parseFloat(price).toFixed(2));
    }
  }

  // Auto-populate tax rate based on tax rate type
  if (taxRateType) {
    const taxRateSelect = document.getElementById('tax_rate');
    if (taxRateSelect) {
      // Get tax class rate map from the embedded JSON
      const mapElement = document.getElementById('tax-class-rate-map');
      if (mapElement && mapElement.textContent) {
        try {
          const taxClassRateMap = JSON.parse(mapElement.textContent);
          console.log('[updateProductInfo] Tax class rate map:', taxClassRateMap);

          if (taxClassRateMap[taxRateType]) {
            const rateInfo = taxClassRateMap[taxRateType];
            const rateId = rateInfo.rate_id;

            // Find and select the option with matching rate ID
            for (let i = 0; i < taxRateSelect.options.length; i++) {
              const optionValue = taxRateSelect.options[i].value;
              if (optionValue == rateId) {
                taxRateSelect.selectedIndex = i;
                console.log('[updateProductInfo] Tax rate set to:', rateInfo.name, '(' + rateInfo.percentage + '%)');
                break;
              }
            }
          }
        } catch (e) {
          console.error('[updateProductInfo] Error parsing tax class rate map:', e);
        }
      }
    }
  }

  calculateLineTotal();
}

function updateLineItemTotal() {
  calculateLineTotal();
}

// Add event listeners for real-time calculation
document.addEventListener('DOMContentLoaded', function() {
  // Set default due date on create form
  setDefaultDueDate();

  // Add real-time calculation listeners
  const quantityInput = document.getElementById('quantity');
  const priceInput = document.getElementById('unit-price');
  const taxRateInput = document.getElementById('tax-rate');

  if (quantityInput) {
    quantityInput.addEventListener('input', calculateLineTotal);
  }
  if (priceInput) {
    priceInput.addEventListener('input', calculateLineTotal);
  }
  if (taxRateInput) {
    taxRateInput.addEventListener('input', calculateLineTotal);
  }

  // Close modals on escape key
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
      });
    }
  });

  // Close alert messages
  document.querySelectorAll('.alert .close').forEach(btn => {
    btn.addEventListener('click', function() {
      this.closest('.alert').remove();
    });
  });

  // Auto-format currency inputs
  document.querySelectorAll('[type="number"][data-currency]').forEach(input => {
    input.addEventListener('change', function() {
      if (this.value) {
        this.value = parseFloat(this.value).toFixed(2);
      }
    });
  });
});

// ━━━━━ DATE UTILITIES ━━━━━

function setDefaultDueDate(offset = 30) {
  const dueDateInput = document.getElementById('due_date');
  if (dueDateInput && !dueDateInput.value) {
    const today = new Date();
    const dueDate = new Date(today.getTime() + offset * 24 * 60 * 60 * 1000);
    dueDateInput.value = dueDate.toISOString().split('T')[0];
  }
}

function formatDate(date) {
  if (!(date instanceof Date)) {
    date = new Date(date);
  }
  return date.toISOString().split('T')[0];
}

// ━━━━━ FORM HANDLING ━━━━━

function handleInvoiceCreate(event) {
  event.preventDefault();

  const form = event.target;
  const client = form.querySelector('[name="client"]');

  if (!client?.value) {
    showAlert('Please select a client', 'warning');
    return;
  }

  showLoadingIndicator();
  form.submit();
}

function handleBulkAction(action) {
  const checkboxes = document.querySelectorAll('input[name="invoice-select"]:checked');
  if (checkboxes.length === 0) {
    showAlert('Please select at least one invoice', 'warning');
    return;
  }

  const ids = Array.from(checkboxes).map(cb => cb.value);

  if (action === 'issue') {
    if (confirm(`Issue ${ids.length} invoice(s)?`)) {
      bulkIssueInvoices(ids);
    }
  } else if (action === 'send') {
    if (confirm(`Send ${ids.length} invoice(s) via email?`)) {
      bulkSendInvoices(ids);
    }
  }
}

// ━━━━━ API CALLS ━━━━━

function bulkIssueInvoices(ids) {
  showLoadingIndicator();

  fetch('/api/v1/invoices/bulk-issue/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ ids })
  })
  .then(response => {
    hideLoadingIndicator();
    if (response.ok) {
      showAlert(`Successfully issued ${ids.length} invoice(s)`, 'success');
      setTimeout(() => location.reload(), 1500);
    } else {
      showAlert('Error issuing invoices', 'danger');
    }
  })
  .catch(error => {
    hideLoadingIndicator();
    console.error('Error:', error);
    showAlert('Error issuing invoices', 'danger');
  });
}

function bulkSendInvoices(ids) {
  showLoadingIndicator();

  fetch('/api/v1/invoices/bulk-send/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ ids })
  })
  .then(response => {
    hideLoadingIndicator();
    if (response.ok) {
      showAlert(`Successfully sent ${ids.length} invoice(s)`, 'success');
      setTimeout(() => location.reload(), 1500);
    } else {
      showAlert('Error sending invoices', 'danger');
    }
  })
  .catch(error => {
    hideLoadingIndicator();
    console.error('Error:', error);
    showAlert('Error sending invoices', 'danger');
  });
}

function deleteInvoice(invoiceId) {
  if (confirm('Are you sure you want to delete this invoice?')) {
    showLoadingIndicator();

    fetch(`/invoices/${invoiceId}/delete/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    })
    .then(response => {
      hideLoadingIndicator();
      if (response.ok || response.status === 302) {
        showAlert('Invoice deleted successfully', 'success');
        setTimeout(() => window.location.href = '/invoices/', 1500);
      } else {
        showAlert('Error deleting invoice', 'danger');
      }
    })
    .catch(error => {
      hideLoadingIndicator();
      console.error('Error:', error);
      showAlert('Error deleting invoice', 'danger');
    });
  }
}

function addLineItemAPI(invoiceId, lineItem) {
  showLoadingIndicator();

  fetch(`/api/v1/invoices/${invoiceId}/add-line-item/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify(lineItem)
  })
  .then(response => {
    hideLoadingIndicator();
    if (response.ok) {
      return response.json();
    } else {
      throw new Error('Failed to add line item');
    }
  })
  .then(data => {
    showAlert('Line item added successfully', 'success');
    setTimeout(() => location.reload(), 1000);
  })
  .catch(error => {
    console.error('Error:', error);
    showAlert('Error adding line item', 'danger');
  });
}

function removeLineItemAPI(invoiceId, lineItemId) {
  if (confirm('Are you sure you want to remove this line item?')) {
    showLoadingIndicator();

    fetch(`/api/v1/invoices/${invoiceId}/remove-line-item/${lineItemId}/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    })
    .then(response => {
      hideLoadingIndicator();
      if (response.ok) {
        showAlert('Line item removed successfully', 'success');
        setTimeout(() => location.reload(), 1000);
      } else {
        showAlert('Error removing line item', 'danger');
      }
    })
    .catch(error => {
      hideLoadingIndicator();
      console.error('Error:', error);
      showAlert('Error removing line item', 'danger');
    });
  }
}

// ━━━━━ LINE ITEM EDIT/DELETE MODAL FUNCTIONS ━━━━━

function editLineItem(itemId) {
  // Get the row data
  const row = document.querySelector(`tr[data-item-id="${itemId}"]`);
  if (!row) {
    console.error('Line item not found:', itemId);
    alert('Could not find line item');
    return;
  }

  // Extract data from data attributes (or fall back to cell parsing)
  const description = row.getAttribute('data-description') || row.cells[0].textContent.trim().split('\n')[0];
  const quantity = parseFloat(row.getAttribute('data-quantity')) || parseFloat(row.cells[1].textContent.trim());
  const unitPrice = parseFloat(row.getAttribute('data-unit-price')) || parseFloat(row.cells[2].textContent.replace(/[^\d.]/g, ''));
  const taxAmount = parseFloat(row.getAttribute('data-tax-amount')) || parseFloat(row.cells[3].textContent.replace(/[^\d.]/g, ''));

  // Calculate tax rate from tax amount and line amount
  let taxRate = 0;
  const lineAmount = quantity * unitPrice;
  if (lineAmount > 0 && taxAmount > 0) {
    taxRate = ((taxAmount / lineAmount) * 100).toFixed(2);
  }

  // Populate the edit form
  document.getElementById('edit-item-id').value = itemId;
  document.getElementById('edit-modal-description').value = description;
  document.getElementById('edit-modal-quantity').value = quantity.toFixed(4);
  document.getElementById('edit-modal-unit-price').value = unitPrice.toFixed(2);
  document.getElementById('edit-modal-tax-rate').value = taxRate;

  calculateEditLineItemTotal();

  // Show the modal
  const modal = document.getElementById('edit-line-item-modal');
  if (modal) {
    modal.style.display = 'flex';
    // Focus on the first input field
    setTimeout(() => {
      document.getElementById('edit-modal-description')?.focus();
    }, 100);
  }
}

function closeEditLineItemModal() {
  const modal = document.getElementById('edit-line-item-modal');
  if (modal) {
    modal.style.display = 'none';
  }
}

function calculateEditLineItemTotal() {
  const qty = parseFloat(document.getElementById('edit-modal-quantity')?.value) || 0;
  const price = parseFloat(document.getElementById('edit-modal-unit-price')?.value) || 0;
  const taxRate = parseFloat(document.getElementById('edit-modal-tax-rate')?.value) || 0;

  const subtotal = qty * price;
  const tax = subtotal * (taxRate / 100);
  const total = subtotal + tax;

  const totalElement = document.getElementById('edit-modal-line-total');
  if (totalElement) {
    totalElement.textContent = total.toFixed(2);
  }
}

function submitEditLineItem() {
  const itemId = document.getElementById('edit-item-id')?.value;
  const invoiceId = document.querySelector('[data-invoice-id]')?.getAttribute('data-invoice-id') ||
                   window.location.pathname.match(/\/invoices\/(\d+)\//)?.[1];

  if (!invoiceId || !itemId) {
    console.error('Missing IDs - invoiceId:', invoiceId, 'itemId:', itemId);
    alert('Could not determine IDs');
    return;
  }

  const data = {
    description: document.getElementById('edit-modal-description')?.value || '',
    quantity: document.getElementById('edit-modal-quantity')?.value || '1',
    unit_price: document.getElementById('edit-modal-unit-price')?.value || '0',
    tax_rate: document.getElementById('edit-modal-tax-rate')?.value || '0',
  };

  console.log(`Submitting edit for item ${itemId}, invoice ${invoiceId}`, data);

  fetch(`/invoices/${invoiceId}/edit-line-item/${itemId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams(data),
  })
  .then(response => {
    console.log('Edit response status:', response.status);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log('Edit response data:', data);
    if (data.success) {
      closeEditLineItemModal();
      alert('Line item updated successfully');
      window.location.reload();
    } else {
      alert('Error: ' + (data.error || 'Unknown error'));
    }
  })
  .catch(error => {
    console.error('Error updating line item:', error);
    alert('Error updating line item: ' + error.message);
  });
}

function deleteLineItem(itemId) {
  if (!confirm('Are you sure you want to delete this line item?')) {
    return;
  }

  // Get invoice ID from data attribute or URL
  const invoiceId = document.querySelector('[data-invoice-id]')?.getAttribute('data-invoice-id') ||
                   window.location.pathname.match(/\/invoices\/(\d+)\//)?.[1];

  if (!invoiceId) {
    console.error('Could not determine invoice ID');
    alert('Could not determine invoice ID');
    return;
  }

  console.log(`Deleting line item ${itemId} from invoice ${invoiceId}`);

  fetch(`/invoices/${invoiceId}/remove-line-item/${itemId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  .then(response => {
    console.log('Delete response status:', response.status);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log('Delete response data:', data);
    if (data.success) {
      alert('Line item deleted successfully');
      setTimeout(() => {
        window.location.reload();
      }, 500);
    } else {
      alert('Error: ' + (data.error || 'Unknown error'));
    }
  })
  .catch(error => {
    console.error('Error deleting line item:', error);
    alert('Error deleting line item: ' + error.message);
  });
}

function submitAddLineItem() {
  const form = document.getElementById('add-item-form');
  if (!form) return;

  const invoiceId = document.querySelector('[data-invoice-id]')?.getAttribute('data-invoice-id') ||
                   window.location.pathname.match(/\/invoices\/(\d+)\//)?.[1];

  if (!invoiceId) {
    alert('Could not determine invoice ID');
    return;
  }

  const data = {
    product: document.getElementById('product')?.value || '',
    description: document.getElementById('description')?.value || '',
    quantity: document.getElementById('quantity')?.value || '1',
    unit_price: document.getElementById('unit-price')?.value || '0',
    tax_rate: document.getElementById('tax_rate')?.value || '0',
  };

  fetch(`/invoices/${invoiceId}/add-line-item/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams(data),
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    if (data.success) {
      alert('Line item added successfully');
      window.location.reload();
    } else {
      alert('Error: ' + (data.error || 'Unknown error'));
    }
  })
  .catch(error => {
    console.error('Error adding line item:', error);
    alert('Error adding line item: ' + error.message);
  });
}

// ━━━━━ UTILITIES ━━━━━

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function formatCurrency(amount, currency = 'KES') {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: currency
  }).format(amount);
}

// ━━━━━ INVOICE SEARCH/FILTER ━━━━━

function filterInvoicesByStatus(status) {
  const url = new URL(window.location);
  if (status) {
    url.searchParams.set('status', status);
  } else {
    url.searchParams.delete('status');
  }
  window.location = url.toString();
}

function searchInvoices(searchTerm) {
  const url = new URL(window.location);
  if (searchTerm) {
    url.searchParams.set('search', searchTerm);
  } else {
    url.searchParams.delete('search');
  }
  url.searchParams.set('page', '1');
  window.location = url.toString();
}

// ━━━━━ KEYBOARD SHORTCUTS ━━━━━

document.addEventListener('keydown', function(event) {
  // Ctrl+S or Cmd+S to save form
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault();
    const form = document.querySelector('form');
    if (form && form.id !== 'search-form' && form.id !== 'filter-form') {
      form.submit();
    }
  }

  // Ctrl+Escape to close modal
  if (event.ctrlKey && event.key === 'Escape') {
    event.preventDefault();
    const modal = document.querySelector('.modal[style*="display: flex"]');
    if (modal) {
      modal.style.display = 'none';
    }
  }
});

// ━━━━━ INITIALIZATION ━━━━━

document.addEventListener('DOMContentLoaded', function() {
  // Set default due date on create form
  setDefaultDueDate();

  // Close modals on escape key
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
      });
    }
  });

  // Close alert messages
  document.querySelectorAll('.alert .close').forEach(btn => {
    btn.addEventListener('click', function() {
      this.closest('.alert').remove();
    });
  });

  // Auto-format currency inputs
  document.querySelectorAll('[type="number"][data-currency]').forEach(input => {
    input.addEventListener('change', function() {
      if (this.value) {
        this.value = parseFloat(this.value).toFixed(2);
      }
    });
  });
});

// ━━━━━ EXPORT FUNCTIONS ━━━━━

function exportToCSV() {
  const table = document.querySelector('.admin-table');
  if (!table) return;

  let csv = [];
  const rows = table.querySelectorAll('tr');

  rows.forEach(row => {
    const cols = row.querySelectorAll('td, th');
    let csvRow = [];

    cols.forEach(col => {
      csvRow.push('"' + col.textContent.replace(/"/g, '""') + '"');
    });

    csv.push(csvRow.join(','));
  });

  const csvContent = csv.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'invoices_' + new Date().toISOString().split('T')[0] + '.csv';
  a.click();
  window.URL.revokeObjectURL(url);
}

function printInvoice() {
  window.print();
}

// ━━━━━ THEME SUPPORT ━━━━━

function isDarkMode() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

// Watch for theme changes
if (window.matchMedia) {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    document.documentElement.style.colorScheme = isDarkMode() ? 'dark' : 'light';
  });
}

// ━━━━━ RESPONSIVE UTILITIES ━━━━━

function isMobileView() {
  return window.innerWidth <= 768;
}

window.addEventListener('resize', () => {
  if (isMobileView()) {
    // Mobile-specific adjustments
    document.querySelectorAll('.invoice-search-panel').forEach(panel => {
      panel.style.flexDirection = 'column';
    });
  } else {
    document.querySelectorAll('.invoice-search-panel').forEach(panel => {
      panel.style.flexDirection = 'row';
    });
  }
});

console.log('Invoice management JavaScript loaded');
