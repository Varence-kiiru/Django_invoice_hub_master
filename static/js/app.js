/**
 * InvoiceHub - Main Application Module
 * Bootstrap and initialization for the entire application
 */

class Application {
  constructor() {
    this.initialized = false;
  }

  /**
   * Initialize the application
   */
  init() {
    if (this.initialized) return;

    console.log('🚀 Initializing InvoiceHub Application');

    this.setupEventListeners();
    this.setupGlobalHandlers();
    this.initializeModules();

    this.initialized = true;
    console.log('✅ InvoiceHub initialized successfully');
  }

  /**
   * Setup global event listeners
   */
  setupEventListeners() {
    // User menu dropdown
    const userMenuToggle = document.getElementById('user-menu-toggle');
    const userDropdownMenu = document.getElementById('user-dropdown-menu');

    if (userMenuToggle && userDropdownMenu) {
      userMenuToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdownMenu.classList.toggle('active');
      });

      // Close dropdown when clicking outside
      document.addEventListener('click', (e) => {
        if (
          !userMenuToggle.contains(e.target) &&
          !userDropdownMenu.contains(e.target)
        ) {
          userDropdownMenu.classList.remove('active');
        }
      });
    }

    // Global search
    const globalSearch = document.getElementById('global-search');
    if (globalSearch) {
      globalSearch.addEventListener('input', (e) => {
        this.handleGlobalSearch(e.target.value);
      });
    }

    // CSRF token setup for AJAX
    this.setupAjaxCSRFToken();
  }

  /**
   * Setup global error and notification handlers
   */
  setupGlobalHandlers() {
    // Handle AJAX errors
    document.addEventListener('ajaxError', (e) => {
      this.handleAjaxError(e.detail);
    });

    // Handle form submissions
    document.addEventListener('submit', (e) => {
      const form = e.target;
      if (form.classList.contains('ajax-form')) {
        e.preventDefault();
        this.handleFormSubmit(form);
      }
    });

    // Dismiss alerts on close button click
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('alert-close')) {
        const alert = e.target.closest('.alert');
        if (alert) {
          alert.remove();
        }
      }
    });
  }

  /**
   * Initialize application modules
   */
  initializeModules() {
    // Note: Modules should self-register via DOMContentLoaded
    // This ensures they're initialized in the correct order
    console.log('📦 Application modules initialized');
  }

  /**
   * Setup CSRF token for AJAX requests
   */
  setupAjaxCSRFToken() {
    // Get CSRF token from cookie
    const csrftoken = this.getCookie('csrftoken');

    if (csrftoken) {
      // Set default header for all fetch requests
      const originalFetch = window.fetch;
      window.fetch = function (...args) {
        if (!args[1]) args[1] = {};
        if (!args[1].headers) args[1].headers = {};
        args[1].headers['X-CSRFToken'] = csrftoken;
        return originalFetch.apply(this, args);
      };
    }
  }

  /**
   * Get cookie value by name
   */
  getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + '=') {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  /**
   * Handle global search
   */
  handleGlobalSearch(query) {
    if (!query || query.length < 2) {
      return;
    }

    // TODO: Implement search functionality
    // This could trigger an API call to search across invoices, clients, products, etc.
    console.log('🔍 Searching for:', query);
  }

  /**
   * Handle form submission
   */
  handleFormSubmit(form) {
    // TODO: Implement AJAX form submission
    console.log('📝 Submitting form:', form);
  }

  /**
   * Handle AJAX errors
   */
  handleAjaxError(error) {
    console.error('❌ AJAX Error:', error);

    if (error.status === 401) {
      // Redirect to login
      window.location.href = '/auth/login/';
    } else if (error.status === 403) {
      this.showNotification('You do not have permission to perform this action.', 'error');
    } else if (error.status === 404) {
      this.showNotification('The requested resource was not found.', 'error');
    } else {
      this.showNotification('An error occurred. Please try again.', 'error');
    }
  }

  /**
   * Show a notification message
   */
  showNotification(message, type = 'info') {
    if (window.notificationManager) {
      window.notificationManager.show(message, type);
    }
  }

  /**
   * Get CSRF token
   */
  getCSRFToken() {
    return this.getCookie('csrftoken');
  }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const app = new Application();
  app.init();

  // Expose to window for debugging
  window.app = app;
});

// Handle page visibility
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    console.log('👋 Page hidden');
  } else {
    console.log('👁️ Page visible');
  }
});

// Log page performance metrics
window.addEventListener('load', () => {
  const perfData = window.performance.timing;
  const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
  console.log(`⏱️ Page load time: ${pageLoadTime}ms`);
});
