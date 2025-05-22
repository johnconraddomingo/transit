"""
Metrics collector module that orchestrates data collection from various sources.
"""

class MetricsCollector:
    """
    Collector for metrics from various data sources.
    This class manages the data sources and maps metric types to the appropriate sources.
    """
    
    def __init__(self):
        """Initialize the MetricsCollector with empty data sources and mappings."""
        self.data_sources = {}
        self.metric_mappings = {
            'merged_pr': ('bitbucket', 'get_merged_prs')
        }
    
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
            print(f"Warning: Unknown metric type '{metric_type}'")
            return None
            
        source_name, method_name = self.metric_mappings[metric_type]
        
        if source_name not in self.data_sources:
            print(f"Warning: Data source '{source_name}' not registered")
            return None
            
        data_source = self.data_sources[source_name]
        method = getattr(data_source, method_name)
        
        try:
            return method(project, year, month)
        except Exception as e:
            print(f"Error collecting metric '{metric_type}' for project '{project}': {e}")
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
