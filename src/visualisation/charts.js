// Modern, modular chart renderer for dashboard metrics
// Supports integer, float, and percentage Y-axis labels with smart formatting
// Plots lines, points, and tooltips. Uses options from Python backend.

function drawLineGraph(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) return;

    // Debug: print chart data and options
    console.log('[Chart Debug]', { canvasId, data, options });

    const ctx = canvas.getContext('2d');

    // Make canvas responsive to container size while maintaining aspect ratio
    const container = canvas.parentElement;
    const containerStyle = window.getComputedStyle(container);
    const containerWidth = parseInt(containerStyle.width, 10);
    const containerHeight = parseInt(containerStyle.height, 10);

    // Set canvas dimensions based on container
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.width = containerWidth;
    canvas.height = containerHeight;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    const padding = options.padding || 40;
    const lineColor = options.lineColor || '#4285F4';
    const baselineColor = options.baselineColor || '#CCCCCC';
    const baselineValue = options.baselineValue;
    const axisColor = '#888888';
    const textColor = '#333333';
    const pointRadius = 5;

    // Compute min/max
    let minValue = Math.min(...data.map(p => p.value));
    let maxValue = Math.max(...data.map(p => p.value));
    if (baselineValue !== undefined) {
        minValue = Math.min(minValue, baselineValue);
        maxValue = Math.max(maxValue, baselineValue);
    }
    // For small-range integer charts (max ≤ 5), force Y-axis from 0 to 5
    if (options.isInteger && maxValue <= 5) {
        minValue = 0;
        maxValue = 5;
    } else if (options.isInteger) {
        const valueRange = maxValue - minValue || 1;
        minValue -= valueRange * 0.2;
        maxValue += valueRange * 0.2;
        minValue = Math.floor(minValue); // keep integer steps
        maxValue = Math.ceil(maxValue);
    } else {
        const valueRange = maxValue - minValue || 1;
        minValue -= valueRange * 0.2;
        maxValue += valueRange * 0.2;
    }

    // Axis mapping
    const getX = i => padding + (i / (data.length - 1)) * (width - padding * 2);
    const getY = val => height - padding - ((val - minValue) / (maxValue - minValue)) * (height - padding * 2);

    // Draw axes
    ctx.strokeStyle = axisColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();

    // Draw baseline
    if (baselineValue !== undefined) {
        const y = getY(baselineValue);
        ctx.setLineDash([5, 3]);
        ctx.strokeStyle = baselineColor;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = textColor;
        ctx.font = '10px sans-serif';
        ctx.fillText('Baseline', padding, y - 5);
    }

    // Draw line
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    data.forEach((pt, i) => {
        const x = getX(i), y = getY(pt.value);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Draw points
    data.forEach((pt, i) => {
        const x = getX(i), y = getY(pt.value);
        ctx.fillStyle = lineColor;
        ctx.beginPath();
        ctx.arc(x, y, pointRadius, 0, Math.PI * 2);
        ctx.fill();
    });

    // Draw X-axis labels
    ctx.fillStyle = textColor;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    data.forEach((pt, i) => {
        const x = getX(i);
        ctx.fillText(pt.label, x, height - padding + 15);
    });

    // Draw Y-axis labels
    if (options.isPercentage) {
        drawYAxisLabelsPercentage(ctx, getY, minValue, maxValue, padding, textColor);
    } else if (options.isInteger) {
        drawYAxisLabelsInteger(ctx, getY, minValue, maxValue, padding, textColor);
    } else {
        drawYAxisLabelsFloat(ctx, getY, minValue, maxValue, padding, textColor, options.decimals || 2);
    }

    // Tooltip logic
    canvas.onmousemove = function (e) {
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        let found = null;
        data.forEach((pt, i) => {
            const x = getX(i), y = getY(pt.value);
            if (Math.abs(mx - x) < pointRadius * 1.5 && Math.abs(my - y) < pointRadius * 1.5) {
                found = { x, y, pt };
            }
        });
        canvas.style.cursor = found ? 'pointer' : '';
        ctx.clearRect(0, 0, width, height);
        drawLineGraph(canvasId, data, options); // Redraw
        if (found) {
            drawTooltip(ctx, found.x, found.y, found.pt, width, padding);
        }
    };
    canvas.onmouseleave = function () {
        ctx.clearRect(0, 0, width, height);
        drawLineGraph(canvasId, data, options);
    };
}

function drawYAxisLabelsPercentage(ctx, getY, minValue, maxValue, padding, textColor) {
    ctx.fillStyle = textColor;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    let step = 0.05;
    for (let v = Math.ceil(minValue * 20) / 20; v <= maxValue + 0.0001; v += step) {
        const y = getY(v);
        const label = Math.round(v * 100) + '%';
        ctx.fillText(label, padding - 5, y + 3);
    }
}

function drawYAxisLabelsInteger(ctx, getY, minValue, maxValue, padding, textColor) {
    ctx.fillStyle = textColor;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    let range = maxValue - minValue;
    let step = 1;
    if (range > 20) step = 5;
    if (range > 50) step = 10;
    if (range > 100) step = 20;
    if (range > 250) step = 50;
    if (range > 500) step = 100;
    for (let v = Math.floor(minValue); v <= maxValue + 0.0001; v += step) {
        const y = getY(v);
        const label = Math.round(v);
        ctx.fillText(label, padding - 5, y + 3);
    }
}

function drawYAxisLabelsFloat(ctx, getY, minValue, maxValue, padding, textColor, decimals = 2) {
    ctx.fillStyle = textColor;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    let step = (maxValue - minValue) / 5;
    for (let k = 0; k <= 5; k++) {
        let v = minValue + step * k;
        const y = getY(v);
        const label = decimals === 0 ? Math.round(v).toString() : v.toFixed(decimals);
        ctx.fillText(label, padding - 5, y + 3);
    }
}

function drawTooltip(ctx, x, y, pt, width, padding) {
    const text = pt.label + ': ' + pt.value;
    ctx.save();
    ctx.font = '12px sans-serif';
    const textWidth = ctx.measureText(text).width;
    const boxWidth = textWidth + 16;
    const boxHeight = 28;
    const boxX = Math.min(Math.max(x - boxWidth / 2, padding), width - boxWidth - padding);
    const boxY = y - boxHeight - 10;
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    ctx.strokeStyle = '#888';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 6);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = '#222';
    ctx.textAlign = 'left';
    ctx.fillText(text, boxX + 8, boxY + 18);
    ctx.restore();
}

function drawBarChart(containerId, data, options = {}) {
    console.log('Drawing bar chart for', containerId, 'with data:', data);

    // Instead of clearing and recreating, use the existing canvas
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Container not found:', containerId);
        return;
    }

    if (!data || data.length === 0) {
        console.error('No data provided for bar chart');
        return;
    }

    try {
        // Use the existing canvas element directly
        const canvas = container;
        const ctx = canvas.getContext('2d');

        // Set canvas size
        const width = canvas.width || container.clientWidth;
        const height = canvas.height || container.clientHeight;

        console.log('Canvas dimensions:', width, 'x', height);

        // Clear the canvas
        ctx.clearRect(0, 0, width, height);

        // Set colors
        const barColor = '#4E9896';
        const textColor = '#333333';
        const baselineColor = options.baselineColor || '#CCCCCC';
        const baselineValue = options.baselineValue;

        // Calculate min and max values
        let minValue = Math.min(...data.map(p => parseFloat(p.value)));
        let maxValue = Math.max(...data.map(p => parseFloat(p.value)));

        console.log('Raw min/max:', minValue, maxValue);

        if (baselineValue !== undefined) {
            minValue = Math.min(minValue, parseFloat(baselineValue));
            maxValue = Math.max(maxValue, parseFloat(baselineValue));
        }

        // Add padding to the range
        if (options.isInteger) {
            minValue = Math.max(0, Math.floor(minValue)); // Integer charts start at 0
            maxValue = Math.ceil(maxValue * 1.2);
        } else {
            const range = maxValue - minValue || 1;
            minValue = Math.max(0, minValue - range * 0.1);
            maxValue = maxValue + range * 0.1;
        }

        // Ensure we have a minimum bar height
        if (maxValue === minValue) {
            maxValue = minValue + 1;
        }

        console.log('Adjusted value range:', minValue, 'to', maxValue);

        // Padding and measurements
        const padding = 40;
        const barPadding = 10;
        const availableWidth = width - padding * 2;
        const barWidth = Math.max(15, (availableWidth / data.length) - barPadding);

        // Function to convert value to Y position with safer debug info
        const getY = val => {
            // Ensure the value is a number
            const numVal = typeof val === 'string' ? parseFloat(val) : val;

            // Handle NaN values
            if (isNaN(numVal)) {
                console.warn('Invalid value for Y conversion: ' + val);
                return height - padding; // Return bottom of chart area
            }

            // Use simpler debug logging to avoid string template issues
            console.log('Converting value to Y coordinate:');
            console.log(' - Value type:', typeof val);
            console.log(' - Parsed value:', numVal);
            console.log(' - Min:', minValue, 'Max:', maxValue);

            const normalized = (numVal - minValue) / (maxValue - minValue);
            console.log(' - Normalized (0-1):', normalized);

            const availableHeight = height - padding * 2;
            console.log(' - Available height:', availableHeight);

            const result = height - padding - (normalized * availableHeight);
            console.log(' - Final Y coordinate:', result);

            return result;
        };

        // Function to get X position for a bar
        const getBarX = (i) => padding + i * (barWidth + barPadding) + barPadding / 2;

        // Draw axes
        ctx.strokeStyle = '#888888';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();

        // Draw baseline if provided
        if (baselineValue !== undefined) {
            const y = getY(baselineValue);
            ctx.setLineDash([5, 3]);
            ctx.strokeStyle = baselineColor;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
            ctx.setLineDash([]);

            // Draw baseline label
            ctx.fillStyle = '#666';
            ctx.font = '10px sans-serif';
            ctx.fillText('Baseline', width - padding - 50, y - 5);
        }

        // Draw Y-axis labels
        if (options.isPercentage) {
            drawYAxisLabelsPercentage(ctx, getY, minValue, maxValue, padding, textColor);
        } else if (options.isInteger) {
            drawYAxisLabelsInteger(ctx, getY, minValue, maxValue, padding, textColor);
        } else {
            drawYAxisLabelsFloat(ctx, getY, minValue, maxValue, padding, textColor, options.decimals || 2);
        }

        // Draw bars
        data.forEach((point, i) => {
            // Calculate bar dimensions
            const barX = getBarX(i);
            const value = parseFloat(point.value);
            const y = getY(value);
            const barHeight = Math.max(1, height - padding - y); // Ensure at least 1px height            console.log('Bar', i, ': value=', value, ', y=', y, ', height=', barHeight);

            // Draw bar
            ctx.fillStyle = barColor;
            ctx.beginPath();
            ctx.rect(barX, y, barWidth, barHeight);
            ctx.fill();

            // Draw X-axis label
            ctx.fillStyle = textColor;
            ctx.font = '10px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(point.label, barX + barWidth / 2, height - padding + 15);

            // Draw value on top of bar
            ctx.fillStyle = textColor;
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(value.toString(), barX + barWidth / 2, y - 5);
        });

        // Store reference to draw function for tooltips
        const redrawChart = function () {
            ctx.clearRect(0, 0, width, height);

            // Redraw axes
            ctx.strokeStyle = '#888888';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(padding, padding);
            ctx.lineTo(padding, height - padding);
            ctx.lineTo(width - padding, height - padding);
            ctx.stroke();

            // Redraw baseline
            if (baselineValue !== undefined) {
                const y = getY(baselineValue);
                ctx.setLineDash([5, 3]);
                ctx.strokeStyle = baselineColor;
                ctx.beginPath();
                ctx.moveTo(padding, y);
                ctx.lineTo(width - padding, y);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.fillStyle = '#666';
                ctx.font = '10px sans-serif';
                ctx.fillText('Baseline', width - padding - 50, y - 5);
            }

            // Redraw Y-axis labels
            if (options.isPercentage) {
                drawYAxisLabelsPercentage(ctx, getY, minValue, maxValue, padding, textColor);
            } else if (options.isInteger) {
                drawYAxisLabelsInteger(ctx, getY, minValue, maxValue, padding, textColor);
            } else {
                drawYAxisLabelsFloat(ctx, getY, minValue, maxValue, padding, textColor, options.decimals || 2);
            }

            // Redraw bars
            data.forEach((point, i) => {
                const barX = getBarX(i);
                const value = parseFloat(point.value);
                const y = getY(value);
                const barHeight = Math.max(1, height - padding - y);

                ctx.fillStyle = barColor;
                ctx.beginPath();
                ctx.rect(barX, y, barWidth, barHeight);
                ctx.fill();

                ctx.fillStyle = textColor;
                ctx.font = '10px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(point.label, barX + barWidth / 2, height - padding + 15);

                ctx.fillStyle = textColor;
                ctx.font = '11px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(value.toString(), barX + barWidth / 2, y - 5);
            });
        };

        // Add tooltip functionality
        canvas.addEventListener('mousemove', function (e) {
            const rect = canvas.getBoundingClientRect();
            const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
            const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height);

            // Check if mouse is over any bar
            let foundBar = null;
            data.forEach((point, i) => {
                const barX = getBarX(i);
                const value = parseFloat(point.value);
                const y = getY(value);
                const barHeight = Math.max(1, height - padding - y);

                if (mouseX >= barX && mouseX <= barX + barWidth &&
                    mouseY >= y && mouseY <= y + barHeight) {
                    foundBar = { x: barX + barWidth / 2, y, point };
                }
            });

            if (foundBar) {
                canvas.style.cursor = 'pointer';

                // Redraw chart first
                redrawChart();

                // Then draw tooltip
                const text = foundBar.point.label + ': ' + foundBar.point.value;
                ctx.save();
                ctx.font = '12px sans-serif';
                const textWidth = ctx.measureText(text).width;
                const boxWidth = textWidth + 16;
                const boxHeight = 28;
                const boxX = Math.min(Math.max(foundBar.x - boxWidth / 2, padding), width - boxWidth - padding);
                const boxY = foundBar.y - boxHeight - 10;

                ctx.fillStyle = 'rgba(255,255,255,0.95)';
                ctx.strokeStyle = '#888';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 6);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = '#222';
                ctx.textAlign = 'left';
                ctx.fillText(text, boxX + 8, boxY + 18);
                ctx.restore();
            } else {
                canvas.style.cursor = '';
            }
        });

        canvas.addEventListener('mouseleave', function () {
            redrawChart();
        });

        console.log('Bar chart created successfully for', containerId);
    } catch (error) {
        console.error('Error creating bar chart:', error);
    }
}

function initCharts() {
    try {
        document.querySelectorAll('[data-chart]').forEach(chart => {
            try {
                // Debug info
                console.log('Processing chart:', chart.id);

                // Set proper dimensions for the canvas first
                ensureCanvasDimensions(chart);

                // Parse data and options safely
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
                    return; // Skip this chart
                }

                // Check if this is Deployment Frequency in executive summary
                const metricKey = chart.getAttribute('data-metric-key');
                console.log('Chart metric key:', metricKey, 'Chart ID:', chart.id);

                if (metricKey === 'd_deployment_frequency' && chart.id.includes('executive_')) {
                    console.log("Found deployment frequency chart in executive summary:", chart.id);

                    try {
                        // Draw the bar chart directly on the canvas
                        drawBarChart(chart.id, data, options);
                    } catch (barChartError) {
                        console.error('Error creating bar chart:', barChartError, barChartError.stack);
                    }
                } else {
                    // For all other charts, use the line graph
                    drawLineGraph(chart.id, data, options);
                }
            } catch (chartError) {
                console.error('Error processing chart:', chartError, chartError.stack);
            }
        });
    } catch (error) {
        console.error('Error initializing charts:', error, error.stack);
    }
}

// Helper function to ensure canvas has proper dimensions set
function ensureCanvasDimensions(canvas) {
    const container = canvas.parentElement;
    if (!container) return;

    // Get container dimensions
    const containerStyle = window.getComputedStyle(container);
    const containerWidth = parseInt(containerStyle.width, 10);
    const containerHeight = parseInt(containerStyle.height, 10);

    // Set canvas dimensions to match container
    canvas.style.width = '100%';
    canvas.style.height = '100%';

    // Set explicit width/height properties (crucial for proper rendering)
    if ((!canvas.width || canvas.width < 50) && containerWidth > 0) {
        canvas.width = containerWidth;
    }

    if ((!canvas.height || canvas.height < 50) && containerHeight > 0) {
        canvas.height = containerHeight;
    } console.log('Canvas', canvas.id, 'dimensions set to', canvas.width, 'x', canvas.height);
}

window.addEventListener('load', initCharts);
window.addEventListener('resize', initCharts);

