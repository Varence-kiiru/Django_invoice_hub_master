/**
 * Invoice Line Items Management - Page Initialization
 * Shared functions (editLineItem, deleteLineItem, submitEditLineItem, etc.) are in pages/invoices.js
 */

document.addEventListener('DOMContentLoaded', function() {
  // Form submission for ADD item
  const addForm = document.getElementById('add-item-form');
  if (addForm) {
    addForm.addEventListener('submit', function(e) {
      e.preventDefault();
      submitAddLineItem();
    });
  }

  // Form submission for EDIT item
  const editForm = document.getElementById('edit-line-item-form');
  if (editForm) {
    editForm.addEventListener('submit', function(e) {
      e.preventDefault();
      submitEditLineItem();
    });
  }

  // Real-time calculation for ADD form
  const quantityInput = document.getElementById('quantity');
  const priceInput = document.getElementById('unit-price');
  const taxRateInput = document.getElementById('tax_rate');

  [quantityInput, priceInput, taxRateInput].forEach(input => {
    if (input) {
      input.addEventListener('input', calculateLineTotal);
      input.addEventListener('change', calculateLineTotal);
    }
  });

  // Real-time calculation for EDIT form
  const editQuantityInput = document.getElementById('edit-modal-quantity');
  const editPriceInput = document.getElementById('edit-modal-unit-price');
  const editTaxRateInput = document.getElementById('edit-modal-tax-rate');

  [editQuantityInput, editPriceInput, editTaxRateInput].forEach(input => {
    if (input) {
      input.addEventListener('input', calculateEditLineItemTotal);
      input.addEventListener('change', calculateEditLineItemTotal);
    }
  });

  // Close edit modal on escape key
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      const modal = document.getElementById('edit-line-item-modal');
      if (modal && modal.style.display === 'flex') {
        closeEditLineItemModal();
      }
    }
  });

  // Close edit modal on overlay click
  const modalOverlay = document.querySelector('#edit-line-item-modal .modal-overlay');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', function(e) {
      if (e.target === this) {
        closeEditLineItemModal();
      }
    });
  }
});

console.log('Invoice line items page initialized');
