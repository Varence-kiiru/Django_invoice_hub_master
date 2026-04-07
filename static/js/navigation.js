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
    attachSidebarToggleListener();
    attachOverlayListener();
    attachSidebarLinkListener();
    attachWindowResizeListener();
    // NOTE: attachSidebarToggleLinkListeners() removed - sidebar.js SidebarManager handles this properly
    attachSmartSubmenuPositioning();
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

  // ==================== SIDEBAR COLLAPSE & TOGGLE ====================

  /**
   * Restores sidebar state from localStorage
   */
  function restoreSidebarState() {
    if (state.isSidebarCollapsed) {
      applySidebarCollapsed();
    }
  }

  /**
   * Toggles sidebar collapse state on desktop/tablet
   * On mobile, handles open/close with overlay
   */
  function toggleSidebarCollapse() {
    const sidebar = document.querySelector(CONFIG.sidebarSelector);
    const overlay = document.querySelector('.sidebar-overlay');
    const isMobile = window.innerWidth < 768;

    if (isMobile) {
      // Mobile: toggle slide-in sidebar
      if (sidebar) {
        sidebar.classList.toggle('open');
      }
      if (overlay) {
        overlay.classList.toggle('active');
      }
    } else {
      // Desktop/Tablet: toggle collapsed state
      state.isSidebarCollapsed = !state.isSidebarCollapsed;
      localStorage.setItem('sidebar-collapsed', state.isSidebarCollapsed);

      if (state.isSidebarCollapsed) {
        applySidebarCollapsed();
      } else {
        removeSidebarCollapsed();
      }
    }
  }

  /**
   * Applies collapsed state to sidebar (desktop/tablet only)
   */
  function applySidebarCollapsed() {
    document.body.classList.add('sidebar-collapsed');
  }

  /**
   * Removes collapsed state from sidebar
   */
  function removeSidebarCollapsed() {
    document.body.classList.remove('sidebar-collapsed');
  }

  /**
   * Closes sidebar (mobile only)
   */
  function closeSidebar() {
    const sidebar = document.querySelector(CONFIG.sidebarSelector);
    const overlay = document.querySelector('.sidebar-overlay');
    if (sidebar) {
      sidebar.classList.remove('open');
    }
    if (overlay) {
      overlay.classList.remove('active');
    }
  }

  /**
   * Attaches sidebar toggle button listener
   */
  function attachSidebarToggleListener() {
    const toggleBtn = document.getElementById(CONFIG.sidebarToggleButtonId);
    if (toggleBtn) {
      toggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleSidebarCollapse();
      });
    }
  }

  /**
   * Attaches overlay click listener to close sidebar (mobile only)
   */
  function attachOverlayListener() {
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          closeSidebar();
        }
      });
    }
  }

  // ==================== SIDEBAR TOGGLE SECTIONS (COLLAPSIBLE) ====================

  /**
   * REMOVED: This function was causing conflicts with sidebar.js SidebarManager
   * The sidebar.js properly handles submenu expansion with:
   * - Section-aware accordion behavior (only one menu per section opens)
   * - Support for both collapsed ('pinned') and expanded ('open') modes
   * - Proper aria-expanded attribute management
   *
   * This function was closing ALL submenus globally, breaking the accordion behavior.
   */
  // function attachSidebarToggleLinkListeners() {
  //   // REMOVED - Use sidebar.js instead
  // }

  // ==================== SMART SUBMENU POSITIONING ====================

  /**
   * Adjusts floating submenu position to prevent going off-screen
   * Useful for mini sidebar floating submenus
   */
  function attachSmartSubmenuPositioning() {
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
      item.addEventListener('mouseenter', () => {
        if (!document.body.classList.contains('sidebar-collapsed')) return;

        const submenu = item.querySelector('.sidebar-submenu');
        if (!submenu) return;

        const rect = submenu.getBoundingClientRect();

        // Position submenu: if it goes off bottom, align to bottom of item
        if (rect.bottom > window.innerHeight - 20) {
          submenu.style.top = 'auto';
          submenu.style.bottom = '0';
        } else {
          submenu.style.top = '0';
          submenu.style.bottom = 'auto';
        }

        // Right-side check (if needed for RTL or edge cases)
        if (rect.right > window.innerWidth - 20) {
          submenu.style.left = 'auto';
          submenu.style.right = '100%';
        } else {
          submenu.style.left = 'var(--sidebar-width, 70px)';
          submenu.style.right = 'auto';
        }
      });
    });
  }

  /**
   * Closes sidebar when a link is clicked (mobile only)
   */
  function attachSidebarLinkListener() {
    const sidebarLinks = document.querySelectorAll('.sidebar-nav-link, .sidebar-submenu-link');
    sidebarLinks.forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth < 768) {
          closeSidebar();
        }
      });
    });
  }

  /**
   * Public method to toggle sidebar
   */
  window.toggleSidebar = function() {
    toggleSidebarCollapse();
  };

  /**
   * Handle window resize - close sidebar overlay on mobile->desktop transition
   */
  function attachWindowResizeListener() {
    window.addEventListener('resize', () => {
      if (window.innerWidth >= 768) {
        // Desktop - close overlay if open
        const overlay = document.querySelector('.sidebar-overlay');
        if (overlay && overlay.classList.contains('active')) {
          overlay.classList.remove('active');
        }
        const sidebar = document.querySelector(CONFIG.sidebarSelector);
        if (sidebar && sidebar.classList.contains('open')) {
          sidebar.classList.remove('open');
        }
      }
    });
  }

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
