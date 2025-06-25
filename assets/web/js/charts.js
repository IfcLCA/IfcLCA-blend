/**
 * Charts Module
 * Handles all chart creation and updates
 */

import { state } from './state.js';
import { formatNumber, truncateLabel, generateColors, getClassDataFromElements, getElementsFromData } from './utils.js';

/**
 * Update all charts based on current view mode
 */
export function updateCharts() {
    if (state.globalViewMode === 'material') {
        updateMaterialCharts();
    } else if (state.globalViewMode === 'class') {
        updateClassCharts();
    } else {
        updateElementCharts();
    }
}

/**
 * Destroy all existing charts
 */
function destroyCharts() {
    Object.values(state.charts).forEach(chart => chart.destroy());
    state.charts = {};
}

/**
 * Update charts for material view
 */
function updateMaterialCharts() {
    const materials = Object.entries(state.detailedResults)
        .filter(([_, data]) => (data.total_carbon || data.gwp || 0) > 0)
        .sort((a, b) => (b[1].total_carbon || b[1].gwp || 0) - (a[1].total_carbon || a[1].gwp || 0));

    if (materials.length === 0) return;

    destroyCharts();

    // Create doughnut chart
    createDoughnutChart(
        materials.map(([name, _]) => truncateLabel(name, 20)),
        materials.map(([_, data]) => data.total_carbon || data.gwp || 0),
        materials.length,
        (context) => {
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${context.label}: ${formatNumber(value, 1)} kg CO₂-eq (${percentage}%)`;
        }
    );

    // Create bar chart - Top 10
    const top10 = materials.slice(0, 10);
    createBarChart(
        top10.map(([name, _]) => truncateLabel(name, 15)),
        top10.map(([_, data]) => data.total_carbon || data.gwp || 0),
        '#3498db',
        '#2980b9',
        (context) => `${formatNumber(context.parsed.y, 1)} kg CO₂-eq`
    );

    // Create bubble chart
    const bubbleData = materials.map(([name, data]) => ({
        x: data.total_volume || 0.001,
        y: data.total_carbon || data.gwp || 0.001,
        r: Math.max(5, Math.min(30, Math.sqrt(data.total_mass || 0) * 0.01)),
        label: name,
        mass: data.total_mass
    }));

    createBubbleChart(bubbleData, 'Materials', 'rgba(52, 152, 219, 0.6)', false);
}

/**
 * Update charts for class view
 */
function updateClassCharts() {
    const types = getClassDataFromElements(state.detailedResults, state.elementsData)
        .sort((a, b) => b.carbon - a.carbon);

    if (types.length === 0) return;

    destroyCharts();

    // Create doughnut chart
    createDoughnutChart(
        types.map(t => t.name),
        types.map(t => t.carbon),
        types.length,
        (context) => {
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            const type = types[context.dataIndex];
            return [
                `${context.label}: ${formatNumber(value, 1)} kg CO₂-eq (${percentage}%)`,
                `Count: ${type.count} elements`
            ];
        }
    );

    // Create bar chart
    createBarChart(
        types.map(t => t.name),
        types.map(t => t.carbon),
        '#9b59b6',
        '#8e44ad',
        (context) => {
            const type = types[context.dataIndex];
            return [
                `Carbon: ${formatNumber(context.parsed.y, 1)} kg CO₂-eq`,
                `Elements: ${type.count}`
            ];
        }
    );

    // Create bubble chart
    const bubbleData = types.map(type => ({
        x: type.volume || 0.001,
        y: type.carbon || 0.001,
        r: Math.max(8, Math.min(40, Math.sqrt(type.count) * 5)),
        label: type.name,
        count: type.count
    }));

    createBubbleChart(bubbleData, 'IFC Classes', 'rgba(155, 89, 182, 0.6)', false);
}

/**
 * Update charts for element view
 */
function updateElementCharts() {
    const elements = getElementsFromData(state.detailedResults, state.elementsData);
    const sortedElements = elements
        .filter(e => e.carbon > 0)
        .sort((a, b) => b.carbon - a.carbon);

    if (sortedElements.length === 0) return;

    destroyCharts();

    // Doughnut Chart - Show top 15 individual elements
    const top15Elements = sortedElements.slice(0, 15);
    const otherElements = sortedElements.slice(15);
    const otherCarbon = otherElements.reduce((sum, e) => sum + e.carbon, 0);

    const doughnutLabels = top15Elements.map(e => truncateLabel(e.name, 20));
    const doughnutData = top15Elements.map(e => e.carbon);

    if (otherCarbon > 0) {
        doughnutLabels.push(`Other (${otherElements.length} elements)`);
        doughnutData.push(otherCarbon);
    }

    createDoughnutChart(
        doughnutLabels,
        doughnutData,
        doughnutLabels.length,
        (context) => {
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);

            if (context.dataIndex < top15Elements.length) {
                const elem = top15Elements[context.dataIndex];
                return [
                    `${context.label}`,
                    `${formatNumber(value, 1)} kg CO₂-eq (${percentage}%)`,
                    `Type: ${elem.type}`,
                    `Material: ${truncateLabel(elem.material, 20)}`
                ];
            } else {
                return `Other: ${formatNumber(value, 1)} kg CO₂-eq (${percentage}%)`;
            }
        }
    );

    // Bar Chart - Top 10 Elements
    const top10Elements = sortedElements.slice(0, 10);
    createElementBarChart(top10Elements);

    // Bubble Chart
    createElementBubbleChart(sortedElements);
}

// Helper functions for creating charts

function createDoughnutChart(labels, data, colorCount, tooltipLabel) {
    const doughnutCtx = document.getElementById('doughnutChart').getContext('2d');
    state.charts.doughnut = new Chart(doughnutCtx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: generateColors(colorCount),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { padding: 10, font: { size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        label: tooltipLabel
                    }
                }
            }
        }
    });
}

function createBarChart(labels, data, bgColor, borderColor, tooltipLabel) {
    const barCtx = document.getElementById('barChart').getContext('2d');
    state.charts.bar = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Carbon Impact (kg CO₂-eq)',
                data: data,
                backgroundColor: bgColor,
                borderColor: borderColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: (value) => formatNumber(value, 0) }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: tooltipLabel
                    }
                }
            }
        }
    });
}

function createBubbleChart(data, label, color, useLogScale) {
    const bubbleCtx = document.getElementById('bubbleChart').getContext('2d');
    state.charts.bubble = new Chart(bubbleCtx, {
        type: 'bubble',
        data: {
            datasets: [{
                label: label,
                data: data,
                backgroundColor: color,
                borderColor: color.replace('0.6', '1'),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Volume (m³)' },
                    type: useLogScale ? 'logarithmic' : 'linear',
                    ticks: useLogScale ? {
                        callback: function (value) {
                            if (value === 0.001) return '0';
                            return formatNumber(value, 3);
                        }
                    } : undefined
                },
                y: {
                    title: { display: true, text: 'Carbon Impact (kg CO₂-eq)' },
                    type: useLogScale ? 'logarithmic' : 'linear',
                    ticks: useLogScale ? {
                        callback: function (value) {
                            if (value === 0.001) return '0';
                            return formatNumber(value, 1);
                        }
                    } : undefined
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const point = context.raw;
                            const lines = [];

                            if (label === 'Materials') {
                                lines.push(
                                    `Material: ${truncateLabel(point.label, 30)}`,
                                    `Volume: ${formatNumber(point.x, 2)} m³`,
                                    `Carbon: ${formatNumber(point.y, 1)} kg CO₂-eq`,
                                    `Mass: ${formatNumber(point.mass, 0)} kg`
                                );
                            } else if (label === 'IFC Classes') {
                                lines.push(
                                    `Class: ${point.label}`,
                                    `Elements: ${point.count}`,
                                    `Volume: ${formatNumber(point.x, 2)} m³`,
                                    `Carbon: ${formatNumber(point.y, 1)} kg CO₂-eq`
                                );
                            } else {
                                lines.push(
                                    `Element: ${point.label}`,
                                    `Type: ${point.type}`,
                                    `Material: ${truncateLabel(point.material, 20)}`,
                                    `Volume: ${formatNumber(point.x, 3)} m³`,
                                    `Carbon: ${formatNumber(point.y, 2)} kg CO₂-eq`
                                );
                            }

                            return lines;
                        }
                    }
                }
            }
        }
    });
}

function createElementBarChart(top10Elements) {
    const barCtx = document.getElementById('barChart').getContext('2d');
    state.charts.bar = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: top10Elements.map(e => truncateLabel(e.name, 15)),
            datasets: [{
                label: 'Carbon Impact (kg CO₂-eq)',
                data: top10Elements.map(e => e.carbon),
                backgroundColor: '#2ecc71',
                borderColor: '#27ae60',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: (value) => formatNumber(value, 0) }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (context) => {
                            const elem = top10Elements[context[0].dataIndex];
                            return elem.name;
                        },
                        label: (context) => {
                            const elem = top10Elements[context.dataIndex];
                            return [
                                `Carbon: ${formatNumber(context.parsed.y, 1)} kg CO₂-eq`,
                                `Type: ${elem.type}`,
                                `Material: ${truncateLabel(elem.material, 20)}`
                            ];
                        }
                    }
                }
            }
        }
    });
}

function createElementBubbleChart(sortedElements) {
    let bubbleElements = [];
    const maxBubbles = 100;

    if (sortedElements.length <= maxBubbles) {
        bubbleElements = sortedElements;
    } else {
        bubbleElements = sortedElements.slice(0, maxBubbles - 1);
        const remainingElements = sortedElements.slice(maxBubbles - 1);
        const remainingVolume = remainingElements.reduce((sum, e) => sum + e.volume, 0);
        const remainingCarbon = remainingElements.reduce((sum, e) => sum + e.carbon, 0);

        bubbleElements.push({
            name: `Other (${remainingElements.length} elements)`,
            type: 'Various',
            carbon: remainingCarbon,
            volume: remainingVolume,
            material: 'Various'
        });
    }

    const bubbleData = bubbleElements.map((elem, index) => ({
        x: elem.volume || 0.001,
        y: elem.carbon || 0.001,
        r: Math.max(3, Math.min(25, Math.sqrt(elem.carbon) * 0.5)),
        label: elem.name,
        type: elem.type,
        material: elem.material
    }));

    createBubbleChart(bubbleData, 'Elements', 'rgba(46, 204, 113, 0.6)', true);
} 