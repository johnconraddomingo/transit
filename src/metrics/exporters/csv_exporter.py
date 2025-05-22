"""
CSV exporter for saving metrics to CSV files.
"""

import os
import csv


class CSVExporter:
    """
    Exports metrics data to CSV files.
    """
    
    def export(self, results, output_path):
        """
        Export the collected metrics to a CSV file.
        
        Args:
            results (dict): Dictionary containing metrics results by project
            output_path (str): Base path for the output file
                
        Returns:
            str: Path to the exported file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Initialize counters to aggregate metrics across projects
        aggregated_metrics = {}
        
        # Aggregate metrics across all projects
        for project, metrics in results.items():
            for metric_name, value in metrics.items():
                if metric_name not in aggregated_metrics:
                    aggregated_metrics[metric_name] = 0
                
                if value is not None:  # Only add valid values
                    aggregated_metrics[metric_name] += value
        
        # Write the aggregated metrics to CSV
        with open(output_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write each metric and its value
            for metric_name, value in aggregated_metrics.items():
                csv_writer.writerow([metric_name, value])
        
        return output_path
