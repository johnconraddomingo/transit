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
        api_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests?state=ALL&limit=100"
        url = urljoin(self.base_url, api_endpoint)
        all_prs = []
        start = 0
        while True:
            paged_url = f"{url}&start={start}"
            self.logger.info(3, f"Fetching PRs page starting at {start} for {project_path}")
            try:
                if self.auth:
                    response = requests.get(paged_url, headers=self.headers, auth=self.auth)
                else:
                    response = requests.get(paged_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                page_prs = data.get('values', [])
                if not page_prs:
                    break
                all_prs.extend(page_prs)
                if data.get('isLastPage', True):
                    break
                start = data.get('nextPageStart', start + len(page_prs))
            except requests.exceptions.RequestException as e:
                self.logger.error(3, f"Error fetching PRs page: {e}")
                break
 
        self.logger.info(3, f"Total PRs fetched: {len(all_prs)}. Now fetching details for each PR.")
        detailed_prs = []
        for pr in all_prs:
            pr_id = pr.get('id')
            if not pr_id:
                continue
            pr_detail_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests/{pr_id}"
            pr_detail_url = urljoin(self.base_url, pr_detail_endpoint)
            self.logger.info(4, f"Fetching details for PR #{pr_id}")
            try:
                if self.auth:
                    pr_detail_response = requests.get(pr_detail_url, headers=self.headers, auth=self.auth)
                else:
                    pr_detail_response = requests.get(pr_detail_url, headers=self.headers)
                pr_detail_response.raise_for_status()
                pr_detail = pr_detail_response.json()
                detailed_prs.append(pr_detail)
            except requests.exceptions.RequestException as e:
                self.logger.error(3, f"Error fetching details for PR {pr_id}: {e}")
                continue
        self.logger.info(3, f"Fetched details for {len(detailed_prs)} PRs in {project_path}")
       
        # Convert start and end dates to UTC timestamps in milliseconds for comparison
        # Bitbucket API uses UTC timestamps (in milliseconds since epoch)
        from dateutil import parser
       
        # Parse ISO format dates with timezone info
        start_dt = parser.parse(start_date)
        end_dt = parser.parse(end_date)
       
        # Convert to milliseconds timestamp (same format as Bitbucket API)
        start_timestamp = int(start_dt.timestamp() * 1000)
        end_timestamp = int(end_dt.timestamp() * 1000)
 
        self.logger.info(3, f"Filtering merged PRs between {start_date} and {end_date} (timestamps: {start_timestamp} - {end_timestamp})")
 
         # Filter PRs by closedDate that fall within our date range
        filtered_prs = [
            pr for pr in detailed_prs
            if pr.get('closedDate')
            and start_timestamp <= pr.get('closedDate') <= end_timestamp
            and pr.get('state', '').upper() == 'MERGED'
        ]
       
        pr_count = len(filtered_prs)
        self.logger.info(3, f"Found {pr_count} merged PRs in {project_path} for {year}-{month}")
       
        # Return the count of PRs that were closed within the date range
        return pr_count
   
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
       
        # Fetch all PRs using paging and get their full details
        api_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests?state=ALL&limit=100"
        url = urljoin(self.base_url, api_endpoint)
        all_prs = []
        start = 0
        while True:
            paged_url = f"{url}&start={start}"
            self.logger.info(3, f"Fetching PRs page starting at {start} for {project_path}")
            try:
                if self.auth:
                    response = requests.get(paged_url, headers=self.headers, auth=self.auth)
                else:
                    response = requests.get(paged_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                page_prs = data.get('values', [])
                if not page_prs:
                    break
                all_prs.extend(page_prs)
                if data.get('isLastPage', True):
                    break
                start = data.get('nextPageStart', start + len(page_prs))
            except requests.exceptions.RequestException as e:
                self.logger.error(3, f"Error fetching PRs page: {e}")
                break
 
        self.logger.info(3, f"Total PRs fetched: {len(all_prs)}. Now fetching details for each PR.")
        detailed_prs = []
        for pr in all_prs:
            pr_id = pr.get('id')
            if not pr_id:
                continue
            pr_detail_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests/{pr_id}"
            pr_detail_url = urljoin(self.base_url, pr_detail_endpoint)
            self.logger.info(4, f"Fetching details for PR #{pr_id}")
            try:
                if self.auth:
                    pr_detail_response = requests.get(pr_detail_url, headers=self.headers, auth=self.auth)
                else:
                    pr_detail_response = requests.get(pr_detail_url, headers=self.headers)
                pr_detail_response.raise_for_status()
                pr_detail = pr_detail_response.json()
                detailed_prs.append(pr_detail)
            except requests.exceptions.RequestException as e:
                self.logger.error(3, f"Error fetching details for PR {pr_id}: {e}")
                continue
        self.logger.info(3, f"Fetched details for {len(detailed_prs)} PRs in {project_path}")
 
        # Calculate PR review time (creation to approval) for all PRs
        from dateutil import parser
        import pytz
        aus_timezone = pytz.timezone('Australia/Sydney')
        start_dt = parser.parse(start_date).astimezone(aus_timezone)
        end_dt = parser.parse(end_date).astimezone(aus_timezone)
        start_timestamp = int(start_dt.timestamp() * 1000)
        end_timestamp = int(end_dt.timestamp() * 1000)
 
        total_review_time = 0
        pr_count = 0
        for pr in detailed_prs:
            created_date = pr.get('createdDate')
            pr_id = pr.get('id')
            # Fetch activities for each PR to find approval
            pr_activities_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests/{pr_id}/activities"
            pr_activities_url = urljoin(self.base_url, pr_activities_endpoint)
            approval_date = None
            try:
                if self.auth:
                    activities_response = requests.get(pr_activities_url, headers=self.headers, auth=self.auth)
                else:
                    activities_response = requests.get(pr_activities_url, headers=self.headers)
                activities_response.raise_for_status()
                activities = activities_response.json().get('values', [])
                for activity in activities:
                    if activity.get('action') == 'APPROVED':
                        approval_date = activity.get('createdDate')
                        break
            except requests.exceptions.RequestException as e:
                self.logger.error(3, f"Error fetching activities for PR {pr_id}: {e}")
                continue
            if created_date and approval_date and start_timestamp <= approval_date <= end_timestamp:
                created_datetime = datetime.fromtimestamp(created_date / 1000)
                approval_datetime = datetime.fromtimestamp(approval_date / 1000)
                review_time = (approval_datetime - created_datetime).total_seconds() / 3600
                total_review_time += review_time
                pr_count += 1
                self.logger.info(4, f"PR #{pr_id} review time: {review_time:.2f} hours")
        if pr_count > 0:
            avg_review_time = total_review_time / pr_count
            avg_review_time_rounded = round(avg_review_time, 2)
            self.logger.info(3, f"Average PR review time for {project_path}: {avg_review_time_rounded:.2f} hours")
            return avg_review_time_rounded
        else:
            self.logger.info(3, f"No PRs with approval found for {project_path} in {year}-{month}")
            return 0