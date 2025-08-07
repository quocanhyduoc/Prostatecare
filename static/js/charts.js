/**
 * Chart.js Integration for Prostate Cancer Patient Management System
 * Handles blood test data visualization (PSA and Testosterone levels)
 */

// Chart configuration and utilities
const ChartConfig = {
    // Medical color scheme
    colors: {
        primary: '#2E7D9A',
        secondary: '#4CAF50',
        accent: '#FF9800',
        success: '#66BB6A',
        danger: '#f44336',
        warning: '#ff9800',
        info: '#2196f3',
        light: '#f8f9fa',
        dark: '#343a40'
    },
    
    // Default chart options
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    font: {
                        family: 'Roboto, sans-serif',
                        size: 12,
                        weight: '500'
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(33, 37, 41, 0.95)',
                titleColor: '#ffffff',
                bodyColor: '#ffffff',
                borderColor: '#2E7D9A',
                borderWidth: 1,
                cornerRadius: 8,
                titleFont: {
                    family: 'Roboto, sans-serif',
                    size: 14,
                    weight: '600'
                },
                bodyFont: {
                    family: 'Roboto, sans-serif',
                    size: 13
                },
                displayColors: true,
                usePointStyle: true
            }
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                    borderColor: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    font: {
                        family: 'Roboto, sans-serif',
                        size: 11
                    },
                    color: '#212121'
                }
            },
            y: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                    borderColor: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    font: {
                        family: 'Roboto, sans-serif',
                        size: 11
                    },
                    color: '#212121'
                }
            }
        },
        elements: {
            point: {
                radius: 6,
                hoverRadius: 8,
                borderWidth: 2,
                hoverBorderWidth: 3
            },
            line: {
                borderWidth: 3,
                tension: 0.1
            }
        },
        interaction: {
            intersect: false,
            mode: 'index'
        }
    }
};

/**
 * Create PSA and Testosterone blood test chart
 * @param {string} canvasId - Canvas element ID
 * @param {Object} data - Chart data containing dates and test values
 */
function createPSAChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas with ID '${canvasId}' not found`);
        return;
    }

    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.psaChart && typeof window.psaChart.destroy === 'function') {
        window.psaChart.destroy();
    }

    // Prepare datasets
    const datasets = [];
    
    // Free PSA dataset
    if (data.free_psa && data.free_psa.some(val => val !== null)) {
        datasets.push({
            label: 'FREE PSA (ng/mL)',
            data: data.free_psa,
            borderColor: ChartConfig.colors.info,
            backgroundColor: ChartConfig.colors.info + '20',
            fill: false,
            tension: 0.1,
            pointBackgroundColor: ChartConfig.colors.info,
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: ChartConfig.colors.info
        });
    }
    
    // Total PSA dataset
    if (data.total_psa && data.total_psa.some(val => val !== null)) {
        datasets.push({
            label: 'TOTAL PSA (ng/mL)',
            data: data.total_psa,
            borderColor: ChartConfig.colors.primary,
            backgroundColor: ChartConfig.colors.primary + '20',
            fill: false,
            tension: 0.1,
            pointBackgroundColor: ChartConfig.colors.primary,
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: ChartConfig.colors.primary
        });
    }
    
    // Testosterone dataset (with secondary y-axis)
    if (data.testosterone && data.testosterone.some(val => val !== null)) {
        datasets.push({
            label: 'Testosterone (ng/dL)',
            data: data.testosterone,
            borderColor: ChartConfig.colors.secondary,
            backgroundColor: ChartConfig.colors.secondary + '20',
            fill: false,
            tension: 0.1,
            yAxisID: 'y1',
            pointBackgroundColor: ChartConfig.colors.secondary,
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: ChartConfig.colors.secondary
        });
    }

    // Chart configuration
    const config = {
        type: 'line',
        data: {
            labels: data.dates.map(date => {
                const d = new Date(date);
                return d.toLocaleDateString('vi-VN', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                });
            }),
            datasets: datasets
        },
        options: {
            ...ChartConfig.defaultOptions,
            plugins: {
                ...ChartConfig.defaultOptions.plugins,
                title: {
                    display: true,
                    text: 'Biểu đồ theo dõi xét nghiệm máu',
                    font: {
                        family: 'Roboto, sans-serif',
                        size: 16,
                        weight: '600'
                    },
                    color: ChartConfig.colors.dark,
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                },
                tooltip: {
                    ...ChartConfig.defaultOptions.plugins.tooltip,
                    callbacks: {
                        title: function(context) {
                            return 'Ngày: ' + context[0].label;
                        },
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(2);
                                if (context.dataset.label.includes('PSA')) {
                                    label += ' ng/mL';
                                } else if (context.dataset.label.includes('Testosterone')) {
                                    label += ' ng/dL';
                                }
                            } else {
                                label += 'Không có dữ liệu';
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ...ChartConfig.defaultOptions.scales.x,
                    title: {
                        display: true,
                        text: 'Ngày xét nghiệm',
                        font: {
                            family: 'Roboto, sans-serif',
                            size: 12,
                            weight: '500'
                        },
                        color: ChartConfig.colors.dark
                    }
                },
                y: {
                    ...ChartConfig.defaultOptions.scales.y,
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'PSA (ng/mL)',
                        font: {
                            family: 'Roboto, sans-serif',
                            size: 12,
                            weight: '500'
                        },
                        color: ChartConfig.colors.primary
                    },
                    beginAtZero: true
                },
                // Secondary y-axis for testosterone
                y1: {
                    ...ChartConfig.defaultOptions.scales.y,
                    type: 'linear',
                    display: datasets.some(d => d.yAxisID === 'y1'),
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Testosterone (ng/dL)',
                        font: {
                            family: 'Roboto, sans-serif',
                            size: 12,
                            weight: '500'
                        },
                        color: ChartConfig.colors.secondary
                    },
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    };

    // Create the chart
    try {
        window.psaChart = new Chart(ctx, config);
        
        // Add reference lines for PSA normal ranges
        addPSAReferenceLines(window.psaChart);
        
    } catch (error) {
        console.error('Error creating PSA chart:', error);
        showChartError(canvasId, 'Không thể tạo biểu đồ. Vui lòng thử lại.');
    }
}

/**
 * Add reference lines for PSA normal ranges
 * @param {Chart} chart - Chart.js instance
 */
function addPSAReferenceLines(chart) {
    const plugin = {
        id: 'psaReferenceLines',
        beforeDraw: (chart) => {
            const ctx = chart.ctx;
            const chartArea = chart.chartArea;
            const yScale = chart.scales.y;
            
            // PSA reference values
            const normalPSA = 4.0; // ng/mL
            const highPSA = 10.0; // ng/mL
            
            ctx.save();
            
            // Normal PSA line (4.0 ng/mL)
            const normalY = yScale.getPixelForValue(normalPSA);
            if (normalY >= chartArea.top && normalY <= chartArea.bottom) {
                ctx.strokeStyle = ChartConfig.colors.warning;
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(chartArea.left, normalY);
                ctx.lineTo(chartArea.right, normalY);
                ctx.stroke();
                
                // Add label
                ctx.fillStyle = ChartConfig.colors.warning;
                ctx.font = '12px Roboto, sans-serif';
                ctx.fillText('PSA bình thường (4.0)', chartArea.left + 10, normalY - 5);
            }
            
            // High PSA line (10.0 ng/mL)
            const highY = yScale.getPixelForValue(highPSA);
            if (highY >= chartArea.top && highY <= chartArea.bottom) {
                ctx.strokeStyle = ChartConfig.colors.danger;
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(chartArea.left, highY);
                ctx.lineTo(chartArea.right, highY);
                ctx.stroke();
                
                // Add label
                ctx.fillStyle = ChartConfig.colors.danger;
                ctx.font = '12px Roboto, sans-serif';
                ctx.fillText('PSA cao (10.0)', chartArea.left + 10, highY - 5);
            }
            
            ctx.restore();
        }
    };
    
    Chart.register(plugin);
}

/**
 * Show error message when chart cannot be created
 * @param {string} canvasId - Canvas element ID
 * @param {string} message - Error message to display
 */
function showChartError(canvasId, message) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const container = canvas.parentElement;
    container.innerHTML = `
        <div class="alert alert-danger text-center" role="alert">
            <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
            <h6>Lỗi tạo biểu đồ</h6>
            <p class="mb-0">${message}</p>
        </div>
    `;
}

/**
 * Create a simple trend chart for dashboard
 * @param {string} canvasId - Canvas element ID
 * @param {Object} data - Simplified chart data
 * @param {string} title - Chart title
 */
function createTrendChart(canvasId, data, title) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas with ID '${canvasId}' not found`);
        return;
    }

    const ctx = canvas.getContext('2d');
    
    const config = {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: title,
                data: data.values,
                borderColor: ChartConfig.colors.primary,
                backgroundColor: ChartConfig.colors.primary + '20',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false,
                    beginAtZero: true
                }
            },
            elements: {
                point: {
                    radius: 0
                }
            },
            interaction: {
                intersect: false
            }
        }
    };

    try {
        new Chart(ctx, config);
    } catch (error) {
        console.error('Error creating trend chart:', error);
    }
}

/**
 * Utility function to format dates for Vietnamese locale
 * @param {string} dateString - Date string to format
 * @returns {string} Formatted date string
 */
function formatVietnameseDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

/**
 * Calculate PSA ratio and add warning indicators
 * @param {number} freePSA - Free PSA value
 * @param {number} totalPSA - Total PSA value
 * @returns {Object} PSA ratio and risk assessment
 */
function calculatePSARatio(freePSA, totalPSA) {
    if (!freePSA || !totalPSA || totalPSA === 0) {
        return { ratio: null, risk: 'unknown' };
    }
    
    const ratio = (freePSA / totalPSA) * 100;
    let risk = 'low';
    
    if (ratio < 10) {
        risk = 'high';
    } else if (ratio < 15) {
        risk = 'moderate';
    }
    
    return { ratio: ratio.toFixed(1), risk };
}

/**
 * Initialize all charts on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Auto-initialize any charts marked with data attributes
    const chartElements = document.querySelectorAll('[data-chart-type]');
    
    chartElements.forEach(element => {
        const chartType = element.getAttribute('data-chart-type');
        const dataUrl = element.getAttribute('data-chart-url');
        
        if (chartType === 'psa' && dataUrl) {
            fetch(dataUrl)
                .then(response => response.json())
                .then(data => {
                    createPSAChart(element.id, data);
                })
                .catch(error => {
                    console.error('Error loading chart data:', error);
                    showChartError(element.id, 'Không thể tải dữ liệu biểu đồ.');
                });
        }
    });
});

/**
 * Resize all charts when window is resized
 */
window.addEventListener('resize', function() {
    // Chart.js automatically handles resize for responsive charts
    // This is here for any custom resize logic if needed
});

// Export functions for global access
window.ChartUtils = {
    createPSAChart,
    createTrendChart,
    formatVietnameseDate,
    calculatePSARatio,
    showChartError
};
