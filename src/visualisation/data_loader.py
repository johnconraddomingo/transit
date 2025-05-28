"""
Data loader for the metrics visualization dashboard.
"""
import os
import csv
from collections import defaultdict
from datetime import datetime
import re


def load_csv_data(file_path):
    """
    Load data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dictionary with metric names as keys and values as values
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
    
    Args:
        filename: Filename to extract date from
        
    Returns:
        datetime object or None if no date pattern found
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
    
    Args:
        baseline_folder: Path to the baseline folder
        ongoing_folder: Path to the ongoing data folder
        
    Returns:
        Tuple of (baseline_data, time_series_data)
        where time_series_data is a dictionary with dates as keys
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
                else:
                    # Use filename as the key if date pattern not found
                    data = load_csv_data(file_path)
                    time_series_data[filename] = data
    
    return baseline_data, time_series_data


def get_metrics_by_category(metric_mapping):
    """
    Group metrics by their categories.
    
    Args:
        metric_mapping: Dictionary mapping metric keys to their metadata
        
    Returns:
        Dictionary with categories as keys and lists of metric keys as values
    """
    categories = defaultdict(list)
    
    for metric_key, metadata in metric_mapping.items():
        category = metadata.get('category', 'Uncategorized')
        categories[category].append(metric_key)
        
    return categories
