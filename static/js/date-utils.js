/**
 * Date/Time utilities - No external dependencies
 */

/**
 * Format date to string with pattern
 * Patterns: YYYY, MM, DD, HH, mm, SS
 * Example: formatDate(new Date(), 'YYYY-MM-DD') => "2024-01-15"
 */
function formatDate(date, pattern = 'YYYY-MM-DD') {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  
  if (!(date instanceof Date) || isNaN(date.getTime())) {
    return '';
  }
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  return pattern
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('SS', seconds);
}

/**
 * Format date and time together
 * Example: formatDateTime(new Date()) => "Jan 15, 2024 2:30 PM"
 */
function formatDateTime(date, timeFormat = '12h') {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  
  if (!(date instanceof Date) || isNaN(date.getTime())) {
    return '';
  }
  
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthStr = months[date.getMonth()];
  const dateStr = date.getDate();
  const yearStr = date.getFullYear();
  
  let timeStr = '';
  
  if (timeFormat === '12h') {
    const hours = date.getHours() % 12 || 12;
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const ampm = date.getHours() >= 12 ? 'PM' : 'AM';
    timeStr = `${hours}:${minutes} ${ampm}`;
  } else {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    timeStr = `${hours}:${minutes}`;
  }
  
  return `${monthStr} ${dateStr}, ${yearStr} ${timeStr}`;
}

/**
 * Calculate days between two dates
 */
function daysBetween(date1, date2) {
  const d1 = new Date(date1).getTime();
  const d2 = new Date(date2).getTime();
  
  if (isNaN(d1) || isNaN(d2)) return 0;
  
  const msPerDay = 24 * 60 * 60 * 1000;
  return Math.floor(Math.abs(d2 - d1) / msPerDay);
}

/**
 * Check if invoice/bill is overdue
 */
function isOverdue(dueDate, referenceDate = null) {
  const due = new Date(dueDate).getTime();
  const ref = referenceDate ? new Date(referenceDate).getTime() : Date.now();
  
  if (isNaN(due) || isNaN(ref)) return false;
  
  return ref > due;
}

/**
 * Calculate days overdue
 */
function daysOverdue(dueDate, referenceDate = null) {
  const due = new Date(dueDate);
  const ref = referenceDate ? new Date(referenceDate) : new Date();
  
  if (isNaN(due.getTime()) || isNaN(ref.getTime())) return 0;
  
  const days = daysBetween(due, ref);
  return isOverdue(due, ref) ? days : 0;
}

/**
 * Format time in relative format
 * Example: relativeTime(new Date(Date.now() - 3600000)) => "1 hour ago"
 */
function relativeTime(date, now = new Date()) {
  const timestamp = new Date(date).getTime();
  const nowTime = new Date(now).getTime();
  
  if (isNaN(timestamp)) return '';
  
  const seconds = Math.floor((nowTime - timestamp) / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const weeks = Math.floor(days / 7);
  const months = Math.floor(days / 30);
  const years = Math.floor(days / 365);
  
  if (seconds < 60) return 'just now';
  if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`;
  if (weeks < 4) return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
  if (months < 12) return `${months} month${months > 1 ? 's' : ''} ago`;
  return `${years} year${years > 1 ? 's' : ''} ago`;
}

/**
 * Add days to a date
 */
function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

/**
 * Subtract days from a date
 */
function subtractDays(date, days) {
  return addDays(date, -days);
}

/**
 * Get start of day (00:00:00)
 */
function startOfDay(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

/**
 * Get end of day (23:59:59)
 */
function endOfDay(date) {
  const d = new Date(date);
  d.setHours(23, 59, 59, 999);
  return d;
}

/**
 * Get start of month
 */
function startOfMonth(date) {
  const d = new Date(date);
  d.setDate(1);
  d.setHours(0, 0, 0, 0);
  return d;
}

/**
 * Get end of month
 */
function endOfMonth(date) {
  const d = new Date(date);
  d.setMonth(d.getMonth() + 1);
  d.setDate(0);
  d.setHours(23, 59, 59, 999);
  return d;
}

/**
 * Get start of year
 */
function startOfYear(date) {
  const d = new Date(date);
  d.setMonth(0);
  d.setDate(1);
  d.setHours(0, 0, 0, 0);
  return d;
}

/**
 * Get end of year
 */
function endOfYear(date) {
  const d = new Date(date);
  d.setMonth(11);
  d.setDate(31);
  d.setHours(23, 59, 59, 999);
  return d;
}

/**
 * Check if date is today
 */
function isToday(date) {
  const today = new Date();
  const checkDate = new Date(date);
  
  return checkDate.getFullYear() === today.getFullYear() &&
         checkDate.getMonth() === today.getMonth() &&
         checkDate.getDate() === today.getDate();
}

/**
 * Check if date is this week
 */
function isThisWeek(date) {
  const today = new Date();
  const checkDate = new Date(date);
  
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - today.getDay());
  
  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);
  
  return checkDate >= startOfWeek && checkDate <= endOfWeek;
}

/**
 * Check if date is this month
 */
function isThisMonth(date) {
  const today = new Date();
  const checkDate = new Date(date);
  
  return checkDate.getFullYear() === today.getFullYear() &&
         checkDate.getMonth() === today.getMonth();
}

/**
 * Check if date is this year
 */
function isThisYear(date) {
  const today = new Date();
  const checkDate = new Date(date);
  
  return checkDate.getFullYear() === today.getFullYear();
}

/**
 * Calculate age in years from birth date
 */
function getAge(birthDate) {
  const today = new Date();
  const birth = new Date(birthDate);
  
  if (isNaN(birth.getTime())) return null;
  
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  
  return age;
}

/**
 * Get day name from date
 */
function getDayName(date, format = 'short') {
  const d = new Date(date);
  const days = format === 'short' 
    ? ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    : ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  
  return days[d.getDay()];
}

/**
 * Get month name from date
 */
function getMonthName(date, format = 'short') {
  const d = new Date(date);
  const months = format === 'short'
    ? ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    : ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  
  return months[d.getMonth()];
}

/**
 * Check if year is leap year
 */
function isLeapYear(year) {
  return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
}

/**
 * Get number of days in month
 */
function getDaysInMonth(date) {
  const d = new Date(date);
  return new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
}
