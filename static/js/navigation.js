/**
 * Layout Navigation - Sidebar and Dropdown Menu Interactions
 * Handles active states, toggle behaviors, and responsive interactions
 * No external dependencies - vanilla JavaScript only
 */

(function() {
  'use strict';

  // ==================== CONFIGURATION ====================
  const CONFIG = {
    activeClass: 'active',
    sidebarToggleButtonId: 'sidebar-toggle',
    navLinkSelector: '.nav-link',
    dropdownSelector: '.dropdown',
    dropdownToggleSelector: '.dropdown-toggle',
    dropdownMenuSelector: '.dropdown-menu',
    sidebarSelector: '#sidebar',
    mainSelector: 'main',
    navListSelector: '.nav-list',
  };

  // ==================== STATE ====================
  const state = {
    currentUrl: window.location.pathname,
    isSidebarCollapsed: localStorage.getItem('sidebar-collapsed') === 'true',
  };

  // ==================== INITIALIZATION ====================
  function init() {
    setActiveNavLink();
    attachDropdownListeners();
    attachNavLinkListeners();
    attachOutsideClickListener();
    restoreSidebarState();
  }

  // ==================== ACTIVE NAVIGATION LINK ====================

  /**
   * Sets the active navigation link based on current URL
   * Handles exact and partial path matching
   */
  function setActiveNavLink() {
    const navLinks = document.querySelectorAll(CONFIG.navLinkSelector);

    navLinks.forEach(link => {
      const href = link.getAttribute('href');

      // Exact match or starts with match
      if (href && (state.currentUrl === href || state.currentUrl.startsWith(href + '/'))) {
        // Remove active class from all links
        navLinks.forEach(l => l.classList.remove(CONFIG.activeClass));
        // Add active class to current link
        link.classList.add(CONFIG.activeClass);
      }
    });
  }

  // ==================== DROPDOWN MENU HANDLING ====================

  /**
   * Attaches click listeners to dropdown toggles
   */
  function attachDropdownListeners() {
    const dropdowns = document.querySelectorAll(CONFIG.dropdownSelector);

    dropdowns.forEach(dropdown => {
      const toggle = dropdown.querySelector(CONFIG.dropdownToggleSelector);

      if (toggle) {
        toggle.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          toggleDropdown(dropdown);
        });
      }
    });
  }

  /**
   * Toggles a dropdown menu open/closed
   * @param {HTMLElement} dropdown - The dropdown container element
   */
  function toggleDropdown(dropdown) {
    const isActive = dropdown.classList.contains(CONFIG.activeClass);

    // Close all dropdowns
    closeAllDropdowns();

    // Open the clicked dropdown if it wasn't open
    if (!isActive) {
      dropdown.classList.add(CONFIG.activeClass);
    }
  }

  /**
   * Closes all open dropdown menus
   */
  function closeAllDropdowns() {
    const dropdowns = document.querySelectorAll(CONFIG.dropdownSelector);
    dropdowns.forEach(dropdown => {
      dropdown.classList.remove(CONFIG.activeClass);
    });
  }

  /**
   * Attaches listener to close dropdowns when clicking outside
   */
  function attachOutsideClickListener() {
    document.addEventListener('click', (e) => {
      const isDropdown = e.target.closest(CONFIG.dropdownSelector);
      if (!isDropdown) {
        closeAllDropdowns();
      }
    });

    // Close dropdowns on ESC key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeAllDropdowns();
      }
    });
  }

  // ==================== NAVIGATION LINK HANDLING ====================

  /**
   * Attaches click listeners to navigation links
   */
  function attachNavLinkListeners() {
    const navLinks = document.querySelectorAll(CONFIG.navLinkSelector);

    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        // Allow normal link navigation but update active state
        handleNavLinkClick(link, e);
      });
    });
  }

  /**
   * Handles navigation link click
   * @param {HTMLElement} link - The clicked link element
   * @param {Event} e - The click event
   */
  function handleNavLinkClick(link, e) {
    // Update active state immediately for better UX
    const navLinks = document.querySelectorAll(CONFIG.navLinkSelector);
    navLinks.forEach(l => l.classList.remove(CONFIG.activeClass));
    link.classList.add(CONFIG.activeClass);

    // Close any open dropdowns
    closeAllDropdowns();
  }

  // ==================== SIDEBAR COLLAPSE (Future Enhancement) ====================

  /**
   * Restores sidebar state from localStorage
   */
  function restoreSidebarState() {
    if (state.isSidebarCollapsed) {
      applySidebarCollapsed();
    }
  }

  /**
   * Toggles sidebar collapse state
   */
  function toggleSidebarCollapse() {
    state.isSidebarCollapsed = !state.isSidebarCollapsed;
    localStorage.setItem('sidebar-collapsed', state.isSidebarCollapsed);

    if (state.isSidebarCollapsed) {
      applySidebarCollapsed();
    } else {
      removeSidebarCollapsed();
    }
  }

  /**
   * Applies collapsed state styling to sidebar
   */
  function applySidebarCollapsed() {
    const sidebar = document.querySelector(CONFIG.sidebarSelector);
    if (sidebar) {
      sidebar.setAttribute('data-collapsed', 'true');
    }
  }

  /**
   * Removes collapsed state from sidebar
   */
  function removeSidebarCollapsed() {
    const sidebar = document.querySelector(CONFIG.sidebarSelector);
    if (sidebar) {
      sidebar.removeAttribute('data-collapsed');
    }
  }

  /**
   * Public method to toggle sidebar (for future button use)
   */
  window.toggleSidebar = function() {
    toggleSidebarCollapse();
  };

  // ==================== UTILITY FUNCTIONS ====================

  /**
   * Closes all dropdowns and resets active states
   */
  window.resetNavigation = function() {
    closeAllDropdowns();
    setActiveNavLink();
  };

  /**
   * Gets the current active navigation link
   * @returns {HTMLElement|null} The active navigation link
   */
  window.getActiveNavLink = function() {
    return document.querySelector(CONFIG.navLinkSelector + '.' + CONFIG.activeClass);
  };

  // ==================== DOM READY ====================

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Also initialize on page visibility change (useful for SPAs)
  document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
      setActiveNavLink();
    }
  });

})();
