window.drawTooltip = function (ctx, x, y, pt, width, padding) {
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
