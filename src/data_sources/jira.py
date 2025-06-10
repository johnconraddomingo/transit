"""
JIRA data source for retrieving metrics from a JIRA server.
"""
 
import requests
from datetime import datetime
import calendar
from urllib.parse import urljoin
import json
from src.utils.logger import get_logger
 
 
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
        self.logger = get_logger("jira_data_source")
       
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
        # Make sure we're using the correct path with /jira/rest/api/2/search
        if '/jira/' not in self.base_url:
            # If base_url doesn't already have /jira/, add it
            api_endpoint = "/jira/rest/api/2/search"
        else:
            # If it already has /jira/, just use normal path
            api_endpoint = "/rest/api/2/search"
           
        url = urljoin(self.base_url, api_endpoint)
       
        # Create the JQL query for the project key
        jql = f'project = "{project_key}" AND status in (Done, Closed, Resolved) AND resolutiondate >= "{start_date}" AND resolutiondate <= "{end_date}"'
          # Request payload with JQL query
        payload = {
            "jql": jql,
            "fields": ["customfield_10010", "customfield_10026", "status", "resolutiondate"], # Try both common story point fields
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
            issues_with_points = 0
            issues_without_points = 0
           
            self.logger.info(3, f"Found {len(data.get('issues', []))} issues in {project_key} for {year}-{month}")
           
            for issue in data.get('issues', []):
                # Try multiple common story point fields - check customfield_10010 first (found in SNZPA1-2132)
                story_points = None
               
                # First try customfield_10010 (confirmed in our debug)
                story_points = issue.get('fields', {}).get('customfield_10010')
               
                # If not found, try customfield_10026 which is sometimes used
                if story_points is None:
                    story_points = issue.get('fields', {}).get('customfield_10026')
               
                issue_key = issue.get('key', 'Unknown')
                status = issue.get('fields', {}).get('status', {}).get('name', 'Unknown')
               
                if story_points is not None and isinstance(story_points, (int, float)):
                    total_story_points += story_points
                    issues_with_points += 1
                    self.logger.info(4, f"Issue {issue_key} (Status: {status}) has {story_points} story points")
                else:
                    issues_without_points += 1
           
            self.logger.info(3, f"Summary for {project_key}: Found {issues_with_points} issues with story points, {issues_without_points} issues without points")
            self.logger.info(3, f"Total story points: {total_story_points}")
           
            return total_story_points
           
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching story points from JIRA: {e}")
            return 0