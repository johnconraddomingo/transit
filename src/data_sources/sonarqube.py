"""
SonarQube data source for retrieving metrics from a SonarQube server.
"""

import requests
from datetime import datetime
import calendar
from urllib.parse import urljoin


class SonarQubeDataSource:
    """
    Data source for connecting to a SonarQube server and retrieving metrics.
    """
    
    def __init__(self, base_url, token=None, username=None, password=None):
        """
        Initialize the SonarQubeDataSource.
        
        Args:
            base_url (str): Base URL of the SonarQube server
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
            # SonarQube uses token as username and empty password for token auth
            self.auth = (token, '')
        elif username and password:
            self.auth = (username, password)
        else:
            raise ValueError("Either token or username/password must be provided for authentication")
    
    def get_bugs(self, project_key, year, month):
        """
        Get the number of bugs for a specific project and month.
        
        Args:
            project_key (str): SonarQube project key
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
            
        Returns:
            int: Number of bugs reported by SonarQube
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API
        from_date = f"{year}-{month}-01T00:00:00+0000"
        to_date = f"{year}-{month}-{last_day}T23:59:59+0000"
        
        # Construct API endpoint for issues
        api_endpoint = "/api/issues/search"
        url = urljoin(self.base_url, api_endpoint)
        
        # Parameters for the API request
        params = {
            'componentKeys': project_key,
            'types': 'BUG',
            'createdAfter': from_date,
            'createdBefore': to_date,
            'ps': 1,  # Page size, we only need the count
            'facets': 'types'  # Include facets to get counts
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, auth=self.auth)
            response.raise_for_status()
            data = response.json()
            
            # Return the count of bugs
            return data.get('total', 0)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching bugs from SonarQube: {e}")
            return 0
