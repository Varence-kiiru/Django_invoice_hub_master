/**
 * Text/Number formatting utilities
 */

/**
 * Format number as currency
 * Example: currency(1234.5) => "$1,234.50"
 */
function currency(value, symbol = '$', decimals = 2) {
  if (typeof value !== 'number') {
    value = parseFloat(value) || 0;
  }
  
  return symbol + number(value.toFixed(decimals));
}

/**
 * Format number with thousands separator
 * Example: number(1234567) => "1,234,567"
 */
function number(value, separator = ',') {
  if (typeof value !== 'number') {
    value = parseFloat(value) || 0;
  }
  
  return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, separator);
}

/**
 * Format decimal as percentage
 * Example: percentage(0.856) => "85.6%"
 */
function percentage(value, decimals = 1) {
  if (typeof value !== 'number') {
    value = parseFloat(value) || 0;
  }
  
  const percent = (value * 100).toFixed(decimals);
  return percent + '%';
}

/**
 * Convert bytes to human-readable file size
 * Example: fileSize(1234567) => "1.18 MB"
 */
function fileSize(bytes) {
  if (typeof bytes !== 'number' || bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Truncate string with ellipsis
 * Example: truncate('Hello World', 8) => "Hello..."
 */
function truncate(str, maxLength = 50, suffix = '...') {
  if (typeof str !== 'string') return '';
  
  if (str.length <= maxLength) return str;
  
  return str.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * Convert string to title case
 * Example: titleCase('hello world') => "Hello World"
 */
function titleCase(str) {
  if (typeof str !== 'string') return '';
  
  return str
    .toLowerCase()
    .split(/[\s_-]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Capitalize first letter of string
 * Example: capitalize('hello') => "Hello"
 */
function capitalize(str) {
  if (typeof str !== 'string') return '';
  
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Convert string to URL slug
 * Example: slug('Hello World') => "hello-world"
 */
function slug(str) {
  if (typeof str !== 'string') return '';
  
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special characters
    .replace(/[\s_]+/g, '-')    // Replace spaces/underscores with hyphen
    .replace(/-+/g, '-');       // Remove duplicate hyphens
}

/**
 * Format phone number
 * Example: phone('1234567890') => "(123) 456-7890"
 */
function phone(str) {
  if (typeof str !== 'string') return '';
  
  const cleaned = str.replace(/\D/g, '');
  
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  } else if (cleaned.length === 11) {
    return `+${cleaned[0]} (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  }
  
  return str;
}

/**
 * Mask email address for privacy
 * Example: maskEmail('john@example.com') => "jo**@example.com"
 */
function maskEmail(email) {
  if (typeof email !== 'string') return '';
  
  const [name, domain] = email.split('@');
  
  if (!name || !domain) return email;
  
  const visibleChars = Math.max(1, Math.floor(name.length / 2));
  const masked = name.substring(0, visibleChars) + '*'.repeat(Math.max(2, name.length - visibleChars));
  
  return masked + '@' + domain;
}

/**
 * Format credit card number
 * Example: creditCard('4532123456789010') => "4532 1234 5678 9010"
 */
function creditCard(str) {
  if (typeof str !== 'string') return '';
  
  const cleaned = str.replace(/\D/g, '');
  
  return cleaned
    .padEnd(16, '0')
    .substring(0, 16)
    .replace(/(.{4})/g, '$1 ')
    .trim();
}

/**
 * Format date object to readable string
 * Example: formatDate(new Date()) => "Jan 15, 2024"
 */
function formatDate(date, format = 'MMM DD, YYYY') {
  if (!(date instanceof Date)) {
    date = new Date(date);
  }
  
  if (isNaN(date.getTime())) {
    return '';
  }
  
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const year = date.getFullYear();
  const month = months[date.getMonth()];
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  return format
    .replace('YYYY', year)
    .replace('MMM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('MM', minutes)
    .replace('SS', seconds);
}

/**
 * Highlight text in string with HTML markup
 * Example: highlight('Hello World', 'World') => "Hello <mark>World</mark>"
 */
function highlight(str, searchStr, className = 'highlight') {
  if (typeof str !== 'string') return '';
  if (!searchStr) return str;
  
  const regex = new RegExp(`(${searchStr})`, 'gi');
  return str.replace(regex, `<mark class="${className}">$1</mark>`);
}

/**
 * Sanitize HTML string to prevent XSS
 * Removes script tags and dangerous attributes
 */
function sanitizeHTML(str) {
  if (typeof str !== 'string') return '';
  
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Format JSON for display
 */
function formatJSON(obj, indent = 2) {
  try {
    return JSON.stringify(obj, null, indent);
  } catch (error) {
    console.error('JSON formatting error:', error);
    return String(obj);
  }
}
