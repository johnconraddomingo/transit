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
from src.data_sources.jira import JiraDataSource
from src.data_sources.jenkins import JenkinsDataSource
from src.data_sources.github import GitHubDataSource
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
        print(f"Error: Invalid year-month format. Expected YYYY-MM, got {args.year_month}")
        sys.exit(1)
    
    # Load configurations
    projects_config = load_config('projects.json')
    servers_config = load_config('servers.json')
    tokens_config = load_config('tokens.json')
    
    # Initialize collector
    collector = MetricsCollector()
    
    # Initialize enabled data sources
    if servers_config['servers']['bitbucket'].get('enabled', True):
        bitbucket_url = servers_config['servers']['bitbucket']['url']
        bitbucket_auth = tokens_config.get('bitbucket', {})
        bitbucket = BitbucketDataSource(bitbucket_url, **bitbucket_auth)
        collector.register_data_source('bitbucket', bitbucket)
        
    if servers_config['servers']['sonarqube'].get('enabled', True):
        sonarqube_url = servers_config['servers']['sonarqube']['url']
        sonarqube_auth = tokens_config.get('sonarqube', {})
        sonarqube = SonarQubeDataSource(sonarqube_url, **sonarqube_auth)
        collector.register_data_source('sonarqube', sonarqube)
          
    if servers_config['servers']['jira'].get('enabled', True):
        jira_url = servers_config['servers']['jira']['url']
        jira_auth = tokens_config.get('jira', {})
        jira = JiraDataSource(jira_url, **jira_auth)
        collector.register_data_source('jira', jira)
          
    if servers_config['servers']['jenkins'].get('enabled', True):
        jenkins_url = servers_config['servers']['jenkins']['url']
        jenkins_auth = tokens_config.get('jenkins', {})
        jenkins = JenkinsDataSource(jenkins_url, **jenkins_auth)
        collector.register_data_source('jenkins', jenkins)
        
    if servers_config['servers']['github'].get('enabled', True):
        github_url = servers_config['servers']['github']['url']
        github_auth = tokens_config.get('github', {})
        github = GitHubDataSource(github_url, **github_auth)
        collector.register_data_source('github', github)
    
     # Initialize a single consolidated results dictionary for all projects
    consolidated_results = {
        'a_active_users': 0,
        'a_ai_adoption_rate': 0,
        'a_ai_usage': 0,
        'a_code_suggestions': 0,
        'a_code_accepted': 0,
        's_merged_prs': 0,
        's_pr_review_time': 0,
        's_story_points': 0,
        'q_code_smells': 0,
        'q_coverage': 0,
        'q_bugs': 0,
        'q_vulnerabilities': 0,
        'd_deployment_frequency': 0,
        'e_user_satisfaction': 0,
        'e_adoption': 0,
        'e_productivity': 0,
        'e_use_cases': 0
    }

    # Track the number of projects for averaging percentage metrics
    percentage_metrics = ['a_ai_adoption_rate', 'a_ai_usage', 'q_coverage', 
                          'e_user_satisfaction', 'e_adoption', 'e_productivity']
    project_count = len(projects_config['projects'])
    
    # Get organization name from config upfront
    org_name = projects_config['organisation']

    # Extract year and month for later use
    year, month = args.year_month.split('-')
    
    for project in projects_config['projects']:
        print(f"Collecting metrics for project: {project}")
        
        # Collect merged PRs
        merged_prs = collector.collect_metric('merged_pr', project, year, month)
        consolidated_results['s_merged_prs'] += merged_prs
        
        # Collect PR review time
        pr_review_time = collector.collect_metric('pr_review_time', project, year, month)
        consolidated_results['s_pr_review_time'] += pr_review_time
        
        # Collect bugs from SonarQube
        bugs = collector.collect_metric('bugs', project, year, month)
        consolidated_results['q_bugs'] += bugs
        
        # Collect code smells from SonarQube
        code_smells = collector.collect_metric('code_smells', project, year, month)
        consolidated_results['q_code_smells'] += code_smells

        # Collect code coverage
        code_coverage = collector.collect_metric('code_coverage', project, year, month)
        consolidated_results['q_coverage'] += code_coverage

        # Collect vulnerabilities from SonarQube
        vulnerabilities = collector.collect_metric('vulnerabilities', project, year, month)
        consolidated_results['q_vulnerabilities'] += vulnerabilities
        
        # Collect story points from JIRA
        story_points = collector.collect_metric('story_points', project, year, month)
        consolidated_results['s_story_points'] += story_points
        
        # Process deployment frequency
        if 'deployments' in projects_config:
            for deployment in projects_config['deployments']:
                deployment_freq = collector.collect_metric('deployment_frequency', deployment, year, month)
                consolidated_results['d_deployment_frequency'] += deployment_freq
        
    # Process deployment frequency 
    if 'deployments' in projects_config:
        print("Collecting deployment metrics...")
        for deployment in projects_config['deployments']:
            deployment_freq = collector.collect_metric('deployment_frequency', deployment, year, month)
            consolidated_results['d_deployment_frequency'] += deployment_freq
    
    # Collect organization-wide metrics once (for GitHub/Copilot metrics)
    consolidated_results['a_active_users'] = collector.collect_metric('active_users', org_name, year, month)
    consolidated_results['a_ai_usage'] = collector.collect_metric('ai_usage', org_name, year, month)
    consolidated_results['a_code_suggestions'] = collector.collect_metric('suggested_lines', org_name, year, month)
    consolidated_results['a_code_accepted'] = collector.collect_metric('accepted_lines', org_name, year, month)
    consolidated_results['a_ai_adoption_rate'] = collector.collect_metric('adoption_rate', org_name, year, month)
    
    # Average the percentage metrics
    for metric in percentage_metrics:
        if metric == 'q_coverage':  # This one was collected per project
            consolidated_results[metric] /= project_count
    
    # Export consolidated results to CSV
    exporter = CSVExporter()
    output_path = os.path.join(os.path.dirname(__file__), 'ongoing', f"{args.year_month}.csv")
    exporter.export_consolidated(consolidated_results, output_path)
    
    print(f"Metrics collection completed. Results exported to {output_path}")

if __name__ == "__main__":
    main()
