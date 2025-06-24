window.initCharts = function () {
    try {
        document.querySelectorAll('[data-chart]').forEach(chart => {
            try {
                console.log('Processing chart:', chart.id);
                ensureCanvasDimensions(chart);

                let data = [];
                let options = {};

                try {
                    const dataStr = chart.getAttribute('data-chart');
                    const optionsStr = chart.getAttribute('data-options');

                    console.log('Raw data-chart:', dataStr);
                    console.log('Raw data-options:', optionsStr);

                    data = JSON.parse(dataStr || '[]');
                    options = JSON.parse(optionsStr || '{}');

                    console.log('Parsed data:', data);
                    console.log('Parsed options:', options);
                } catch (parseError) {
                    console.error('Error parsing chart data/options:', parseError);
                    return;
                }

                const chartType = chart.getAttribute('data-type');
                const metricKey = chart.getAttribute('data-metric-key');
                console.log('Chart type:', chartType, 'Chart metric key:', metricKey, 'Chart ID:', chart.id);

                if (chartType === 'donut') {
                    console.log("Found donut chart:", chart.id);
                    try {
                        drawDonutChart(chart.id, data, options);
                    } catch (donutChartError) {
                        console.error('Error creating donut chart:', donutChartError, donutChartError.stack);
                    }
                } else {
                    const isDeploymentFrequencyExecutive =
                        (chart.id.includes('executive_') && chart.id.includes('deployment_frequency')) ||
                        (metricKey === 'd_deployment_frequency' && chart.id.includes('executive_'));

                    if (isDeploymentFrequencyExecutive) {
                        console.log("Found deployment frequency chart in executive summary:", chart.id);
                        try {
                            drawBarChart(chart.id, data, options);
                        } catch (barChartError) {
                            console.error('Error creating bar chart:', barChartError, barChartError.stack);
                        }
                    } else {
                        drawLineGraph(chart.id, data, options);
                    }
                }
            } catch (chartError) {
                console.error('Error processing chart:', chartError, chartError.stack);
            }
        });
    } catch (error) {
        console.error('Error initializing charts:', error, error.stack);
    }
}

function drawDonutChart(chartId, data, options) {
    const canvas = document.getElementById(chartId);
    const ctx = canvas.getContext('2d');    // Create a Chart.js donut chart
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
            cutout: '60%',
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
                    sidePadding: 20
                }
            }
        },
        plugins: [{
            id: 'customCenterText',
            afterDraw: function (chart) {
                if (chart.config.options.plugins.customCenterText) {
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

window.addEventListener('load', initCharts);
window.addEventListener('resize', initCharts);
