/**
 * State Management Module
 * Manages global application state
 */

export const state = {
    // View mode: 'material', 'class', or 'element'
    globalViewMode: 'material',

    // Data from the API
    detailedResults: {},
    elementsData: {},

    // Table sorting
    currentSort: {
        field: 'carbon',
        direction: 'desc'
    },

    // Pagination
    currentPage: 1,
    pageSize: 20,

    // Chart instances (managed by charts module)
    charts: {}
};

// State update functions
export function setViewMode(mode) {
    state.globalViewMode = mode;
    state.currentPage = 1; // Reset to first page on view change
}

export function setDetailedResults(results) {
    state.detailedResults = results;
}

export function setElementsData(data) {
    state.elementsData = data;
}

export function setSortField(field, direction = null) {
    if (state.currentSort.field === field && direction === null) {
        // Toggle direction if same field
        state.currentSort.direction = state.currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        state.currentSort.field = field;
        state.currentSort.direction = direction ||
            (['carbon', 'volume', 'mass', 'density', 'elements', 'count'].includes(field) ? 'desc' : 'asc');
    }
    state.currentPage = 1; // Reset to first page on sort change
}

export function setCurrentPage(page) {
    state.currentPage = page;
}

export function setPageSize(size) {
    state.pageSize = size === 'all' ? 'all' : parseInt(size);
    state.currentPage = 1; // Reset to first page on page size change
} 