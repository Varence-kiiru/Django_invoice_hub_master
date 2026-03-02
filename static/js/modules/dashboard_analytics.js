/**
 * Dashboard Analytics Module
 * Handles dashboard data loading, processing, and visualization
 * 
 * Usage:
 *   const dashboard = new DashboardAnalytics({ period: 30 });
 *   dashboard.refresh();
 */

class DashboardAnalytics {
  constructor(options = {}) {
    this.period = options.period || 30;
    this.autoRefresh = options.autoRefresh !== false;
    this.refreshInterval = options.refreshInterval || 5 * 60 * 1000;
    this.currencyCode = 'KES'; // Default currency, will be updated from API
    
    // Chart instances
    this.charts = {
      invoiceTimeline: null,
      paymentTimeline: null,
      paymentMethod: null
    };

    // Data caches
    this.data = {
      summary: null,
      timeline: null,
      aging: null,
      topClients: null,
      paymentMethods: null
    };

    // DOM element cache
    this.elements = {
      loadingSpinner: document.getElementById('loadingSpinner'),
      errorAlert: document.getElementById('errorAlert'),
      errorMessage: document.getElementById('errorMessage'),
      refreshBtn: document.getElementById('refreshBtn'),
      
      // Financial cards
      totalRevenue: document.getElementById('totalRevenue'),
      revenueChange: document.getElementById('revenueChange'),
      outstandingAR: document.getElementById('outstandingAR'),
      arPercentage: document.getElementById('arPercentage'),
      avgTransaction: document.getElementById('avgTransaction'),
      transactionCount: document.getElementById('transactionCount'),
      paymentRate: document.getElementById('paymentRate'),
      paymentStats: document.getElementById('paymentStats'),
      
      // Charts
      invoiceTimelineChart: document.getElementById('invoiceTimelineChart'),
      paymentTimelineChart: document.getElementById('paymentTimelineChart'),
      paymentMethodChart: document.getElementById('paymentMethodChart'),
      
      // Aging report
      currentCount: document.getElementById('current-count'),
      currentBar: document.getElementById('current-bar'),
      currentAmount: document.getElementById('current-amount'),
      '30-60Count': document.getElementById('30-60-count'),
      '30-60Bar': document.getElementById('30-60-bar'),
      '30-60Amount': document.getElementById('30-60-amount'),
      '60-90Count': document.getElementById('60-90-count'),
      '60-90Bar': document.getElementById('60-90-bar'),
      '60-90Amount': document.getElementById('60-90-amount'),
      '90plusCount': document.getElementById('90plus-count'),
      '90plusBar': document.getElementById('90plus-bar'),
      '90plusAmount': document.getElementById('90plus-amount'),
      totalAR: document.getElementById('total-ar'),
      
      // Top clients
      topClientsTable: document.getElementById('topClientsTable'),
      
      // Payment methods legend
      paymentMethodLegend: document.getElementById('paymentMethodLegend')
    };

    this.init();
  }

  /**
   * Initialize dashboard
   */
  init() {
    // Load initial data
    this.refresh();

    // Set up auto-refresh if enabled
    if (this.autoRefresh) {
      this.setupAutoRefresh();
    }
  }

  /**
   * Setup auto-refresh interval
   */
  setupAutoRefresh() {
    this.refreshTimer = setInterval(() => {
      this.refresh();
    }, this.refreshInterval);
  }

  /**
   * Stop auto-refresh
   */
  stopAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  }

  /**
   * Refresh all dashboard data
   */
  async refresh() {
    try {
      this.showLoading(true);
      this.hideError();

      // Load all data in parallel
      await Promise.all([
        this.loadSummary(),
        this.loadTimeline(),
        this.loadAging(),
        this.loadTopClients(),
        this.loadPaymentMethods()
      ]);

      // Update UI with loaded data
      this.updateFinancialCards();
      this.updateCharts();
      this.updateAgingReport();
      this.updateTopClientsTable();

      this.showLoading(false);
    } catch (error) {
      console.error('Dashboard refresh error:', error);
      this.showError(`Failed to load analytics: ${error.message}`);
      this.showLoading(false);
    }
  }

  /**
   * Set period and refresh data
   */
  setPeriod(period) {
    this.period = period;
    this.refresh();
  }

  /**
   * Load summary metrics
   */
  async loadSummary() {
    try {
      const response = await fetch(`/api/analytics/summary/?period=${this.period}`, {
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to load summary');

      const result = await response.json();
      this.data.summary = result.data;
      
      // Capture currency code from API
      if (result.data.currency_code) {
        this.currencyCode = result.data.currency_code;
      }
      
      return this.data.summary;
    } catch (error) {
      console.error('Summary load error:', error);
      throw error;
    }
  }

  /**
   * Load timeline data
   */
  async loadTimeline() {
    try {
      const response = await fetch(`/api/analytics/timeline/?period=${this.period}`, {
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to load timeline');

      const result = await response.json();
      this.data.timeline = result.data;
      return this.data.timeline;
    } catch (error) {
      console.error('Timeline load error:', error);
      throw error;
    }
  }

  /**
   * Load aging report data
   */
  async loadAging() {
    try {
      const response = await fetch('/api/analytics/aging/', {
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to load aging report');

      const result = await response.json();
      this.data.aging = result.data;
      return this.data.aging;
    } catch (error) {
      console.error('Aging load error:', error);
      throw error;
    }
  }

  /**
   * Load top clients data
   */
  async loadTopClients() {
    try {
      const response = await fetch(`/api/analytics/top-clients/?period=${this.period}`, {
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to load top clients');

      const result = await response.json();
      this.data.topClients = result.data;
      return this.data.topClients;
    } catch (error) {
      console.error('Top clients load error:', error);
      throw error;
    }
  }

  /**
   * Load payment methods data
   */
  async loadPaymentMethods() {
    try {
      const response = await fetch(`/api/analytics/payment-methods/?period=${this.period}`, {
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to load payment methods');

      const result = await response.json();
      this.data.paymentMethods = result.data;
      return this.data.paymentMethods;
    } catch (error) {
      console.error('Payment methods load error:', error);
      throw error;
    }
  }

  /**
   * Update financial summary cards
   */
  updateFinancialCards() {
    if (!this.data.summary) return;

    const summary = this.data.summary;

    // Total Revenue
    this.elements.totalRevenue.textContent = this.formatCurrency(summary.total_revenue || 0);
    const revenueChangePercent = summary.revenue_change_percent || 0;
    this.elements.revenueChange.innerHTML = 
      `${revenueChangePercent >= 0 ? '↑' : '↓'} ${Math.abs(revenueChangePercent)}% vs last period`;

    // Outstanding A/R
    this.elements.outstandingAR.textContent = this.formatCurrency(summary.outstanding_ar || 0);
    const arPercentage = summary.ar_percentage || 0;
    this.elements.arPercentage.textContent = `${arPercentage.toFixed(1)}% of revenue`;

    // Average Transaction
    const avgTransaction = summary.average_transaction || 0;
    this.elements.avgTransaction.textContent = this.formatCurrency(avgTransaction);
    const invoiceCount = summary.invoice_count || 0;
    this.elements.transactionCount.textContent = `${invoiceCount} invoices`;

    // Payment Rate
    const paymentRate = (summary.payment_rate || 0) * 100;
    this.elements.paymentRate.textContent = `${paymentRate.toFixed(1)}%`;
    const paidCount = summary.paid_invoices || 0;
    const totalInvoices = summary.invoice_count || 0;
    this.elements.paymentStats.textContent = `${paidCount} / ${totalInvoices} paid`;
  }

  /**
   * Update all charts
   */
  updateCharts() {
    // Only update if timeline data exists and we have a canvas
    if (this.data.timeline && this.elements.invoiceTimelineChart) {
      this.updateInvoiceTimelineChart();
      this.updatePaymentTimelineChart();
    }

    if (this.data.paymentMethods && this.elements.paymentMethodChart) {
      this.updatePaymentMethodChart();
    }
  }

  /**
   * Update invoice timeline chart (Line chart)
   */
  updateInvoiceTimelineChart() {
    const data = this.data.timeline;
    const ctx = this.elements.invoiceTimelineChart.getContext('2d');

    // Destroy existing chart if it exists
    if (this.charts.invoiceTimeline) {
      this.charts.invoiceTimeline.destroy();
    }

    // Prepare data with last 30 days
    const dates = data.dates || this.generateDateLabels(this.period);
    const amounts = data.invoice_amounts || [];

    this.charts.invoiceTimeline = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{
          label: 'Invoice Amount',
          data: amounts,
          fill: true,
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          borderColor: 'rgb(54, 162, 235)',
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: 'rgb(54, 162, 235)',
          pointHoverRadius: 6,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => '$' + value.toLocaleString()
            }
          }
        }
      }
    });
  }

  /**
   * Update payment timeline chart
   */
  updatePaymentTimelineChart() {
    const data = this.data.timeline;
    const ctx = this.elements.paymentTimelineChart.getContext('2d');

    // Destroy existing chart if it exists
    if (this.charts.paymentTimeline) {
      this.charts.paymentTimeline.destroy();
    }

    // Prepare data
    const dates = data.dates || this.generateDateLabels(this.period);
    const amounts = data.payment_amounts || [];

    this.charts.paymentTimeline = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{
          label: 'Payment Amount',
          data: amounts,
          fill: true,
          backgroundColor: 'rgba(75, 192, 75, 0.1)',
          borderColor: 'rgb(75, 192, 75)',
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: 'rgb(75, 192, 75)',
          pointHoverRadius: 6,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => '$' + value.toLocaleString()
            }
          }
        }
      }
    });
  }

  /**
   * Update payment method pie chart
   */
  updatePaymentMethodChart() {
    const data = this.data.paymentMethods;
    const ctx = this.elements.paymentMethodChart.getContext('2d');

    // Destroy existing chart if it exists
    if (this.charts.paymentMethod) {
      this.charts.paymentMethod.destroy();
    }

    const methods = data.methods || [];
    const colors = [
      'rgb(255, 107, 107)', // red
      'rgb(75, 192, 192)',  // teal
      'rgb(255, 206, 86)',  // yellow
      'rgb(153, 102, 255)', // purple
      'rgb(255, 159, 64)',  // orange
      'rgb(54, 162, 235)'   // blue
    ];

    this.charts.paymentMethod = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: methods.map(m => m.method_name),
        datasets: [{
          data: methods.map(m => m.count),
          backgroundColor: colors.slice(0, methods.length),
          borderColor: '#fff',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom'
          }
        }
      }
    });

    // Update legend
    this.updatePaymentMethodLegend(methods);
  }

  /**
   * Update payment method legend
   */
  updatePaymentMethodLegend(methods) {
    const colors = [
      '#ff6b6b', '#4bc0c0', '#ffce56', '#9966ff', '#ff9f40', '#36a2eb'
    ];

    let html = '<div class="row">';
    methods.forEach((method, index) => {
      html += `
        <div class="col-md-6 mb-2">
          <span style="display: inline-block; width: 12px; height: 12px; background-color: ${colors[index % colors.length]}; border-radius: 2px; margin-right: 8px;"></span>
          <span>${method.method_name}: ${method.count} payments (${this.formatCurrency(method.amount)})</span>
        </div>
      `;
    });
    html += '</div>';

    this.elements.paymentMethodLegend.innerHTML = html;
  }

  /**
   * Update aging report display
   */
  updateAgingReport() {
    if (!this.data.aging) return;

    const aging = this.data.aging;
    const total = aging.total_ar || 1; // Avoid division by zero

    // Current (0-30)
    const current = aging.current || { count: 0, amount: 0 };
    this.updateAgingBucket('current', current, total);

    // 31-60
    const thirtyToSixty = aging.thirty_to_sixty || { count: 0, amount: 0 };
    this.updateAgingBucket('30-60', thirtyToSixty, total);

    // 61-90
    const sixtyToNinety = aging.sixty_to_ninety || { count: 0, amount: 0 };
    this.updateAgingBucket('60-90', sixtyToNinety, total);

    // 90+
    const ninetyPlus = aging.ninety_plus || { count: 0, amount: 0 };
    this.updateAgingBucket('90plus', ninetyPlus, total);

    // Total A/R
    this.elements.totalAR.textContent = this.formatCurrency(total);
  }

  /**
   * Update single aging bucket
   */
  updateAgingBucket(bucket, data, total) {
    const prefix = bucket === '90plus' ? '90plus' : bucket;
    const countElement = document.getElementById(`${prefix}-count`);
    const barElement = document.getElementById(`${prefix}-bar`);
    const amountElement = document.getElementById(`${prefix}-amount`);

    if (countElement) countElement.textContent = data.count || 0;
    if (amountElement) amountElement.textContent = this.formatCurrency(data.amount || 0);
    
    if (barElement) {
      const percentage = total > 0 ? (data.amount / total) * 100 : 0;
      barElement.style.width = percentage + '%';
    }
  }

  /**
   * Update top clients table
   */
  updateTopClientsTable() {
    if (!this.data.topClients) {
      this.elements.topClientsTable.innerHTML = `
        <tr>
          <td colspan="7" class="text-center text-muted py-4">No top clients data available</td>
        </tr>
      `;
      return;
    }

    const clients = this.data.topClients.slice(0, 10); // Top 10 clients

    if (clients.length === 0) {
      this.elements.topClientsTable.innerHTML = `
        <tr>
          <td colspan="7" class="text-center text-muted py-4">No clients found</td>
        </tr>
      `;
      return;
    }

    const html = clients.map((client, index) => {
      const statusBadge = client.payment_rate >= 0.8 
        ? '<span class="badge badge-success">Good</span>'
        : client.payment_rate >= 0.5
        ? '<span class="badge badge-warning">At Risk</span>'
        : '<span class="badge badge-danger">Overdue</span>';

      return `
        <tr>
          <td><strong>${index + 1}</strong></td>
          <td>
            <strong>${this.escapeHtml(client.name)}</strong>
            ${client.email ? `<br><small class="text-muted">${this.escapeHtml(client.email)}</small>` : ''}
          </td>
          <td class="text-right">${this.formatCurrency(client.total_revenue || 0)}</td>
          <td class="text-right">${client.invoice_count || 0}</td>
          <td class="text-right">${this.formatCurrency(client.average_invoice || 0)}</td>
          <td class="text-center">${(client.payment_rate * 100).toFixed(0)}%</td>
          <td class="text-center">${statusBadge}</td>
        </tr>
      `;
    }).join('');

    this.elements.topClientsTable.innerHTML = html;
  }

  /**
   * Generate date labels for timeline
   */
  generateDateLabels(days) {
    const labels = [];
    const today = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    
    return labels;
  }

  /**
   * Format number as currency
   */
  formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this.currencyCode
    }).format(value);
  }

  /**
   * Escape HTML characters
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Show loading indicator
   */
  showLoading(show) {
    this.elements.loadingSpinner.style.display = show ? 'block' : 'none';
    if (show) {
      this.elements.refreshBtn.disabled = true;
    } else {
      this.elements.refreshBtn.disabled = false;
    }
  }

  /**
   * Show error message
   */
  showError(message) {
    this.elements.errorMessage.textContent = message;
    this.elements.errorAlert.style.display = 'block';
  }

  /**
   * Hide error message
   */
  hideError() {
    this.elements.errorAlert.style.display = 'none';
  }

  /**
   * Cleanup on page unload
   */
  destroy() {
    this.stopAutoRefresh();
    Object.values(this.charts).forEach(chart => {
      if (chart) chart.destroy();
    });
  }
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
  if (window.dashboardAnalytics instanceof DashboardAnalytics) {
    window.dashboardAnalytics.destroy();
  }
});
