/**
 * Date Utilities
 * Date manipulation, formatting, and calculation functions
 * Note: Requires moment.js for full functionality
 */

const DateUtils = {
  /**
   * Format date using custom format string or locale
   * @param {Date|string} date - Date to format
   * @param {string} format - Format string or style
   * @returns {string} Formatted date
   */
  format: function(date, format = 'MMM DD, YYYY') {
    if (!date) return '';
    
    // If moment is available, use it
    if (typeof moment !== 'undefined') {
      return moment(date).format(format);
    }
    
    // Fallback to standard Date formatting
    const d = new Date(date);
    const options = {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    };
    return d.toLocaleDateString('en-US', options);
  },

  /**
   * Format date and time
   * @param {Date|string} date - Date to format
   * @returns {string} Formatted date time
   */
  formatDateTime: function(date) {
    if (!date) return '';
    
    if (typeof moment !== 'undefined') {
      return moment(date).format('MMM DD, YYYY [at] h:mm A');
    }
    
    const d = new Date(date);
    const options = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      meridiem: 'short'
    };
    return d.toLocaleDateString('en-US', options) + ' ' + d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', meridiem: 'short' });
  },

  /**
   * Calculate days between two dates
   * @param {Date|string} date1 - First date
   * @param {Date|string} date2 - Second date
   * @returns {number} Number of days between dates
   */
  daysBetween: function(date1, date2) {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    const diffTime = Math.abs(d2 - d1);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  },

  /**
   * Check if date is overdue
   * @param {Date|string} dueDate - Due date
   * @returns {boolean} True if overdue
   */
  isOverdue: function(dueDate) {
    return new Date(dueDate) < new Date();
  },

  /**
   * Get days overdue
   * @param {Date|string} dueDate - Due date
   * @returns {number} Number of days overdue (0 if not overdue)
   */
  daysOverdue: function(dueDate) {
    const today = new Date();
    const due = new Date(dueDate);
    
    if (due >= today) return 0;
    
    const diffTime = today - due;
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
  },

  /**
   * Get relative time string (e.g., "2 days ago")
   * @param {Date|string} date - Date to calculate from
   * @returns {string} Relative time string
   */
  relativeTime: function(date) {
    if (typeof moment !== 'undefined') {
      return moment(date).fromNow();
    }
    
    const now = new Date();
    const then = new Date(date);
    const secondsAgo = Math.floor((now - then) / 1000);
    
    if (secondsAgo < 60) return 'just now';
    if (secondsAgo < 3600) return Math.floor(secondsAgo / 60) + ' minutes ago';
    if (secondsAgo < 86400) return Math.floor(secondsAgo / 3600) + ' hours ago';
    
    const daysAgo = Math.floor(secondsAgo / 86400);
    if (daysAgo === 1) return 'yesterday';
    if (daysAgo < 7) return daysAgo + ' days ago';
    if (daysAgo < 30) return Math.floor(daysAgo / 7) + ' weeks ago';
    if (daysAgo < 365) return Math.floor(daysAgo / 30) + ' months ago';
    
    return Math.floor(daysAgo / 365) + ' years ago';
  },

  /**
   * Add days to a date
   * @param {Date|string} date - Base date
   * @param {number} days - Number of days to add
   * @returns {Date} New date
   */
  addDays: function(date, days) {
    if (typeof moment !== 'undefined') {
      return moment(date).add(days, 'days').toDate();
    }
    
    const d = new Date(date);
    d.setDate(d.getDate() + days);
    return d;
  },

  /**
   * Get start of period (week, month, quarter, year)
   * @param {Date|string} date - Reference date
   * @param {string} period - 'week', 'month', 'quarter', 'year'
   * @returns {Date} Start date of period
   */
  startOf: function(date, period = 'month') {
    if (typeof moment !== 'undefined') {
      return moment(date).startOf(period).toDate();
    }
    
    const d = new Date(date);
    switch (period.toLowerCase()) {
      case 'week':
        d.setDate(d.getDate() - d.getDay());
        break;
      case 'month':
        d.setDate(1);
        break;
      case 'quarter':
        d.setMonth(Math.floor(d.getMonth() / 3) * 3);
        d.setDate(1);
        break;
      case 'year':
        d.setMonth(0);
        d.setDate(1);
        break;
    }
    d.setHours(0, 0, 0, 0);
    return d;
  },

  /**
   * Get end of period (week, month, quarter, year)
   * @param {Date|string} date - Reference date
   * @param {string} period - 'week', 'month', 'quarter', 'year'
   * @returns {Date} End date of period
   */
  endOf: function(date, period = 'month') {
    if (typeof moment !== 'undefined') {
      return moment(date).endOf(period).toDate();
    }
    
    const d = new Date(date);
    switch (period.toLowerCase()) {
      case 'week':
        d.setDate(d.getDate() - d.getDay() + 6);
        break;
      case 'month':
        d.setMonth(d.getMonth() + 1);
        d.setDate(0);
        break;
      case 'quarter':
        d.setMonth(Math.floor(d.getMonth() / 3) * 3 + 2);
        d.setDate(new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate());
        break;
      case 'year':
        d.setMonth(11);
        d.setDate(31);
        break;
    }
    d.setHours(23, 59, 59, 999);
    return d;
  },

  /**
   * Check if date is today
   * @param {Date|string} date - Date to check
   * @returns {boolean} True if date is today
   */
  isToday: function(date) {
    const today = new Date();
    const d = new Date(date);
    return d.getDate() === today.getDate() &&
           d.getMonth() === today.getMonth() &&
           d.getFullYear() === today.getFullYear();
  },

  /**
   * Check if date is this week
   * @param {Date|string} date - Date to check
   * @returns {boolean} True if date is this week
   */
  isThisWeek: function(date) {
    const d = new Date(date);
    const today = new Date();
    const start = new Date(today);
    start.setDate(today.getDate() - today.getDay());
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    
    return d >= start && d <= end;
  },

  /**
   * Format date for SQL/database
   * @param {Date|string} date - Date to format
   * @returns {string} ISO date string (YYYY-MM-DD)
   */
  toSQL: function(date) {
    const d = new Date(date);
    return d.toISOString().split('T')[0];
  },

  /**
   * Format date for input type="date"
   * @param {Date|string} date - Date to format
   * @returns {string} ISO date string (YYYY-MM-DD)
   */
  toInputValue: function(date) {
    return this.toSQL(date);
  },

  /**
   * Get month name
   * @param {number} month - Month number (0-11) or Date object
   * @returns {string} Month name
   */
  monthName: function(month) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December'];
    if (month instanceof Date) {
      month = month.getMonth();
    }
    return months[month] || '';
  },

  /**
   * Get day name
   * @param {number} day - Day number (0-6) or Date object
   * @returns {string} Day name
   */
  dayName: function(day) {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    if (day instanceof Date) {
      day = day.getDay();
    }
    return days[day] || '';
  },

  /**
   * Get age in years
   * @param {Date|string} birthDate - Birth date
   * @returns {number} Age in years
   */
  getAge: function(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const month = today.getMonth() - birth.getMonth();
    
    if (month < 0 || (month === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    
    return age;
  }
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DateUtils;
}
