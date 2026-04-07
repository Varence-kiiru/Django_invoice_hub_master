/**
 * Navbar Manager Module
 * Handles navbar interactions, dropdowns, user menu, notifications, and datetime display
 *
 * NOTE: Sidebar toggle is handled by navigation.js (attachSidebarToggleListener)
 * which manages desktop collapse and mobile open/close states with localStorage persistence
 */

class NavbarManager {
  constructor() {
    this.userToggle = document.getElementById('user-toggle');
    this.userDropdown = document.getElementById('user-dropdown');
    this.notifToggle = document.getElementById('notification-toggle');
    this.notifPanel = document.getElementById('notification-panel');
    this.dateTimeInterval = null;

    this.init();
  }

  init() {
    this.attachUserMenuListeners();
    this.attachNotificationListeners();
    this.attachGlobalEscListener();
    this.startDateTimeUpdater();
  }

  attachUserMenuListeners() {
    if (!this.userToggle || !this.userDropdown) return;

    this.userToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.toggleUserDropdown();
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!this.userToggle.contains(e.target) && !this.userDropdown.contains(e.target)) {
        this.closeUserDropdown();
      }
    });
  }

  attachNotificationListeners() {
    if (!this.notifToggle || !this.notifPanel) return;

    this.notifToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.toggleNotificationPanel();
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!this.notifToggle.contains(e.target) && !this.notifPanel.contains(e.target)) {
        this.closeNotificationPanel();
      }
    });
  }

  attachGlobalEscListener() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeAllDropdowns();
      }
    });
  }

  toggleUserDropdown() {
    const isOpen = this.userDropdown.classList.contains('show');

    if (isOpen) {
      this.closeUserDropdown();
    } else {
      this.closeNotificationPanel(); // Close other dropdowns
      this.openUserDropdown();
    }
  }

  openUserDropdown() {
    const expanded = this.userToggle.getAttribute('aria-expanded') === 'true';
    if (!expanded) {
      this.userToggle.setAttribute('aria-expanded', 'true');
      this.userDropdown.setAttribute('aria-hidden', 'false');
      this.userDropdown.classList.add('show');
    }
  }

  closeUserDropdown() {
    this.userToggle.setAttribute('aria-expanded', 'false');
    this.userDropdown.setAttribute('aria-hidden', 'true');
    this.userDropdown.classList.remove('show');
  }

  toggleNotificationPanel() {
    const isOpen = this.notifPanel.classList.contains('show');

    if (isOpen) {
      this.closeNotificationPanel();
    } else {
      this.closeUserDropdown(); // Close other dropdowns
      this.openNotificationPanel();
    }
  }

  openNotificationPanel() {
    const expanded = this.notifToggle.getAttribute('aria-expanded') === 'true';
    if (!expanded) {
      this.notifToggle.setAttribute('aria-expanded', 'true');
      this.notifPanel.setAttribute('aria-hidden', 'false');
      this.notifPanel.classList.add('show');
    }
  }

  closeNotificationPanel() {
    this.notifToggle.setAttribute('aria-expanded', 'false');
    this.notifPanel.setAttribute('aria-hidden', 'true');
    this.notifPanel.classList.remove('show');
  }

  closeAllDropdowns() {
    this.closeUserDropdown();
    this.closeNotificationPanel();
  }

  updateDateTime() {
    const now = new Date();
    const timeElement = document.getElementById('current-time');
    const dateElement = document.getElementById('current-date');

    if (timeElement) {
      const timeFormat = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });
      timeElement.textContent = timeFormat;
    }

    if (dateElement) {
      const dateFormat = now.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
      dateElement.textContent = dateFormat;
    }
  }

  startDateTimeUpdater() {
    // Clear any existing interval to prevent memory leaks
    if (this.dateTimeInterval) {
      clearInterval(this.dateTimeInterval);
    }

    // Update immediately on init
    this.updateDateTime();

    // Update every second
    this.dateTimeInterval = setInterval(() => this.updateDateTime(), 1000);
  }

  destroy() {
    // Clean up interval to prevent memory leaks
    if (this.dateTimeInterval) {
      clearInterval(this.dateTimeInterval);
      this.dateTimeInterval = null;
    }
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const navbarManager = new NavbarManager();

  // Expose to window for external access if needed
  window.navbarManager = navbarManager;
});
