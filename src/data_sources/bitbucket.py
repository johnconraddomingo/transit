"""
Bitbucket data source for retrieving metrics from a Bitbucket server.
"""
 
import requests
from datetime import datetime
import calendar
from urllib.parse import urljoin
from src.utils.logger import get_logger
 
 
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
        self.logger = get_logger("bitbucket_data_source")
       
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
        api_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests?state=MERGED"
        url = urljoin(self.base_url, api_endpoint)
         
        try:
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)
               
            response.raise_for_status()
            data = response.json()
             
            # Convert start and end dates to UTC timestamps in milliseconds for comparison
            # Bitbucket API uses UTC timestamps (in milliseconds since epoch)
            from dateutil import parser
           
            # Parse ISO format dates with timezone info
            start_dt = parser.parse(start_date)
            end_dt = parser.parse(end_date)
           
            # Convert to milliseconds timestamp (same format as Bitbucket API)
            start_timestamp = int(start_dt.timestamp() * 1000)
            end_timestamp = int(end_dt.timestamp() * 1000)
             # Filter PRs by closedDate that fall within our date range
            filtered_prs = [
                pr for pr in data.get('values', [])
                if pr.get('closedDate') and start_timestamp <= pr.get('closedDate') <= end_timestamp
            ]
           
            pr_count = len(filtered_prs)
            self.logger.info(3, f"Found {pr_count} merged PRs in {project_path} for {year}-{month}")
           
            # Return the count of PRs that were closed within the date range
            return pr_count
       
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching merged PRs from Bitbucket: {e}")
            return 0
   
    def get_pr_review_time(self, project_path, year, month):
        """
        Get the average PR review time (creation to approval) for a specific project and month.
       
        Args:
            project_path (str): Project path in format "PROJECT/REPO"
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            float: Average PR review time in hours or 0 if no PRs
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
        api_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests?state=MERGED"
        url = urljoin(self.base_url, api_endpoint)
         
        try:
            from dateutil import parser
            import pytz
           
            # Define Australian timezone (AEST/AEDT)
            aus_timezone = pytz.timezone('Australia/Sydney')
           
            # Parse ISO format dates with timezone info
            start_dt = parser.parse(start_date).astimezone(aus_timezone)
            end_dt = parser.parse(end_date).astimezone(aus_timezone)
           
            # Convert to milliseconds timestamp
            start_timestamp = int(start_dt.timestamp() * 1000)
            end_timestamp = int(end_dt.timestamp() * 1000)
           
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)
               
            response.raise_for_status()
            data = response.json()
             # Get PR details for calculating review time
            prs = data.get('values', [])
           
            if not prs:
                self.logger.info(3, f"No PRs found for {project_path} in {year}-{month}")
                return 0  # Return 0 if no PRs found
           
            total_review_time = 0
            pr_count = 0
           
            for pr in prs:
                # Extract creation timestamp
                created_date = pr.get('createdDate')
               
                # Get the approval date from the PR activities
                # Need to make another API call for each PR
                pr_id = pr.get('id')
               
                # Construct the activities URL properly using the base path
                pr_activities_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests/{pr_id}/activities"
                pr_activities_url = urljoin(self.base_url, pr_activities_endpoint)
               
                try:
                    if self.auth:
                        activities_response = requests.get(pr_activities_url, headers=self.headers, auth=self.auth)
                    else:
                        activities_response = requests.get(pr_activities_url, headers=self.headers)
                   
                    activities_response.raise_for_status()
                    activities = activities_response.json().get('values', [])
                   
                    # Find the first approval activity
                    approval_date = None
                    for activity in activities:
                        if activity.get('action') == 'APPROVED':
                            approval_date = activity.get('createdDate')
                            break
                   
                    # Check if approval date is within the specified date range
                    if created_date and approval_date and start_timestamp <= approval_date <= end_timestamp:
                        # Convert timestamps to datetime objects (timestamps are in milliseconds)
                        created_datetime = datetime.fromtimestamp(created_date / 1000)
                        approval_datetime = datetime.fromtimestamp(approval_date / 1000)
                         # Calculate review time in hours
                        review_time = (approval_datetime - created_datetime).total_seconds() / 3600
                       
                        total_review_time += review_time
                        pr_count += 1
                        self.logger.info(4, f"PR #{pr_id} review time: {review_time:.2f} hours")
                except requests.exceptions.RequestException as e:
                    self.logger.error(3, f"Error fetching activities for PR {pr_id}: {e}")
                    continue
             # Calculate the average review time
            if pr_count > 0:
                avg_review_time = total_review_time / pr_count
                self.logger.info(3, f"Average PR review time for {project_path}: {avg_review_time:.2f} hours")
                return avg_review_time
            else:
                self.logger.info(3, f"No PRs with approval found for {project_path} in {year}-{month}")
                return 0
       
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching PR review time from Bitbucket: {e}")
            return 0
 