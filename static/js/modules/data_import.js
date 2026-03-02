/**
 * Data Importer Module
 * Handles CSV/Excel file import with preview, validation, and progress tracking
 * 
 * Usage:
 *   const importer = new DataImporter('#dataImportModal');
 *   importer.show();
 */

class DataImporter {
  constructor(modalSelector = '#dataImportModal') {
    this.modal = document.querySelector(modalSelector);
    this.entities = ['invoice', 'payment', 'client', 'quotation'];
    this.currentFile = null;
    this.fileData = null;
    this.importResults = null;
    
    // Cache DOM elements
    this.elements = {
      entityType: document.getElementById('entityType'),
      csvFile: document.getElementById('csvFile'),
      fileLabel: document.querySelector('.custom-file-label'),
      previewBtn: document.getElementById('previewBtn'),
      backBtn: document.getElementById('backBtn'),
      confirmImportBtn: document.getElementById('confirmImportBtn'),
      importAgainBtn: document.getElementById('importAgainBtn'),
      downloadTemplate: document.getElementById('downloadTemplate'),
      
      // Steps
      stepFileSelection: document.getElementById('step-file-selection'),
      stepPreview: document.getElementById('step-preview'),
      stepProgress: document.getElementById('step-progress'),
      stepResults: document.getElementById('step-results'),
      
      // Preview elements
      previewTable: document.getElementById('previewTable'),
      previewWarning: document.getElementById('previewWarning'),
      previewMessage: document.getElementById('previewMessage'),
      totalRows: document.getElementById('totalRows'),
      validRows: document.getElementById('validRows'),
      errorRows: document.getElementById('errorRows'),
      
      // Progress elements
      importProgress: document.getElementById('importProgress'),
      progressText: document.getElementById('progressText'),
      progressStatus: document.getElementById('progressStatus'),
      
      // Result elements
      resultAlert: document.getElementById('resultAlert'),
      resultCreated: document.getElementById('resultCreated'),
      resultUpdated: document.getElementById('resultUpdated'),
      resultSkipped: document.getElementById('resultSkipped'),
      resultFailed: document.getElementById('resultFailed'),
      errorDetails: document.getElementById('errorDetails'),
      errorTable: document.getElementById('errorTable'),
      errorTableBody: document.getElementById('errorTableBody'),
      toggleErrors: document.getElementById('toggleErrors'),
    };
    
    this.init();
  }

  /**
   * Initialize event listeners
   */
  init() {
    // File input change
    this.elements.csvFile.addEventListener('change', (e) => this.handleFileSelect(e));
    
    // Preview button
    this.elements.previewBtn.addEventListener('click', () => this.showPreview());
    
    // Back button
    this.elements.backBtn.addEventListener('click', () => this.backToFileSelection());
    
    // Confirm import button
    this.elements.confirmImportBtn.addEventListener('click', () => this.startImport());
    
    // Import again button
    this.elements.importAgainBtn.addEventListener('click', () => this.reset());
    
    // Download template
    this.elements.downloadTemplate.addEventListener('click', (e) => {
      e.preventDefault();
      this.downloadTemplate();
    });
    
    // Toggle errors
    if (this.elements.toggleErrors) {
      this.elements.toggleErrors.addEventListener('click', () => this.toggleErrorDisplay());
    }
  }

  /**
   * Show modal
   */
  show() {
    $(this.modal).modal('show');
  }

  /**
   * Hide modal
   */
  hide() {
    $(this.modal).modal('hide');
  }

  /**
   * Handle file selection
   */
  handleFileSelect(event) {
    const file = event.target.files[0];
    
    if (!file) {
      this.elements.fileLabel.textContent = 'Choose file...';
      return;
    }

    // Validate file
    const validExtensions = ['csv', 'xlsx', 'xls'];
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(fileExt)) {
      this.showError('Invalid file type. Please upload CSV or Excel file.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10 MB
      this.showError('File is too large. Maximum size is 10 MB.');
      return;
    }

    this.currentFile = file;
    this.elements.fileLabel.textContent = file.name;
    this.elements.previewBtn.disabled = false;
  }

  /**
   * Parse CSV file
   */
  async parseCSV(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const csv = e.target.result;
          const lines = csv.trim().split('\n');
          const headers = lines[0].split(',').map(h => h.trim());
          
          const data = lines.slice(1).map(line => {
            const values = line.split(',').map(v => v.trim());
            const row = {};
            headers.forEach((header, index) => {
              row[header] = values[index] || '';
            });
            return row;
          });
          
          resolve({ headers, data });
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(reader.error);
      reader.readAsText(file);
    });
  }

  /**
   * Parse Excel file
   */
  async parseExcel(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = async (e) => {
        try {
          // Using a simple approach - in production use a library like xlsx
          // For now, show message that Excel parsing requires additional setup
          if (!window.XLSX) {
            this.showError('Excel parsing requires XLSX library. Please convert to CSV or contact support.');
            reject(new Error('XLSX library not loaded'));
            return;
          }
          
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          const sheet = workbook.Sheets[workbook.SheetNames[0]];
          const rows = XLSX.utils.sheet_to_json(sheet);
          
          const headers = rows.length > 0 ? Object.keys(rows[0]) : [];
          resolve({ headers, data: rows });
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(reader.error);
      reader.readAsArrayBuffer(file);
    });
  }

  /**
   * Show preview step
   */
  async showPreview() {
    const entityType = this.elements.entityType.value;
    
    if (!entityType) {
      this.showError('Please select an entity type');
      return;
    }

    if (!this.currentFile) {
      this.showError('Please select a file');
      return;
    }

    try {
      this.showStep('preview');
      this.elements.progressStatus.textContent = 'Parsing file...';
      
      // Parse file based on extension
      const fileExt = this.currentFile.name.split('.').pop().toLowerCase();
      
      if (fileExt === 'csv') {
        this.fileData = await this.parseCSV(this.currentFile);
      } else if (['xlsx', 'xls'].includes(fileExt)) {
        this.fileData = await this.parseExcel(this.currentFile);
      }

      // Get import template to validate fields
      await this.getImportTemplate(entityType);
      
      // Validate data
      const validation = this.validateData(entityType);
      
      // Display preview
      this.displayPreview(validation);
      
    } catch (error) {
      console.error('Preview error:', error);
      this.showError(`Error parsing file: ${error.message}`);
      this.showStep('file-selection');
    }
  }

  /**
   * Get import template from API
   */
  async getImportTemplate(entityType) {
    try {
      const response = await fetch(`/api/import/template/?entity_type=${entityType}`, {
        credentials: 'include'
      });
      
      if (!response.ok) throw new Error('Failed to fetch template');
      
      const data = await response.json();
      this.template = data.data;
      return this.template;
    } catch (error) {
      console.error('Template fetch error:', error);
      this.showError('Failed to load import template. Please try again.');
      throw error;
    }
  }

  /**
   * Validate imported data
   */
  validateData(entityType) {
    const validation = {
      total: this.fileData.data.length,
      valid: 0,
      errors: [],
      rows: []
    };

    const requiredFields = this.template?.required_fields || [];
    
    this.fileData.data.forEach((row, index) => {
      const rowErrors = [];
      
      // Check required fields
      requiredFields.forEach(field => {
        if (!row[field] || row[field].trim() === '') {
          rowErrors.push(`Missing required field: ${field}`);
        }
      });

      if (rowErrors.length === 0) {
        validation.valid++;
      } else {
        validation.errors.push({
          row: index + 2, // +2 because of header row and 0-indexing
          errors: rowErrors
        });
      }

      validation.rows.push({ ...row, errors: rowErrors });
    });

    return validation;
  }

  /**
   * Display preview in table
   */
  displayPreview(validation) {
    // Update stats
    this.elements.totalRows.textContent = validation.total;
    this.elements.validRows.textContent = validation.valid;
    this.elements.errorRows.textContent = validation.errors.length;

    // Build preview table
    const headers = this.fileData.headers.slice(0, 5);
    let html = '<table class="table table-sm table-bordered"><thead><tr>';
    
    headers.forEach(header => {
      html += `<th>${this.escapeHtml(header)}</th>`;
    });
    html += '</tr></thead><tbody>';

    // Show first 5 rows
    this.fileData.data.slice(0, 5).forEach((row, index) => {
      html += '<tr>';
      headers.forEach(header => {
        const value = row[header] || '';
        const hasError = validation.rows[index]?.errors?.length > 0;
        html += `<td class="${hasError ? 'bg-danger bg-opacity-10' : ''}">${this.escapeHtml(value)}</td>`;
      });
      html += '</tr>';
    });

    html += '</tbody></table>';
    
    if (this.fileData.data.length > 5) {
      html += `<small class="text-muted">Showing 5 of ${this.fileData.data.length} rows</small>`;
    }

    this.elements.previewTable.innerHTML = html;

    // Show warning/info message
    if (validation.errors.length > 0) {
      this.elements.previewWarning.className = 'alert alert-warning';
      this.elements.previewMessage.textContent = 
        `${validation.errors.length} row(s) have validation errors and will be skipped.`;
      this.elements.confirmImportBtn.disabled = validation.valid === 0;
    } else {
      this.elements.previewWarning.className = 'alert alert-success';
      this.elements.previewMessage.innerHTML = 
        `<i class="fas fa-check-circle"></i> All data looks good! Ready to import.`;
      this.elements.confirmImportBtn.disabled = false;
    }
  }

  /**
   * Start import process
   */
  async startImport() {
    const entityType = this.elements.entityType.value;
    const duplicateHandling = document.querySelector('input[name="duplicateHandling"]:checked').value;

    try {
      this.showStep('progress');
      
      // Prepare FormData
      const formData = new FormData();
      formData.append('csv_file', this.currentFile);
      formData.append('entity_type', entityType);
      formData.append('skip_duplicates', duplicateHandling === 'skip');
      formData.append('update_existing', duplicateHandling === 'update');

      // Get CSRF token
      const csrfToken = this.getCSRFToken();
      
      // Make import request
      const response = await fetch('/api/import/data/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
        },
        body: formData,
        credentials: 'include'
      });

      // Simulate progress
      this.simulateProgress(30);

      const data = await response.json();
      
      this.simulateProgress(100);
      
      // Show results
      await new Promise(resolve => setTimeout(resolve, 500));
      this.displayResults(data);
      this.showStep('results');

    } catch (error) {
      console.error('Import error:', error);
      this.showError(`Import failed: ${error.message}`);
      this.showStep('preview');
    }
  }

  /**
   * Simulate progress bar animation
   */
  simulateProgress(targetPercent) {
    return new Promise(resolve => {
      const interval = setInterval(() => {
        const current = parseInt(this.elements.importProgress.style.width) || 0;
        
        if (current >= targetPercent) {
          clearInterval(interval);
          this.updateProgress(targetPercent);
          resolve();
        } else {
          const increment = Math.random() * (targetPercent - current) * 0.3;
          this.updateProgress(current + increment);
        }
      }, 200);
    });
  }

  /**
   * Update progress bar
   */
  updateProgress(percent) {
    const rounded = Math.min(Math.round(percent), 100);
    this.elements.importProgress.style.width = rounded + '%';
    this.elements.importProgress.setAttribute('aria-valuenow', rounded);
    this.elements.progressText.textContent = rounded + '%';
  }

  /**
   * Display import results
   */
  displayResults(apiResponse) {
    const results = apiResponse.data;
    
    // Update result counts
    this.elements.resultCreated.textContent = results.created_count || 0;
    this.elements.resultUpdated.textContent = results.updated_count || 0;
    this.elements.resultSkipped.textContent = results.skipped_count || 0;
    this.elements.resultFailed.textContent = results.rows_failed || 0;

    // Show result alert
    if (apiResponse.success) {
      this.elements.resultAlert.className = 'alert alert-success';
      this.elements.resultAlert.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <strong>Import completed successfully!</strong>
        ${results.rows_failed > 0 ? '<br>Some rows had errors and were skipped.' : ''}
      `;
    } else {
      this.elements.resultAlert.className = 'alert alert-danger';
      this.elements.resultAlert.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        <strong>Import completed with errors</strong><br>
        ${apiResponse.message || 'Please review the errors below.'}
      `;
    }

    // Display error details if any
    if (results.errors && results.errors.length > 0) {
      this.displayErrorDetails(results.errors);
    } else {
      this.elements.errorDetails.style.display = 'none';
    }

    this.importResults = results;
  }

  /**
   * Display error details table
   */
  displayErrorDetails(errors) {
    this.elements.errorDetails.style.display = 'block';
    
    const html = errors.slice(0, 10).map(error => `
      <tr>
        <td class="font-weight-bold">Row ${error.row}</td>
        <td>
          <ul class="mb-0 pl-3">
            ${error.errors.map(e => `<li>${this.escapeHtml(e)}</li>`).join('')}
          </ul>
        </td>
      </tr>
    `).join('');

    this.elements.errorTableBody.innerHTML = html;

    if (errors.length > 10) {
      this.elements.toggleErrors.textContent = `Show ${errors.length - 10} more errors`;
      this.elements.toggleErrors.style.display = 'block';
    } else {
      this.elements.toggleErrors.style.display = 'none';
    }
  }

  /**
   * Toggle error display
   */
  toggleErrorDisplay() {
    const table = this.elements.errorTableBody;
    const isHidden = table.offsetParent === null;
    table.style.display = isHidden ? 'table-body' : 'none';
  }

  /**
   * Download CSV template
   */
  downloadTemplate() {
    const entityType = this.elements.entityType.value;
    
    if (!entityType) {
      this.showError('Please select an entity type first');
      return;
    }

    const templates = {
      invoice: {
        headers: ['invoice_number', 'client_name', 'invoice_date', 'total_amount', 'currency', 'status'],
        example: ['INV-2024-001', 'Acme Corp', '2024-01-15', '1500.00', 'USD', 'sent']
      },
      payment: {
        headers: ['payment_number', 'invoice_number', 'amount', 'payment_date', 'payment_method'],
        example: ['PAY-2024-001', 'INV-2024-001', '1500.00', '2024-01-20', 'bank_transfer']
      },
      client: {
        headers: ['name', 'email', 'phone', 'company', 'address', 'city'],
        example: ['Acme Corp', 'contact@acme.com', '+1-555-0100', 'Acme Corporation', '123 Main St', 'New York']
      },
      quotation: {
        headers: ['quotation_number', 'client_name', 'quote_date', 'total_amount', 'currency', 'valid_until', 'status'],
        example: ['QT-2024-001', 'Acme Corp', '2024-01-15', '2500.00', 'USD', '2024-02-15', 'draft']
      }
    };

    const template = templates[entityType];
    if (!template) return;

    // Create CSV content
    const csv = [
      template.headers.join(','),
      template.example.join(',')
    ].join('\n');

    // Download file
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${entityType}_import_template.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  /**
   * Reset to initial state
   */
  reset() {
    this.currentFile = null;
    this.fileData = null;
    this.importResults = null;
    this.elements.csvFile.value = '';
    this.elements.entityType.value = '';
    this.elements.fileLabel.textContent = 'Choose file...';
    this.showStep('file-selection');
  }

  /**
   * Go back to file selection
   */
  backToFileSelection() {
    this.showStep('file-selection');
  }

  /**
   * Show specific step
   */
  showStep(step) {
    // Hide all steps
    this.elements.stepFileSelection.style.display = 'none';
    this.elements.stepPreview.style.display = 'none';
    this.elements.stepProgress.style.display = 'none';
    this.elements.stepResults.style.display = 'none';

    // Show selected step
    switch (step) {
      case 'file-selection':
        this.elements.stepFileSelection.style.display = 'block';
        break;
      case 'preview':
        this.elements.stepPreview.style.display = 'block';
        break;
      case 'progress':
        this.elements.stepProgress.style.display = 'block';
        this.updateProgress(0);
        this.elements.progressStatus.textContent = 'Starting import...';
        break;
      case 'results':
        this.elements.stepResults.style.display = 'block';
        break;
    }
  }

  /**
   * Show error message
   */
  showError(message) {
    // Alert.js integration or simple alert
    if (typeof showNotification === 'function') {
      showNotification('error', message);
    } else {
      alert('Error: ' + message);
    }
  }

  /**
   * Get CSRF token from cookie or form
   */
  getCSRFToken() {
    // Try to get from cookie
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    
    // Try to get from form
    if (!cookieValue) {
      const tokens = document.querySelectorAll('[name=csrfmiddlewaretoken]');
      if (tokens.length > 0) {
        cookieValue = tokens[0].value;
      }
    }
    
    return cookieValue;
  }

  /**
   * Escape HTML characters
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize on document ready
document.addEventListener('DOMContentLoaded', function() {
  // Make global reference available
  window.dataImporter = new DataImporter('#dataImportModal');
  
  // Add button to show modal (if button exists)
  const importBtn = document.getElementById('showDataImportBtn');
  if (importBtn) {
    importBtn.addEventListener('click', () => {
      window.dataImporter.show();
    });
  }
});
