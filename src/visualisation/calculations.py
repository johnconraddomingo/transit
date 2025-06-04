def calculate_trend(current, baseline):
    if baseline == 0:
        return 100 if current > 0 else 0
    return ((current - baseline) / abs(baseline)) * 100

def get_trend_color(trend_pct, inverse=False):
    if inverse:
        trend_pct = -trend_pct
    if trend_pct > 5:
        return "#34A853"  # Green for good
    elif trend_pct < -5:
        return "#EA4335"  # Red for poor
    else:
        return "#FBBC05"  # Yellow for neutral

def format_value(value, format_type):
    if format_type == "percentage":
        return f"{value * 100:.1f}%"
    elif format_type == "number":
        if isinstance(value, int):
            return f"{int(value):,}"
        elif isinstance(value, float) and value.is_integer():
            return f"{int(value):,}"
        else:
            return f"{value:,.2f}"
    return str(value)

def calculate_productivity_improvement(current, baseline, is_inverse=False, average=None):
    if baseline is None:
        return 0
    reference = average if average is not None else current
    if baseline == 0:
        return 100 if reference > 0 else 0
    improvement = ((reference - baseline) / baseline) * 100
    return -improvement if is_inverse else improvement

def calculate_weighted_productivity_index(metrics_data, metrics_by_category, baseline_data, average_data=None, config=None):
    result = {
        "overall_index": 0.0,
        "categories": {}
    }
    index_inputs = {}

    for category, metric_keys in metrics_by_category.items():
        cat_weight = config.get("category_weights", {}).get(category, 0.0)
        cat_total = 0.0
        cat_metrics = []

        for key in metric_keys:
            if key not in metrics_data or key not in config.get("metrics_mapping", {}):
                continue

            current = metrics_data[key]
            baseline = baseline_data.get(key)
            average = average_data.get(key) if average_data else None
            inverse = config["metrics_mapping"][key].get("inverse", False)

            if baseline is None:
                continue

            improvement = calculate_productivity_improvement(current, baseline, inverse, average)
            raw_weight = config["metrics_mapping"][key].get("weight", 0)
            global_weight = raw_weight * cat_weight

            contribution = improvement * global_weight
            index_inputs[key] = round(contribution, 2)

            cat_metrics.append({
                "key": key,
                "name": config["metrics_mapping"][key].get("label", key),
                "baseline": baseline,
                "current": current,
                "average": average,
                "improvement_pct": improvement,
                "weight_pct": global_weight * 100,
                "weighted_contribution": contribution
            })

            cat_total += contribution

        if cat_metrics:
            result["categories"][category] = {
                "metrics": cat_metrics,
                "weight": cat_weight * 100,
                "total_improvement": cat_total
            }
            result["overall_index"] += cat_total

    result["overall_index"] = round(result["overall_index"], 2)
    result["index_inputs"] = index_inputs
    return result

