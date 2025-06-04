// Function to draw a line graph using Canvas
function drawLineGraph(canvasId, data, options) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) return;

    var ctx = canvas.getContext('2d');
    var width = canvas.clientWidth;
    var height = canvas.clientHeight;

    ctx.clearRect(0, 0, width, height);

    options = options || {};
    var padding = options.padding || 40;
    var lineColor = options.lineColor || '#4285F4';
    var baselineColor = options.baselineColor || '#CCCCCC';
    var baselineValue = options.baselineValue;
    var axisColor = '#888888';
    var textColor = '#333333';

    var minValue = Infinity;
    var maxValue = -Infinity;

    data.forEach(point => {
        if (point.value < minValue) minValue = point.value;
        if (point.value > maxValue) maxValue = point.value;
    });

    if (baselineValue !== undefined) {
        if (baselineValue < minValue) minValue = baselineValue;
        if (baselineValue > maxValue) maxValue = baselineValue;
    }

    var valueRange = maxValue - minValue;
    minValue -= valueRange * 0.1;
    maxValue += valueRange * 0.1;

    function getX(index) {
        return padding + (index / (data.length - 1)) * (width - padding * 2);
    }

    function getY(value) {
        return height - padding - ((value - minValue) / (maxValue - minValue)) * (height - padding * 2);
    }

    // Axes
    ctx.strokeStyle = axisColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();

    // Baseline
    if (baselineValue !== undefined) {
        var baselineY = getY(baselineValue);
        ctx.strokeStyle = baselineColor;
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 3]);
        ctx.beginPath();
        ctx.moveTo(padding, baselineY);
        ctx.lineTo(width - padding, baselineY);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = textColor;
        ctx.font = '10px sans-serif';
        ctx.fillText('Baseline', padding, baselineY - 5);
    }

    // Line
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    data.forEach((point, i) => {
        var x = getX(i);
        var y = getY(point.value);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Points and X-axis labels
    data.forEach((point, i) => {
        var x = getX(i);
        var y = getY(point.value);
        ctx.fillStyle = lineColor;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = textColor;
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(point.label, x, height - padding + 15);
    });

    // Y-axis labels with cleaner formatting
    ctx.fillStyle = textColor;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    for (var k = 0; k <= 5; k++) {
        var value = minValue + (maxValue - minValue) * (k / 5);
        var y = getY(value);

        var rounded = Math.round(value * 10) / 10;
        var formatted = options.isPercentage
            ? Math.round(value * 100) + '%'
            : Math.round(value).toString();

        ctx.fillText(formatted, padding - 5, y + 3);
    }
}

// Auto-initialize charts
function initCharts() {
    var charts = document.querySelectorAll('[data-chart]');
    charts.forEach(chartElement => {
        var chartData = JSON.parse(chartElement.getAttribute('data-chart'));
        var chartOptions = JSON.parse(chartElement.getAttribute('data-options') || '{}');
        var canvas = document.getElementById(chartElement.id);
        var rect = canvas.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        drawLineGraph(chartElement.id, chartData, chartOptions);
    });
}

window.addEventListener('load', initCharts);
window.addEventListener('resize', initCharts);
