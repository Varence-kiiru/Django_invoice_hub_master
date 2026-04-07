/**
 * Modal utilities - Custom implementation (no Bootstrap dependency)
 * Handles confirmation dialogs, alerts, and custom modals
 */

/**
 * Show a confirmation modal
 * Returns a Promise that resolves to true/false based on user action
 */
async function confirm(title = 'Confirm', message = '', options = {}) {
  return new Promise((resolve) => {
    const modalId = options.modalId || 'confirmModal';
    let modal = document.getElementById(modalId);

    if (!modal) {
      modal = createConfirmModal(modalId);
      document.body.appendChild(modal);
    }

    // Set content
    modal.querySelector('.modal-title').textContent = title;
    modal.querySelector('.modal-body').textContent = message;

    // Show custom modal
    showModal(modal);

    // Handle buttons
    const confirmBtn = modal.querySelector('.btn-confirm');
    const cancelBtn = modal.querySelector('.btn-cancel');

    const cleanup = () => {
      confirmBtn.removeEventListener('click', onConfirm);
      cancelBtn.removeEventListener('click', onCancel);
      hideModal(modal);
    };

    const onConfirm = () => {
      cleanup();
      resolve(true);
    };

    const onCancel = () => {
      cleanup();
      resolve(false);
    };

    confirmBtn.addEventListener('click', onConfirm);
    cancelBtn.addEventListener('click', onCancel);
  });
}

/**
 * Show an alert modal
 * Returns a Promise that resolves when user acknowledges
 */
async function alert(title = 'Alert', message = '', type = 'info') {
  return new Promise((resolve) => {
    const modalId = 'alertModal';
    let modal = document.getElementById(modalId);

    if (!modal) {
      modal = createAlertModal(modalId);
      document.body.appendChild(modal);
    }

    // Set content
    modal.querySelector('.modal-title').textContent = title;
    modal.querySelector('.modal-body').textContent = message;
    modal.classList.remove('alert-info', 'alert-success', 'alert-warning', 'alert-danger');
    modal.classList.add(`alert-${type}`);

    // Show custom modal
    showModal(modal);

    // Handle button
    const okBtn = modal.querySelector('.btn-ok');

    const cleanup = () => {
      okBtn.removeEventListener('click', onOk);
      hideModal(modal);
    };

    const onOk = () => {
      cleanup();
      resolve();
    };

    okBtn.addEventListener('click', onOk);
  });
}

/**
 * Show a delete confirmation modal
 * Returns a Promise that resolves to true/false
 */
async function confirmDelete(itemName = 'this item') {
  return confirm('Delete Confirmation', `Are you sure you want to permanently delete ${itemName}? This action cannot be undone.`);
}

/**
 * Show a loading modal with spinner
 * Returns a function to close the modal
 */
function loading(message = 'Loading...') {
  const modalId = 'loadingModal';
  let modal = document.getElementById(modalId);

  if (!modal) {
    modal = createLoadingModal(modalId);
    document.body.appendChild(modal);
  }

  // Set message
  modal.querySelector('.loading-text').textContent = message;

  // Show custom modal
  showModal(modal);

  // Return close function
  return () => hideModal(modal);
}

/**
 * Close modal by ID
 */
function close(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    hideModal(modal);
  }
}

/**
 * Show modal using custom CSS classes
 */
function showModal(modal) {
  if (!modal) return;

  modal.classList.add('show');
  modal.style.display = 'flex';
  modal.setAttribute('aria-hidden', 'false');

  // Prevent body scroll
  document.body.classList.add('modal-open');
  document.body.style.overflow = 'hidden';
}

/**
 * Hide modal using custom CSS classes
 */
function hideModal(modal) {
  if (!modal) return;

  modal.classList.remove('show');
  modal.classList.remove('fade');
  modal.style.display = 'none';
  modal.setAttribute('aria-hidden', 'true');

  // Restore body scroll - remove the inline style that was blocking it
  document.body.classList.remove('modal-open');

  // Set overflow back to auto only if no other modals are open
  const activeModals = document.querySelectorAll('.modal.show, .modal[style*="display: flex"]');
  if (activeModals.length === 0) {
    document.body.style.overflow = 'auto';
  }
}

/**
 * Helper to create confirmation modal HTML
 */
function createConfirmModal(id) {
  const modal = document.createElement('div');
  modal.id = id;
  modal.className = 'modal fade';
  modal.tabIndex = -1;
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-hidden', 'true');

  modal.innerHTML = `
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title"></h5>
          <button type="button" class="btn-close" aria-label="Close"></button>
        </div>
        <div class="modal-body"></div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-cancel">Cancel</button>
          <button type="button" class="btn btn-primary btn-confirm">Confirm</button>
        </div>
      </div>
    </div>
  `;

  // Close on X button
  modal.querySelector('.btn-close').addEventListener('click', () => {
    hideModal(modal);
  });

  return modal;
}

/**
 * Helper to create alert modal HTML
 */
function createAlertModal(id) {
  const modal = document.createElement('div');
  modal.id = id;
  modal.className = 'modal fade alert-modal';
  modal.tabIndex = -1;
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-hidden', 'true');

  modal.innerHTML = `
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title"></h5>
          <button type="button" class="btn-close" aria-label="Close"></button>
        </div>
        <div class="modal-body"></div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary btn-ok">OK</button>
        </div>
      </div>
    </div>
  `;

  // Close on X button
  modal.querySelector('.btn-close').addEventListener('click', () => {
    hideModal(modal);
  });

  return modal;
}

/**
 * Helper to create loading modal HTML
 */
function createLoadingModal(id) {
  const modal = document.createElement('div');
  modal.id = id;
  modal.className = 'modal fade';
  modal.tabIndex = -1;
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-hidden', 'true');

  modal.innerHTML = `
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-body text-center">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="loading-text mt-3">Loading...</p>
        </div>
      </div>
    </div>
  `;

  return modal;
}

/**
 * DEPRECATED: Auto-initialize delete buttons with modal confirmation
 * This function is no longer used - the global modal system (confirm_delete.html)
 * handles all delete button confirmations using the .btn-delete class.
 * Keeping function signature for backward compatibility if needed.
 */
function initializeDeleteButtons() {
  // DISABLED: Using global delete modal from confirm_delete.html instead
  // Do not initialize old delete button handlers
}
