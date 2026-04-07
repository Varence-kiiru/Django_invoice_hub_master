/**
 * Global Search JavaScript
 * Handles search bar interactions and suggestions
 */

class GlobalSearch {
    constructor() {
        this.searchInput = document.getElementById('globalSearchInput');
        this.suggestionsContainer = document.getElementById('searchSuggestions');
        this.searchTimeout = null;
        this.minChars = 2;

        this.init();
    }

    init() {
        if (!this.searchInput) return;

        // Search on input
        this.searchInput.addEventListener('input', (e) => this.handleInput(e));

        // Close suggestions on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSuggestions();
            }
        });

        // Close suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.global-search-container')) {
                this.closeSuggestions();
            }
        });
    }

    handleInput(event) {
        const query = event.target.value.trim();

        // Clear previous timeout
        clearTimeout(this.searchTimeout);

        if (query.length < this.minChars) {
            this.closeSuggestions();
            return;
        }

        // Debounce search
        this.searchTimeout = setTimeout(() => {
            this.fetchSuggestions(query);
        }, 300);
    }

    fetchSuggestions(query) {
        fetch(`/api/search/suggestions/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => this.displaySuggestions(data, query))
            .catch(error => console.error('Search error:', error));
    }

    displaySuggestions(data, query) {
        if (!data.suggestions || Object.keys(data.suggestions).length === 0) {
            this.showNoResults(query);
            return;
        }

        let html = '';

        // Invoices
        if (data.suggestions.invoices && data.suggestions.invoices.length > 0) {
            html += '<div class="suggestion-group">';
            html += '<div class="suggestion-group-title">📄 Invoices</div>';
            data.suggestions.invoices.forEach(item => {
                html += `
                    <a href="/invoices/${item.id}/" class="suggestion-item">
                        <div class="suggestion-item-title">${this.highlightQuery(item.invoice_number, query)}</div>
                        <div class="suggestion-item-subtitle">${this.escapeHtml(item.client_name)}</div>
                    </a>
                `;
            });
            html += '</div>';
        }

        // Payments
        if (data.suggestions.payments && data.suggestions.payments.length > 0) {
            html += '<div class="suggestion-group">';
            html += '<div class="suggestion-group-title">💰 Payments</div>';
            data.suggestions.payments.forEach(item => {
                html += `
                    <a href="/payments/${item.id}/" class="suggestion-item">
                        <div class="suggestion-item-title">Payment #${item.id}</div>
                        <div class="suggestion-item-subtitle">${this.escapeHtml(item.invoice_number)} - ${this.escapeHtml(item.client_name)}</div>
                    </a>
                `;
            });
            html += '</div>';
        }

        // Clients
        if (data.suggestions.clients && data.suggestions.clients.length > 0) {
            html += '<div class="suggestion-group">';
            html += '<div class="suggestion-group-title">👥 Clients</div>';
            data.suggestions.clients.forEach(item => {
                html += `
                    <a href="/clients/${item.id}/" class="suggestion-item">
                        <div class="suggestion-item-title">${this.highlightQuery(item.name, query)}</div>
                        <div class="suggestion-item-subtitle">${this.escapeHtml(item.email)}</div>
                    </a>
                `;
            });
            html += '</div>';
        }

        // View all results button
        html += '<div class="suggestion-group">';
        html += `<a href="/search/?q=${encodeURIComponent(query)}" class="suggestion-item" style="text-align: center; color: #3498db; font-weight: 500;">View all results →</a>`;
        html += '</div>';

        this.suggestionsContainer.innerHTML = html;
        this.showSuggestions();
    }

    showNoResults(query) {
        this.suggestionsContainer.innerHTML = `
            <div class="suggestion-group">
                <div class="suggestion-item" style="text-align: center; color: #999;">
                    No results for "<strong>${this.escapeHtml(query)}</strong>"
                </div>
                <a href="/search/?q=${encodeURIComponent(query)}" class="suggestion-item" style="text-align: center; color: #3498db; font-weight: 500;">Search anyway →</a>
            </div>
        `;
        this.showSuggestions();
    }

    showSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.style.display = 'block';
        }
    }

    closeSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.style.display = 'none';
        }
    }

    highlightQuery(text, query) {
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<strong style="color: #3498db; font-weight: 600;">$1</strong>');
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// Initialize search on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new GlobalSearch();
});
