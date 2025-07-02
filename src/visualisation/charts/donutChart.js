window.drawDonutChart = function (containerId, data, options = {}) {

    console.log('Drawing donut chart for', containerId, 'with data:', data);

    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Container not found:', containerId);
        return;
    }

    // Destroy existing chart on this canvas if it exists
    const existingChart = Chart.getChart(containerId);
    if (existingChart) {
        console.log('Destroying existing chart for', containerId);
        existingChart.destroy();
    }

    const canvas = container;
    const ctx = canvas.getContext('2d');    // Create a Chart.js donut chart

    // Default to showing center text unless explicitly set to false
    const showCenterText = options.showCenterText !== false;

    // Determine if it's a pie chart (no hole) or donut chart (with hole)
    const chartStyle = options.chartStyle || 'donut';
    const cutoutPercentage = chartStyle === 'pie' ? '0%' : '60%';

    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                data: data.map(d => d.value),
                backgroundColor: options.colors,
                borderColor: 'white',
                borderWidth: 2
            }]
        },
        options: {
            cutout: cutoutPercentage, // Use the determined cutout percentage
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    callbacks: {
                        label: function (context) {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return context.label + ': ' + value + ' (' + percentage + '%)';
                        }
                    }
                },
                customCenterText: {
                    text: function (chart) {
                        const current = chart.data.datasets[0].data[0];
                        const total = chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        return ((current / total) * 100).toFixed(1) + '%';
                    },
                    color: '#000',
                    fontStyle: 'bold',
                    sidePadding: 20,
                    enabled: showCenterText
                }
            }
        },
        plugins: [{
            id: 'customCenterText',
            afterDraw: function (chart) {
                if (chart.config.options.plugins.customCenterText &&
                    chart.config.options.plugins.customCenterText.enabled) {
                    const centerConfig = chart.config.options.plugins.customCenterText;
                    const ctx = chart.ctx;
                    const centerX = chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2;
                    const centerY = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2; ctx.save();
                    // Draw background circle for better visibility
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, chart.innerRadius * 0.8, 0, Math.PI * 2);
                    ctx.fillStyle = 'rgba(78, 152, 150, 0.9)'; // Match the widget background
                    ctx.fill();

                    // Draw the text
                    ctx.font = 'bold 24px Arial';
                    ctx.fillStyle = centerConfig.color;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    const text = typeof centerConfig.text === 'function' ? centerConfig.text(chart) : centerConfig.text;
                    ctx.fillText(text, centerX, centerY);
                    ctx.restore();
                }
            }
        }]
    });
}