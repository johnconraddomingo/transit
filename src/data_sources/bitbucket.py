"""
Bitbucket data source for retrieving metrics from a Bitbucket server.
"""

import requests
from datetime import datetime
import calendar
from urllib.parse import urljoin


class BitbucketDataSource:
    """
    Data source for connecting to a Bitbucket server and retrieving metrics.
    """
    
    def __init__(self, base_url, token=None, username=None, password=None):
        """
        Initialize the BitbucketDataSource.
        
        Args:
            base_url (str): Base URL of the Bitbucket server
            token (str, optional): Authentication token for API access
            username (str, optional): Username for basic authentication
            password (str, optional): Password for basic authentication
        
        Note:
            Either token OR username/password must be provided for authentication.
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.username = username
        self.password = password
        
        # Set up authentication headers
        self.headers = {
            'Accept': 'application/json'
        }
        
        # Set up authentication method
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
            self.auth = None
        elif username and password:
            self.auth = (username, password)
        else:
            raise ValueError("Either token or username/password must be provided for authentication")
    
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
        # Split project path into project and repo parts
        project, repo = project_path.split('/')
        
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API
        start_date = f"{year}-{month}-01T00:00:00.000Z"
        end_date = f"{year}-{month}-{last_day}T23:59:59.999Z"
        
        # Construct API endpoint for pull requests
        api_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests"
        url = urljoin(self.base_url, api_endpoint)
        
        # Parameters for the API request
        params = {
            'state': 'MERGED',
            'mergedSince': start_date,
            'mergedUntil': end_date,
            'limit': 1000  # Adjust as needed, may need pagination for large repos
        }
        
        try:
            if self.auth:
                response = requests.get(url, headers=self.headers, params=params, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers, params=params)
                
            response.raise_for_status()
            data = response.json()
            
            # Return the count of merged PRs
            return data.get('size', 0)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching merged PRs from Bitbucket: {e}")
            return 0
