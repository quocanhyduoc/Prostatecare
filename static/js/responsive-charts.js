/**
 * Responsive and Interactive Blood Test Charts
 * Optimized for mobile and desktop viewing
 */

// Global chart configuration for responsiveness
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;
Chart.defaults.plugins.legend.display = true;
Chart.defaults.plugins.tooltip.enabled = true;

// Mobile detection
function isMobile() {
    return window.innerWidth <= 768;
}

// Common responsive options
function getResponsiveOptions(title) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            intersect: false,
            mode: 'index'
        },
        plugins: {
            title: {
                display: true,
                text: title,
                font: {
                    size: isMobile() ? 14 : 16,
                    weight: 'bold'
                },
                padding: {
                    top: 10,
                    bottom: 20
                }
            },
            legend: {
                display: true,
                position: isMobile() ? 'bottom' : 'top',
                labels: {
                    usePointStyle: true,
                    padding: isMobile() ? 15 : 20,
                    font: {
                        size: isMobile() ? 11 : 12
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: '#007bff',
                borderWidth: 1,
                cornerRadius: 8,
                displayColors: true,
                padding: 12,
                titleFont: {
                    size: isMobile() ? 12 : 14
                },
                bodyFont: {
                    size: isMobile() ? 11 : 13
                },
                callbacks: {
                    title: function(context) {
                        return 'Ngày: ' + context[0].label;
                    },
                    label: function(context) {
                        const value = context.parsed.y;
                        const unit = context.dataset.label.includes('PSA') ? ' ng/mL' : ' ng/dL';
                        return context.dataset.label + ': ' + value.toFixed(2) + unit;
                    }
                }
            }
        },
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: 'Ngày xét nghiệm',
                    font: {
                        size: isMobile() ? 11 : 12
                    }
                },
                ticks: {
                    font: {
                        size: isMobile() ? 10 : 11
                    },
                    maxRotation: isMobile() ? 45 : 0,
                    maxTicksLimit: isMobile() ? 5 : 8
                },
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
            y: {
                display: true,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Giá trị',
                    font: {
                        size: isMobile() ? 11 : 12
                    }
                },
                ticks: {
                    font: {
                        size: isMobile() ? 10 : 11
                    }
                },
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            }
        }
    };
}

// PSA Chart with enhanced interactivity
function createPSAChart(canvasId, bloodTests) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !bloodTests || bloodTests.length === 0) return null;

    // Process data
    const dates = bloodTests.map(test => new Date(test.test_date).toLocaleDateString('vi-VN'));
    const freePSA = bloodTests.map(test => test.free_psa || 0);
    const totalPSA = bloodTests.map(test => test.total_psa || 0);
    const psaRatio = bloodTests.map(test => test.psa_ratio || 0);

    const data = {
        labels: dates,
        datasets: [
            {
                label: 'PSA tự do',
                data: freePSA,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1,
                pointRadius: isMobile() ? 4 : 5,
                pointHoverRadius: isMobile() ? 6 : 8,
                pointBackgroundColor: '#28a745',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            },
            {
                label: 'PSA tổng',
                data: totalPSA,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1,
                pointRadius: isMobile() ? 4 : 5,
                pointHoverRadius: isMobile() ? 6 : 8,
                pointBackgroundColor: '#dc3545',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            },
            {
                label: 'Tỷ lệ PSA (%)',
                data: psaRatio,
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1,
                pointRadius: isMobile() ? 4 : 5,
                pointHoverRadius: isMobile() ? 6 : 8,
                pointBackgroundColor: '#ffc107',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                yAxisID: 'y1'
            }
        ]
    };

    const options = getResponsiveOptions('Biểu đồ PSA theo thời gian');
    
    // Add second y-axis for PSA ratio
    options.scales.y1 = {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
            display: true,
            text: 'Tỷ lệ PSA (%)',
            font: {
                size: isMobile() ? 11 : 12
            }
        },
        ticks: {
            font: {
                size: isMobile() ? 10 : 11
            }
        },
        grid: {
            drawOnChartArea: false
        }
    };

    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: options
    });
}

// Testosterone Chart
function createTestosteroneChart(canvasId, bloodTests) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !bloodTests || bloodTests.length === 0) return null;

    // Filter tests with testosterone data
    const testsWithTestosterone = bloodTests.filter(test => test.testosterone != null);
    if (testsWithTestosterone.length === 0) return null;

    const dates = testsWithTestosterone.map(test => new Date(test.test_date).toLocaleDateString('vi-VN'));
    const testosterone = testsWithTestosterone.map(test => test.testosterone);

    const data = {
        labels: dates,
        datasets: [{
            label: 'Testosterone',
            data: testosterone,
            borderColor: '#007bff',
            backgroundColor: 'rgba(0, 123, 255, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.1,
            pointRadius: isMobile() ? 4 : 5,
            pointHoverRadius: isMobile() ? 6 : 8,
            pointBackgroundColor: '#007bff',
            pointBorderColor: '#fff',
            pointBorderWidth: 2
        }]
    };

    const options = getResponsiveOptions('Biểu đồ Testosterone theo thời gian');
    options.scales.y.title.text = 'Testosterone (ng/dL)';

    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: options
    });
}

// Combined Overview Chart
function createOverviewChart(canvasId, bloodTests) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !bloodTests || bloodTests.length === 0) return null;

    const dates = bloodTests.map(test => new Date(test.test_date).toLocaleDateString('vi-VN'));
    const totalPSA = bloodTests.map(test => test.total_psa || 0);

    const data = {
        labels: dates,
        datasets: [{
            label: 'PSA tổng',
            data: totalPSA,
            backgroundColor: function(context) {
                const value = context.parsed?.y;
                if (value > 10) return 'rgba(220, 53, 69, 0.8)'; // Red for high
                if (value > 4) return 'rgba(255, 193, 7, 0.8)';   // Yellow for elevated
                return 'rgba(40, 167, 69, 0.8)';                  // Green for normal
            },
            borderColor: function(context) {
                const value = context.parsed?.y;
                if (value > 10) return '#dc3545';
                if (value > 4) return '#ffc107';
                return '#28a745';
            },
            borderWidth: 2,
            borderRadius: 4,
            borderSkipped: false
        }]
    };

    const options = getResponsiveOptions('Tổng quan PSA');
    options.scales.y.title.text = 'PSA (ng/mL)';
    
    // Add reference lines
    options.plugins.annotation = {
        annotations: {
            normalLine: {
                type: 'line',
                yMin: 4,
                yMax: 4,
                borderColor: '#ffc107',
                borderWidth: 2,
                borderDash: [5, 5],
                label: {
                    display: true,
                    content: 'Ngưỡng bình thường (4.0)',
                    position: 'end'
                }
            },
            highLine: {
                type: 'line',
                yMin: 10,
                yMax: 10,
                borderColor: '#dc3545',
                borderWidth: 2,
                borderDash: [5, 5],
                label: {
                    display: true,
                    content: 'Ngưỡng cao (10.0)',
                    position: 'end'
                }
            }
        }
    };

    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: options
    });
}

// Chart container management
function createChartContainer(chartId, title) {
    return `
        <div class="chart-container mb-4">
            <div class="chart-header d-flex justify-content-between align-items-center mb-3">
                <h6 class="chart-title mb-0">${title}</h6>
                <div class="chart-controls">
                    <button class="btn btn-sm btn-outline-secondary" onclick="toggleChartFullscreen('${chartId}')">
                        <i class="fas fa-expand"></i>
                    </button>
                </div>
            </div>
            <div class="chart-wrapper position-relative">
                <canvas id="${chartId}" class="blood-test-chart"></canvas>
            </div>
        </div>
    `;
}

// Fullscreen toggle
function toggleChartFullscreen(chartId) {
    const container = document.getElementById(chartId).closest('.chart-container');
    container.classList.toggle('chart-fullscreen');
    
    // Trigger chart resize
    setTimeout(() => {
        const chart = Chart.getChart(chartId);
        if (chart) {
            chart.resize();
        }
    }, 100);
}

// Responsive handling
function handleResize() {
    Chart.helpers.each(Chart.instances, function(chart) {
        chart.resize();
    });
}

// Initialize responsive behavior
window.addEventListener('resize', debounce(handleResize, 250));

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for global use
window.BloodTestCharts = {
    createPSAChart,
    createTestosteroneChart,
    createOverviewChart,
    createChartContainer,
    toggleChartFullscreen
};