// Common utilities for drawing chart axes and labels

window.drawYAxisLabelsPercentage = function (ctx, getY, minValue, maxValue, padding, textColor, chartHeight) {
    ctx.fillStyle = textColor;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';

    // Calculate optimal number of labels based on chart height
    const availableHeight = (chartHeight || ctx.canvas.height) - (padding * 2);
    const minLabelSpacing = 25; // Minimum pixels between labels
    const maxLabels = Math.floor(availableHeight / minLabelSpacing);
    const targetLabels = Math.min(Math.max(maxLabels, 3), 8); // Between 3-8 labels

    const range = maxValue - minValue;
    let step = range / (targetLabels - 1);

    // Round step to nice values for percentages
    const niceSteps = [0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5];
    step = niceSteps.find(s => s >= step) || Math.ceil(step * 20) / 20;

    for (let v = Math.ceil(minValue / step) * step; v <= maxValue + 0.0001; v += step) {
        const y = getY(v);
        const label = Math.round(v * 100) + '%';
        ctx.fillText(label, padding - 5, y + 3);
    }
}

window.drawYAxisLabelsInteger = function (ctx, getY, minValue, maxValue, padding, textColor, chartHeight) {
    ctx.fillStyle = textColor;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';

    // Calculate optimal number of labels based on chart height
    const availableHeight = (chartHeight || ctx.canvas.height) - (padding * 2);
    const minLabelSpacing = 25; // Minimum pixels between labels
    const maxLabels = Math.floor(availableHeight / minLabelSpacing);
    const targetLabels = Math.min(Math.max(maxLabels, 3), 10); // Between 3-10 labels

    let range = maxValue - minValue;
    let step = range / (targetLabels - 1);

    // Round step to nice integer values
    if (step <= 1) step = 1;
    else if (step <= 2) step = 2;
    else if (step <= 5) step = 5;
    else if (step <= 10) step = 10;
    else if (step <= 20) step = 20;
    else if (step <= 25) step = 25;
    else if (step <= 50) step = 50;
    else if (step <= 100) step = 100;
    else if (step <= 200) step = 200;
    else if (step <= 250) step = 250;
    else if (step <= 500) step = 500;
    else step = Math.ceil(step / 100) * 100;

    for (let v = Math.ceil(minValue / step) * step; v <= maxValue + 0.0001; v += step) {
        const y = getY(v);
        const label = Math.round(v);
        ctx.fillText(label, padding - 5, y + 3);
    }
}

window.drawYAxisLabelsFloat = function (ctx, getY, minValue, maxValue, padding, textColor, decimals = 2, chartHeight) {
    ctx.fillStyle = textColor;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';

    // Calculate optimal number of labels based on chart height
    const availableHeight = (chartHeight || ctx.canvas.height) - (padding * 2);
    const minLabelSpacing = 25; // Minimum pixels between labels
    const maxLabels = Math.floor(availableHeight / minLabelSpacing);
    const targetLabels = Math.min(Math.max(maxLabels, 3), 8); // Between 3-8 labels

    let step = (maxValue - minValue) / (targetLabels - 1);

    // Round step to a nice value
    const magnitude = Math.pow(10, Math.floor(Math.log10(step)));
    const normalizedStep = step / magnitude;
    let niceStep;
    if (normalizedStep <= 1) niceStep = 1;
    else if (normalizedStep <= 2) niceStep = 2;
    else if (normalizedStep <= 5) niceStep = 5;
    else niceStep = 10;
    step = niceStep * magnitude;

    for (let k = 0; k < targetLabels; k++) {
        let v = minValue + step * k;
        if (v > maxValue + step * 0.1) break; // Stop if we exceed max value
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