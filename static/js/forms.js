/**
 * Form utilities - Form handling and validation
 * Works with custom modal system (no Bootstrap dependency)
 */

/**
 * Extract form data as key-value object
 */
function getData(formSelector) {
  const form = typeof formSelector === 'string' 
    ? document.querySelector(formSelector) 
    : formSelector;
  
  if (!form) return null;
  
  const formData = new FormData(form);
  const data = {};
  
  for (const [key, value] of formData.entries()) {
    if (data[key]) {
      // Handle multiple values (checkboxes, multi-select)
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
}

/**
 * Populate form with data object
 */
function setData(formSelector, data) {
  const form = typeof formSelector === 'string' 
    ? document.querySelector(formSelector) 
    : formSelector;
  
  if (!form) return;
  
  Object.entries(data).forEach(([key, value]) => {
    const field = form.elements[key];
    
    if (field) {
      if (field.type === 'checkbox') {
        field.checked = value === true || value === 'on' || value === '1';
      } else if (field.type === 'radio') {
        const radioButton = form.querySelector(`input[name="${key}"][value="${value}"]`);
        if (radioButton) radioButton.checked = true;
      } else if (field.tagName === 'SELECT') {
        field.value = value;
      } else {
        field.value = value;
      }
    }
  });
}

/**
 * Clear all form fields
 */
function clear(formSelector) {
  const form = typeof formSelector === 'string' 
    ? document.querySelector(formSelector) 
    : formSelector;
  
  if (!form) return;
  
  form.reset();
  // Clear validation errors
  form.querySelectorAll('.error-feedback').forEach(el => {
    el.textContent = '';
    el.style.display = 'none';
  });
  form.querySelectorAll('.is-invalid').forEach(el => {
    el.classList.remove('is-invalid');
  });
}

/**
 * Validate form with optional custom validation rules
 * Returns object: { isValid: bool, errors: { fieldName: [messages] } }
 */
function validate(formSelector, rules = {}) {
  const form = typeof formSelector === 'string' 
    ? document.querySelector(formSelector) 
    : formSelector;
  
  if (!form) return { isValid: false, errors: {} };
  
  const errors = {};
  
  // Built-in HTML5 validation
  form.querySelectorAll('[required], [pattern], [type="email"], [type="number"]').forEach(field => {
    if (!field.checkValidity()) {
      const fieldName = field.name || field.id;
      const message = field.validationMessage || `${field.name || field.id} is invalid`;
      
      if (!errors[fieldName]) {
        errors[fieldName] = [];
      }
      errors[fieldName].push(message);
    }
  });
  
  // Custom validation rules
  Object.entries(rules).forEach(([fieldName, rule]) => {
    const field = form.elements[fieldName];
    
    if (field && !rule(field.value, field)) {
      if (!errors[fieldName]) {
        errors[fieldName] = [];
      }
      errors[fieldName].push(`${fieldName} validation failed`);
    }
  });
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

/**
 * Display validation errors in form
 */
function displayErrors(formSelector, errors) {
  const form = typeof formSelector === 'string' 
    ? document.querySelector(formSelector) 
    : formSelector;
  
  if (!form) return;
  
  // Clear previous errors
  form.querySelectorAll('.error-feedback').forEach(el => {
    el.textContent = '';
    el.style.display = 'none';
  });
  form.querySelectorAll('.is-invalid').forEach(el => {
    el.classList.remove('is-invalid');
  });
  
  // Display new errors
  Object.entries(errors).forEach(([fieldName, messages]) => {
    const field = form.elements[fieldName];
    
    if (field) {
      // Mark field as invalid
      field.classList.add('is-invalid');
      
      // Show error message
      let errorEl = field.parentElement?.querySelector('.error-feedback');
      if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.className = 'error-feedback';
        field.parentElement?.appendChild(errorEl);
      }
      
      errorEl.textContent = messages[0];
      errorEl.style.display = 'block';
    }
  });
}

/**
 * Disable all form fields
 */
function disable(formSelector) {
  const form = typeof formSelector === 'string' 
    ? document.querySelector(formSelector) 
    : formSelector;
  
  if (!form) return;
  
  form.querySelectorAll('input, select, textarea, button').forEach(field => {
    field.disabled = true;
  });
}

/**
 * Enable all form fields
 */
function enable(formSelector) {
  const form = typeof formSelector === 'string' 
    ? document.querySelector(formSelector) 
    : formSelector;
  
  if (!form) return;
  
  form.querySelectorAll('input, select, textarea, button').forEach(field => {
    field.disabled = false;
  });
}

/**
 * Show loading state on form/button
 */
function setLoading(element, isLoading = true) {
  const target = typeof element === 'string' 
    ? document.querySelector(element) 
    : element;
  
  if (!target) return;
  
  if (isLoading) {
    target.classList.add('is-loading');
    target.setAttribute('disabled', 'disabled');
    
    // Save original content if it's a button
    if (target.tagName === 'BUTTON' && !target.dataset.originalContent) {
      target.dataset.originalContent = target.innerHTML;
      target.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...`;
    }
  } else {
    target.classList.remove('is-loading');
    target.removeAttribute('disabled');
    
    // Restore original content if it's a button
    if (target.tagName === 'BUTTON' && target.dataset.originalContent) {
      target.innerHTML = target.dataset.originalContent;
      delete target.dataset.originalContent;
    }
  }
}

/**
 * Handle form submission with validation and optional modal confirmation
 */
async function handleSubmit(formSelector, options = {}) {
  const form = typeof formSelector === 'string' 
    ? document.querySelector(formSelector) 
    : formSelector;
  
  if (!form) return;
  
  const {
    onValidate = null,
    onConfirm = null,
    confirmMessage = null,
    onSubmit = null,
    onError = null,
    submitButton = null,
    validationRules = {}
  } = options;
  
  // Prevent default submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get submit button
    const btn = submitButton 
      ? (typeof submitButton === 'string' ? form.querySelector(submitButton) : submitButton)
      : form.querySelector('button[type="submit"]');
    
    // Validate form
    const validation = validate(form, validationRules);
    
    if (!validation.isValid) {
      displayErrors(form, validation.errors);
      if (onValidate) {
        onValidate(validation);
      }
      return;
    }
    
    // Show confirmation if needed
    if (confirmMessage) {
      const confirmed = await confirm('Confirm Action', confirmMessage);
      if (!confirmed) return;
      
      if (onConfirm) {
        onConfirm();
      }
    }
    
    // Set loading state
    if (btn) {
      setLoading(btn, true);
    }
    
    try {
      // Get form data
      const data = getData(form);
      
      // Call custom submit handler
      if (onSubmit) {
        await onSubmit(data, form);
      } else {
        // Default: Submit form normally
        form.submit();
      }
    } catch (error) {
      if (onError) {
        onError(error);
      } else {
        console.error('Form submission error:', error);
      }
    } finally {
      if (btn) {
        setLoading(btn, false);
      }
    }
  });
}

/**
 * Async form submission handler
 * Submits form via AJAX and returns response
 */
async function submitAsync(formSelector, url = null) {
  const form = typeof formSelector === 'string' 
    ? document.querySelector(formSelector) 
    : formSelector;
  
  if (!form) return null;
  
  const data = new FormData(form);
  const submitUrl = url || form.action || window.location.href;
  const method = (form.method || 'POST').toUpperCase();
  
  try {
    const response = await fetch(submitUrl, {
      method,
      body: data,
      headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
      }
    });
    
    return {
      ok: response.ok,
      status: response.status,
      data: await response.json().catch(() => null),
      text: await response.text()
    };
  } catch (error) {
    console.error('Form submission failed:', error);
    throw error;
  }
}
