/**
 * Data Module
 * Handles API calls and data loading
 */

import { setDetailedResults, setElementsData } from './state.js';

/**
 * Load all data from the API
 * @returns {Promise<Object>} Object with detailedResults and elementsData
 */
export async function loadAllData() {
    try {
        // Load material results
        const response = await fetch('/results');
        if (!response.ok) {
            throw new Error(`Failed to load results: ${response.status}`);
        }

        const detailedResults = await response.json();
        console.log('Loaded material data:', detailedResults);
        setDetailedResults(detailedResults);

        // Try to load element data - fallback gracefully if not available
        let elementsData = {};
        try {
            console.log('Attempting to load element data from /api/elements...');
            const elementsResponse = await fetch('/api/elements');

            if (elementsResponse.ok) {
                elementsData = await elementsResponse.json();
                console.log('Loaded element data:', elementsData);
            } else {
                console.log('Element API not available');
            }
        } catch (e) {
            console.log('Element API not available:', e);
        }

        setElementsData(elementsData);

        return { detailedResults, elementsData };
    } catch (error) {
        console.error('Error loading data:', error);
        throw error;
    }
}

/**
 * Reload data from the API
 * @returns {Promise<Object>} Object with detailedResults and elementsData
 */
export async function reloadData() {
    return loadAllData();
} 