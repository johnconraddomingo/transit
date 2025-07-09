window.drawLineGraph = function (canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) return;

    console.log('[Chart Debug]', { canvasId, data, options });

    // Destroy existing chart on this canvas if it exists
    const existingChart = Chart.getChart(canvasId);
    if (existingChart) {
        console.log('Destroying existing chart for', canvasId);
        existingChart.destroy();
    }

    const ctx = canvas.getContext('2d');

    // Make canvas responsive
    const container = canvas.parentElement;
    const containerStyle = window.getComputedStyle(container);
    const containerWidth = parseInt(containerStyle.width, 10);
    const containerHeight = parseInt(containerStyle.height, 10);

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
    if (options.isInteger && maxValue <= 5) {
        minValue = 0;
        maxValue = 5;
    } else if (options.isInteger) {
        const valueRange = maxValue - minValue || 1;
        minValue -= valueRange * 0.2;
        maxValue += valueRange * 0.2;
        minValue = Math.floor(minValue);
        maxValue = Math.ceil(maxValue);
    } else {
        const valueRange = maxValue - minValue || 1;
        minValue -= valueRange * 0.2;
        maxValue += valueRange * 0.2;
    }

    // Axis mapping
    const getX = i => {
        // Handle single data point case - center it horizontally
        if (data.length === 1) {
            return width / 2;
        }
        return padding + (i / (data.length - 1)) * (width - padding * 2);
    };
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
    }

    // Draw line (only if there are multiple points)
    if (data.length > 1) {
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 2;
        ctx.beginPath();
        data.forEach((pt, i) => {
            const x = getX(i), y = getY(pt.value);
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
        ctx.stroke();
    }

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
        drawYAxisLabelsPercentage(ctx, getY, minValue, maxValue, padding, textColor, height);
    } else if (options.isInteger) {
        drawYAxisLabelsInteger(ctx, getY, minValue, maxValue, padding, textColor, height);
    } else {
        drawYAxisLabelsFloat(ctx, getY, minValue, maxValue, padding, textColor, options.decimals || 2, height);
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