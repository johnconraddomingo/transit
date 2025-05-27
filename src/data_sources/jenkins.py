"""
Jenkins data source for retrieving metrics from a Jenkins server.
"""

import requests
from datetime import datetime
import calendar
from urllib.parse import urljoin
import json


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
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API (Jenkins uses milliseconds since epoch)
        start_date = int(datetime(year_int, month_int, 1, 0, 0, 0).timestamp() * 1000)
        end_date = int(datetime(year_int, month_int, last_day, 23, 59, 59).timestamp() * 1000)
        
        # Process the deployment_job to handle different formats (simple job or multi-branch)
        job_parts = deployment_job.split('/')
        
        # Construct API endpoint for job builds
        # Handle both simple jobs and jobs in folders/branches
        api_path = '/job/' + '/job/'.join(job_parts) + '/api/json'
        api_endpoint = api_path
        url = urljoin(self.base_url, api_endpoint)
        
        # Parameters for the API request
        params = {
            'tree': 'builds[number,timestamp,result,duration]',  # Get only the fields we need
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, auth=self.auth)
            response.raise_for_status()
            data = response.json()
            
            # Count successful deployments within the date range
            successful_deployments = 0
            for build in data.get('builds', []):
                # Check if build timestamp is within our range and was successful
                if (start_date <= build.get('timestamp', 0) <= end_date and 
                    build.get('result') == 'SUCCESS'):
                    successful_deployments += 1
                    
            return successful_deployments
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching deployment data from Jenkins: {e}")
            return 0
