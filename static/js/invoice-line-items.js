/**
 * Invoice Line Items Modal - Calculation & Management
 * Handles modal operations, product selection, and line item calculations
 */

const LineItemsModal = {
  currentInvoiceId: null,
  allProducts: [],

  // Initialize modal functionality
  init: function() {
    console.log('✓ LineItemsModal initializing...');
    this.attachEventListeners();
    this.logSystemStatus();
  },

  // Log status for debugging
  logSystemStatus: function() {
    const modal = document.getElementById('line-items-modal');
    const form = document.getElementById('add-line-item-form');
    const inputs = {
      quantity: document.getElementById('modal-quantity'),
      unitPrice: document.getElementById('modal-unit-price'),
      taxRate: document.getElementById('modal-tax-rate'),
      total: document.getElementById('modal-line-total')
    };

    console.log('[System Check]', {
      modal: modal ? '✓' : '✗',
      form: form ? '✓' : '✗',
      inputs: Object.keys(inputs).reduce((acc, key) => {
        acc[key] = inputs[key] ? '✓' : '✗';
        return acc;
      }, {})
    });
  },

  // Attach all event listeners
  attachEventListeners: function() {
    // Quantity input
    const qtyInput = document.getElementById('modal-quantity');
    if (qtyInput) {
      // Ensure it has a default value
      if (!qtyInput.value || qtyInput.value === '') {
        qtyInput.value = '1';
      }
      qtyInput.addEventListener('input', () => this.calculateTotal());
      qtyInput.addEventListener('change', () => this.calculateTotal());
    }

    // Unit price input
    const priceInput = document.getElementById('modal-unit-price');
    if (priceInput) {
      // Ensure it has a default value
      if (!priceInput.value || priceInput.value === '') {
        priceInput.value = '0';
      }
      priceInput.addEventListener('input', () => this.calculateTotal());
      priceInput.addEventListener('change', () => this.calculateTotal());
    }

    // Tax rate input
    const rateInput = document.getElementById('modal-tax-rate');
    if (rateInput) {
      // Ensure it has a default value
      if (!rateInput.value || rateInput.value === '') {
        rateInput.value = '0';
      }
      rateInput.addEventListener('input', () => this.calculateTotal());
      rateInput.addEventListener('change', () => this.calculateTotal());
    }

    // Product selection
    const productSelect = document.getElementById('modal-product');
    if (productSelect) {
      productSelect.addEventListener('change', () => this.handleProductSelection());
    }

    console.log('✓ Event listeners attached');
  },

  // Calculate line item total
  calculateTotal: function() {
    console.log('[Calculate] Starting calculation...');

    const qtyElement = document.getElementById('modal-quantity');
    const priceElement = document.getElementById('modal-unit-price');
    const rateElement = document.getElementById('modal-tax-rate');
    const totalElement = document.getElementById('modal-line-total');

    // Validate elements exist
    if (!qtyElement || !priceElement || !rateElement || !totalElement) {
      console.error('[Calculate] Missing required elements');
      return;
    }

    // Parse values
    const qty = parseFloat(qtyElement.value) || 0;
    const price = parseFloat(priceElement.value) || 0;
    const rate = parseFloat(rateElement.value) || 0;

    console.log(`[Calculate] Values: qty=${qty}, price=${price}, rate=${rate}%`);

    // Validate values
    if (qty < 0 || price < 0 || rate < 0) {
      console.warn('[Calculate] Invalid values detected');
      totalElement.textContent = '0.00';
      return;
    }

    // Calculate: subtotal first, then add tax
    const subtotal = qty * price;
    const taxAmount = subtotal * (rate / 100);
    const total = subtotal + taxAmount;

    // Update display
    totalElement.textContent = total.toFixed(2);

    console.log(`[Calculate] ✓ Result: ${qty} × KES ${price.toFixed(2)} = KES ${subtotal.toFixed(2)} + ${rate}% tax (KES ${taxAmount.toFixed(2)}) = KES ${total.toFixed(2)}`);
  },

  // Handle product selection
  handleProductSelection: function() {
    const productSelect = document.getElementById('modal-product');
    const selectedId = productSelect.value;

    console.log(`[Product] Selected: ${selectedId}`);

    if (!selectedId) {
      // Clear fields if no selection
      document.getElementById('modal-description').value = '';
      document.getElementById('modal-unit-price').value = '0';
      document.getElementById('modal-tax-rate').value = '0';
      document.getElementById('modal-line-total').textContent = '0.00';
      document.getElementById('modal-quantity').value = '1';
      return;
    }

    // Find product in list
    const product = this.allProducts.find(p => p.id == selectedId);
    if (!product) {
      console.warn(`[Product] Product not found: ${selectedId}`);
      return;
    }

    console.log(`[Product] Found: ${product.name} - Price: KES ${product.unit_price}`);

    // Auto-fill form fields
    document.getElementById('modal-description').value = product.description || product.name;
    document.getElementById('modal-unit-price').value = parseFloat(product.unit_price).toFixed(2);
    document.getElementById('modal-quantity').value = '1';

    // Set tax rate based on tax class
    let taxRate = 0;
    if (product.tax_class && product.tax_class.rate_type) {
      const rateMap = {
        'standard': 16,
        'zero': 0,
        'exempt': 0
      };
      taxRate = rateMap[product.tax_class.rate_type] || 0;
      console.log(`[Product] ✓ Tax rate set: ${taxRate}% (${product.tax_class.rate_type})`);
    }
    document.getElementById('modal-tax-rate').value = taxRate;

    // Recalculate total
    this.calculateTotal();
  },

  // Load products from API
  loadProducts: function() {
    const productSelect = document.getElementById('modal-product');
    if (!productSelect) {
      console.error('[Load Products] Select element not found');
      return;
    }

    console.log('[Load Products] Fetching from API...');
    productSelect.disabled = true;
    productSelect.innerHTML = '<option value="">Loading products...</option>';

    fetch('/api/v1/products/', {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCsrfToken()
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      const products = data.results || data;
      this.allProducts = products;

      console.log(`[Load Products] ✓ Loaded ${products.length} products`);

      // Rebuild dropdown
      productSelect.innerHTML = '<option value="">--- Select Product ---</option>';

      if (products.length === 0) {
        productSelect.innerHTML += '<option disabled>No products found</option>';
        productSelect.disabled = true;
        return;
      }

      products.forEach(product => {
        const option = document.createElement('option');
        option.value = product.id;
        option.textContent = `${product.name} (${product.sku}) - KES ${parseFloat(product.unit_price).toFixed(2)}`;
        productSelect.appendChild(option);
      });

      productSelect.disabled = false;
    })
    .catch(error => {
      console.error('[Load Products] Error:', error);
      productSelect.innerHTML = `<option>Error: ${error.message}</option>`;
      productSelect.disabled = false;
    });
  },

  // Get CSRF token
  getCsrfToken: function() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  },

  // Open modal
  openModal: function() {
    console.log('[Modal] Opening...');
    const modal = document.getElementById('line-items-modal');
    if (modal) {
      // Ensure inputs have default values before opening
      this.resetForm();
      modal.style.display = 'flex';
      this.loadProducts();
      // Trigger initial calculation
      setTimeout(() => this.calculateTotal(), 100);
    }
  },

  // Close modal
  closeModal: function() {
    console.log('[Modal] Closing...');
    const modal = document.getElementById('line-items-modal');
    if (modal) {
      modal.style.display = 'none';
    }
    this.resetForm();
  },

  // Reset form
  resetForm: function() {
    const form = document.getElementById('add-line-item-form');
    if (form) {
      form.reset();
    }
    
    // Explicitly set default values - use optional chaining for safety
    const productSelect = document.getElementById('modal-product');
    const descInput = document.getElementById('modal-description');
    const qtyInput = document.getElementById('modal-quantity');
    const priceInput = document.getElementById('modal-unit-price');
    const rateInput = document.getElementById('modal-tax-rate');
    const totalDisplay = document.getElementById('modal-line-total');

    if (productSelect) productSelect.value = '';
    if (descInput) descInput.value = '';
    if (qtyInput) qtyInput.value = '1';
    if (priceInput) priceInput.value = '0';
    if (rateInput) rateInput.value = '0';
    if (totalDisplay) totalDisplay.textContent = '0.00';
    
    console.log('[Reset] Form reset to defaults - qty=1, price=0, tax=0');
  },

  // Submit line item
  submitLineItem: function() {
    const invoiceId = window.location.pathname.split('/')[2];
    const productId = document.getElementById('modal-product')?.value || '';
    const description = document.getElementById('modal-description')?.value || '';
    
    // Get input elements and their values
    const qtyElement = document.getElementById('modal-quantity');
    const priceElement = document.getElementById('modal-unit-price');
    const rateElement = document.getElementById('modal-tax-rate');

    // Check elements exist
    if (!qtyElement || !priceElement || !rateElement) {
      alert('Error: Form elements not found. Please refresh the page.');
      console.error('[Submit] Missing form elements');
      return;
    }

    // Get raw string values from inputs
    const qtyStr = String(qtyElement.value || '1').trim();
    const priceStr = String(priceElement.value || '0').trim();
    const rateStr = String(rateElement.value || '0').trim();

    console.log('%c[Submit] ===== SUBMISSION DEBUG =====', 'color: blue; font-weight: bold;');
    console.log('[Submit] Raw input values:');
    console.log('  qtyElement.value:', JSON.stringify(qtyElement.value));
    console.log('  priceElement.value:', JSON.stringify(priceElement.value));
    console.log('  rateElement.value:', JSON.stringify(rateElement.value));
    console.log('[Submit] After string conversion:');
    console.log('  qtyStr:', JSON.stringify(qtyStr));
    console.log('  priceStr:', JSON.stringify(priceStr));
    console.log('  rateStr:', JSON.stringify(rateStr));

    // Parse to numbers
    const quantity = parseFloat(qtyStr);
    const unitPrice = parseFloat(priceStr);
    const taxRate = parseFloat(rateStr);

    console.log('[Submit] Parsed numeric values:');
    console.log('  quantity:', quantity, 'isNaN:', isNaN(quantity), 'isFinite:', isFinite(quantity));
    console.log('  unitPrice:', unitPrice, 'isNaN:', isNaN(unitPrice), 'isFinite:', isFinite(unitPrice));
    console.log('  taxRate:', taxRate, 'isNaN:', isNaN(taxRate), 'isFinite:', isFinite(taxRate));

    // Validate
    if (!productId && !description) {
      alert('Please select a product or enter a description');
      return;
    }
    if (isNaN(quantity) || !isFinite(quantity) || quantity <= 0) {
      alert('Quantity must be a valid number greater than 0');
      console.error('[Submit] Quantity validation failed:', { quantity, isNaN: isNaN(quantity), isFinite: isFinite(quantity) });
      return;
    }
    if (isNaN(unitPrice) || !isFinite(unitPrice) || unitPrice < 0) {
      alert('Unit price must be a valid number');
      console.error('[Submit] Unit price validation failed:', { unitPrice, isNaN: isNaN(unitPrice), isFinite: isFinite(unitPrice) });
      return;
    }
    if (isNaN(taxRate) || !isFinite(taxRate) || taxRate < 0) {
      alert('Tax rate must be a valid number');
      console.error('[Submit] Tax rate validation failed:', { taxRate, isNaN: isNaN(taxRate), isFinite: isFinite(taxRate) });
      return;
    }

    console.log('[Submit] All validations passed');

    const submitBtn = event?.target || document.querySelector('[onclick*="submitLineItem"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = '⏳ Adding...';
    }

    // Build form data - IMPORTANT: Must append CSRF token to FormData, not just headers
    const formData = new FormData();
    const qtyForSubmit = String(quantity);
    const priceForSubmit = String(unitPrice);
    const rateForSubmit = String(taxRate);
    const csrfToken = this.getCsrfToken();

    formData.append('product', productId);
    formData.append('description', description);
    formData.append('quantity', qtyForSubmit);
    formData.append('unit_price', priceForSubmit);
    formData.append('tax_rate', rateForSubmit);
    formData.append('csrfmiddlewaretoken', csrfToken);

    console.log('[Submit] FormData prepared (strings to be sent):');
    console.log('  product:', JSON.stringify(productId));
    console.log('  description:', JSON.stringify(description));
    console.log('  quantity:', JSON.stringify(qtyForSubmit));
    console.log('  unit_price:', JSON.stringify(priceForSubmit));
    console.log('  tax_rate:', JSON.stringify(rateForSubmit));
    console.log('  csrfmiddlewaretoken:', JSON.stringify(csrfToken));

    // Log what FormData actually contains (FormData doesn't have direct access, but we can list keys)
    console.log('[Submit] FormData entries:');
    for (let [key, value] of formData.entries()) {
      console.log(`  ${key}: ${JSON.stringify(value)}`);
    }

    console.log(`[Submit] Sending POST to /invoices/${invoiceId}/add-line-item/`);

    fetch(`/invoices/${invoiceId}/add-line-item/`, {
      method: 'POST',
      credentials: 'same-origin',
      body: formData
      // NOTE: Do NOT set Content-Type header with FormData - let browser set it
    })
    .then(response => {
      console.log('[Submit] Response status:', response.status);
      if (!response.ok) {
        return response.json().then(data => {
          console.log('[Submit] Error response data:', data);
          throw new Error(data.error || `HTTP ${response.status}`);
        }).catch(parseErr => {
          console.error('[Submit] Error parsing response:', parseErr);
          throw new Error(`HTTP ${response.status}`);
        });
      }
      return response.json();
    })
    .then(data => {
      console.log('[Submit] ✓ Success:', data);
      this.resetForm();
      this.closeModal();
      alert('Line item added successfully!');
      setTimeout(() => location.reload(), 500);
    })
    .catch(error => {
      console.error('[Submit] Error caught:', error.message);
      alert(`Error: ${error.message}`);
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = '➕ Add Item';
      }
    });
  },

  // Close modal when clicking overlay
  handleOverlayClick: function(event) {
    if (event.target.id === 'line-items-modal' || event.target.classList.contains('modal-overlay')) {
      this.closeModal();
    }
  }
};

// Global references for inline onclick handlers
window.showLineItemsModal = () => LineItemsModal.openModal();
window.openLineItemsModal = () => LineItemsModal.openModal();
window.closeLineItemsModal = () => LineItemsModal.closeModal();
window.updateLineItemTotal = () => LineItemsModal.calculateTotal();
window.updateProductSelect = () => LineItemsModal.handleProductSelection();
window.submitLineItem = () => LineItemsModal.submitLineItem();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('[Init] DOM loaded, initializing LineItemsModal...');
    LineItemsModal.init();
  });
} else {
  console.log('[Init] DOM already loaded, initializing LineItemsModal immediately...');
  LineItemsModal.init();
}

// Handle modal overlay click
document.addEventListener('click', (e) => {
  if (e.target.id === 'line-items-modal' || e.target.classList.contains('modal-overlay')) {
    LineItemsModal.closeModal();
  }
});

console.log('✓ invoice-line-items.js loaded');
