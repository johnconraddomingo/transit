"""
Bitbucket data source for retrieving metrics from a Bitbucket server.
This package provides modules to connect to a Bitbucket server and extract metrics.
"""

from .client import BitbucketClient
from .cache import BitbucketCache
from .metrics import BitbucketMetrics

class BitbucketDataSource:
    """
    Data source for connecting to a Bitbucket server and retrieving metrics.
    Acts as a facade for the underlying implementation.
    """
    def __init__(self, base_url, token=None, username=None, password=None, max_workers=10, requests_per_second=5):
        """
        Initialize the BitbucketDataSource.
       
        Args:
            base_url (str): Base URL of the Bitbucket server
            token (str, optional): Authentication token for API access
            username (str, optional): Username for basic authentication
            password (str, optional): Password for basic authentication
            max_workers (int, optional): Maximum number of concurrent API requests
            requests_per_second (int, optional): Maximum number of requests per second (rate limit)
       
        Note:
            Either token OR username/password must be provided for authentication.
        """
        self.client = BitbucketClient(base_url, token, username, password, max_workers, requests_per_second)
        self.cache = BitbucketCache(self.client.logger)
        self.metrics = BitbucketMetrics(self.client, self.cache)

    def get_merged_prs(self, project_path, year, month):
        """
        Get the number of merged pull requests for a specific project and month.
       
        Args:
            project_path (str): Project path in format "PROJECT/REPO"
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            int: Number of merged pull requests
        """
        return self.metrics.get_merged_prs(project_path, year, month)
   
    def get_pr_review_time(self, project_path, year, month):
        """
        Get the average PR review time (creation to approval) for a specific project and month.
       
        Args:
            project_path (str): Project path in format "PROJECT/REPO"
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            float: Average PR review time in hours (rounded to 2 decimal places) or 0 if no PRs
        """
        return self.metrics.get_pr_review_time(project_path, year, month)
    
    def cleanup_cache(self):
        """Clean up temporary cache file when done."""
        self.cache.cleanup()
