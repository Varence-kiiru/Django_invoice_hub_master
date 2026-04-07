/**
 * Sidebar Navigation Module
 * Handles sidebar interactions, toggle, submenu expansion
 */

class SidebarManager {
  constructor() {
    this.sidebar = document.getElementById('sidebar');
    this.sidebarToggle = document.getElementById('sidebar-toggle');
    this.toggleLinks = document.querySelectorAll('.sidebar-toggle-link');
    this.isMobile = window.innerWidth <= 768;
    this.init();
  }

  init() {
    if (!this.sidebar) return;

    // Mobile sidebar toggle
    this.sidebarToggle?.addEventListener('click', () => this.toggleSidebar());

    // Submenu toggles
    this.toggleLinks.forEach(link => {
      link.addEventListener('click', (e) => this.handleToggleClick(e, link));
    });

    // Close sidebar on link click (mobile)
    const navLinks = this.sidebar.querySelectorAll('a[href]');
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 1024) {
          this.closeSidebar();
        }
      });
    });

    // Close sidebar when clicking outside (mobile)
    document.addEventListener('click', (e) => {
      if (
        window.innerWidth <= 1024 &&
        !this.sidebar.contains(e.target) &&
        !this.sidebarToggle?.contains(e.target) &&
        this.sidebar.classList.contains('active')
      ) {
        this.closeSidebar();
      }
    });

    // Handle window resize
    window.addEventListener('resize', () => {
      if (window.innerWidth > 1024) {
        this.closeSidebar();
      }
    });
  }

  toggleSidebar() {
    this.sidebar.classList.toggle('active');
  }

  closeSidebar() {
    this.sidebar.classList.remove('active');
  }

  openSidebar() {
    this.sidebar.classList.add('active');
  }

  handleToggleClick(e, link) {
    e.preventDefault();

    const menuId = link.getAttribute('data-toggle');
    const menu = document.getElementById(menuId);
    const toggleIcon = link.querySelector('.sidebar-toggle-icon');

    if (!menu) return;

    const isCollapsed = document.body.classList.contains('sidebar-collapsed');

    // ✅ In collapsed mode → pin/unpin submenu (stays visible after click)
    if (isCollapsed) {
      const isPinned = menu.classList.toggle('pinned');
      toggleIcon?.classList.toggle('open', isPinned);
      link.setAttribute('aria-expanded', isPinned.toString());
      return; // Don't close other menus in collapsed mode
    }

    // ✅ Normal (expanded mode) behavior - accordion style
    const isOpen = menu.classList.toggle('open');
    toggleIcon?.classList.toggle('open');
    link.setAttribute('aria-expanded', isOpen.toString());

    // Close others in same section (accordion)
    const section = link.closest('.sidebar-section');
    if (section) {
      const otherMenus = section.querySelectorAll('.sidebar-submenu');
      otherMenus.forEach(otherMenu => {
        if (otherMenu !== menu && otherMenu.classList.contains('open')) {
          otherMenu.classList.remove('open');

          const otherToggleLink = otherMenu.closest('.sidebar-nav-item')?.querySelector('.sidebar-toggle-link');
          otherToggleLink?.setAttribute('aria-expanded', 'false');

          const otherIcon = otherToggleLink?.querySelector('.sidebar-toggle-icon');
          otherIcon?.classList.remove('open');
        }
      });
    }
  }

  // Highlight active menu based on current URL
  setActiveMenu() {
    const currentPath = window.location.pathname;
    const isCollapsed = document.body.classList.contains('sidebar-collapsed');
    const links = this.sidebar.querySelectorAll('a[href]');

    links.forEach(link => {
      const href = link.getAttribute('href');
      if (href && currentPath.includes(href)) {
        link.classList.add('active');

        // Expand parent submenu if applicable
        const submenu = link.closest('.sidebar-submenu');
        if (submenu) {
          // In collapsed mode, use 'pinned' class; in expanded mode, use 'open'
          if (isCollapsed) {
            submenu.classList.add('pinned');
          } else {
            submenu.classList.add('open');
          }

          const toggleLink = submenu.closest('.sidebar-nav-item')?.querySelector('.sidebar-toggle-link');
          toggleLink?.setAttribute('aria-expanded', 'true');
          const toggleIcon = toggleLink?.querySelector('.sidebar-toggle-icon');
          toggleIcon?.classList.add('open');
        }
      }
    });
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const sidebarManager = new SidebarManager();
  sidebarManager.setActiveMenu();

  // Expose to window for external access if needed
  window.sidebarManager = sidebarManager;
});
