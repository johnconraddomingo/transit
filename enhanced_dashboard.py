"""
Simple HTML dashboard generator for GitHub Copilot Metrics Framework.
This version uses only built-in Python libraries to avoid dependency issues.
"""
import os
import sys
import re
import json
from datetime import datetime

# Configuration for visualizing metrics data
METRICS_MAPPING = {
    # Adoption metrics
    "a_active_users": {
        "label": "Active Users",
        "category": "Adoption",
        "format": "number"
    },
    "a_ai_adoption_rate": {
        "label": "AI Adoption Rate",
        "category": "Adoption",
        "format": "percentage"
    },
    "a_ai_usage": {
        "label": "AI Usage",
        "category": "Adoption",
        "format": "percentage"
    },
    "a_code_suggestions": {
        "label": "Code Suggestions",
        "category": "Adoption",
        "format": "number"
    },
    "a_code_accepted": {
        "label": "Code Accepted",
        "category": "Adoption",
        "format": "number"
    },
    
    # Speed metrics
    "s_merged_prs": {
        "label": "Merged PRs",
        "category": "Speed",
        "format": "number"
    },
    "s_pr_review_time": {
        "label": "PR Review Time (minutes)",
        "category": "Speed",
        "format": "number"
    },
    "s_story_points": {
        "label": "Story Points Completed",
        "category": "Speed",
        "format": "number"
    },
    
    # Quality metrics
    "q_code_smells": {
        "label": "Code Smells",
        "category": "Quality",
        "format": "number",
        "inverse": True  # Lower is better
    },
    "q_coverage": {
        "label": "Code Coverage",
        "category": "Quality",
        "format": "percentage"
    },
    "q_bugs": {
        "label": "Bugs",
        "category": "Quality",
        "format": "number",
        "inverse": True  # Lower is better
    },
    "q_vulnerabilities": {
        "label": "Vulnerabilities",
        "category": "Quality",
        "format": "number",
        "inverse": True  # Lower is better
    },
    
    # Experience metrics
    "e_user_satisfaction": {
        "label": "User Satisfaction",
        "category": "Experience",
        "format": "percentage"
    },
    "e_adoption": {
        "label": "Team Adoption",
        "category": "Experience",
        "format": "percentage"
    },
    "e_productivity": {
        "label": "Perceived Productivity",
        "category": "Experience",
        "format": "percentage"
    },
    "e_use_cases": {
        "label": "Use Cases",
        "category": "Experience",
        "format": "number"
    },
    
    # Delivery metrics
    "d_deployment_frequency": {
        "label": "Deployment Frequency (per week)",
        "category": "Delivery",
        "format": "number"
    }
}

# Define category display order
CATEGORY_ORDER = ["Adoption", "Speed", "Quality", "Experience", "Delivery"]

# Define color scheme for charts
CHART_COLORS = {
    "Adoption": "#4285F4",  # Blue
    "Speed": "#EA4335",     # Red
    "Quality": "#34A853",   # Green
    "Experience": "#FBBC05", # Yellow
    "Delivery": "#8334A4"    # Purple
}

# Dashboard title
DASHBOARD_TITLE = "GitHub Copilot Metrics Framework"

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
                    time_series_data[date.strftime("%Y-%m")] = data
                    print(f"Loaded {filename} with {len(data)} metrics")
    
    return baseline_data, time_series_data

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

def generate_simple_dashboard():
    """Generate a simple HTML dashboard"""
    # Load the data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    baseline_dir = os.path.join(current_dir, "baseline")
    ongoing_dir = os.path.join(current_dir, "ongoing")
    output_dir = os.path.join(current_dir, "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading data...")
    baseline_data, time_series_data = load_all_data(baseline_dir, ongoing_dir)
    
    print(f"Baseline metrics: {len(baseline_data)}")
    print(f"Time series data points: {len(time_series_data)}")
    
    # Get the latest data point
    latest_date = max(time_series_data.keys()) if time_series_data else None
    latest_data = time_series_data.get(latest_date, {}) if latest_date else {}
    
    # Group metrics by category
    metrics_by_category = {}
    for metric_key, metadata in METRICS_MAPPING.items():
        category = metadata.get('category', 'Uncategorized')
        if category not in metrics_by_category:
            metrics_by_category[category] = []
        metrics_by_category[category].append(metric_key)
    
    # Sort categories according to the defined order
    sorted_categories = sorted(
        metrics_by_category.keys(),
        key=lambda x: CATEGORY_ORDER.index(x) if x in CATEGORY_ORDER else len(CATEGORY_ORDER)
    )
    
    # Generate HTML content
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{DASHBOARD_TITLE}</title>
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
        }}
        .metric-chart {{
            margin-top: 20px;
        }}
        .metric-chart canvas {{
            width: 100%;
            height: 150px;
            border: 1px solid #e1e4e8;
            border-radius: 4px;
            background-color: #fff;
        }}
        .generation-info {{
            text-align: center;
            margin-top: 40px;
            color: #586069;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1 class="dashboard-title">{DASHBOARD_TITLE}</h1>
        <p class="dashboard-subtitle">
            Data from {latest_date if latest_date else 'No data'} compared to baseline
        </p>
    </div>
    """
    
    # Add category sections
    chart_data = {}
    
    for category in sorted_categories:
        category_color = CHART_COLORS.get(category, "#4285F4")
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
                baseline_value = baseline_data.get(metric_key)
                
                # Calculate trend
                trend_pct = calculate_trend(current_value, baseline_value) if baseline_value is not None else None
                
                # Check if this metric is inverse (lower is better)
                is_inverse = METRICS_MAPPING[metric_key].get('inverse', False)
                
                # Get trend color
                trend_color = get_trend_color(trend_pct, is_inverse) if trend_pct is not None else None
                
                # Format values
                format_type = METRICS_MAPPING[metric_key].get('format', 'number')
                formatted_current = format_value(current_value, format_type)
                formatted_baseline = format_value(baseline_value, format_type) if baseline_value is not None else 'N/A'
                
                # Prepare chart data
                metric_data = []
                labels = []
                
                # Sort dates chronologically
                sorted_dates = sorted(time_series_data.keys())
                
                # Prepare data for chart
                for date in sorted_dates:
                    if metric_key in time_series_data[date]:
                        value = time_series_data[date][metric_key]
                        metric_data.append(value)
                        labels.append(date)
                
                # Include baseline if available
                if baseline_value is not None:
                    baseline_data_point = {
                        "label": "Baseline",
                        "data": [baseline_value] * len(labels),
                        "borderColor": "#888888",
                        "borderDash": [5, 5],
                        "fill": False,
                        "pointRadius": 0
                    }
                else:
                    baseline_data_point = None
                
                # Store chart data for JavaScript
                chart_id = f"chart_{metric_key}"
                chart_data[chart_id] = {
                    "labels": labels,
                    "datasets": [
                        {
                            "label": METRICS_MAPPING[metric_key].get('label', metric_key),
                            "data": metric_data,
                            "borderColor": category_color,
                            "backgroundColor": category_color + "33",  # Add alpha transparency
                            "fill": False,
                            "tension": 0.3
                        }
                    ]
                }
                
                if baseline_data_point:
                    chart_data[chart_id]["datasets"].append(baseline_data_point)
                
                html_content += f"""
            <div class="metric-card">
                <div class="metric-title">{METRICS_MAPPING[metric_key].get('label', metric_key)}</div>
                <div class="metric-value">{formatted_current}</div>
                <div class="metric-baseline">Baseline: {formatted_baseline}</div>
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
                
                # Add historical data
                html_content += """
                <div class="metric-history">
                    <strong>Historical Data</strong>
                """
                
                # Add historical data points
                for date in sorted_dates:
                    if metric_key in time_series_data[date]:
                        value = time_series_data[date][metric_key]
                        formatted_value = format_value(value, format_type)
                        
                        html_content += f"""
                    <div class="metric-history-item">
                        <span>{date}</span>
                        <span>{formatted_value}</span>
                    </div>
                        """
                
                html_content += """
                </div>
                """
                
                # Add chart
                html_content += f"""
                <div class="metric-chart">
                    <canvas id="{chart_id}"></canvas>
                </div>
            </div>
                """
        
        html_content += """
        </div>
    </div>
        """
    
    # Add JavaScript for charts
    html_content += """
    <script>
    // Chart.js-like minimal line chart implementation using Canvas API
    function drawLineChart(canvasId, chartData) {
        const canvas = document.getElementById(canvasId);
        const ctx = canvas.getContext('2d');
        const labels = chartData.labels;
        const datasets = chartData.datasets;
        
        // Set canvas size and DPI
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        
        // Calculate dimensions
        const width = rect.width;
        const height = rect.height;
        const padding = { top: 20, right: 20, bottom: 30, left: 50 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;
        
        // Find min and max values
        let minValue = Number.MAX_VALUE;
        let maxValue = Number.MIN_VALUE;
        
        datasets.forEach(dataset => {
            const values = dataset.data;
            const localMin = Math.min(...values);
            const localMax = Math.max(...values);
            
            if (localMin < minValue) minValue = localMin;
            if (localMax > maxValue) maxValue = localMax;
        });
        
        // Add some padding to the value range
        const valueRange = maxValue - minValue;
        minValue -= valueRange * 0.1;
        maxValue += valueRange * 0.1;
        
        // Function to convert data point to canvas coordinates
        function toCanvasX(index) {
            return padding.left + (index / (labels.length - 1)) * chartWidth;
        }
        
        function toCanvasY(value) {
            return padding.top + chartHeight - ((value - minValue) / (maxValue - minValue)) * chartHeight;
        }
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Draw axes
        ctx.beginPath();
        ctx.strokeStyle = '#e1e4e8';
        ctx.lineWidth = 1;
        
        // Draw X axis
        ctx.moveTo(padding.left, padding.top + chartHeight);
        ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
        
        // Draw Y axis
        ctx.moveTo(padding.left, padding.top);
        ctx.lineTo(padding.left, padding.top + chartHeight);
        ctx.stroke();
        
        // Draw horizontal grid lines
        const gridCount = 5;
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.font = '10px sans-serif';
        ctx.fillStyle = '#586069';
        
        for (let i = 0; i <= gridCount; i++) {
            const y = padding.top + (i / gridCount) * chartHeight;
            const value = maxValue - (i / gridCount) * (maxValue - minValue);
            
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(padding.left + chartWidth, y);
            ctx.strokeStyle = '#e1e4e8';
            ctx.lineWidth = 0.5;
            ctx.stroke();
            
            // Draw Y-axis labels
            ctx.fillText(value.toFixed(1), padding.left - 5, y);
        }
        
        // Draw X-axis labels
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        
        // Draw only first, middle, and last label if there are many
        const labelIndices = labels.length <= 5 ? 
                             labels.map((_, i) => i) : 
                             [0, Math.floor(labels.length / 2), labels.length - 1];
        
        labelIndices.forEach(i => {
            const x = toCanvasX(i);
            ctx.fillText(labels[i], x, padding.top + chartHeight + 5);
        });
        
        // Draw datasets
        datasets.forEach(dataset => {
            const points = dataset.data.map((value, index) => ({
                x: toCanvasX(index),
                y: toCanvasY(value)
            }));
            
            // Draw lines
            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }
            
            ctx.strokeStyle = dataset.borderColor || '#000';
            ctx.lineWidth = 2;
            
            // Apply line dash if specified
            if (dataset.borderDash) {
                ctx.setLineDash(dataset.borderDash);
            } else {
                ctx.setLineDash([]);
            }
            
            ctx.stroke();
            
            // Reset line dash
            ctx.setLineDash([]);
            
            // Fill if specified
            if (dataset.fill) {
                ctx.lineTo(points[points.length - 1].x, toCanvasY(minValue));
                ctx.lineTo(points[0].x, toCanvasY(minValue));
                ctx.closePath();
                ctx.fillStyle = dataset.backgroundColor || 'rgba(66, 133, 244, 0.2)';
                ctx.fill();
            }
            
            // Draw points
            const radius = dataset.pointRadius !== undefined ? dataset.pointRadius : 3;
            if (radius > 0) {
                ctx.fillStyle = dataset.borderColor || '#000';
                points.forEach(point => {
                    ctx.beginPath();
                    ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
                    ctx.fill();
                });
            }
        });
        
        // Draw legend
        if (datasets.length > 1) {
            const legendY = padding.top + 10;
            let legendX = padding.left + 10;
            
            datasets.forEach(dataset => {
                ctx.fillStyle = dataset.borderColor || '#000';
                ctx.fillRect(legendX, legendY, 15, 2);
                
                ctx.fillStyle = '#586069';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText(dataset.label, legendX + 20, legendY);
                
                legendX += ctx.measureText(dataset.label).width + 40;
            });
        }
    }
    
    // Chart data
    const chartData = {
    """
    
    # Add chart data as JavaScript
    for chart_id, data in chart_data.items():
        html_content += f"'{chart_id}': {json.dumps(data)},\n"
    
    html_content += """
    };
    
    // Draw all charts when page loads
    window.addEventListener('load', function() {
        for (const chartId in chartData) {
            drawLineChart(chartId, chartData[chartId]);
        }
        
        // Redraw on window resize
        window.addEventListener('resize', function() {
            for (const chartId in chartData) {
                drawLineChart(chartId, chartData[chartId]);
            }
        });
    });
    </script>
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
    generate_simple_dashboard()
