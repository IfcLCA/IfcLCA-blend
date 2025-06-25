/**
 * Table Module
 * Handles all table creation and updates
 */

import { state, setSortField, setCurrentPage } from './state.js';
import { formatNumber, getClassDataFromElements, getElementsFromData } from './utils.js';

/**
 * Update the table based on view mode
 */
export function updateTable() {
    const header = document.getElementById('tableHeader');
    const body = document.getElementById('tableBody');
    const expandControls = document.getElementById('expandControls');

    // Show/hide expand controls based on view mode
    expandControls.style.display = state.globalViewMode === 'element' ? 'block' : 'none';

    if (state.globalViewMode === 'material') {
        updateMaterialTable(header, body);
    } else if (state.globalViewMode === 'class') {
        updateClassTable(header, body);
    } else {
        updateElementTable(header, body);
    }

    updatePagination();
    updateSortIndicators();
}

/**
 * Update table for material view
 */
function updateMaterialTable(header, body) {
    header.innerHTML = `
        <tr>
            <th onclick="window.sortTable('name')">Material Name</th>
            <th onclick="window.sortTable('elements')" class="number">Elements</th>
            <th onclick="window.sortTable('volume')" class="number">Volume (m³)</th>
            <th onclick="window.sortTable('mass')" class="number">Mass (kg)</th>
            <th onclick="window.sortTable('carbon')" class="number">Carbon (kg CO₂-eq)</th>
            <th onclick="window.sortTable('density')" class="number">Density (kg/m³)</th>
        </tr>
    `;

    const materials = getSortedMaterials();
    const paginatedData = paginateData(materials);

    body.innerHTML = paginatedData.map(([name, data]) => `
        <tr>
            <td>${name}</td>
            <td class="number">${data.element_count || data.elements || 0}</td>
            <td class="number">${formatNumber(data.total_volume || 0, 2)}</td>
            <td class="number">${formatNumber(data.total_mass || 0, 0)}</td>
            <td class="number">${formatNumber(data.total_carbon || data.gwp || 0, 1)}</td>
            <td class="number">${formatNumber(data.density || 0, 0)}</td>
        </tr>
    `).join('');
}

/**
 * Update table for class view
 */
function updateClassTable(header, body) {
    header.innerHTML = `
        <tr>
            <th onclick="window.sortTable('class')">IFC Class</th>
            <th onclick="window.sortTable('count')" class="number">Count</th>
            <th onclick="window.sortTable('volume')" class="number">Volume (m³)</th>
            <th onclick="window.sortTable('mass')" class="number">Mass (kg)</th>
            <th onclick="window.sortTable('carbon')" class="number">Carbon (kg CO₂-eq)</th>
        </tr>
    `;

    const classes = getClassDataFromElements(state.detailedResults, state.elementsData);
    const sortedClasses = sortClassData(classes);
    const paginatedData = paginateData(sortedClasses);

    body.innerHTML = paginatedData.map(cls => `
        <tr>
            <td>${cls.name}</td>
            <td class="number">${cls.count}</td>
            <td class="number">${formatNumber(cls.volume, 2)}</td>
            <td class="number">${formatNumber(cls.mass, 0)}</td>
            <td class="number">${formatNumber(cls.carbon, 1)}</td>
        </tr>
    `).join('');
}

/**
 * Update table for element view
 */
function updateElementTable(header, body) {
    header.innerHTML = `
        <tr>
            <th onclick="window.sortTable('name')">Element Name</th>
            <th onclick="window.sortTable('type')">IFC Type</th>
            <th onclick="window.sortTable('material')">Material</th>
            <th onclick="window.sortTable('volume')" class="number">Volume (m³)</th>
            <th onclick="window.sortTable('carbon')" class="number">Carbon (kg CO₂-eq)</th>
        </tr>
    `;

    const elements = getElementsFromData(state.detailedResults, state.elementsData);

    // Group elements by name and type
    const groupedElements = {};
    elements.forEach(elem => {
        const key = `${elem.name}|${elem.type}`;
        if (!groupedElements[key]) {
            groupedElements[key] = {
                name: elem.name,
                type: elem.type,
                materials: [],
                totalVolume: 0,
                totalCarbon: 0
            };
        }
        groupedElements[key].materials.push({
            name: elem.material,
            volume: elem.volume,
            carbon: elem.carbon
        });
        groupedElements[key].totalVolume += elem.volume;
        groupedElements[key].totalCarbon += elem.carbon;
    });

    // Consolidate materials with same name within each group
    Object.values(groupedElements).forEach(group => {
        const materialMap = {};
        group.materials.forEach(mat => {
            if (!materialMap[mat.name]) {
                materialMap[mat.name] = {
                    name: mat.name,
                    volume: 0,
                    carbon: 0
                };
            }
            materialMap[mat.name].volume += mat.volume;
            materialMap[mat.name].carbon += mat.carbon;
        });
        group.materials = Object.values(materialMap);
    });

    // Convert to array and sort
    const elementGroups = Object.values(groupedElements);
    const sortedGroups = sortElementGroups(elementGroups);
    const paginatedData = paginateData(sortedGroups);

    // Build table HTML
    let tableHTML = '';
    paginatedData.forEach((group, groupIndex) => {
        if (group.materials.length === 1) {
            // Single material - simple row
            tableHTML += `
                <tr>
                    <td>${group.name}</td>
                    <td>${group.type}</td>
                    <td>${group.materials[0].name}</td>
                    <td class="number">${formatNumber(group.totalVolume, 3)}</td>
                    <td class="number">${formatNumber(group.totalCarbon, 2)}</td>
                </tr>
            `;
        } else {
            // Multiple different materials - expandable row
            const rowId = `group-${state.currentPage}-${groupIndex}`;
            tableHTML += `
                <tr class="expandable-row" onclick="window.toggleElementDetails('${rowId}')">
                    <td>${group.name}</td>
                    <td>${group.type}</td>
                    <td class="material-varies">varies (${group.materials.length} materials)</td>
                    <td class="number">${formatNumber(group.totalVolume, 3)}</td>
                    <td class="number">${formatNumber(group.totalCarbon, 2)}</td>
                </tr>
            `;

            // Add detail rows for each material
            group.materials.forEach(mat => {
                tableHTML += `
                    <tr class="detail-row hidden" data-parent="${rowId}">
                        <td>${group.name}</td>
                        <td></td>
                        <td>${mat.name}</td>
                        <td class="number">${formatNumber(mat.volume, 3)}</td>
                        <td class="number">${formatNumber(mat.carbon, 2)}</td>
                    </tr>
                `;
            });
        }
    });

    body.innerHTML = tableHTML;
}

/**
 * Sort table by field
 */
export function sortTable(field) {
    setSortField(field);
    updateTable();
}

/**
 * Get sorted materials data
 */
function getSortedMaterials() {
    const materials = Object.entries(state.detailedResults);

    return materials.sort((a, b) => {
        let aVal, bVal;

        switch (state.currentSort.field) {
            case 'name':
                aVal = a[0].toLowerCase();
                bVal = b[0].toLowerCase();
                break;
            case 'elements':
                aVal = a[1].element_count || a[1].elements || 0;
                bVal = b[1].element_count || b[1].elements || 0;
                break;
            case 'carbon':
                aVal = a[1].total_carbon || a[1].gwp || 0;
                bVal = b[1].total_carbon || b[1].gwp || 0;
                break;
            case 'volume':
                aVal = a[1].total_volume || 0;
                bVal = b[1].total_volume || 0;
                break;
            case 'mass':
                aVal = a[1].total_mass || 0;
                bVal = b[1].total_mass || 0;
                break;
            case 'density':
                aVal = a[1].density || 0;
                bVal = b[1].density || 0;
                break;
            default:
                aVal = a[1].total_carbon || a[1].gwp || 0;
                bVal = b[1].total_carbon || b[1].gwp || 0;
        }

        if (state.currentSort.direction === 'asc') {
            return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        } else {
            return bVal < aVal ? -1 : bVal > aVal ? 1 : 0;
        }
    });
}

/**
 * Sort class data
 */
function sortClassData(classes) {
    return classes.sort((a, b) => {
        let aVal, bVal;

        switch (state.currentSort.field) {
            case 'class':
                aVal = a.name;
                bVal = b.name;
                break;
            case 'count':
                aVal = a.count || 0;
                bVal = b.count || 0;
                break;
            case 'volume':
                aVal = a.volume || 0;
                bVal = b.volume || 0;
                break;
            case 'mass':
                aVal = a.mass || 0;
                bVal = b.mass || 0;
                break;
            case 'carbon':
                aVal = a.carbon || 0;
                bVal = b.carbon || 0;
                break;
            default:
                aVal = a.carbon || 0;
                bVal = b.carbon || 0;
        }

        if (state.currentSort.direction === 'asc') {
            return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        } else {
            return bVal < aVal ? -1 : bVal > aVal ? 1 : 0;
        }
    });
}

/**
 * Sort element groups
 */
function sortElementGroups(groups) {
    return groups.sort((a, b) => {
        let aVal, bVal;

        switch (state.currentSort.field) {
            case 'name':
                aVal = a.name;
                bVal = b.name;
                break;
            case 'type':
                aVal = a.type;
                bVal = b.type;
                break;
            case 'material':
                // Sort by first material name or "varies"
                aVal = a.materials.length === 1 ? a.materials[0].name.toLowerCase() : 'varies';
                bVal = b.materials.length === 1 ? b.materials[0].name.toLowerCase() : 'varies';
                break;
            case 'volume':
                aVal = a.totalVolume || 0;
                bVal = b.totalVolume || 0;
                break;
            case 'carbon':
                aVal = a.totalCarbon || 0;
                bVal = b.totalCarbon || 0;
                break;
            default:
                aVal = a.totalCarbon || 0;
                bVal = b.totalCarbon || 0;
        }

        if (state.currentSort.direction === 'asc') {
            return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        } else {
            return bVal < aVal ? -1 : bVal > aVal ? 1 : 0;
        }
    });
}

/**
 * Update sort indicators
 */
function updateSortIndicators() {
    document.querySelectorAll('th').forEach(th => {
        th.classList.remove('sorted-asc', 'sorted-desc');
    });

    const clickHandlers = document.querySelectorAll('th[onclick]');
    clickHandlers.forEach(th => {
        const field = th.getAttribute('onclick').match(/sortTable\('(.+?)'\)/)?.[1];
        if (field === state.currentSort.field) {
            th.classList.add(`sorted-${state.currentSort.direction}`);
        }
    });
}

/**
 * Paginate data
 */
function paginateData(data) {
    if (state.pageSize === 'all') return data;

    const start = (state.currentPage - 1) * state.pageSize;
    const end = start + state.pageSize;
    return data.slice(start, end);
}

/**
 * Update pagination controls
 */
function updatePagination() {
    let data;
    if (state.globalViewMode === 'material') {
        data = Object.entries(state.detailedResults);
    } else if (state.globalViewMode === 'class') {
        data = getClassDataFromElements(state.detailedResults, state.elementsData);
    } else {
        // For element view, count groups not individual elements
        const elements = getElementsFromData(state.detailedResults, state.elementsData);
        const groupedElements = {};
        elements.forEach(elem => {
            const key = `${elem.name}|${elem.type}`;
            if (!groupedElements[key]) {
                groupedElements[key] = true;
            }
        });
        data = Object.keys(groupedElements);
    }

    const totalItems = data.length;
    const totalPages = state.pageSize === 'all' ? 1 : Math.ceil(totalItems / state.pageSize);

    let html = '';

    if (totalPages > 1) {
        html += `<button onclick="window.goToPage(1)" ${state.currentPage === 1 ? 'disabled' : ''}>First</button>`;
        html += `<button onclick="window.goToPage(${state.currentPage - 1})" ${state.currentPage === 1 ? 'disabled' : ''}>Previous</button>`;

        html += `<span class="pagination-info">Page ${state.currentPage} of ${totalPages}</span>`;

        html += `<button onclick="window.goToPage(${state.currentPage + 1})" ${state.currentPage === totalPages ? 'disabled' : ''}>Next</button>`;
        html += `<button onclick="window.goToPage(${totalPages})" ${state.currentPage === totalPages ? 'disabled' : ''}>Last</button>`;
    }

    document.getElementById('pagination').innerHTML = html;
}

/**
 * Go to specific page
 */
export function goToPage(page) {
    setCurrentPage(page);
    updateTable();
}

/**
 * Toggle element details (expand/collapse)
 */
export function toggleElementDetails(rowId) {
    const parentRow = event.currentTarget;
    const detailRows = document.querySelectorAll(`tr[data-parent="${rowId}"]`);

    parentRow.classList.toggle('expanded');
    detailRows.forEach(row => {
        row.classList.toggle('hidden');
    });
}

/**
 * Expand/collapse all element groups
 */
export function toggleAllElementGroups(expand) {
    const expandableRows = document.querySelectorAll('.expandable-row');
    const detailRows = document.querySelectorAll('.detail-row');

    expandableRows.forEach(row => {
        if (expand) {
            row.classList.add('expanded');
        } else {
            row.classList.remove('expanded');
        }
    });

    detailRows.forEach(row => {
        if (expand) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
} 