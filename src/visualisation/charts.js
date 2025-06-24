// Modern chart renderer that loads functions in the correct order
// Note: All functions are exposed directly to window

// Load utilities first
function loadScript(src) {
    const script = document.createElement('script');
    script.src = src;
    script.async = false;
    document.head.appendChild(script);
}

loadScript('./charts/axisUtils.js');
loadScript('./charts/tooltips.js');

// Load chart implementations
loadScript('./charts/lineChart.js');
loadScript('./charts/barChart.js');
loadScript('./charts/donutChart.js');

// Load chart initialization
loadScript('./charts/index.js');

