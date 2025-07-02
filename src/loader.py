import os
import json
import re
from datetime import datetime
import pandas as pd

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


def get_latest_excel_file(folder):
    """Find the most recent .xlsx file in the folder based on filename date."""
    excel_files = [f for f in os.listdir(folder) if f.endswith('.xlsx')]
    if not excel_files:
        return None
    
    # Sort by date in filename (assuming YYYY-MM format)
    sorted_files = sorted(excel_files, key=lambda x: extract_date_from_filename(x) or datetime.min)
    if sorted_files:
        return os.path.join(folder, sorted_files[-1])  # Return the latest file
    return None

def load_survey_data(ongoing_folder):
    """Load survey data from the latest Excel file in the ongoing folder."""
    excel_file = get_latest_excel_file(ongoing_folder)
    if not excel_file:
        return None
    
    try:
        df = pd.read_excel(excel_file)
        survey_data = {
            'writing_new_code': df.iloc[:, 8].value_counts().to_dict(),
            'refactoring_code': df.iloc[:, 9].value_counts().to_dict(),
            'writing_tests': df.iloc[:, 10].value_counts().to_dict(),
            'source_file': os.path.basename(excel_file)
        }
        return survey_data
    except Exception as e:
        print(f"Error loading survey data: {e}")
        return None

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
    
    # Load survey data from the latest Excel file
    survey_data = load_survey_data(ongoing_folder)

    return baseline_data, time_series_data, average_data, survey_data
