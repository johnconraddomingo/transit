"""
CSV exporter for saving metrics to CSV files.
"""

import os
import csv


class CSVExporter:
    """
    Exports metrics data to CSV files.
    """ 

    def export_consolidated(self, consolidated_data, output_path):
        """
        Export consolidated metrics to a CSV file with one metric per row.
        
        Args:
            consolidated_data (dict): Dictionary with metric names as keys and values
            output_path (str): Path to save the CSV file
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write each metric on its own row
            for metric, value in consolidated_data.items():
                csv_writer.writerow([metric, value])