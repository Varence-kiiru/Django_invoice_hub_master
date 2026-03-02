/**
 * Modal Component JS
 * Handles modal interactions and integrations
 */

const Modals = {
  /**
   * Show a confirmation modal with custom message and action
   * @param {object} options - Options object
   * @param {string} options.title - Modal title
   * @param {string} options.message - Modal message
   * @param {string} options.confirmText - Confirm button text
   * @param {string} options.cancelText - Cancel button text
   * @param {function} options.onConfirm - Callback on confirm
   * @param {string} options.danger - Set to true for danger styling
   * @returns {Promise} Promise that resolves with user choice
   */
  confirm: function(options = {}) {
    return new Promise((resolve) => {
      const {
        title = 'Confirm',
        message = 'Are you sure?',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        danger = false,
        onConfirm
      } = options;

      const modalId = 'modal-' + Math.random().toString(36).substr(2, 9);
      
      // Create modal HTML
      const modalHTML = `
        <div class="modal fade" id="${modalId}" tabindex="-1" role="dialog" aria-labelledby="${modalId}-label" aria-hidden="true">
          <div class="modal-dialog modal-md" role="document">
            <div class="modal-content">
              <div class="modal-header${danger ? ' bg-danger bg-opacity-10' : ''}">
                <h5 class="modal-title" id="${modalId}-label">${title}</h5>
                <button type="button" class="btn-close" data-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body">
                <p>${message}</p>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">${cancelText}</button>
                <button type="button" class="btn ${danger ? 'btn-danger' : 'btn-primary'}" id="${modalId}-confirm">${confirmText}</button>
              </div>
            </div>
          </div>
        </div>
      `;

      // Add to DOM
      const container = document.createElement('div');
      container.innerHTML = modalHTML;
      document.body.appendChild(container.firstElementChild);

      const modalEl = document.getElementById(modalId);
      const confirmBtn = document.getElementById(modalId + '-confirm');

      // Show modal using Bootstrap
      const modal = new bootstrap.Modal(modalEl);
      modal.show();

      // Handle responses
      confirmBtn.addEventListener('click', () => {
        modal.hide();
        if (onConfirm) onConfirm();
        resolve(true);
        // Cleanup
        setTimeout(() => modalEl.remove(), 300);
      });

      modalEl.addEventListener('hidden.bs.modal', () => {
        resolve(false);
        // Cleanup
        setTimeout(() => modalEl.remove(), 300);
      });
    });
  },

  /**
   * Show a delete confirmation modal
   * @param {object} options - Options object
   * @param {string} options.itemName - Name of item being deleted
   * @param {string} options.warning - Additional warning text
   * @param {function} options.onConfirm - Callback on confirm
   * @returns {Promise} Promise that resolves with user choice
   */
  confirmDelete: function(options = {}) {
    const {
      itemName = 'this item',
      warning = 'This action cannot be undone.',
      onConfirm
    } = options;

    return this.confirm({
      title: 'Delete ' + itemName + '?',
      message: `Are you sure you want to delete ${itemName}? ${warning}`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      danger: true,
      onConfirm
    });
  },

  /**
   * Show an alert modal
   * @param {object} options - Options object
   * @param {string} options.title - Modal title
   * @param {string} options.message - Modal message
   * @param {string} options.type - Alert type (info, success, warning, danger)
   * @param {string} options.buttonText - Button text
   * @returns {Promise} Promise that resolves when closed
   */
  alert: function(options = {}) {
    return new Promise((resolve) => {
      const {
        title = 'Alert',
        message = '',
        type = 'info',
        buttonText = 'OK'
      } = options;

      const modalId = 'modal-' + Math.random().toString(36).substr(2, 9);
      const alertClass = `alert alert-${type}`;

      const modalHTML = `
        <div class="modal fade" id="${modalId}" tabindex="-1" role="dialog" aria-hidden="true">
          <div class="modal-dialog modal-md" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">${title}</h5>
                <button type="button" class="btn-close" data-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body">
                <div class="${alertClass}" role="alert">${message}</div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-primary" data-dismiss="modal">${buttonText}</button>
              </div>
            </div>
          </div>
        </div>
      `;

      const container = document.createElement('div');
      container.innerHTML = modalHTML;
      document.body.appendChild(container.firstElementChild);

      const modalEl = document.getElementById(modalId);
      const modal = new bootstrap.Modal(modalEl);
      modal.show();

      modalEl.addEventListener('hidden.bs.modal', () => {
        resolve();
        setTimeout(() => modalEl.remove(), 300);
      });
    });
  },

  /**
   * Show a loading modal
   * @param {object} options - Options object
   * @param {string} options.title - Modal title
   * @param {string} options.message - Loading message
   * @returns {HTMLElement} Modal element (call remove() to close)
   */
  loading: function(options = {}) {
    const {
      title = 'Loading',
      message = 'Please wait...'
    } = options;

    const modalId = 'modal-' + Math.random().toString(36).substr(2, 9);

    const modalHTML = `
      <div class="modal fade show" id="${modalId}" tabindex="-1" role="dialog" aria-hidden="true" style="display: block;">
        <div class="modal-dialog modal-md" role="document">
          <div class="modal-content">
            <div class="modal-body modal-loading text-center">
              <div class="spinner-border text-primary mb-3" role="status" aria-hidden="true"></div>
              <h5>${title}</h5>
              <p class="text-muted">${message}</p>
            </div>
          </div>
        </div>
      </div>
    `;

    const container = document.createElement('div');
    container.innerHTML = modalHTML;
    document.body.appendChild(container.firstElementChild);

    return document.getElementById(modalId);
  },

  /**
   * Auto-trigger delete modal from button
   * Setup: Add class "btn-delete" and data attributes to button
   * data-delete-url: URL to post delete request to
   * data-delete-name: Name of item being deleted
   * data-csrf-token: CSRF token for POST request
   */
  initializeDeleteButtons: function() {
    document.querySelectorAll('.btn-delete').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        
        const url = btn.getAttribute('data-delete-url');
        const name = btn.getAttribute('data-delete-name') || 'this item';
        const csrfToken = btn.getAttribute('data-csrf-token');

        const confirmed = await this.confirmDelete({
          itemName: name
        });

        if (confirmed && url) {
          // Send delete request
          try {
            const response = await fetch(url, {
              method: 'POST',
              headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
              }
            });

            if (response.ok) {
              window.location.reload();
            } else {
              this.alert({
                title: 'Error',
                message: 'Failed to delete item. Please try again.',
                type: 'danger'
              });
            }
          } catch (error) {
            this.alert({
              title: 'Error',
              message: 'An error occurred. Please try again.',
              type: 'danger'
            });
          }
        }
      });
    });
  },

  /**
   * Close modal with optional delay
   * @param {HTMLElement|string} modalEl - Modal element or ID
   * @param {number} delay - Delay in ms before closing
   */
  close: function(modalEl, delay = 0) {
    if (typeof modalEl === 'string') {
      modalEl = document.getElementById(modalEl);
    }

    if (!modalEl) return;

    setTimeout(() => {
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) {
        modal.hide();
      } else {
        modalEl.classList.remove('show');
        modalEl.style.display = 'none';
      }
    }, delay);
  }
};

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  Modals.initializeDeleteButtons();
});

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Modals;
}
