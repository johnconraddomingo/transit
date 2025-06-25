window.drawBarChart = function (containerId, data, options = {}) {
    console.log('Drawing bar chart for', containerId, 'with data:', data);

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
        // Destroy existing chart on this canvas if it exists
        const existingChart = Chart.getChart(containerId);
        if (existingChart) {
            console.log('Destroying existing chart for', containerId);
            existingChart.destroy();
        }

        const canvas = container;
        const ctx = canvas.getContext('2d');

        const width = canvas.width || container.clientWidth;
        const height = canvas.height || container.clientHeight;

        console.log('Canvas dimensions:', width, 'x', height);

        ctx.clearRect(0, 0, width, height);

        const barColor = '#4E9896';
        const textColor = '#333333';
        const baselineColor = options.baselineColor || '#CCCCCC';
        const baselineValue = options.baselineValue;

        // Calculate min and max values
        let minValue = Math.min(...data.map(p => parseFloat(p.value)));
        let maxValue = Math.max(...data.map(p => parseFloat(p.value)));

        if (baselineValue !== undefined) {
            minValue = Math.min(minValue, parseFloat(baselineValue));
            maxValue = Math.max(maxValue, parseFloat(baselineValue));
        }

        if (options.isInteger) {
            minValue = Math.max(0, Math.floor(minValue));
            maxValue = Math.ceil(maxValue * 1.2);
        } else {
            const range = maxValue - minValue || 1;
            minValue = Math.max(0, minValue - range * 0.1);
            maxValue = maxValue + range * 0.1;
        }

        if (maxValue === minValue) {
            maxValue = minValue + 1;
        }

        const padding = 40;
        const barPadding = 10;
        const availableWidth = width - padding * 2;
        const barWidth = Math.max(15, (availableWidth / data.length) - barPadding);

        const getY = val => {
            const numVal = typeof val === 'string' ? parseFloat(val) : val;
            if (isNaN(numVal)) {
                console.warn('Invalid value for Y conversion: ' + val);
                return height - padding;
            }
            const normalized = (numVal - minValue) / (maxValue - minValue);
            const availableHeight = height - padding * 2;
            return height - padding - (normalized * availableHeight);
        };

        const getBarX = (i) => padding + i * (barWidth + barPadding) + barPadding / 2;

        // Draw axes
        ctx.strokeStyle = '#888888';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();

        if (baselineValue !== undefined) {
            const y = getY(baselineValue);
            ctx.setLineDash([5, 3]);
            ctx.strokeStyle = baselineColor;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // Draw Y-axis labels
        if (options.isPercentage) {
            drawYAxisLabelsPercentage(ctx, getY, minValue, maxValue, padding, textColor);
        } else if (options.isInteger) {
            drawYAxisLabelsInteger(ctx, getY, minValue, maxValue, padding, textColor);
        } else {
            drawYAxisLabelsFloat(ctx, getY, minValue, maxValue, padding, textColor, options.decimals || 2);
        }

        // Draw bars and labels
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

        // Add tooltip functionality
        canvas.addEventListener('mousemove', function (e) {
            const rect = canvas.getBoundingClientRect();
            const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
            const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height);

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
                const redrawChart = () => drawBarChart(containerId, data, options);
                redrawChart();
                drawTooltip(ctx, foundBar.x, foundBar.y, foundBar.point, width, padding);
            } else {
                canvas.style.cursor = '';
            }
        });

        canvas.addEventListener('mouseleave', function () {
            drawBarChart(containerId, data, options);
        });

    } catch (error) {
        console.error('Error creating bar chart:', error);
    }
}
