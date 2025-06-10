"""
Jenkins data source for retrieving metrics from a Jenkins server.
"""
 
import requests
from datetime import datetime
import calendar
from urllib.parse import urljoin
import json
from src.utils.logger import get_logger
 
 
class JenkinsDataSource:
    """
    Data source for connecting to a Jenkins server and retrieving metrics.
    """
   
    def __init__(self, base_url, token=None, username=None, password=None):
        """
        Initialize the JenkinsDataSource.
       
        Args:
            base_url (str): Base URL of the Jenkins server
            token (str, optional): Authentication token for API access
            username (str, optional): Username for basic authentication
            password (str, optional): Password for basic authentication
       
        Note:
            Either token OR username/password must be provided for authentication.        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.logger = get_logger("jenkins_data_source")
        self.username = username
        self.password = password
       
        # Set up authentication headers
        self.headers = {
            'Accept': 'application/json'
        }
       
        # Set up authentication method
        if token:
            # Jenkins uses an API token as a password with the username
            self.auth = (username or 'token', token)
        elif username and password:
            self.auth = (username, password)
        else:
            raise ValueError("Either token or username/password must be provided for authentication")
 
    def get_deployment_frequency(self, deployment_job, year, month):
        """
        Get the frequency of successful deployments for a specific Jenkins job and month.
       
        Args:
            deployment_job (str): Jenkins job identifier (job name or path for multi-branch jobs)
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            int: Number of successful deployments for the given job and month
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
         
        # Format the job path for URL using '/job/' between each part
        # If the path already has '/job/' segments, use it as is; otherwise split by '/'
        if '/job/' in deployment_job:
            encoded_path = deployment_job
        else:
            encoded_path = '/job/'.join(deployment_job.split('/'))
       
        # Ensure it ends with a trailing slash for the API path
        if not encoded_path.endswith('/'):
            encoded_path += '/'
       
        # Construct API endpoint for job builds
        api_url = f"{self.base_url}/job/{encoded_path}api/json"
       
        # Parameters for the API request
        params = {
            'tree': 'builds[number,timestamp,result,duration]',  # Get only the fields we need
        }
       
        try:
            response = requests.get(api_url, headers=self.headers, params=params, auth=self.auth)
            response.raise_for_status()
            data = response.json()
             
            successful_deployments = 0
            for build in data.get('builds', []):
                build_timestamp = build.get('timestamp', 0)
                # Convert to datetime in Australian timezone
                build_time = datetime.fromtimestamp(build_timestamp / 1000)
               
                # Check if the build is in the target month and year, regardless of result
                if build_time.year == year_int and build_time.month == month_int:
                    successful_deployments += 1
                   
            return successful_deployments
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching deployment data from Jenkins: {e}")
            return 0
 
    def get_code_coverage(self, project, year, month):
        """
        Get the code coverage percentage for a specific project and month.
       
        Args:
            project (str): Project identifier (can be job name or project path)
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            float: Average code coverage percentage for the given project and month,
                or None if no coverage data is available
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
       
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
       
        # Format dates for the API (Jenkins uses milliseconds since epoch)
        start_date = int(datetime(year_int, month_int, 1, 0, 0, 0).timestamp() * 1000)
        end_date = int(datetime(year_int, month_int, last_day, 23, 59, 59).timestamp() * 1000)
       
        # Process the project to determine the job path in Jenkins
        # This assumes project names follow a format like "DPI/mac-motor-bicc-ui"
        project_parts = project.split('/')
       
        # Map the project to a Jenkins job - you might need to customize this mapping
        # based on your Jenkins job structure
        if len(project_parts) >= 2:
            job_path = project  # Use the project path directly
        else:
            # If only a project name is provided without a path
            # You might have a naming convention to determine the Jenkins job
            job_path = project
       
        # Construct API endpoint for job builds
        # Handle both simple jobs and jobs in folders/branches
        api_path = '/job/' + '/job/'.join(job_path.split('/')) + '/api/json'
        url = urljoin(self.base_url, api_path)
           
        # Parameters for the API request
        params = {
            'tree': 'builds[number,timestamp,result,actions[*]]',  # Need actions for coverage data
        }
       
        try:
            response = requests.get(url, headers=self.headers, params=params, auth=self.auth)
            response.raise_for_status()
            data = response.json()
           
            coverage_values = []
            for build in data.get('builds', []):
                # Check if build timestamp is within our range and was successful
                if (start_date <= build.get('timestamp', 0) <= end_date and
                    build.get('result') == 'SUCCESS'):
                    # Get code coverage from build actions
                    actions = build.get('actions', [])
                    for action in actions:
                        # Check for JaCoCo coverage data
                        if 'jacoco' in action:
                            coverage = action.get('jacoco', {}).get('percentageFloat')
                            if coverage is not None:
                                coverage_values.append(coverage)
                        # Check for Cobertura coverage data
                        elif 'cobertura' in action:
                            coverage = action.get('cobertura', {}).get('lineCoverage')
                            if coverage is not None:
                                coverage_values.append(coverage * 100)  # Convert to percentage
                        # Check for generic coverage report
                        elif action.get('_class', '').endswith('CoverageAction'):
                            coverage = action.get('lineCoverage')
                            if coverage is not None:
                                coverage_values.append(coverage * 100)  # Convert to percentage
           
            if coverage_values:
                # Calculate the average coverage
                return round(sum(coverage_values) / len(coverage_values), 2)
            else:
                self.logger.info(3, f"No coverage data found for project {project} in {year}-{month}")
                return None
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching code coverage data from Jenkins: {e}")
            return None