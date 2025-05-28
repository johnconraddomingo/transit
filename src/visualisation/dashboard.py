"""
Dashboard generator for GitHub Copilot Metrics Framework.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
import seaborn as sns
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import numpy as np

from .config import METRICS_MAPPING, CATEGORY_ORDER, CHART_COLORS, DASHBOARD_TITLE
from .data_loader import load_all_data, get_metrics_by_category


def format_value(value, format_type):
    """
    Format a value according to the specified format type.
    
    Args:
        value: The value to format
        format_type: The type of formatting to apply
        
    Returns:
        Formatted string representation of the value
    """
    if format_type == "percentage":
        return f"{value * 100:.1f}%"
    elif format_type == "number":
        if isinstance(value, int) or value.is_integer():
            return f"{int(value):,}"
        else:
            return f"{value:,.2f}"
    else:
        return str(value)


def calculate_trend(current, baseline):
    """
    Calculate the trend between current and baseline values.
    
    Args:
        current: Current value
        baseline: Baseline value
        
    Returns:
        Percentage change as a float
    """
    if baseline == 0:
        return 100 if current > 0 else 0
    
    return ((current - baseline) / abs(baseline)) * 100


def get_trend_color(trend_pct, inverse=False):
    """
    Determine color for trend indicator.
    
    Args:
        trend_pct: Percentage change
        inverse: Whether a negative change is good (e.g., for bugs)
        
    Returns:
        CSS color string
    """
    if inverse:
        trend_pct = -trend_pct
        
    if trend_pct > 5:
        return "#34A853"  # Green for positive
    elif trend_pct < -5:
        return "#EA4335"  # Red for negative
    else:
        return "#FBBC05"  # Yellow for neutral


def generate_time_series_chart(metric_key, time_series_data, baseline_value=None):
    """
    Generate a time series chart for a specific metric.
    
    Args:
        metric_key: The key of the metric to chart
        time_series_data: Dictionary with dates as keys and metric data as values
        baseline_value: Optional baseline value to include
        
    Returns:
        Path to the saved chart image
    """
    plt.figure(figsize=(8, 4))
    
    # Get metadata for the metric
    metadata = METRICS_MAPPING.get(metric_key, {})
    title = metadata.get('label', metric_key)
    category = metadata.get('category', 'Uncategorized')
    chart_color = CHART_COLORS.get(category, "#4285F4")
    
    # Prepare data for plotting
    dates = []
    values = []
    
    for date, data in sorted(time_series_data.items()):
        if metric_key in data:
            dates.append(date)
            values.append(data[metric_key])
    
    # Plot time series
    plt.plot(dates, values, marker='o', linestyle='-', color=chart_color, linewidth=2)
    
    # Add baseline if provided
    if baseline_value is not None:
        plt.axhline(y=baseline_value, color='gray', linestyle='--', alpha=0.7)
        plt.text(dates[0], baseline_value, f"Baseline: {format_value(baseline_value, metadata.get('format', 'number'))}", 
                 va='bottom', ha='left', alpha=0.7)
    
    # Format the chart
    plt.title(title, fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Format y-axis based on the metric type
    if metadata.get('format') == 'percentage':
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
    
    # Save the chart
    output_dir = os.path.join(os.getcwd(), 'reports', 'charts')
    os.makedirs(output_dir, exist_ok=True)
    
    chart_filename = f"{metric_key}_chart.png"
    chart_path = os.path.join(output_dir, chart_filename)
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    # Return the relative path for HTML inclusion
    return os.path.join('charts', chart_filename)


def create_dashboard(output_path='reports', baseline_folder='baseline', ongoing_folder='ongoing'):
    """
    Create a dashboard HTML file with visualizations.
    
    Args:
        output_path: Path to save the dashboard HTML
        baseline_folder: Path to the baseline data folder
        ongoing_folder: Path to the ongoing data folder
    
    Returns:
        Path to the generated HTML file
    """
    # Ensure output directories exist
    os.makedirs(output_path, exist_ok=True)
    charts_dir = os.path.join(output_path, 'charts')
    os.makedirs(charts_dir, exist_ok=True)
    
    # Load all data
    baseline_data, time_series_data = load_all_data(baseline_folder, ongoing_folder)
    
    # Get the latest data point
    latest_date = max(time_series_data.keys()) if time_series_data else None
    latest_data = time_series_data.get(latest_date, {}) if latest_date else {}
    
    # Group metrics by category
    metrics_by_category = get_metrics_by_category(METRICS_MAPPING)
    
    # Sort categories according to the defined order
    sorted_categories = sorted(
        metrics_by_category.keys(),
        key=lambda x: CATEGORY_ORDER.index(x) if x in CATEGORY_ORDER else len(CATEGORY_ORDER)
    )
    
    # Prepare data for the template
    dashboard_data = []
    chart_paths = {}
    
    for category in sorted_categories:
        category_metrics = []
        for metric_key in metrics_by_category[category]:
            if metric_key in latest_data:
                current_value = latest_data[metric_key]
                baseline_value = baseline_data.get(metric_key)
                
                # Generate chart for this metric
                chart_path = generate_time_series_chart(
                    metric_key, 
                    time_series_data,
                    baseline_value
                )
                chart_paths[metric_key] = chart_path
                
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
                
                category_metrics.append({
                    'key': metric_key,
                    'label': METRICS_MAPPING[metric_key].get('label', metric_key),
                    'current_value': current_value,
                    'formatted_current': formatted_current,
                    'baseline_value': baseline_value,
                    'formatted_baseline': formatted_baseline,
                    'trend_pct': trend_pct,
                    'formatted_trend': f"{trend_pct:+.1f}%" if trend_pct is not None else 'N/A',
                    'trend_color': trend_color,
                    'chart_path': chart_path,
                    'is_inverse': is_inverse
                })
        
        if category_metrics:
            dashboard_data.append({
                'category': category,
                'metrics': category_metrics,
                'color': CHART_COLORS.get(category, "#4285F4")
            })
    
    # Create an HTML template using Jinja2
    template = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ dashboard_title }}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f7fa;
        }
        .dashboard-header {
            text-align: center;
            margin-bottom: 40px;
        }
        .dashboard-title {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #24292e;
        }
        .dashboard-subtitle {
            font-size: 16px;
            color: #586069;
        }
        .category-section {
            margin-bottom: 40px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .category-header {
            padding: 15px 20px;
            font-size: 18px;
            font-weight: 600;
            color: white;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        .metric-card {
            padding: 15px;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            background-color: #fff;
        }
        .metric-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #24292e;
        }
        .metric-value {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .metric-baseline {
            font-size: 14px;
            color: #586069;
            margin-bottom: 10px;
        }
        .metric-trend {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            color: white;
        }
        .chart-container {
            margin-top: 15px;
        }
        .chart-container img {
            width: 100%;
            height: auto;
            border-radius: 4px;
            border: 1px solid #e1e4e8;
        }
        .generation-info {
            text-align: center;
            margin-top: 40px;
            color: #586069;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1 class="dashboard-title">{{ dashboard_title }}</h1>
        <p class="dashboard-subtitle">
            Data from {{ latest_date_formatted }} compared to baseline
        </p>
    </div>
    
    {% for category in dashboard_data %}
        <div class="category-section">
            <div class="category-header" style="background-color: {{ category.color }};">
                {{ category.category }}
            </div>
            <div class="metrics-grid">
                {% for metric in category.metrics %}
                    <div class="metric-card">
                        <div class="metric-title">{{ metric.label }}</div>
                        <div class="metric-value">{{ metric.formatted_current }}</div>
                        <div class="metric-baseline">Baseline: {{ metric.formatted_baseline }}</div>
                        {% if metric.trend_pct is not none %}
                            <div class="metric-trend" style="background-color: {{ metric.trend_color }};">
                                {{ metric.formatted_trend }}
                                {% if metric.is_inverse %}
                                    {% if metric.trend_pct < 0 %}
                                        ▼ (Better)
                                    {% else %}
                                        ▲ (Worse)
                                    {% endif %}
                                {% else %}
                                    {% if metric.trend_pct > 0 %}
                                        ▲ (Better)
                                    {% else %}
                                        ▼ (Worse)
                                    {% endif %}
                                {% endif %}
                            </div>
                        {% endif %}
                        <div class="chart-container">
                            <img src="{{ metric.chart_path }}" alt="Chart for {{ metric.label }}">
                        </div>
                    </div>
                {% endfor %}
            </div>
        </div>
    {% endfor %}
    
    <div class="generation-info">
        Generated on {{ generation_date }} | GitHub Copilot Metrics Framework
    </div>
</body>
</html>
    """
    
    # Format latest date and generation date
    latest_date_formatted = latest_date.strftime('%B %Y') if latest_date else 'No data'
    generation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Render the HTML template
    html_content = Environment().from_string(template).render(
        dashboard_title=DASHBOARD_TITLE,
        dashboard_data=dashboard_data,
        latest_date_formatted=latest_date_formatted,
        generation_date=generation_date
    )
    
    # Save the HTML file
    output_file = os.path.join(output_path, 'dashboard.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file
