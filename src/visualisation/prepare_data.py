import os
from datetime import datetime
from src.utils import encode_image_to_base64
from visualisation.calculations import (
    calculate_weighted_productivity_index,
    calculate_trend,
    format_value,
    get_trend_color
)

def prepare_dashboard_context(config, baseline_data, time_series_data, average_data):
    # Encode logo image
    logo_path = os.path.join("images", "suncorp-logo.png")
    logo_base64 = encode_image_to_base64(logo_path)

    # Determine latest available data
    latest_date = max(time_series_data.keys()) if time_series_data else None
    latest_data = time_series_data.get(latest_date, {}) if latest_date else baseline_data

    # Set subtitle
    subtitle = (
        latest_date.strftime("Data from %B %Y compared to baseline")
        if latest_date else "Baseline data only - No historical data available"
    )

    # Group metrics by category
    metrics_by_category = {}
    for metric_key, meta in config.get("metrics_mapping", {}).items():
        category = meta.get("category", "Uncategorised")
        metrics_by_category.setdefault(category, []).append(metric_key)

    # Sort categories
    sorted_categories = sorted(
        metrics_by_category,
        key=lambda x: config.get("category_order", []).index(x) if x in config.get("category_order", []) else float('inf')
    )

    # Calculate overall and per-metric productivity index
    productivity_data = calculate_weighted_productivity_index(
        latest_data, metrics_by_category, baseline_data, average_data, config
    )

    # Prepare structured data for rendering
    categories = []
    for category_name in sorted_categories:
        category_color = config.get("chart_colors", {}).get(category_name, "#4285F4")
        metrics = []

        for metric_key in metrics_by_category[category_name]:
            meta = config["metrics_mapping"][metric_key]
            current_val = latest_data.get(metric_key)
            baseline_val = baseline_data.get(metric_key)
            average_val = average_data.get(metric_key)

            fmt = meta.get("format", "number")
            label = meta.get("label", metric_key)
            is_inverse = meta.get("inverse", False)

            formatted_current = format_value(current_val, fmt) if current_val is not None else "N/A"
            formatted_baseline = format_value(baseline_val, fmt) if baseline_val is not None else "N/A"
            formatted_average = format_value(average_val, fmt) if average_val is not None else "N/A"            # Collect monthly trend data
            chart_data = []
            for dt in sorted(time_series_data.keys()):
                val = time_series_data[dt].get(metric_key)
                if val is not None:
                    chart_data.append({
                        "label": dt.strftime("%b"),  # Only show month name without year
                        "value": val
                    })

            # Calculate global weight
            raw_weight = meta.get("weight", 0)
            category_weight = config.get("category_weights", {}).get(meta.get("category", ""), 0)
            global_weight = raw_weight * category_weight
            weight_pct = f"{global_weight * 100:.1f}%" if global_weight else "—"

            # Chart options including baseline reference
            chart_options = {
                "lineColor": category_color,
                "weight_pct": weight_pct,
                "baselineColor": "#CCCCCC"
            }
            if fmt == "percentage":
                chart_options["isPercentage"] = True
            else:
                chart_options["isInteger"] = True
                chart_options["decimals"] = 0
            if baseline_val is not None:
                chart_options["baselineValue"] = baseline_val

            # Trend analysis
            trend = None
            if average_val is not None and baseline_val is not None:
                pct = calculate_trend(average_val, baseline_val)
                arrow = "▲" if pct > 0 else "▼"
                better = "Better" if (pct > 0 and not is_inverse) or (pct < 0 and is_inverse) else "Worse"
                trend = {
                    "pct": f"{abs(pct):.1f}%",
                    "arrow": arrow,
                    "description": better,
                    "color": get_trend_color(pct, is_inverse)
                }            # Combine metric data
            metrics.append({
                "key": metric_key,
                "label": label,
                "current": formatted_current,
                "baseline": formatted_baseline,
                "average": formatted_average,
                "trend": trend,
                "chart_id": f"chart_{metric_key}",
                "chart_data": chart_data,
                "chart_options": chart_options,
                "index_input": productivity_data.get("index_inputs", {}).get(metric_key),
                "weight_pct": weight_pct,
                "global_weight": global_weight
            })

        # Add category after processing all its metrics
        if metrics:
            categories.append({
                "name": category_name,
                "color": category_color,
                "metrics": metrics
            })

    # Executive summary metrics (e.g., Story Points, AI Adoption Rate, Deployment Frequency)
    executive_summary_metrics = []    # Add Story Points, AI Adoption Rate, Bugs, and Deployment Frequency if present
    for category in categories:
        for metric in category["metrics"]:
            if metric["key"] in ["s_story_points", "a_ai_adoption_rate", "q_bugs", "d_deployment_frequency"]:
                executive_summary_metrics.append(metric)

    # Prepare active users data for donut chart
    active_users_metric = next((metric for cat in categories for metric in cat["metrics"] if metric["key"] == "a_active_users"), None)
    active_users_total = 5000  # From all.csv
    if active_users_metric:
        current_value = int(active_users_metric["current"].replace(",", "")) if active_users_metric["current"] != "N/A" else 0
        active_users_data = {
            "current": current_value,
            "total": active_users_total,
            "trend": active_users_metric["trend"],
            "chart_data": [
                {"label": "Active Users", "value": current_value},
                {"label": "Remaining", "value": max(0, active_users_total - current_value)}
            ],
            "chart_options": {
                "type": "donut",
                "colors": ["#4285F4", "#E8EAED"],
                "isInteger": True,
                "decimals": 0
            }
        }
    else:
        active_users_data = None

    return {
        "dashboard_title": config.get("dashboard_title", "Dashboard"),
        "logo_base64": logo_base64,
        "subtitle": subtitle,
        "categories": categories,
        "overall_index": productivity_data.get("overall_index", 0),
        "executive_summary_metrics": executive_summary_metrics,
        "active_users": active_users_data
    }
