"""
JIRA data source for retrieving metrics from a JIRA server.
"""

import requests
from datetime import datetime
import calendar
from urllib.parse import urljoin
import json


class JiraDataSource:
    """
    Data source for connecting to a JIRA server and retrieving metrics.
    """
    
    def __init__(self, base_url, token=None, username=None, password=None):
        """
        Initialize the JiraDataSource.
        
        Args:
            base_url (str): Base URL of the JIRA server
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
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Set up authentication method
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
            self.auth = None
        elif username and password:
            self.auth = (username, password)
        else:
            raise ValueError("Either token or username/password must be provided for authentication")
    
    def get_story_points(self, project_key, year, month):
        """
        Get the completed story points for a specific project and month.
        
        Args:
            project_key (str): JIRA project key
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
            
        Returns:
            int: Number of completed story points for the given project and month
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API
        start_date = f"{year}-{month}-01"
        end_date = f"{year}-{month}-{last_day}"
        
        # Construct API endpoint for JQL search
        api_endpoint = "/rest/api/2/search"
        url = urljoin(self.base_url, api_endpoint)
        
        # JQL query to get completed issues within the time period with their story points
        jql = f'project = "{project_key}" AND status = "Done" AND resolution = "Done" AND resolutiondate >= "{start_date}" AND resolutiondate <= "{end_date}"'
        
        # Request payload with JQL query
        payload = {
            "jql": jql,
            "fields": ["customfield_10002"], # Assuming story points field is customfield_10002, may need adjustment
            "maxResults": 1000  # Adjust as needed, may need pagination for large projects
        }
        
        try:
            if self.auth:
                response = requests.post(url, headers=self.headers, data=json.dumps(payload), auth=self.auth)
            else:
                response = requests.post(url, headers=self.headers, data=json.dumps(payload))
                
            response.raise_for_status()
            data = response.json()
            
            # Sum up story points from all completed issues
            total_story_points = 0
            
            for issue in data.get('issues', []):
                story_points = issue.get('fields', {}).get('customfield_10002')
                if story_points is not None:
                    total_story_points += story_points
            
            return total_story_points
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching story points from JIRA: {e}")
            return 0
