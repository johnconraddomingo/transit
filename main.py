"""
Metrics Collection Application

This script collects metrics from various data sources for a specified month
across predefined projects.
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Add the src directory to the path so we can import modules from there
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

# Now import the modules
from src.data_sources.bitbucket import BitbucketDataSource
from src.data_sources.sonarqube import SonarQubeDataSource
from src.metrics.collector import MetricsCollector
from src.metrics.exporters.csv_exporter import CSVExporter

def load_config(config_file):
    """Load a configuration file from the config directory."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', config_file)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file {config_file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Configuration file {config_file} is not valid JSON.")
        sys.exit(1)

def validate_year_month(year_month):
    """Validate that the provided year-month string is in the correct format."""
    try:
        datetime.strptime(year_month, "%Y-%m")
        return True
    except ValueError:
        return False

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Collect metrics for projects.')
    parser.add_argument('year_month', help='Year and month in format YYYY-MM (e.g. 2025-05)')
    args = parser.parse_args()
    
    # Validate year_month format
    if not validate_year_month(args.year_month):
        print(f"Error: Invalid year-month format: {args.year_month}. Expected format: YYYY-MM (e.g. 2025-05)")
        sys.exit(1)
    
    # Extract year and month for later use
    year, month = args.year_month.split('-')
    
    # Load configurations
    projects_config = load_config('projects.json')
    servers_config = load_config('servers.json')
    auth_config = load_config('tokens.json')
    
    # Create metrics collector
    collector = MetricsCollector()
      # Register data sources
    # Create Bitbucket data source with appropriate authentication
    bitbucket_auth = auth_config.get('bitbucket', {})
    
    # Determine authentication method for Bitbucket
    if 'token' in bitbucket_auth and bitbucket_auth['token']:
        # Token authentication
        bitbucket_source = BitbucketDataSource(
            base_url=servers_config['servers']['bitbucket'],
            token=bitbucket_auth['token']
        )
    elif 'username' in bitbucket_auth and 'password' in bitbucket_auth:
        # Username/password authentication
        bitbucket_source = BitbucketDataSource(
            base_url=servers_config['servers']['bitbucket'],
            username=bitbucket_auth['username'],
            password=bitbucket_auth['password']
        )
    else:
        print("Error: No valid authentication method found for Bitbucket.")
        print("Please provide either 'token' or 'username' and 'password' in tokens.json")
        sys.exit(1)
    
    # Register Bitbucket data source
    collector.register_data_source('bitbucket', bitbucket_source)
    
    # Create SonarQube data source with appropriate authentication
    sonarqube_auth = auth_config.get('sonarqube', {})
    
    # Determine authentication method for SonarQube
    if 'token' in sonarqube_auth and sonarqube_auth['token']:
        # Token authentication
        sonarqube_source = SonarQubeDataSource(
            base_url=servers_config['servers']['sonarqube'],
            token=sonarqube_auth['token']
        )
    elif 'username' in sonarqube_auth and 'password' in sonarqube_auth:
        # Username/password authentication
        sonarqube_source = SonarQubeDataSource(
            base_url=servers_config['servers']['sonarqube'],
            username=sonarqube_auth['username'],
            password=sonarqube_auth['password']
        )
    else:
        print("Error: No valid authentication method found for SonarQube.")
        print("Please provide either 'token' or 'username' and 'password' in tokens.json")
        sys.exit(1)
    
    # Register SonarQube data source
    collector.register_data_source('sonarqube', sonarqube_source)
      # Collect metrics for all projects
    results = {}
    for project in projects_config['projects']:
        print(f"Collecting metrics for project: {project}")
        
        if project not in results:
            results[project] = {}
          # Collect merged PRs - this will automatically use the bitbucket datasource
        merged_prs = collector.collect_metric('merged_pr', project, year, month)
        results[project]['s_merged_prs'] = merged_prs
          # Collect bugs from SonarQube - this will automatically use the sonarqube datasource
        # For SonarQube, we use the same project identifier as it should match the SonarQube project key
        bugs = collector.collect_metric('bugs', project, year, month)
        results[project]['q_bugs'] = bugs
    
    # Export results to CSV
    exporter = CSVExporter()
    output_path = os.path.join(os.path.dirname(__file__), 'ongoing', args.year_month)
    exporter.export(results, output_path)
    
    print(f"Metrics collection completed. Results exported to {output_path}")

if __name__ == "__main__":
    main()
