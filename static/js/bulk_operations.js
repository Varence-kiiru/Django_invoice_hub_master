/**
 * Bulk Operations System
 * Handles selection, bulk actions, and API communication
 */

class BulkOperations {
    constructor(entityType) {
        this.entityType = entityType;
        this.selectedIds = new Set();
        this.init();
    }

    init() {
        // Select all checkbox
        const selectAllCheckbox = document.querySelector('.bulk-select-all');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => this.handleSelectAll(e));
        }

        // Individual row checkboxes
        document.querySelectorAll('.bulk-select-item').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handleItemSelect(e));
        });

        // Bulk action buttons
        document.querySelector('.bulk-status-update')?.addEventListener('click', () => this.showStatusModal());
        document.querySelector('.bulk-send-email')?.addEventListener('click', () => this.showEmailModal());
        document.querySelector('.bulk-delete')?.addEventListener('click', () => this.confirmDelete());

        // Modal close buttons
        document.querySelector('.bulk-status-close')?.addEventListener('click', () => this.closeStatusModal());
        document.querySelector('.bulk-email-close')?.addEventListener('click', () => this.closeEmailModal());

        // Modal submit buttons
        document.querySelector('.bulk-status-submit')?.addEventListener('click', () => this.submitStatusUpdate());
        document.querySelector('.bulk-email-submit')?.addEventListener('click', () => this.submitEmail());
    }

    handleSelectAll(event) {
        const isChecked = event.target.checked;

        document.querySelectorAll('.bulk-select-item').forEach(checkbox => {
            checkbox.checked = isChecked;
            const rowId = checkbox.dataset.id;

            if (isChecked) {
                this.selectedIds.add(rowId);
            } else {
                this.selectedIds.delete(rowId);
            }
        });

        this.updateBulkActionsUI();
    }

    handleItemSelect(event) {
        const rowId = event.target.dataset.id;

        if (event.target.checked) {
            this.selectedIds.add(rowId);
        } else {
            this.selectedIds.delete(rowId);
            // Uncheck "select all" if not all are selected
            const selectAllCheckbox = document.querySelector('.bulk-select-all');
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
            }
        }

        this.updateBulkActionsUI();
    }

    updateBulkActionsUI() {
        const bulkActionsContainer = document.querySelector('.bulk-actions');
        const count = this.selectedIds.size;

        if (count > 0) {
            if (bulkActionsContainer) {
                bulkActionsContainer.style.display = 'flex';
            }
            const countElement = document.querySelector('.bulk-count');
            if (countElement) {
                countElement.textContent = `${count} selected`;
            }
        } else {
            if (bulkActionsContainer) {
                bulkActionsContainer.style.display = 'none';
            }
        }
    }

    showStatusModal() {
        if (this.selectedIds.size === 0) {
            this.showNotification('Please select at least one item', 'error');
            return;
        }

        // Fetch available status options
        fetch('/api/bulk/options/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: JSON.stringify({ entity_type: this.entityType })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.querySelector('.bulk-status-select');
                select.innerHTML = '<option value="">-- Select Status --</option>';

                data.options.status_options.forEach(status => {
                    const option = document.createElement('option');
                    option.value = status;
                    option.textContent = this.formatStatus(status);
                    select.appendChild(option);
                });

                document.querySelector('.bulk-status-modal').style.display = 'block';
            }
        });
    }

    showEmailModal() {
        if (this.selectedIds.size === 0) {
            this.showNotification('Please select at least one item', 'error');
            return;
        }

        // Fetch available email types
        fetch('/api/bulk/options/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: JSON.stringify({ entity_type: this.entityType })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.querySelector('.bulk-email-type-select');
                select.innerHTML = '<option value="">-- Select Email Type --</option>';

                data.options.email_types.forEach(emailType => {
                    const option = document.createElement('option');
                    option.value = emailType;
                    option.textContent = this.formatEmailType(emailType);
                    select.appendChild(option);
                });

                // Show/hide custom message fields based on selection
                select.addEventListener('change', (e) => {
                    const customFields = document.querySelector('.bulk-email-custom-fields');
                    if (e.target.value === 'custom') {
                        customFields.style.display = 'block';
                    } else {
                        customFields.style.display = 'none';
                    }
                });

                document.querySelector('.bulk-email-modal').style.display = 'block';
            }
        });
    }

    closeStatusModal() {
        document.querySelector('.bulk-status-modal').style.display = 'none';
    }

    closeEmailModal() {
        document.querySelector('.bulk-email-modal').style.display = 'none';
    }

    submitStatusUpdate() {
        const status = document.querySelector('.bulk-status-select').value;

        if (!status) {
            this.showNotification('Please select a status', 'error');
            return;
        }

        const payload = {
            entity_type: this.entityType,
            ids: Array.from(this.selectedIds),
            status: status
        };

        fetch('/api/bulk/status-update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification(`Updated ${data.updated_count} items`, 'success');
                this.closeStatusModal();
                // Reload page after short delay
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.showNotification(data.error || 'Failed to update', 'error');
            }
        })
        .catch(error => {
            this.showNotification(`Error: ${error}`, 'error');
        });
    }

    submitEmail() {
        const emailType = document.querySelector('.bulk-email-type-select').value;

        if (!emailType) {
            this.showNotification('Please select an email type', 'error');
            return;
        }

        const payload = {
            entity_type: this.entityType,
            ids: Array.from(this.selectedIds),
            email_type: emailType
        };

        // Add custom subject/message if custom email type
        if (emailType === 'custom') {
            payload.subject = document.querySelector('.bulk-email-subject').value;
            payload.message = document.querySelector('.bulk-email-message').value;

            if (!payload.subject || !payload.message) {
                this.showNotification('Please enter subject and message', 'error');
                return;
            }
        }

        fetch('/api/bulk/send-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification(`Sent ${data.sent_count} emails`, 'success');
                this.closeEmailModal();
                // Reload after delay
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.showNotification(data.error || 'Failed to send emails', 'error');
            }
        })
        .catch(error => {
            this.showNotification(`Error: ${error}`, 'error');
        });
    }

    confirmDelete() {
        if (this.selectedIds.size === 0) {
            this.showNotification('Please select at least one item', 'error');
            return;
        }

        if (!confirm(`Delete ${this.selectedIds.size} items? This cannot be undone.`)) {
            return;
        }

        const payload = {
            entity_type: this.entityType,
            ids: Array.from(this.selectedIds)
        };

        fetch('/api/bulk/delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification(`Deleted ${data.deleted_count} items`, 'success');
                // Reload after delay
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.showNotification(data.error || 'Failed to delete', 'error');
            }
        })
        .catch(error => {
            this.showNotification(`Error: ${error}`, 'error');
        });
    }

    formatStatus(status) {
        const map = {
            'draft': 'Draft',
            'sent': 'Sent',
            'issued': 'Issued',
            'paid': 'Paid',
            'partially_paid': 'Partially Paid',
            'overdue': 'Overdue',
            'cancelled': 'Cancelled',
            'pending': 'Pending',
            'successful': 'Successful',
            'failed': 'Failed',
            'refunded': 'Refunded',
            'viewed': 'Viewed',
            'accepted': 'Accepted',
            'rejected': 'Rejected',
            'expired': 'Expired',
            'converted': 'Converted',
            'archived': 'Archived',
            'active': 'Active',
            'inactive': 'Inactive'
        };
        return map[status] || status;
    }

    formatEmailType(emailType) {
        const map = {
            'invoice': 'Send Invoice',
            'quotation': 'Send Quotation',
            'reminder': 'Send Reminder',
            'custom': 'Custom Email'
        };
        return map[emailType] || emailType;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `bulk-notification bulk-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
            color: white;
            border-radius: 4px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    getCookie(name) {
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
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const entityType = document.querySelector('[data-entity-type]')?.dataset.entityType;
    if (entityType) {
        window.bulkOps = new BulkOperations(entityType);
    }
});
