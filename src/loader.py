import os
import json
import re
from datetime import datetime

def load_config(config_path="config/dashboard.json"):
    with open(config_path, "r") as f:
        return json.load(f)

def extract_date_from_filename(filename):
    match = re.search(r'(\d{4}-\d{2})', filename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m")
        except ValueError:
            return None
    return None

def load_csv_data(file_path):
    data = {}
    with open(file_path, 'r') as f:
        # Skip comment lines starting with //
        lines = [line.strip() for line in f if not line.strip().startswith('//')]

        for line in lines:
            if line and ',' in line:
                key, value = line.split(',', 1)
                value = value.strip()

                # Skip missing values like [] or empty
                if value in ["", "[]"]:
                    continue

                try:
                    if '.' in value:
                        data[key] = float(value)
                    else:
                        data[key] = int(value)
                except ValueError:
                    # If not numeric, skip or log
                    continue

    return data


def load_all_data(baseline_folder, ongoing_folder):
    baseline_file = os.path.join(baseline_folder, "baseline.csv")
    baseline_data = load_csv_data(baseline_file) if os.path.exists(baseline_file) else {}

    time_series_data = {}
    if os.path.exists(ongoing_folder):
        for filename in sorted(os.listdir(ongoing_folder)):
            if filename.endswith(".csv"):
                date = extract_date_from_filename(filename)
                if date:
                    filepath = os.path.join(ongoing_folder, filename)
                    time_series_data[date] = load_csv_data(filepath)

    # Calculate simple average for each metric
    average_data = {}
    if time_series_data:
        all_keys = set().union(*(d.keys() for d in time_series_data.values()))
        for key in all_keys:
            values = [v[key] for v in time_series_data.values() if key in v]
            if values:
                average_data[key] = sum(values) / len(values)

    return baseline_data, time_series_data, average_data
