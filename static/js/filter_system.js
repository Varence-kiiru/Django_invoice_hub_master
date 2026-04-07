/**
 * Advanced Filter System JavaScript
 * Handles filter interactions, date pickers, and saved filters
 */

// Toggle advanced filter panel
function toggleAdvancedFilter(filterId) {
    const filterPanel = document.getElementById(filterId);
    const filterToggle = event.target.closest('.filter-toggle');

    if (filterPanel) {
        if (filterPanel.style.display === 'none') {
            filterPanel.style.display = 'block';
            filterToggle.classList.add('open');
        } else {
            filterPanel.style.display = 'none';
            filterToggle.classList.remove('open');
        }
    }
}

// Open save filter modal
function openSaveFilterModal(filterType) {
    const modal = document.getElementById('saveFilterModal');
    const filterTypeInput = document.getElementById('filterType');

    if (modal) {
        filterTypeInput.value = filterType;
        modal.style.display = 'flex';
        modal.classList.add('show');

        // Focus on filter name input
        setTimeout(() => {
            document.getElementById('filterName').focus();
        }, 100);
    }
}

// Close save filter modal
function closeSaveFilterModal() {
    const modal = document.getElementById('saveFilterModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        // Reset form
        document.getElementById('saveFilterForm').reset();
    }
}

// Open saved filters management modal
function openSavedFiltersModal() {
    const modal = document.getElementById('savedFiltersModal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('show');
        loadSavedFiltersList();
    }
}

// Close saved filters modal
function closeSavedFiltersModal() {
    const modal = document.getElementById('savedFiltersModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
}

// Load saved filter and apply it
function loadSavedFilter(filterId) {
    if (!filterId) return;

    // Fetch the saved filter and navigate to URL with params
    fetch(`/api/filters/${filterId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.filter_criteria) {
                // Build URL with filter parameters
                const params = new URLSearchParams();
                Object.keys(data.filter_criteria).forEach(key => {
                    const value = data.filter_criteria[key];
                    if (value !== null && value !== '' && value !== undefined) {
                        params.append(key, value);
                    }
                });

                // Redirect to list page with filters applied
                window.location.href = `${window.location.pathname}?${params.toString()}`;
            }
        })
        .catch(error => console.error('Error loading filter:', error));
}

// Delete a saved filter
function deleteSavedFilter(filterId) {
    if (confirm('Are you sure you want to delete this saved filter?')) {
        fetch(`/api/filters/${filterId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => {
            if (response.ok) {
                loadSavedFiltersList(); // Reload filter list
                showNotification('Filter deleted successfully', 'success');
            } else {
                showNotification('Error deleting filter', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error deleting filter', 'error');
        });
    }
}

// Edit a saved filter
function editSavedFilter(filterId) {
    // Open edit modal with filter data
    fetch(`/api/filters/${filterId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('filterName').value = data.name;
            document.getElementById('filterDescription').value = data.description || '';
            document.getElementById('filterGlobal').checked = data.is_global;
            document.getElementById('filterType').value = data.filter_type;

            // Change modal action to update
            const form = document.getElementById('saveFilterForm');
            form.action = `/api/filters/${filterId}/`;
            form.dataset.method = 'PATCH';

            openSaveFilterModal(data.filter_type);
        })
        .catch(error => console.error('Error loading filter:', error));
}

// Load and display saved filters list
function loadSavedFiltersList() {
    const container = document.getElementById('savedFiltersList');

    fetch('/api/filters/')
        .then(response => response.json())
        .then(data => {
            if (data.filters && data.filters.length > 0) {
                let html = '';
                data.filters.forEach(filter => {
                    html += `
                        <div class="saved-filter-item">
                            <div class="saved-filter-name">${escapeHtml(filter.name)}</div>
                            ${filter.description ? `<div class="saved-filter-description">${escapeHtml(filter.description)}</div>` : ''}
                            <div class="saved-filter-meta">
                                <span>📁 ${capitalizeFirst(filter.filter_type)}</span>
                                <span>👤 ${escapeHtml(filter.created_by)}</span>
                                <span>📅 ${new Date(filter.last_used).toLocaleDateString() || 'Never'}</span>
                                <span>✨ Used ${filter.use_count} times</span>
                                ${filter.is_global ? '<span class="global-badge">Global</span>' : ''}
                            </div>
                            <div class="saved-filter-actions">
                                <button onclick="loadSavedFilter('${filter.id}')" type="button">Use Filter</button>
                                <button onclick="editSavedFilter('${filter.id}')" type="button">Edit</button>
                                <button onclick="deleteSavedFilter('${filter.id}')" class="btn-delete" type="button">Delete</button>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            } else {
                container.innerHTML = '<p style="text-align: center; color: #999;">No saved filters yet. Create one to get started!</p>';
            }
        })
        .catch(error => {
            console.error('Error loading filters:', error);
            container.innerHTML = '<p style="color: red;">Error loading filters</p>';
        });
}

// Save filter form submission
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('saveFilterForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const filterType = document.getElementById('filterType').value;
            const formData = new FormData(form);

            // Get current filter criteria from URL
            const urlParams = new URLSearchParams(window.location.search);
            const criteria = {};

            urlParams.forEach((value, key) => {
                if (key !== 'page' && key !== 'csrfmiddlewaretoken') {
                    criteria[key] = value;
                }
            });

            // Prepare submission data
            const submitData = {
                name: formData.get('name'),
                description: formData.get('description'),
                filter_type: filterType,
                filter_criteria: criteria,
                is_global: formData.get('is_global') === 'true'
            };

            // Determine if POST (create) or PATCH (update)
            const method = form.dataset.method || 'POST';
            const url = form.action || '/api/filters/';

            fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(submitData)
            })
            .then(response => {
                if (response.ok) {
                    closeSaveFilterModal();
                    showNotification('Filter saved successfully!', 'success');
                    // Reload filters if modal open
                    if (document.getElementById('savedFiltersModal').style.display === 'flex') {
                        loadSavedFiltersList();
                    }
                } else {
                    showNotification('Error saving filter', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error saving filter', 'error');
            });
        });
    }

    // Close modals when clicking outside
    document.addEventListener('click', function(e) {
        const modal = document.getElementById('saveFilterModal');
        if (modal && e.target === modal) {
            closeSaveFilterModal();
        }

        const savedModal = document.getElementById('savedFiltersModal');
        if (savedModal && e.target === savedModal) {
            closeSavedFiltersModal();
        }
    });
});

// Utility functions
function getCookie(name) {
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
    return cookieValue;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        z-index: 2000;
        font-size: 14px;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
