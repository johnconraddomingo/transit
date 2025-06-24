// Modern chart renderer that loads functions in the correct order
// Note: All functions are exposed directly to window

// Load utilities first
document.write('<script src="./charts/axisUtils.js"></script>');
document.write('<script src="./charts/tooltips.js"></script>');

// Load chart implementations
document.write('<script src="./charts/lineChart.js"></script>');
document.write('<script src="./charts/barChart.js"></script>');

// Load chart initialization
document.write('<script src="./charts/index.js"></script>');

