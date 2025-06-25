/**
 * Main Application Module
 * Coordinates all modules and initializes the app
 */

import { state, setViewMode, setPageSize } from './state.js';
import { loadAllData } from './data.js';
import { updateCharts } from './charts.js';
import { updateTable, sortTable, goToPage, toggleElementDetails, toggleAllElementGroups } from './table.js';
import { calculateSummary, formatNumber } from './utils.js';

/**
 * Initialize the application
 */
async function init() {
    try {
        // Show loading state
        showLoading();

        // Load data from API
        await loadAllData();

        // Initial UI update
        updateUI();
    } catch (error) {
        showError(error);
    }
}

/**
 * Show loading state
 */
function showLoading() {
    document.getElementById('summaryCards').innerHTML =
        '<div class="loading">Loading data...</div>';
}

/**
 * Show error state
 */
function showError(error) {
    document.getElementById('summaryCards').innerHTML =
        `<div class="error">Error loading data: ${error.message}</div>`;
}

/**
 * Set global view mode
 */
function setGlobalView(mode) {
    setViewMode(mode);

    // Update toggle buttons
    document.querySelectorAll('.view-toggle button').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.toLowerCase().includes(mode));
    });

    // Update all components
    updateUI();
}

/**
 * Update entire UI
 */
function updateUI() {
    updateSummaryCards();
    updateCharts();
    updateTable();
    updateTitles();
}

/**
 * Update titles based on view mode
 */
function updateTitles() {
    if (state.globalViewMode === 'material') {
        document.getElementById('doughnutTitle').textContent = 'Carbon Impact by Material';
        document.getElementById('barTitle').textContent = 'Top 10 Materials by Carbon';
        document.getElementById('bubbleTitle').textContent = 'Material Analysis (Volume vs Carbon vs Mass)';
        document.getElementById('tableTitle').textContent = 'Materials Table';
    } else if (state.globalViewMode === 'class') {
        document.getElementById('doughnutTitle').textContent = 'Carbon Impact by IFC Class';
        document.getElementById('barTitle').textContent = 'Top 10 IFC Classes by Carbon';
        document.getElementById('bubbleTitle').textContent = 'Class Analysis (Volume vs Carbon)';
        document.getElementById('tableTitle').textContent = 'IFC Classes Table';
    } else {
        document.getElementById('doughnutTitle').textContent = 'Carbon Impact by Element';
        document.getElementById('barTitle').textContent = 'Top 10 Elements by Carbon';
        document.getElementById('bubbleTitle').textContent = 'Element Analysis (Volume vs Carbon)';
        document.getElementById('tableTitle').textContent = 'Elements Table';
    }
}

/**
 * Update summary cards
 */
function updateSummaryCards() {
    const summary = calculateSummary(state.detailedResults, state.globalViewMode, state.elementsData);

    let cardsHtml = `
        <div class="card">
            <h3>Total Carbon</h3>
            <div class="value">${formatNumber(summary.totalCarbon, 1)}</div>
            <div class="unit">kg CO₂-eq</div>
        </div>
        <div class="card">
            <h3>Total Volume</h3>
            <div class="value">${formatNumber(summary.totalVolume, 2)}</div>
            <div class="unit">m³</div>
        </div>
        <div class="card">
            <h3>Total Mass</h3>
            <div class="value">${formatNumber(summary.totalMass / 1000, 1)}</div>
            <div class="unit">tons</div>
        </div>
    `;

    if (state.globalViewMode === 'material') {
        cardsHtml += `
            <div class="card">
                <h3>Materials</h3>
                <div class="value">${summary.count}</div>
                <div class="unit">${summary.withImpact} with impact</div>
            </div>
        `;
    } else if (state.globalViewMode === 'class') {
        cardsHtml += `
            <div class="card">
                <h3>IFC Classes</h3>
                <div class="value">${summary.count}</div>
                <div class="unit">class types</div>
            </div>
        `;
    } else {
        cardsHtml += `
            <div class="card">
                <h3>Elements</h3>
                <div class="value">${summary.count}</div>
                <div class="unit">individual elements</div>
            </div>
        `;
    }

    document.getElementById('summaryCards').innerHTML = cardsHtml;
}

/**
 * Update page size
 */
function updatePageSize() {
    const select = document.getElementById('pageSize');
    setPageSize(select.value);
    updateTable();
}

// Expose functions to window for HTML onclick handlers
window.setGlobalView = setGlobalView;
window.sortTable = sortTable;
window.goToPage = goToPage;
window.toggleElementDetails = toggleElementDetails;
window.toggleAllElementGroups = toggleAllElementGroups;
window.updatePageSize = updatePageSize;

// Initialize app when DOM is ready
window.addEventListener('DOMContentLoaded', init); 