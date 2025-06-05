"""
Metrics Collection Application
 
This script collects metrics from various data sources for a specified month
across predefined pro    for project in projects_config['projects']:
        logger.info(f"\n=== Collecting metrics for project: {project} ===")
       
        # Collect merged PRs
        merged_prs = collector.collect_metric('merged_pr', project, year, month)
        if merged_prs is not None:
            consolidated_results['s_merged_prs'] += merged_prs
            logger.info(f"✓ Merged PRs: {merged_prs}")
        else:
            logger.warning(f"⚠ No merged PR data available for {project}")
"""
 
import argparse
import json
import os
import sys
import logging
from datetime import datetime
 
# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
 
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
        logger.error(f"Configuration file {config_file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Configuration file {config_file} is not valid JSON.")
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
        logger.error(f"Invalid year-month format. Expected YYYY-MM, got {args.year_month}")
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
    }    # Track the number of projects for averaging percentage metrics
    percentage_metrics = ['a_ai_adoption_rate', 'a_ai_usage',
                          'e_user_satisfaction', 'e_adoption', 'e_productivity']
    project_count = len(projects_config['projects'])
   
    # Track scan count for averaging code coverage
    scan_count = len(projects_config.get('scans', []))
   
    # Counter for projects with valid PR review time data
    pr_review_time_count = 0    
    # Get organization name from config upfront
    org_name = projects_config['organisation']
   
    # Counter for scans with valid coverage data
    coverage_scan_count = 0
 
    # Extract year and month for later use
    year, month = args.year_month.split('-')
   
    for project in projects_config['projects']:
        logger.info(f"Collecting metrics for project: {project}")
       
        # Collect merged PRs
        merged_prs = collector.collect_metric('merged_pr', project, year, month)
        if merged_prs is not None:
            consolidated_results['s_merged_prs'] += merged_prs
           
        # Collect PR review time - store sum temporarily and track count for averaging later
        pr_review_time = collector.collect_metric('pr_review_time', project, year, month)
        if pr_review_time is not None and pr_review_time > 0:
            consolidated_results['s_pr_review_time'] += pr_review_time
            pr_review_time_count += 1
            logger.info(f"✓ PR Review Time: {pr_review_time}")
        else:
            logger.warning(f"⚠ No PR review time data available for {project}")
 
        # Collect story points from JIRA        
        story_points = collector.collect_metric('story_points', project, year, month)
        if story_points is not None:
            consolidated_results['s_story_points'] += story_points
            logger.info(f"✓ Story Points: {story_points}")
        else:
            logger.warning(f"⚠ No story points data available from JIRA for {project}")
       
        logger.info(f"=== Completed collecting metrics for project: {project} ===\n")
   
    # Process SonarQube metrics from scans
    if 'scans' in projects_config:
        logger.info("\n=== Collecting SonarQube Metrics ===")
        for scan in projects_config['scans']:
            logger.info(f"Collecting SonarQube metrics for scan: {scan}")
           
            # Collect bugs from SonarQube
            bugs = collector.collect_metric('bugs', scan, year, month)
            if bugs is not None:
                consolidated_results['q_bugs'] += bugs
                logger.info(f"✓ SonarQube Bugs: {bugs}")
            else:
                logger.warning(f"⚠ No bug data available from SonarQube for {scan}")
             
            # Collect code smells from SonarQube
            code_smells = collector.collect_metric('code_smells', scan, year, month)
            if code_smells is not None:
                consolidated_results['q_code_smells'] += code_smells
                logger.info(f"✓ Code Smells: {code_smells}")
            else:
                logger.warning(f"⚠ No code smells data available from SonarQube for {scan}")
 
            # Collect vulnerabilities from SonarQube
            vulnerabilities = collector.collect_metric('vulnerabilities', scan, year, month)
            if vulnerabilities is not None:
                consolidated_results['q_vulnerabilities'] += vulnerabilities
                logger.info(f"✓ Vulnerabilities: {vulnerabilities}")
            else:
                logger.warning(f"⚠ No vulnerability data available from SonarQube for {scan}")            # Collect code coverage
            code_coverage = collector.collect_metric('code_coverage', scan, year, month)
            if code_coverage is not None:
                consolidated_results['q_coverage'] += code_coverage
                coverage_scan_count += 1
                logger.info(f"✓ Code Coverage: {code_coverage}%")
            else:
                logger.warning(f"⚠ No code coverage data available from SonarQube for {scan}")
               
            logger.info(f"=== Completed collecting SonarQube metrics for scan: {scan} ===\n")
        logger.info("=== Completed collecting SonarQube metrics ===\n")
     
    # Process deployment frequency
    if 'deployments' in projects_config:
        logger.info("\n=== Collecting Deployment Metrics ===")
        for deployment in projects_config['deployments']:
            deployment_freq = collector.collect_metric('deployment_frequency', deployment, year, month)
            if deployment_freq is not None:
                consolidated_results['d_deployment_frequency'] += deployment_freq
                logger.info(f"✓ Deployment Frequency for {deployment}: {deployment_freq}")
            else:
                logger.warning(f"⚠ No deployment frequency data available for {deployment}")
        logger.info("=== Completed collecting deployment metrics ===\n")    # Collect organization-wide metrics once (for GitHub/Copilot metrics)
    logger.info(f"\n=== Collecting Organization-wide Metrics for {org_name} ===")
   
    active_users = collector.collect_metric('active_users', org_name, year, month)
    if active_users is not None:
        consolidated_results['a_active_users'] = active_users
        logger.info(f"✓ Active Users: {active_users}")
    else:
        logger.warning("⚠ No active users data available")
   
    ai_usage = collector.collect_metric('ai_usage', org_name, year, month)
    if ai_usage is not None:
        consolidated_results['a_ai_usage'] = ai_usage
        logger.info(f"✓ AI Usage: {ai_usage}")
    else:
        logger.warning("⚠ No AI usage data available")
   
    code_suggestions = collector.collect_metric('suggested_lines', org_name, year, month)
    if code_suggestions is not None:
        consolidated_results['a_code_suggestions'] = code_suggestions
        logger.info(f"✓ Code Suggestions: {code_suggestions}")
    else:
        logger.warning("⚠ No code suggestions data available")
   
    code_accepted = collector.collect_metric('accepted_lines', org_name, year, month)
    if code_accepted is not None:
        consolidated_results['a_code_accepted'] = code_accepted
        logger.info(f"✓ Code Accepted: {code_accepted}")
    else:
        logger.warning("⚠ No code accepted data available")
   
    ai_adoption_rate = collector.collect_metric('adoption_rate', org_name, year, month)
    if ai_adoption_rate is not None:
        consolidated_results['a_ai_adoption_rate'] = ai_adoption_rate
        logger.info(f"✓ AI Adoption Rate: {ai_adoption_rate}")
    else:
        logger.warning("⚠ No AI adoption rate data available")
   
    logger.info("=== Completed collecting organization-wide metrics ===\n")
   
    # Calculate average PR review time
    if pr_review_time_count > 0:
        consolidated_results['s_pr_review_time'] = consolidated_results['s_pr_review_time'] / pr_review_time_count
      # Average the percentage metrics
    for metric in percentage_metrics:
        consolidated_results[metric] /= project_count
      # Average code coverage separately using count of scans with actual coverage data
    if coverage_scan_count > 0:
        consolidated_results['q_coverage'] /= coverage_scan_count
        logger.info(f"Average Code Coverage across {coverage_scan_count} scans: {consolidated_results['q_coverage']}%")
   
    # Export consolidated results to CSV
    exporter = CSVExporter()
    output_path = os.path.join(os.path.dirname(__file__), 'ongoing', f"{args.year_month}.csv")
    exporter.export(consolidated_results, output_path)
   
    logger.info(f"Metrics collection completed. Results exported to {output_path}")
 
if __name__ == "__main__":
    main()
 