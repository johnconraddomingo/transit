// Modern, modular chart renderer for dashboard metrics
// Supports integer, float, and percentage Y-axis labels with smart formatting
// Plots lines, points, and tooltips. Uses options from Python backend.

function drawLineGraph(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) return;

    // Debug: print chart data and options
    console.log('[Chart Debug]', { canvasId, data, options });

    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.clientWidth;
    const height = canvas.height = canvas.clientHeight;
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

function initCharts() {
    document.querySelectorAll('[data-chart]').forEach(chart => {
        const data = JSON.parse(chart.getAttribute('data-chart') || '[]');
        const options = JSON.parse(chart.getAttribute('data-options') || '{}');
        drawLineGraph(chart.id, data, options);
    });
}

window.addEventListener('load', initCharts);
window.addEventListener('resize', initCharts);

