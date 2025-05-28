import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import re
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
                    time_series_data[date] = data
    
    return baseline_data, time_series_data

def format_value(value, format_type):
    """
    Format a value according to the specified format type.
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
      # Get the latest data point
    latest_date = max(time_series_data.keys()) if time_series_data else None
    latest_data = time_series_data.get(latest_date, {}) if latest_date else {}
    
    print(f"Latest data date: {latest_date}")
    print(f"Time series data keys: {list(time_series_data.keys())}")
    print(f"Metrics found: {list(latest_data.keys())}")
    
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
            Data from {latest_date.strftime('%B %Y') if latest_date else 'No data'} compared to baseline
        </p>
    </div>
    """
    
    # Add category sections
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
                
                html_content += """
            </div>
                """
        
        html_content += """
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
    generate_simple_dashboard()
