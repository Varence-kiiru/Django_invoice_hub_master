/**
 * Formatting Utilities
 * Number, currency, date, and text formatting functions
 */

const Formatting = {
  /**
   * Format a number as currency
   * @param {number} amount - The amount to format
   * @param {string} currency - Currency code (default: USD)
   * @param {number} decimals - Number of decimal places (default: 2)
   * @returns {string} Formatted currency string
   */
  currency: function(amount, currency = 'USD', decimals = 2) {
    if (isNaN(amount)) return '$0.00';

    const multiplier = Math.pow(10, decimals);
    const rounded = Math.round(amount * multiplier) / multiplier;

    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });

    return formatter.format(rounded);
  },

  /**
   * Format a number with thousands separator
   * @param {number} num - The number to format
   * @param {number} decimals - Number of decimal places
   * @returns {string} Formatted number
   */
  number: function(num, decimals = 0) {
    if (isNaN(num)) return '0';

    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  },

  /**
   * Format a number as a percentage
   * @param {number} value - The value to format (0-100 or 0-1)
   * @param {number} decimals - Number of decimal places
   * @returns {string} Formatted percentage
   */
  percentage: function(value, decimals = 1) {
    if (isNaN(value)) return '0%';

    // If value is between 0-1, multiply by 100
    if (Math.abs(value) <= 1 && value !== 0) {
      value = value * 100;
    }

    return this.number(value, decimals) + '%';
  },

  /**
   * Format bytes as human-readable size
   * @param {number} bytes - Number of bytes
   * @param {number} decimals - Number of decimal places
   * @returns {string} Formatted size
   */
  fileSize: function(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return this.number(bytes / Math.pow(k, i), decimals) + ' ' + sizes[i];
  },

  /**
   * Truncate text to a maximum length
   * @param {string} text - Text to truncate
   * @param {number} maxLength - Maximum length
   * @param {string} suffix - Suffix to append (default: '...')
   * @returns {string} Truncated text
   */
  truncate: function(text, maxLength, suffix = '...') {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - suffix.length) + suffix;
  },

  /**
   * Format a number with commas and optional decimals
   * @param {number} num - Number to format
   * @param {number} digits - Number of decimal places
   * @returns {string} Formatted number
   */
  toFixed: function(num, digits = 2) {
    if (isNaN(num)) return '0.00';
    return parseFloat(num).toFixed(digits);
  },

  /**
   * Convert text to title case
   * @param {string} text - Text to convert
   * @returns {string} Title cased text
   */
  titleCase: function(text) {
    if (!text) return '';
    return text.replace(/\w\S*/g, (txt) => {
      return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
  },

  /**
   * Convert text to slug format
   * @param {string} text - Text to convert
   * @returns {string} Slugified text
   */
  slug: function(text) {
    if (!text) return '';
    return text
      .toString()
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '-')
      .replace(/[^\w\-]+/g, '')
      .replace(/\-\-+/g, '-')
      .replace(/^-+|-+$/g, '');
  },

  /**
   * Capitalize first letter of string
   * @param {string} text - Text to capitalize
   * @returns {string} Capitalized text
   */
  capitalize: function(text) {
    if (!text) return '';
    return text.charAt(0).toUpperCase() + text.slice(1);
  },

  /**
   * Format phone number
   * @param {string} phone - Phone number
   * @returns {string} Formatted phone number
   */
  phone: function(phone) {
    if (!phone) return '';
    const digits = phone.replace(/\D/g, '');
    if (digits.length === 10) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    }
    return phone;
  },

  /**
   * Format email - hide most of it
   * @param {string} email - Email address
   * @returns {string} Partially masked email
   */
  maskEmail: function(email) {
    if (!email) return '';
    const [user, domain] = email.split('@');
    const maskedUser = user.charAt(0) + '*'.repeat(user.length - 2) + user.charAt(user.length - 1);
    return maskedUser + '@' + domain;
  },

  /**
   * Format credit card number
   * @param {string} cardNumber - Card number
   * @returns {string} Formatted card number
   */
  creditCard: function(cardNumber) {
    if (!cardNumber) return '';
    return cardNumber.replace(/\s+/g, '').replace(/(\d{4})/g, '$1 ').trim();
  }
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Formatting;
}
