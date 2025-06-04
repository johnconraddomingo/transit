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
            formatted_average = format_value(average_val, fmt) if average_val is not None else "N/A"

            # Collect monthly trend data
            chart_data = []
            for dt in sorted(time_series_data.keys()):
                val = time_series_data[dt].get(metric_key)
                if val is not None:
                    chart_data.append({
                        "label": dt.strftime("%b %Y"),
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
                "isPercentage": fmt == "percentage",
                "weight_pct": weight_pct,
                "baselineColor": "#CCCCCC"
            }
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
                }

            # Combine metric data
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

        categories.append({
            "name": category_name,
            "color": category_color,
            "metrics": metrics
        })

    return {
        "dashboard_title": config.get("dashboard_title", "Dashboard"),
        "logo_base64": logo_base64,
        "subtitle": subtitle,
        "categories": categories,
        "overall_index": productivity_data.get("overall_index", 0)
    }
