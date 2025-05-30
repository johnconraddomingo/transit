"""
Simple HTML dashboard generator for GitHub Copilot Metrics Framework.
"""
import os
import sys
import re
import json 
from datetime import datetime

# Define the path to the metrics mapping and category weights
def load_config(config_path="config/dashboard.json"):
    with open(config_path, "r") as f:
        return json.load(f)

config = load_config()

# Dashboard title
config["dashboard_title"] = "GitHub Copilot Metrics Framework"

def load_csv_data(file_path):
    """
    Load data from a CSV file.
    """
    data = {}
    with open(file_path, 'r') as f:
        # Skip comments or header lines that start with //
        lines = [line.strip() for line in f if not line.strip().startswith('//')]
        
        for line in lines:
            if line and ',' in line:
                key, value = line.split(',', 1)
                try:
                    # Convert to appropriate type (float or int)
                    if '.' in value:
                        data[key] = float(value)
                    else:
                        data[key] = int(value)
                except ValueError:
                    # Keep as string if conversion fails
                    data[key] = value
    
    return data

def extract_date_from_filename(filename):
    """
    Extract date from filename in format YYYY-MM.csv
    """
    match = re.search(r'(\d{4}-\d{2})', filename)
    if match:
        try:
            date_str = match.group(1)
            return datetime.strptime(date_str, "%Y-%m")
        except ValueError:
            return None
    return None

def load_all_data(baseline_folder, ongoing_folder):
    """
    Load all metric data from baseline and ongoing folders.
    """
    # Load baseline data
    baseline_file = os.path.join(baseline_folder, "baseline.csv")
    baseline_data = load_csv_data(baseline_file) if os.path.exists(baseline_file) else {}
    
    # Load ongoing data (time series)
    time_series_data = {}
    if os.path.exists(ongoing_folder):
        for filename in sorted(os.listdir(ongoing_folder)):
            if filename.endswith('.csv'):
                file_path = os.path.join(ongoing_folder, filename)
                date = extract_date_from_filename(filename)
                if date:
                    data = load_csv_data(file_path)
                    time_series_data[date] = data
                    print(f"Loaded {filename} with {len(data)} metrics")
    
    # Calculate averages across all time periods
    average_data = {}
    if time_series_data:
        for metric in config["metrics_mapping"]:
            avg_value = calculate_metrics_average(time_series_data, metric)
            if avg_value is not None:
                average_data[metric] = avg_value
    
    return baseline_data, time_series_data, average_data

def format_value(value, format_type):
    """
    Format a value according to the specified format type.
    """
    if format_type == "percentage":
        return f"{value * 100:.1f}%"
    elif format_type == "number":
        if isinstance(value, int):
            return f"{int(value):,}"
        elif isinstance(value, float) and value.is_integer():
            return f"{int(value):,}"
        else:
            return f"{value:,.2f}"
    else:
        return str(value)

def calculate_trend(current, baseline):
    """
    Calculate the trend between current and baseline values.
    """
    if baseline == 0:
        return 100 if current > 0 else 0
    
    return ((current - baseline) / abs(baseline)) * 100

def get_trend_color(trend_pct, inverse=False):
    """
    Determine color for trend indicator.
    """
    if inverse:
        trend_pct = -trend_pct
        
    if trend_pct > 5:
        return "#34A853"  # Green for positive
    elif trend_pct < -5:
        return "#EA4335"  # Red for negative
    else:
        return "#FBBC05"  # Yellow for neutral

def calculate_metrics_average(time_series_data, metric_key):
    """
    Calculate the average value for a metric across all available time periods.
    
    Args:
        time_series_data: Dictionary of time series data with dates as keys
        metric_key: The metric key to calculate the average for
        
    Returns:
        Average value of the metric or None if no data available
    """
    values = []
    for date, data in time_series_data.items():
        if metric_key in data:
            values.append(data[metric_key])
    
    if not values:
        return None
    
    return sum(values) / len(values)

def calculate_productivity_improvement(current_value, baseline_value, is_inverse=False):
    """
    Calculate the productivity improvement percentage between current and baseline values.
    
    Args:
        current_value: Current metric value
        baseline_value: Baseline metric value
        is_inverse: Whether a lower value is better (e.g., for bugs)
        
    Returns:
        Productivity improvement percentage
    """
    if baseline_value is None or baseline_value == 0:
        return 0
    
    improvement = ((current_value - baseline_value) / abs(baseline_value)) * 100
    
    # For inverse metrics (where lower is better), negate the improvement
    if is_inverse:
        improvement = -improvement
        
    return improvement

def calculate_weighted_productivity_index(metrics_data, metrics_by_category, baseline_data, average_data=None):
    """
    Calculate the weighted productivity index based on all metrics and their category weights.
    
    Args:
        metrics_data: Dictionary with metrics and their values
        metrics_by_category: Dictionary grouping metrics by their categories
        baseline_data: Dictionary with baseline metric values
        average_data: Optional dictionary with average metrics values
        
    Returns:
        Dictionary with overall index value and details per category
    """
    productivity_data = {
        "overall_index": 0.0,
        "categories": {}
    }
    
    # Process each category and its metrics
    for category_name, metric_keys in metrics_by_category.items():
        category_weight = config["category_weights"].get(category_name, 0.0)
        category_metrics = []
        category_total_improvement = 0.0
        
        # Calculate improvement for each metric in the category
        for metric_key in metric_keys:
            if metric_key in metrics_data and metric_key in config["metrics_mapping"]:
                current_value = metrics_data[metric_key]
                baseline_value = baseline_data[metric_key] if metric_key in baseline_data else None
                avg_value = average_data[metric_key] if average_data and metric_key in average_data else None
                
                if baseline_value is not None:
                    is_inverse = config["metrics_mapping"][metric_key].get('inverse', False)
                    improvement_pct = calculate_productivity_improvement(current_value, baseline_value, is_inverse)
                    
                    # Also calculate improvement against average if available
                    avg_improvement_pct = None
                    if avg_value is not None:
                        avg_improvement_pct = calculate_productivity_improvement(current_value, avg_value, is_inverse)
                    
                    # Weight per metric is the category weight divided by number of metrics in category
                    metric_count = len(metric_keys)
                    metric_weight = category_weight / metric_count if metric_count > 0 else 0
                    
                    # Weight percentage formatted for display
                    weight_pct = metric_weight * 100
                    
                    # Calculate weighted contribution to the index
                    weighted_contribution = improvement_pct * metric_weight
                    
                    metric_data = {
                        "key": metric_key,
                        "name": config["metrics_mapping"][metric_key].get("label", metric_key),
                        "baseline": baseline_value,
                        "current": current_value,
                        "improvement_pct": improvement_pct,
                        "weight_pct": weight_pct,
                        "weighted_contribution": weighted_contribution
                    }
                    
                    # Add average data if available
                    if avg_value is not None:
                        metric_data["average"] = avg_value
                        metric_data["avg_improvement_pct"] = avg_improvement_pct
                    
                    category_metrics.append(metric_data)
                    category_total_improvement += weighted_contribution
        
        # Add category data to results
        if category_metrics:
            productivity_data["categories"][category_name] = {
                "metrics": category_metrics,
                "weight": category_weight * 100,  # Convert to percentage
                "total_improvement": category_total_improvement
            }
            
            # Add to overall index
            productivity_data["overall_index"] += category_total_improvement
    
    return productivity_data

def generate_simple_dashboard(baseline_dir=None, ongoing_dir=None, output_dir=None):
    """
    Generate a simple HTML dashboard
    
    Parameters:
    - baseline_dir: Directory containing baseline metrics data
    - ongoing_dir: Directory containing ongoing metrics data
    - output_dir: Directory to save generated dashboard
    """
    # Load the data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    baseline_dir = baseline_dir or os.path.join(current_dir, "baseline")
    ongoing_dir = ongoing_dir or os.path.join(current_dir, "ongoing")
    output_dir = output_dir or os.path.join(current_dir, "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading data...")
    baseline_data, time_series_data, average_data = load_all_data(baseline_dir, ongoing_dir)
    
    print(f"Baseline metrics: {len(baseline_data)}")
    print(f"Time series data points: {len(time_series_data)}")
    print(f"Average metrics: {len(average_data)}")
    
    # Get the latest data point
    latest_date = max(time_series_data.keys()) if time_series_data else None
    latest_data = time_series_data.get(latest_date, {}) if latest_date else {}
    
    # If there's no ongoing data but baseline data exists, use baseline data as the current values
    if not latest_data and baseline_data:
        print("No ongoing data found. Using baseline data for display.")
        print(f"Baseline data type: {type(baseline_data)}")
        latest_data = baseline_data.copy()
        
    # Group metrics by category
    metrics_by_category = {}
    for metric_key, metadata in config["metrics_mapping"].items():
        category = metadata.get('category', 'Uncategorized')
        if category not in metrics_by_category:
            metrics_by_category[category] = []
        metrics_by_category[category].append(metric_key)
    
    # Sort categories according to the defined order
    sorted_categories = sorted(
        metrics_by_category.keys(),
        key=lambda x: config["category_order"].index(x) if x in config["category_order"] else len(config["category_order"])
    )

    # Sort dates chronologically for time series
    sorted_dates = sorted(time_series_data.keys()) if time_series_data else []
      # Calculate the weighted productivity index
    productivity_data = calculate_weighted_productivity_index(latest_data, metrics_by_category, baseline_data, average_data)
    overall_index = productivity_data["overall_index"]
    
    # JavaScript for line charts (outside of Python f-string)
    js_code = """
    <script>
        // Function to draw a line graph using Canvas
        function drawLineGraph(canvasId, data, options) {
            var canvas = document.getElementById(canvasId);
            if (!canvas || !data || data.length === 0) return;
            
            var ctx = canvas.getContext('2d');
            var width = canvas.clientWidth;
            var height = canvas.clientHeight;
            
            // Clear canvas
            ctx.clearRect(0, 0, width, height);
            
            // Set default options
            options = options || {};
            var padding = options.padding || 40;
            var lineColor = options.lineColor || '#4285F4';
            var baselineColor = options.baselineColor || '#CCCCCC';
            var baselineValue = options.baselineValue;
            var axisColor = '#888888';
            var textColor = '#333333';
            
            // Find min and max values
            var minValue = Infinity;
            var maxValue = -Infinity;
            
            for (var i = 0; i < data.length; i++) {
                var point = data[i];
                if (point.value < minValue) minValue = point.value;
                if (point.value > maxValue) maxValue = point.value;
            }
            
            // Include baseline in min/max if provided
            if (baselineValue !== undefined) {
                if (baselineValue < minValue) minValue = baselineValue;
                if (baselineValue > maxValue) maxValue = baselineValue;
            }
            
            // Add a little padding to min/max
            var valueRange = maxValue - minValue;
            minValue = minValue - (valueRange * 0.1);
            maxValue = maxValue + (valueRange * 0.1);
            
            // Function to convert data point to canvas coordinates
            function getX(index) {
                return padding + (index / (data.length - 1)) * (width - padding * 2);
            }
            
            function getY(value) {
                return height - padding - ((value - minValue) / (maxValue - minValue)) * (height - padding * 2);
            }
            
            // Draw axes
            ctx.strokeStyle = axisColor;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(padding, padding);
            ctx.lineTo(padding, height - padding);
            ctx.lineTo(width - padding, height - padding);
            ctx.stroke();
            
            // Draw baseline if provided
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
                
                // Label baseline
                ctx.fillStyle = textColor;
                ctx.font = '10px sans-serif';
                ctx.textAlign = 'left';
                ctx.fillText('Baseline', padding, baselineY - 5);
            }
            
            // Draw value line
            ctx.strokeStyle = lineColor;
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            for (var j = 0; j < data.length; j++) {
                var x = getX(j);
                var y = getY(data[j].value);
                
                if (j === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
                
                // Draw point
                ctx.fillStyle = lineColor;
                ctx.beginPath();
                ctx.arc(x, y, 4, 0, Math.PI * 2);
                ctx.fill();
                
                // Draw date label
                ctx.fillStyle = textColor;
                ctx.font = '10px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(data[j].label, x, height - padding + 15);
            }
            
            ctx.stroke();
            
            // Draw y-axis labels
            ctx.fillStyle = textColor;
            ctx.font = '10px sans-serif';
            ctx.textAlign = 'right';
            
            var steps = 5;
            for (var k = 0; k <= steps; k++) {
                var value = minValue + (maxValue - minValue) * (k / steps);
                var y = getY(value);
                
                // Format value based on type
                var formattedValue;
                if (options.isPercentage) {
                    formattedValue = (value * 100).toFixed(1) + '%';
                } else {
                    formattedValue = value.toFixed(1);
                }
                
                ctx.fillText(formattedValue, padding - 5, y + 3);
            }
        }

        // Function to initialize all charts after the page loads
        function initCharts() {
            var charts = document.querySelectorAll('[data-chart]');
            for (var i = 0; i < charts.length; i++) {
                var chartElement = charts[i];
                var chartData = JSON.parse(chartElement.getAttribute('data-chart'));
                var chartOptions = JSON.parse(chartElement.getAttribute('data-options') || '{}');
                var canvasId = chartElement.getAttribute('id');
                
                // Ensure canvas is properly sized
                var canvas = document.getElementById(canvasId);
                var rect = canvas.getBoundingClientRect();
                canvas.width = rect.width;
                canvas.height = rect.height;
                
                // Draw the chart
                drawLineGraph(canvasId, chartData, chartOptions);
            }
        }

        // Initialize charts when the page is loaded
        window.addEventListener('load', initCharts);
        window.addEventListener('resize', initCharts);
    </script>
    """
    
    # Generate HTML content
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{config["dashboard_title"]}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f7fa;
        }}
        .dashboard-header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .dashboard-title {{
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #24292e;
        }}
        .dashboard-subtitle {{
            font-size: 16px;
            color: #586069;
        }}
        .category-section {{
            margin-bottom: 40px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .category-header {{
            padding: 15px 20px;
            font-size: 18px;
            font-weight: 600;
            color: white;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            padding: 20px;
        }}
        .metric-card {{
            padding: 15px;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            background-color: #fff;
        }}
        .metric-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #24292e;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        .metric-baseline {{
            font-size: 14px;
            color: #586069;
            margin-bottom: 5px;
        }}
        .metric-average {{
            font-size: 14px;
            color: #0366d6;
            font-weight: 500;
            margin-bottom: 10px;
        }}
        .metric-trend {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            color: white;
        }}
        .metric-history {{
            margin-top: 15px;
            font-size: 14px;
            color: #586069;
        }}
        .metric-history-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
        }}        .generation-info {{
            text-align: center;
            margin-top: 40px;
            color: #586069;
            font-size: 14px;
        }}
        .productivity-summary {{
            margin-top: 40px;
            margin-bottom: 40px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            padding: 20px;
        }}
        .productivity-header {{
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #24292e;
            text-align: center;
        }}
        .productivity-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .productivity-table th, .productivity-table td {{
            padding: 10px;
            border: 1px solid #e1e4e8;
            text-align: center;
        }}
        .productivity-table th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        .productivity-table tr.category-header-row {{
            background-color: #f1f4f8;
            font-weight: 600;
        }}
        .productivity-index {{
            font-size: 20px;
            font-weight: 700;
            margin-top: 30px;
            text-align: center;
        }}
        .productivity-note {{
            font-style: italic;
            color: #586069;
            text-align: center;
            margin-top: 10px;
        }}
        .chart-container {{
            margin-top: 20px;
            width: 100%;
            height: 200px;
            position: relative;
        }}
        .chart-canvas {{
            width: 100%;
            height: 100%;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            background-color: #f8f9fa;
        }}
        .chart-legend {{
            margin-top: 10px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 12px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-right: 15px;
        }}
        .legend-color {{
            width: 12px;
            height: 12px;
            margin-right: 5px;
            display: inline-block;
        }}
    </style>
    {js_code}
</head>
<body>
    <div class="dashboard-header">
        <h1 class="dashboard-title">{config["dashboard_title"]}</h1>
        <p class="dashboard-subtitle">
            {latest_date.strftime('Data from %B %Y compared to baseline') if latest_date else 'Baseline data only - No historical data available'}
        </p>
    </div>
    """
    
    # Add category sections
    for category in sorted_categories:
        category_color = config["chart_colors"].get(category, "#4285F4")
        html_content += f"""
    <div class="category-section">
        <div class="category-header" style="background-color: {category_color};">
            {category}
        </div>
        <div class="metrics-grid">
        """
        
        for metric_key in metrics_by_category[category]:
            if metric_key in latest_data:
                current_value = latest_data[metric_key]
                print(f"Processing metric: {metric_key}, baseline_data type: {type(baseline_data)}")
                baseline_value = baseline_data[metric_key] if metric_key in baseline_data else None
                
                # Calculate trend
                trend_pct = calculate_trend(current_value, baseline_value) if baseline_value is not None else None
                
                # Check if this metric is inverse (lower is better)
                is_inverse = config["metrics_mapping"][metric_key].get('inverse', False)
                
                # Get trend color
                trend_color = get_trend_color(trend_pct, is_inverse) if trend_pct is not None else None
                
                # Format values
                format_type = config["metrics_mapping"][metric_key].get('format', 'number')
                formatted_current = format_value(current_value, format_type)
                formatted_baseline = format_value(baseline_value, format_type) if baseline_value is not None else 'N/A'
                
                # Get average if available
                average_value = average_data.get(metric_key)
                formatted_average = format_value(average_value, format_type) if average_value is not None else 'N/A'
                
                html_content += f"""
            <div class="metric-card">
                <div class="metric-title">{config["metrics_mapping"][metric_key].get('label', metric_key)}</div>
                <div class="metric-value">{formatted_current}</div>
                <div class="metric-baseline">Baseline: {formatted_baseline}</div>
                <div class="metric-average">Average: {formatted_average}</div>
                """
                
                if trend_pct is not None:
                    trending_up = trend_pct > 0
                    better_text = "Better" if (trending_up and not is_inverse) or (not trending_up and is_inverse) else "Worse"
                    trend_arrow = "▲" if trending_up else "▼"
                    
                    html_content += f"""
                <div class="metric-trend" style="background-color: {trend_color};">
                    {trend_pct:+.1f}% {trend_arrow} ({better_text})
                </div>
                """
                
                # Add historical data if available
                if sorted_dates:
                    html_content += """
                    <div class="metric-history">
                        <strong>Historical Data</strong>
                    """
                    
                    # Add historical data points
                    for date in sorted_dates:
                        if metric_key in time_series_data[date]:
                            value = time_series_data[date][metric_key]
                            formatted_value = format_value(value, format_type)
                            month_year = date.strftime('%b %Y')
                            
                            html_content += f"""
                        <div class="metric-history-item">
                            <span>{month_year}</span>
                            <span>{formatted_value}</span>
                        </div>
                            """
                    
                    html_content += """
                    </div>
                    """
                
                # Configure chart options
                chart_options = {
                    'lineColor': category_color,
                    'isPercentage': format_type == 'percentage'
                }
                
                if baseline_value is not None:
                    chart_options['baselineValue'] = baseline_value
                
                # Create unique ID for this chart
                chart_id = f"chart_{metric_key}"
                
                # Add chart to HTML - either with time series data or just baseline
                import json
                
                if sorted_dates:
                    # Add line graph with historical data
                    chart_data = []
                    for date in sorted_dates:
                        if metric_key in time_series_data[date]:
                            value = time_series_data[date][metric_key]
                            chart_data.append({
                                'label': date.strftime('%b %Y'),
                                'value': value
                            })
                    
                    html_content += f"""
                    <div class="chart-container">
                        <canvas id="{chart_id}" 
                                class="chart-canvas" 
                                data-chart='{json.dumps(chart_data)}' 
                                data-options='{json.dumps(chart_options)}'></canvas>
                    </div>
                    <div class="chart-legend">
                        <div class="legend-item">
                            <span class="legend-color" style="background-color: {category_color};"></span>
                            <span>Actual</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background-color: #CCCCCC;"></span>
                            <span>Baseline</span>
                        </div>
                    </div>
                    """
                else:
                    # Just show the baseline value as a horizontal line
                    # Create a minimal dataset with the baseline value (show as a point)
                    baseline_chart_data = [{"label": "Baseline", "value": baseline_value or 0}]
                    
                    html_content += f"""
                    <div class="chart-container">
                        <div class="baseline-only-message" style="text-align: center; padding: 20px; color: #586069;">
                            No historical data available - Only baseline data shown
                        </div>
                    </div>
                    """
                
                html_content += """
            </div>
                """
        
        html_content += """
        </div>
    </div>
        """
    
    # Add metrics summary table
    summary_title = "Baseline Metrics Summary" if not sorted_dates else "Productivity Metrics Dashboard"
    latest_value_label = "Latest Value" if sorted_dates else "Value"
    improvement_label = "Analysis" if not sorted_dates else "Productivity Comparison"

    html_content += f"""
    <div class="productivity-summary">
        <div class="productivity-header">{summary_title}</div>
        <table class="productivity-table">
            <thead>
                <tr>
                    <th>Dimension</th>
                    <th>Metric</th>
                    <th>Baseline</th>
                    <th>{latest_value_label}</th>
                    <th>Average</th>
                    <th>{improvement_label}</th>
                    <th>Weight</th>
                    <th>Index Input</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add rows for each category and its metrics
    for category_name in sorted_categories:
        if category_name in productivity_data["categories"]:
            category_data = productivity_data["categories"][category_name]
            
            # Add category header row
            html_content += f"""
                <tr class="category-header-row">
                    <td><strong>{category_name}</strong></td>
                    <td colspan="6"></td>
                </tr>
            """
            
            # Add rows for each metric
            for metric in category_data["metrics"]:
                # Format the metric values
                baseline_val = format_value(metric["baseline"], config["metrics_mapping"][metric["key"]].get("format", "number"))
                current_val = format_value(metric["current"], config["metrics_mapping"][metric["key"]].get("format", "number"))
                
                # Get and format the average value
                avg_value = average_data.get(metric["key"])
                avg_val = format_value(avg_value, config["metrics_mapping"][metric["key"]].get("format", "number")) if avg_value is not None else 'N/A'
                
                improvement_pct = f"{metric['improvement_pct']:.2f}%"
                weight_pct = f"{metric['weight_pct']:.0f}%"
                index_input = f"{metric['weighted_contribution']:.2f}%"
                
                html_content += f"""
                <tr>
                    <td></td>
                    <td>{metric["name"]}</td>
                    <td>{baseline_val}</td>
                    <td>{current_val}</td>
                    <td>{avg_val}</td>
                    <td>{improvement_pct}</td>
                    <td>{weight_pct}</td>
                    <td>{index_input}</td>
                </tr>
                """
    
    # Close the table and add overall productivity index or baseline message
    if sorted_dates:
        html_content += f"""
            </tbody>
        </table>
        
        <div class="productivity-index">
            <strong>Overall Productivity Index:</strong> {overall_index:.2f}%
        </div>
        <div class="productivity-note">
            <em>This index reflects the weighted improvement across all tracked metrics, providing a holistic view of productivity gains.</em>
        </div>
    </div>
        """
    else:
        html_content += f"""
            </tbody>
        </table>
        
        <div class="productivity-note" style="margin-top: 20px; text-align: center;">
            <em>Baseline metrics are displayed. Add ongoing data to see historical trends and productivity comparisons.</em>
        </div>
    </div>
        """
    
    # Add footer
    generation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_content += f"""
    <div class="generation-info">
        Generated on {generation_date} | GitHub Copilot Metrics Framework
    </div>
</body>
</html>
    """
    
    # Write the HTML file
    output_file = os.path.join(output_dir, 'dashboard.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Dashboard generated: {output_file}")
    return output_file

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        baseline_dir = sys.argv[1] if len(sys.argv) > 1 else None
        ongoing_dir = sys.argv[2] if len(sys.argv) > 2 else None
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        generate_simple_dashboard(baseline_dir, ongoing_dir, output_dir)
    else:
        generate_simple_dashboard()
