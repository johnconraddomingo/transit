"""
GitHub data source for retrieving metrics from GitHub and GitHub Enterprise.
"""

import requests
from datetime import datetime
import calendar
from urllib.parse import urljoin
import json


class GitHubDataSource:
    """
    Data source for connecting to a GitHub/GitHub Enterprise server and retrieving metrics.
    """
    
    def __init__(self, base_url, token=None, username=None, password=None):
        """
        Initialize the GitHubDataSource.
        
        Args:
            base_url (str): Base URL of the GitHub server (api.github.com for public GitHub)
            token (str, optional): Personal access token for API access
            username (str, optional): Username for basic authentication (not preferred for GitHub)
            password (str, optional): Password for basic authentication (not preferred for GitHub)
        
        Note:
            Token authentication is strongly recommended for GitHub.
            Basic authentication is deprecated for GitHub API v3 but might be supported in GitHub Enterprise.
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        
        # Set up authentication headers
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'  # Specify GitHub API version
        }
        
        # GitHub API strongly prefers token authentication
        if token:
            self.headers['Authorization'] = f'token {token}'
            self.auth = None
        # Basic authentication is included but may not work for GitHub.com
        elif username and password:
            self.auth = (username, password)
            print("Warning: Basic authentication for GitHub API is deprecated. Token authentication is recommended.")
        else:
            raise ValueError("Authentication credentials must be provided. Token authentication is recommended.")
    
    def get_active_users(self, organization, year, month):
        """
        Get the number of active GitHub Copilot users for a specific organization and month.
        
        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
            
        Returns:
            int: Number of active GitHub Copilot users for the given organization and month
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API in ISO format
        start_date = f"{year}-{month}-01T00:00:00Z"
        end_date = f"{year}-{month}-{last_day}T23:59:59Z"
        
        # Construct API endpoint for Copilot users
        # Using GitHub Enterprise Reports API to get Copilot user data
        api_endpoint = f"/enterprises/{organization}/settings/billing/copilot"
        
        # For GitHub.com with GraphQL, we would use a different approach
        # But we're using the REST API here as an example
        url = urljoin(self.base_url, api_endpoint)
        
        try:
            # Query the GitHub API for Copilot users
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)
                
            response.raise_for_status()
            data = response.json()
            
            # Extract active users count from the response
            # The actual structure will depend on the GitHub API's response format
            active_users = data.get('active_users', 0)
            
            return active_users
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching GitHub Copilot active users: {e}")
            
            # For demonstration, if the enterprise API fails, try a fallback method
            # This could be a GraphQL query or another endpoint
            try:
                # Fallback to a simpler endpoint that might be available
                fallback_endpoint = f"/orgs/{organization}/copilot/billing"
                fallback_url = urljoin(self.base_url, fallback_endpoint)
                
                if self.auth:
                    response = requests.get(fallback_url, headers=self.headers, auth=self.auth)
                else:
                    response = requests.get(fallback_url, headers=self.headers)
                    
                response.raise_for_status()
                fallback_data = response.json()
                
                return fallback_data.get('active_seats', 0)
            except:
                # If all methods fail, return 0
                return 0
