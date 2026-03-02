/**
 * Theme Management System
 * Handles Light/Dark/Auto theme switching with persistence
 */

class ThemeManager {
  constructor() {
    this.STORAGE_KEY = 'invoicing-theme-preference';
    this.LIGHT = 'light';
    this.DARK = 'dark';
    this.AUTO = 'auto';
    
    // Initialize theme on page load
    this.init();
  }

  /**
   * Initialize theme from saved preference or system preference
   */
  init() {
    const savedTheme = this.getSavedTheme();
    const preferredTheme = savedTheme || this.getSystemPreference();
    
    this.setTheme(preferredTheme);
    this.updateThemeSelector(preferredTheme);
    this.listenForSystemChanges();
  }

  /**
   * Get the saved theme preference from localStorage
   */
  getSavedTheme() {
    return localStorage.getItem(this.STORAGE_KEY);
  }

  /**
   * Get system preference using prefers-color-scheme
   */
  getSystemPreference() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return this.DARK;
    }
    return this.LIGHT;
  }

  /**
   * Set the theme by updating the data-theme attribute
   */
  setTheme(theme) {
    const html = document.documentElement;
    
    if (theme === this.AUTO) {
      // Remove data-theme to let CSS use system preference
      html.removeAttribute('data-theme');
    } else {
      // Set explicit theme
      html.setAttribute('data-theme', theme);
    }
    
    // Save preference
    localStorage.setItem(this.STORAGE_KEY, theme);
    
    // Update display
    this.updateThemeDisplay(theme);
  }

  /**
   * Update the theme selector dropdown to show current choice
   */
  updateThemeSelector(theme) {
    const selector = document.getElementById('theme');
    if (selector) {
      selector.value = theme || this.AUTO;
    }
  }

  /**
   * Update visual indicators of current theme
   */
  updateThemeDisplay(theme) {
    const indicator = document.getElementById('theme-indicator');
    if (indicator) {
      const themeLabels = {
        'light': '☀️ Light',
        'dark': '🌙 Dark',
        'auto': '🔄 Auto'
      };
      indicator.textContent = themeLabels[theme] || themeLabels[this.AUTO];
    }
  }

  /**
   * Listen for changes in system color scheme preference
   */
  listenForSystemChanges() {
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        const savedTheme = this.getSavedTheme();
        
        // Only apply system change if user has auto selected
        if (!savedTheme || savedTheme === this.AUTO) {
          const newTheme = e.matches ? this.DARK : this.LIGHT;
          this.setTheme(newTheme);
          this.updateThemeSelector(newTheme);
        }
      });
    }
  }

  /**
   * Attach event listener to theme selector in settings
   */
  attachSelectorListener() {
    const selector = document.getElementById('theme');
    if (selector) {
      selector.addEventListener('change', (e) => {
        this.setTheme(e.target.value);
      });
    }
  }

  /**
   * Get current active theme
   */
  getCurrentTheme() {
    const html = document.documentElement;
    return html.getAttribute('data-theme') || this.AUTO;
  }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.themeManager = new ThemeManager();
  // Don't attach selector listener globally - let individual pages handle it
});

// Also initialize before DOM loads to prevent flash
if (document.readyState === 'loading') {
  const savedTheme = localStorage.getItem('invoicing-theme-preference') || 'light';
  if (savedTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
} else {
  window.themeManager = new ThemeManager();
  // Don't attach selector listener globally
}
