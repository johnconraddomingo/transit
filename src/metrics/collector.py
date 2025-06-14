"""
Metrics collector module that orchestrates data collection from various sources.
"""
 # Import our custom logger
from src.utils.logger import get_logger
logger = get_logger(__name__)
 
class MetricsCollector:
    """
    Collector for metrics from various data sources.
    This class manages the data sources and maps metric types to the appropriate sources.
    """
    def __init__(self):
        """Initialize the MetricsCollector with empty data sources and mappings."""
        self.data_sources = {}
        self.metric_mappings = {
            'active_users': ('github', 'get_active_users'),
            'adoption_rate': ('github', 'get_copilot_adoption_rate'),
            'ai_usage': ('github', 'get_ai_usage'),
            'suggested_lines': ('github', 'get_copilot_suggested_lines'),
            'accepted_lines': ('github', 'get_copilot_accepted_lines'),
            'merged_pr': ('bitbucket', 'get_merged_prs'),
            'pr_review_time': ('bitbucket', 'get_pr_review_time'),            
            'story_points': ('jira', 'get_story_points'),
            'code_smells': ('sonarqube', 'get_code_smells'),
            'code_coverage': ('sonarqube', 'get_coverage'),
            'bugs': ('sonarqube', 'get_bugs'),            
            'vulnerabilities': ('sonarqube', 'get_vulnerabilities'),
            'deployment_frequency': ('jenkins', 'get_deployment_frequency'),
        }
        self.logger = logger
   
    def register_data_source(self, name, data_source):
        """
        Register a data source with the collector.
       
        Args:
            name (str): Name of the data source
            data_source (object): Data source object
        """
        self.data_sources[name] = data_source  
    def collect_metric(self, metric_type, project, year, month):
        """
        Collect a specific metric for a given project and time period.
       
        Args:
            metric_type (str): Type of metric to collect (e.g., 'merged_pr')
            project (str): Project identifier
            year (str): Year to collect metrics for
            month (str): Month to collect metrics for
           
        Returns:
            The metric value or None if the metric cannot be collected
        """        
        if metric_type not in self.metric_mappings:
            self.logger.warning(2, f"Unknown metric type '{metric_type}'")
            return None
           
        source_name, method_name = self.metric_mappings[metric_type]
       
        if source_name not in self.data_sources:
            self.logger.warning(2, f"Data source '{source_name}' not registered")
            return None
           
        data_source = self.data_sources[source_name]
        method = getattr(data_source, method_name)
       
        try:
            return method(project, year, month)
        except Exception as e:
            self.logger.error(2, f"Error collecting metric '{metric_type}' for project '{project}': {e}")
            return None
   
    def register_metric(self, metric_type, source_name, method_name):
        """
        Register a new metric type with its corresponding data source and method.
       
        Args:
            metric_type (str): Identifier for the metric type
            source_name (str): Name of the data source
            method_name (str): Method name to call on the data source
        """
        self.metric_mappings[metric_type] = (source_name, method_name)