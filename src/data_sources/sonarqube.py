"""
SonarQube data source for retrieving metrics from a SonarQube server.
"""
 
import requests
from datetime import datetime, timedelta
import calendar
from urllib.parse import urljoin
from src.utils.logger import get_logger
 
 
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
            Either token OR username/password must be provided for authentication.        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.username = username
        self.logger = get_logger("sonarqube_data_source")
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
   
    def _get_issues(self, project_key, year, month, issue_type):
        """
        Private helper method to get the number of issues of a specific type for a project and month.
       
        Args:
            project_key (str): SonarQube project key
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
            issue_type (str): Type of issue (BUG, CODE_SMELL, VULNERABILITY)
           
        Returns:
            int: Number of issues reported by SonarQube
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
       
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
       
        # Format dates for the API
        from_date = f"{year}-{month}-01"
        # Add one day to last_day to make to_date inclusive
        to_date_dt = datetime(year_int, month_int, last_day) + timedelta(days=1)
        to_date = to_date_dt.strftime("%Y-%m-%d")
       
        # Construct API endpoint for issues
        api_endpoint = "/api/issues/search"
        url = urljoin(self.base_url, api_endpoint)
 
        # Parameters for the API request
        # Queries all statuses on all branches for the given date range
        params = f'componentKeys={project_key}:&types={issue_type}&ps=1&facets=types&createdAfter={from_date}&createdBefore={to_date}'
 
        try:
            # Convert params to query string and append to URL
            url_with_params = f"{url}?{params}"
            # Make request with params in URL
            response = requests.get(url_with_params, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            data = response.json()
             
            # Return the count of issues
            return data.get('total', 0)
           
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching {issue_type} from SonarQube: {e}")
            return 0
   
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
        return self._get_issues(project_key, year, month, "BUG")
 
    def get_code_smells(self, project_key, year, month):
        """
        Get the number of code smells for a specific project and month.
       
        Args:
            project_key (str): SonarQube project key
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            int: Number of code smells reported by SonarQube
        """
        return self._get_issues(project_key, year, month, "CODE_SMELL")
         
    def get_vulnerabilities(self, project_key, year, month):
        """
        Get the number of vulnerabilities for a specific project and month.
       
        Args:
            project_key (str): SonarQube project key
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            int: Number of vulnerabilities reported by SonarQube
        """
        return self._get_issues(project_key, year, month, "VULNERABILITY")
    def get_coverage(self, project_key, year, month):
        """
        Get the code coverage percentage for a specific project and month.
       
        Args:
            project_key (str): SonarQube project key
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            float: Code coverage percentage reported by SonarQube or 0 if not available, rounded to 4 decimal places
        """
        # Always picking up the latest new coverage, not dependent on month
       
        # Construct API endpoint for measures
        api_endpoint = "/api/measures/component"
        url = urljoin(self.base_url, api_endpoint)
       
        # Parameters for the API request using query string
        # Get both overall and new code coverage metrics
        params = f'component={project_key}:&metricKeys=coverage,new_coverage&branch=master'
       
        try:
            # Convert params to query string and append to URL
            url_with_params = f"{url}?{params}"
            # Make request with params in URL
            response = requests.get(url_with_params, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            data = response.json()
 
            self.logger.debug(3, f"Coverage API response data: {data}")
           
            # Extract coverage value from response
            measures = data.get('component', {}).get('measures', [])
            coverage = None
           
            # First, try to get new_coverage from the periods array
            new_coverage_metric = next((m for m in measures if m.get('metric') == 'new_coverage'), None)
           
            if new_coverage_metric and new_coverage_metric.get('periods'):
                # Get value from the first period
                coverage = new_coverage_metric.get('periods')[0].get('value')
                self.logger.debug(3, f"Found new_coverage in periods: {coverage}")
           
            # If new_coverage is not available, fall back to overall coverage
            if not coverage:
                overall_coverage = next((m.get('value') for m in measures if m.get('metric') == 'coverage'), None)
                if overall_coverage:
                    self.logger.info(3, f"Could not find new coverage, falling back to overall coverage: {overall_coverage}")
                    coverage = overall_coverage
           
            if coverage:
                return round(float(coverage) / 100.0, 4)  # Convert from percentage to decimal, round to 4 decimals
            else:
                self.logger.warning(3, f"No coverage metrics found for project {project_key}")
                return 0
               
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching coverage from SonarQube: {e}")
            return 0