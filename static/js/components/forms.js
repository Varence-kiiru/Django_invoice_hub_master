/**
 * Forms Component JS
 * Form handling, validation, and interactions
 */

const Forms = {
  /**
   * Get form data as object
   * @param {HTMLElement|string} form - Form element or ID
   * @returns {object} Form data as key-value pairs
   */
  getData: function(form) {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    const formData = new FormData(form);
    const data = {};

    for (let [key, value] of formData.entries()) {
      if (data.hasOwnProperty(key)) {
        // Handle multiple values with same key (checkboxes)
        if (Array.isArray(data[key])) {
          data[key].push(value);
        } else {
          data[key] = [data[key], value];
        }
      } else {
        data[key] = value;
      }
    }

    return data;
  },

  /**
   * Populate form with data
   * @param {HTMLElement|string} form - Form element or ID
   * @param {object} data - Data to populate
   */
  setData: function(form, data) {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    for (let key in data) {
      const field = form.elements[key];
      if (!field) continue;

      const value = data[key];

      switch (field.type) {
        case 'checkbox':
          field.checked = value === field.value || value === true;
          break;
        case 'radio':
          const radios = form.querySelectorAll(`input[name="${key}"]`);
          radios.forEach(r => r.checked = r.value === value);
          break;
        case 'select-multiple':
          Array.from(field.options).forEach(option => {
            option.selected = Array.isArray(value) && value.includes(option.value);
          });
          break;
        default:
          field.value = value;
      }
    }
  },

  /**
   * Clear form fields
   * @param {HTMLElement|string} form - Form element or ID
   * @param {string} exclude - Comma-separated field names to exclude
   */
  clear: function(form, exclude = '') {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    const excludeList = exclude.split(',').map(e => e.trim());

    Array.from(form.elements).forEach(field => {
      if (excludeList.includes(field.name)) return;

      switch (field.type) {
        case 'checkbox':
        case 'radio':
          field.checked = false;
          break;
        case 'select-multiple':
          Array.from(field.options).forEach(option => option.selected = false);
          break;
        case 'text':
        case 'email':
        case 'password':
        case 'textarea':
        case 'number':
        case 'date':
        case 'time':
        case 'datetime-local':
        case 'select-one':
          field.value = '';
          break;
      }

      // Clear error state
      field.classList.remove('is-invalid');
      const errorMsg = field.parentElement.querySelector('.invalid-feedback');
      if (errorMsg) errorMsg.textContent = '';
    });
  },

  /**
   * Validate form
   * @param {HTMLElement|string} form - Form element or ID
   * @param {object} rules - Validation rules
   * @returns {object} Validation errors
   */
  validate: function(form, rules = {}) {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    const errors = {};

    for (let fieldName in rules) {
      const field = form.elements[fieldName];
      if (!field) continue;

      const rule = rules[fieldName];
      const value = field.value.trim();

      // Check required
      if (rule.required && !value) {
        errors[fieldName] = rule.requiredMessage || 'This field is required';
        continue;
      }

      if (!value) continue; // Skip validation if not required and empty

      // Check min length
      if (rule.minLength && value.length < rule.minLength) {
        errors[fieldName] = rule.minLengthMessage || `Must be at least ${rule.minLength} characters`;
        continue;
      }

      // Check max length
      if (rule.maxLength && value.length > rule.maxLength) {
        errors[fieldName] = rule.maxLengthMessage || `Must be no more than ${rule.maxLength} characters`;
        continue;
      }

      // Check pattern/regex
      if (rule.pattern && !new RegExp(rule.pattern).test(value)) {
        errors[fieldName] = rule.patternMessage || 'Invalid format';
        continue;
      }

      // Check email
      if (rule.email && !this.isEmail(value)) {
        errors[fieldName] = 'Invalid email address';
        continue;
      }

      // Check custom validator
      if (rule.validator && typeof rule.validator === 'function') {
        const error = rule.validator(value);
        if (error) {
          errors[fieldName] = error;
        }
      }
    }

    // Update UI
    this.displayErrors(form, errors);

    return errors;
  },

  /**
   * Display validation errors
   * @param {HTMLElement|string} form - Form element or ID
   * @param {object} errors - Field errors
   */
  displayErrors: function(form, errors) {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    // Clear all errors first
    form.querySelectorAll('.is-invalid').forEach(field => {
      field.classList.remove('is-invalid');
    });
    form.querySelectorAll('.invalid-feedback').forEach(msg => {
      msg.textContent = '';
    });

    // Display new errors
    for (let fieldName in errors) {
      const field = form.elements[fieldName];
      if (!field) continue;

      field.classList.add('is-invalid');

      let errorMsg = field.parentElement.querySelector('.invalid-feedback');
      if (!errorMsg) {
        errorMsg = document.createElement('div');
        errorMsg.className = 'invalid-feedback';
        field.parentElement.appendChild(errorMsg);
      }
      errorMsg.textContent = errors[fieldName];
    }
  },

  /**
   * Check if email is valid
   * @param {string} email - Email address
   * @returns {boolean} True if valid
   */
  isEmail: function(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  },

  /**
   * Disable form
   * @param {HTMLElement|string} form - Form element or ID
   */
  disable: function(form) {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    Array.from(form.elements).forEach(field => {
      field.disabled = true;
    });
    form.classList.add('disabled');
  },

  /**
   * Enable form
   * @param {HTMLElement|string} form - Form element or ID
   */
  enable: function(form) {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    Array.from(form.elements).forEach(field => {
      field.disabled = false;
    });
    form.classList.remove('disabled');
  },

  /**
   * Add loading state to submit button
   * @param {HTMLElement|string} form - Form element or ID
   * @param {string} message - Loading message
   */
  setLoading: function(form, message = 'Loading...') {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    if (!submitBtn) return;

    submitBtn.disabled = true;
    submitBtn.setAttribute('data-original-text', submitBtn.textContent);
    submitBtn.textContent = message;
    submitBtn.classList.add('loading');
  },

  /**
   * Remove loading state from submit button
   * @param {HTMLElement|string} form - Form element or ID
   */
  clearLoading: function(form) {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    if (!submitBtn) return;

    submitBtn.disabled = false;
    const originalText = submitBtn.getAttribute('data-original-text') || 'Submit';
    submitBtn.textContent = originalText;
    submitBtn.classList.remove('loading');
  },

  /**
   * Handle form submission with validation
   * @param {HTMLElement|string} form - Form element or ID
   * @param {object} options - Options
   * @param {object} options.rules - Validation rules
   * @param {function} options.onSubmit - Submit handler
   * @param {string} options.onSuccess - Success action (url for redirect, callback)
   */
  handleSubmit: function(form, options = {}) {
    if (typeof form === 'string') {
      form = document.getElementById(form);
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Validate
      if (options.rules) {
        const errors = this.validate(form, options.rules);
        if (Object.keys(errors).length > 0) {
          return;
        }
      }

      // Custom submit handler
      if (options.onSubmit) {
        const result = await options.onSubmit(this.getData(form));
        
        if (options.onSuccess) {
          if (typeof options.onSuccess === 'string') {
            window.location.href = options.onSuccess;
          } else if (typeof options.onSuccess === 'function') {
            options.onSuccess(result);
          }
        }
      } else {
        // Default form submission
        form.submit();
      }
    });
  }
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Forms;
}
