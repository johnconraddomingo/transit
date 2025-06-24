// Common utilities for drawing chart axes and labels

window.drawYAxisLabelsPercentage = function (ctx, getY, minValue, maxValue, padding, textColor) {
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

window.drawYAxisLabelsInteger = function (ctx, getY, minValue, maxValue, padding, textColor) {
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

window.drawYAxisLabelsFloat = function (ctx, getY, minValue, maxValue, padding, textColor, decimals = 2) {
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

window.ensureCanvasDimensions = function (canvas) {
    const container = canvas.parentElement;
    if (!container) return;

    const containerStyle = window.getComputedStyle(container);
    const containerWidth = parseInt(containerStyle.width, 10);
    const containerHeight = parseInt(containerStyle.height, 10);

    canvas.style.width = '100%';
    canvas.style.height = '100%';

    if ((!canvas.width || canvas.width < 50) && containerWidth > 0) {
        canvas.width = containerWidth;
    }

    if ((!canvas.height || canvas.height < 50) && containerHeight > 0) {
        canvas.height = containerHeight;
    }
    console.log('Canvas', canvas.id, 'dimensions set to', canvas.width, 'x', canvas.height);
}
