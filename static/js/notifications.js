/* Simple notification helper using browser alerts as fallback */
export function notifySuccess(msg) { console.log('SUCCESS:', msg); alert(msg); }
export function notifyError(msg) { console.error('ERROR:', msg); alert(msg); }

/**
 * Notification Center Management
 * Handles real-time notifications, polling, and interactions
 */

class NotificationCenter {
    constructor(options = {}) {
        this.pollInterval = options.pollInterval || 10000; // 10 seconds
        this.maxNotifications = options.maxNotifications || 10;
        this.notificationPanel = document.getElementById('notification-panel');
        this.notificationList = document.getElementById('notification-list');
        this.notificationToggle = document.getElementById('notification-toggle');
        this.notificationCount = document.getElementById('notification-count');
        this.isOpen = false;
        this.pollTimer = null;

        this.init();
    }

    init() {
        // Setup toggle button
        if (this.notificationToggle) {
            this.notificationToggle.addEventListener('click', () => this.toggle());
        }

        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isOpen &&
                !this.notificationPanel?.contains(e.target) &&
                !this.notificationToggle?.contains(e.target)) {
                this.close();
            }
        });

        // Start polling
        this.startPolling();
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        if (!this.notificationPanel) return;

        this.isOpen = true;
        this.notificationPanel.setAttribute('aria-hidden', 'false');
        this.notificationToggle?.setAttribute('aria-expanded', 'true');
        this.notificationPanel.style.display = 'block';

        // Load notifications when opened
        this.loadNotifications();
    }

    close() {
        if (!this.notificationPanel) return;

        this.isOpen = false;
        this.notificationPanel.setAttribute('aria-hidden', 'true');
        this.notificationToggle?.setAttribute('aria-expanded', 'false');
        this.notificationPanel.style.display = 'none';
    }

    startPolling() {
        // Load immediately
        this.loadNotifications();

        // Then poll every interval
        this.pollTimer = setInterval(() => {
            this.loadNotifications();
        }, this.pollInterval);
    }

    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }

    loadNotifications() {
        fetch('/api/v1/notifications/?limit=' + this.maxNotifications + '&ordering=-created_at')
            .then(response => response.json())
            .then(data => {
                this.renderNotifications(data.results || []);
                this.updateBadge(data.unread_count || 0);
            })
            .catch(error => {
                console.error('Error loading notifications:', error);
                this.renderEmpty();
            });
    }

    renderNotifications(notifications) {
        if (!this.notificationList) return;

        if (notifications.length === 0) {
            this.renderEmpty();
            return;
        }

        let html = '';
        notifications.forEach(notif => {
            html += this.createNotificationHTML(notif);
        });

        this.notificationList.innerHTML = html;

        // Add event listeners
        this.notificationList.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = item.dataset.notificationId;
                this.markAsRead(id);
            });
        });
    }

    renderEmpty() {
        if (this.notificationList) {
            this.notificationList.innerHTML = '<div class="no-notifications">No new notifications</div>';
        }
    }

    createNotificationHTML(notif) {
        const icon = this.getNotificationIcon(notif.notification_type);
        const time = this.formatTime(notif.created_at);

        return `
            <div class="notification-item" data-notification-id="${notif.id}">
                <div class="notification-item-icon">${icon}</div>
                <div class="notification-item-content">
                    <strong>${notif.subject}</strong>
                    <small>${time}</small>
                </div>
                ${!notif.is_read ? '<span class="notification-item-badge">●</span>' : ''}
            </div>
        `;
    }

    getNotificationIcon(type) {
        const icons = {
            'invoice_issued': '📄',
            'payment_received': '💰',
            'payment_confirmation': '💳',
            'quote_accepted': '✓',
            'quote_rejected': '✕',
            'quote_issued': '📝',
            'delivery_confirmed': '📦',
            'delivery_in_transit': '🚚',
            'delivery_completed': '✓',
            'expense_approved': '✓',
            'expense_approval_required': '⚠️',
            'overdue_reminder': '⚠️',
            'member_invited': '👤',
            'financial_report': '📊'
        };

        return icons[type] || 'ℹ️';
    }

    formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;

        // Less than a minute
        if (diff < 60000) return 'just now';

        // Less than an hour
        if (diff < 3600000) {
            const mins = Math.floor(diff / 60000);
            return `${mins}m ago`;
        }

        // Less than a day
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }

        // Less than a week
        if (diff < 604800000) {
            const days = Math.floor(diff / 86400000);
            return `${days}d ago`;
        }

        return date.toLocaleDateString();
    }

    updateBadge(count) {
        if (!this.notificationCount) return;

        if (count > 0) {
            this.notificationCount.textContent = count > 9 ? '9+' : count;
            this.notificationCount.style.display = 'block';
        } else {
            this.notificationCount.style.display = 'none';
        }
    }

    markAsRead(notificationId) {
        fetch(`/api/v1/notifications/${notificationId}/mark-as-read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            this.loadNotifications(); // Reload to update count
        })
        .catch(error => console.error('Error marking notification as read:', error));
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

    destroy() {
        this.stopPolling();
        if (this.notificationToggle) {
            this.notificationToggle.removeEventListener('click', () => this.toggle());
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('notification-toggle')) {
        window.notificationCenter = new NotificationCenter({
            pollInterval: 15000,  // 15 seconds
            maxNotifications: 10
        });
    }
});
