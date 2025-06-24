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


window.addEventListener('load', initCharts);
window.addEventListener('resize', initCharts);
