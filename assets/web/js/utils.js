/**
 * Utilities Module
 * Common helper functions used throughout the application
 */

/**
 * Format a number with specified decimal places
 * @param {number} num - The number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number string
 */
export function formatNumber(num, decimals = 0) {
    if (num === undefined || num === null) return '0';
    return num.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Truncate a label to specified length with ellipsis
 * @param {string} label - The label to truncate
 * @param {number} maxLength - Maximum length before truncation
 * @returns {string} Truncated label
 */
export function truncateLabel(label, maxLength) {
    return label.length > maxLength ?
        label.substring(0, maxLength - 3) + '...' : label;
}

/**
 * Generate an array of colors for charts
 * @param {number} count - Number of colors needed
 * @returns {string[]} Array of color hex codes
 */
export function generateColors(count) {
    const colors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
        '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#d35400',
        '#c0392b', '#27ae60', '#2980b9', '#8e44ad', '#16a085'
    ];

    // Repeat colors if we need more than available
    while (colors.length < count) {
        colors.push(...colors.slice(0, count - colors.length));
    }

    return colors.slice(0, count);
}

/**
 * Calculate summary statistics from detailed results
 * @param {Object} detailedResults - The detailed results object
 * @param {string} viewMode - Current view mode
 * @param {Object} elementsData - Elements data object
 * @returns {Object} Summary statistics
 */
export function calculateSummary(detailedResults, viewMode, elementsData) {
    const values = Object.values(detailedResults);

    const totalCarbon = values.reduce((sum, mat) => sum + (mat.total_carbon || mat.gwp || 0), 0);
    const totalVolume = values.reduce((sum, mat) => sum + (mat.total_volume || 0), 0);
    const totalMass = values.reduce((sum, mat) => sum + (mat.total_mass || 0), 0);

    if (viewMode === 'material') {
        return {
            totalCarbon,
            totalVolume,
            totalMass,
            count: Object.keys(detailedResults).length,
            withImpact: values.filter(mat => (mat.total_carbon || mat.gwp || 0) > 0).length
        };
    } else if (viewMode === 'class') {
        // Count unique IFC classes
        const classData = getClassDataFromElements(detailedResults, elementsData);
        return {
            totalCarbon,
            totalVolume,
            totalMass,
            count: classData.length,
            withImpact: classData.filter(cls => cls.carbon > 0).length
        };
    } else {
        // Count real elements or estimate from materials
        let elementCount = 0;
        if (Object.keys(elementsData).length > 0) {
            // Count real elements from IFC data
            Object.values(elementsData).forEach(materialData => {
                if (materialData.elements && Array.isArray(materialData.elements)) {
                    elementCount += materialData.elements.length;
                }
            });
        } else {
            // Fallback to material element count
            elementCount = values.reduce((sum, mat) => sum + (mat.element_count || mat.elements || 0), 0);
        }
        return {
            totalCarbon,
            totalVolume,
            totalMass,
            count: elementCount,
            withImpact: elementCount
        };
    }
}

/**
 * Get class data from elements
 * @param {Object} detailedResults - Detailed results from API
 * @param {Object} elementsData - Elements data from API
 * @returns {Array} Array of class data objects
 */
export function getClassDataFromElements(detailedResults, elementsData) {
    const classTypes = {};

    if (Object.keys(elementsData).length > 0) {
        Object.entries(elementsData).forEach(([materialName, materialData]) => {
            if (materialData.elements && Array.isArray(materialData.elements)) {
                const materialInfo = detailedResults[materialName];
                if (!materialInfo) return;

                const density = materialInfo.density || materialData.material_info?.density || 0;
                const carbonPerKg = materialInfo.carbon_per_unit ||
                    materialInfo.gwp ||
                    (materialInfo.total_carbon / materialInfo.total_mass) || 0;

                materialData.elements.forEach(elem => {
                    if (elem.volume > 0) {
                        const ifcType = elem.type || 'Unknown';

                        if (!classTypes[ifcType]) {
                            classTypes[ifcType] = {
                                name: ifcType,
                                count: 0,
                                carbon: 0,
                                volume: 0,
                                mass: 0
                            };
                        }

                        const mass = elem.volume * density;
                        const carbon = mass * carbonPerKg;

                        classTypes[ifcType].count += 1;
                        classTypes[ifcType].carbon += carbon;
                        classTypes[ifcType].volume += elem.volume || 0;
                        classTypes[ifcType].mass += mass;
                    }
                });
            }
        });
    }

    return Object.values(classTypes);
}

/**
 * Get individual elements data
 * @param {Object} detailedResults - Detailed results from API
 * @param {Object} elementsData - Elements data from API
 * @returns {Array} Array of element objects
 */
export function getElementsFromData(detailedResults, elementsData) {
    const elements = [];

    if (Object.keys(elementsData).length > 0) {
        Object.entries(elementsData).forEach(([materialName, materialData]) => {
            if (materialData.elements && Array.isArray(materialData.elements)) {
                const materialInfo = detailedResults[materialName];
                if (!materialInfo) return;

                const density = materialInfo.density || materialData.material_info?.density || 0;
                const carbonPerKg = materialInfo.carbon_per_unit ||
                    materialInfo.gwp ||
                    (materialInfo.total_carbon / materialInfo.total_mass) || 0;

                materialData.elements.forEach(elem => {
                    if (elem.volume > 0) {
                        const mass = elem.volume * density;
                        const carbon = mass * carbonPerKg;

                        elements.push({
                            name: elem.name || `${elem.type}_${elem.id}`,
                            type: elem.type || 'Unknown',
                            material: materialName,
                            volume: elem.volume || 0,
                            carbon: carbon
                        });
                    }
                });
            }
        });
    }

    return elements;
} 