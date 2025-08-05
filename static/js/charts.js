// Utility functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function formatNumber(value, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

// Charts and visualizations

let charts = {};

document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadPriceAnalysis();
});

function initializeCharts() {
    // Common chart options
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: false,
                grid: {
                    color: 'rgba(0,0,0,0.1)'
                }
            },
            x: {
                grid: {
                    color: 'rgba(0,0,0,0.1)'
                }
            }
        },
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        }
    };

    // Price Trend Chart
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    charts.priceChart = new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Gold Price (USD)',
                data: [],
                borderColor: '#FFD700',
                backgroundColor: 'rgba(255, 215, 0, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: {
                    ...commonOptions.scales.y,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });

    // Correlation Chart
    const corrCtx = document.getElementById('correlationChart').getContext('2d');
    charts.correlationChart = new Chart(corrCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Correlation with USD',
                data: [],
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                    '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: {
                    beginAtZero: true,
                    max: 1,
                    min: -1
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // Volume Chart
    const volumeCtx = document.getElementById('volumeChart').getContext('2d');
    charts.volumeChart = new Chart(volumeCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Trading Volume',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: commonOptions
    });

    // Distribution Chart
    const distCtx = document.getElementById('distributionChart').getContext('2d');
    charts.distributionChart = new Chart(distCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Frequency',
                data: [],
                backgroundColor: 'rgba(153, 102, 255, 0.6)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: commonOptions
    });

    // Load data for charts
    loadHistoricalData();
    loadCorrelationData();
}

function loadHistoricalData() {
    fetch('/api/historical-data')
        .then(response => response.json())
        .then(data => {
            // Update price chart
            charts.priceChart.data.labels = data.dates.slice(-90); // Last 90 days
            charts.priceChart.data.datasets[0].data = data.prices.slice(-90);
            charts.priceChart.update();

            // Update volume chart
            charts.volumeChart.data.labels = data.dates.slice(-30); // Last 30 days
            charts.volumeChart.data.datasets[0].data = data.volume.slice(-30);
            charts.volumeChart.update();

            // Update distribution chart
            updateDistributionChart(data.prices);
        })
        .catch(error => {
            console.error('Error loading historical data:', error);
            showAlert('Error loading historical data', 'warning');
        });
}

function loadCorrelationData() {
    fetch('/api/correlation-data')
        .then(response => response.json())
        .then(data => {
            const currencies = Object.keys(data);
            const correlations = Object.values(data);

            charts.correlationChart.data.labels = currencies;
            charts.correlationChart.data.datasets[0].data = correlations;
            charts.correlationChart.update();
        })
        .catch(error => {
            console.error('Error loading correlation data:', error);
        });
}

function loadPriceAnalysis() {
    fetch('/api/price-analysis')
        .then(response => response.json())
        .then(data => {
            // Update price overview cards
            document.getElementById('currentPriceCard').textContent = formatCurrency(data.current_price);
            document.getElementById('priceChange24h').textContent = 
                (data.price_change_24h >= 0 ? '+' : '') + formatCurrency(data.price_change_24h);
            document.getElementById('volatility').textContent = formatNumber(data.volatility, 2);
            document.getElementById('avgPrice30d').textContent = formatCurrency(data.avg_price_30d);

            // Update card colors based on price change
            const changeCard = document.getElementById('priceChange24h').closest('.info-card');
            changeCard.className = data.price_change_24h >= 0 ? 
                'info-card bg-success' : 'info-card bg-danger';
        })
        .catch(error => {
            console.error('Error loading price analysis:', error);
        });
}

function updateDistributionChart(prices) {
    // Create histogram data
    const bins = 20;
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const binSize = (max - min) / bins;
    
    const histogram = new Array(bins).fill(0);
    const labels = [];
    
    for (let i = 0; i < bins; i++) {
        labels.push(`$${(min + i * binSize).toFixed(0)}-$${(min + (i + 1) * binSize).toFixed(0)}`);
    }
    
    prices.forEach(price => {
        const binIndex = Math.min(Math.floor((price - min) / binSize), bins - 1);
        histogram[binIndex]++;
    });
    
    charts.distributionChart.data.labels = labels;
    charts.distributionChart.data.datasets[0].data = histogram;
    charts.distributionChart.update();
}

// Chart period controls
document.addEventListener('click', function(e) {
    if (e.target.matches('[data-period]')) {
        const period = parseInt(e.target.getAttribute('data-period'));
        updateChartPeriod(period);
        
        // Update active button
        document.querySelectorAll('[data-period]').forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
    }
});

function updateChartPeriod(days) {
    fetch('/api/historical-data')
        .then(response => response.json())
        .then(data => {
            charts.priceChart.data.labels = data.dates.slice(-days);
            charts.priceChart.data.datasets[0].data = data.prices.slice(-days);
            charts.priceChart.update();
        });
}
