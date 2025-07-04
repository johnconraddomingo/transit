"""
GitHub data source for retrieving metrics from GitHub and GitHub Enterprise.
"""
 
import requests
from datetime import datetime
import calendar
from urllib.parse import urljoin
import json
from src.utils.logger import get_logger
 
 
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
            Basic authentication is deprecated for GitHub API v3 but might be supported in GitHub Enterprise.        """
        self.base_url = base_url.rstrip('/')
        self.logger = get_logger("github_data_source")
        self.token = token
       
        # Set up authentication headers
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'  # Specify GitHub API version
        }
       
        # GitHub API strongly prefers token authentication
        if token:
            self.headers['Authorization'] = f'token {token}'
            self.auth = None        # Basic authentication is included but may not work for GitHub.com
        elif username and password:
            self.auth = (username, password)
            self.logger.warning(3, "Basic authentication for GitHub API is deprecated. Token authentication is recommended.")
        else:
            raise ValueError("Authentication credentials must be provided. Token authentication is recommended.")
   
   
    def get_active_users(self, organization, year, month):
        """
        Get the number of active Copilot users for an organization.
       
        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            int: Maximum number of active Copilot users for the month
        """
        # Construct API endpoint for Copilot metrics
        api_endpoint = f"/enterprises/{organization}/copilot/metrics"
        url = urljoin(self.base_url, api_endpoint)
       
        try:
            # Query the GitHub API for Copilot metrics without any parameters
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)
               
            response.raise_for_status()
            data = response.json()
 
            # Handle if data is a list or dict
            if isinstance(data, dict):
                entries = data.get('data', [])
            elif isinstance(data, list):
                entries = data
            else:
                entries = []
 
            target_date_prefix = f"{year}-{month:0>2}"  # Ensures month is two digits
 
            # Get the maximum total_engaged_users for the month
            max_active_users = max(
                (entry.get('total_engaged_users', 0)
                 for entry in entries
                 if entry.get('date', '').startswith(target_date_prefix)),
                default=0            )
            return max_active_users
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching GitHub Copilot active users: {e}")
            return 0  # Return 0 if there's an error
       
    def get_copilot_suggested_lines(self, organization, year, month):
        """
        Get the total number of code lines suggested by GitHub Copilot for an organization.
       
        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
           
        Returns:
            int: Total number of lines suggested by Copilot for the month
        """
        # Construct API endpoint for Copilot metrics
        api_endpoint = f"/enterprises/{organization}/copilot/metrics"
        url = urljoin(self.base_url, api_endpoint)
       
        try:
            # Query the GitHub API for Copilot metrics without any parameters
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)
               
            response.raise_for_status()
            data = response.json()
            # Handle if data is a list or dict
            if isinstance(data, dict):
                entries = data.get('data', [])
            elif isinstance(data, list):
                entries = data
            else:
                entries = []
 
            target_date_prefix = f"{year}-{month:0>2}"  # Ensures month is two digits
 
            total_suggested_lines = 0
            for entry in entries:
                if entry.get('date', '').startswith(target_date_prefix):
                    completions = entry.get('copilot_ide_code_completions', {})
                    editors = completions.get('editors', [])
                    for editor in editors:
                        for model in editor.get('models', []):
                            for language in model.get('languages', []):                                total_suggested_lines += language.get('total_code_lines_suggested', 0)
            return total_suggested_lines
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching GitHub Copilot suggested lines: {e}")
            return 0  # Return 0 if there's an error
       
    def get_copilot_accepted_lines(self, organization, year, month):
        """
        Get the total number of code lines accepted by GitHub Copilot for an organization.
 
        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
 
        Returns:
            int: Total number of lines accepted by Copilot for the month
        """
        api_endpoint = f"/enterprises/{organization}/copilot/metrics"
        url = urljoin(self.base_url, api_endpoint)
 
        try:
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)
 
            response.raise_for_status()
            data = response.json()
            # Handle if data is a list or dict
            if isinstance(data, dict):
                entries = data.get('data', [])
            elif isinstance(data, list):
                entries = data
            else:
                entries = []
 
            target_date_prefix = f"{year}-{month:0>2}"
 
            total_accepted_lines = 0
            for entry in entries:
                if entry.get('date', '').startswith(target_date_prefix):
                    completions = entry.get('copilot_ide_code_completions', {})
                    editors = completions.get('editors', [])
                    for editor in editors:
                        for model in editor.get('models', []):
                            for language in model.get('languages', []):
                                total_accepted_lines += language.get('total_code_lines_accepted', 0)
            return total_accepted_lines
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching GitHub Copilot accepted lines: {e}")
            return 0  # Return 0 if there's an error
       
    def get_copilot_adoption_rate(self, organization, year, month):
        """
        Calculate the GitHub Copilot adoption rate for an organization based on accepted/suggested lines.

        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")

        Returns:
            float: Copilot adoption rate (accepted lines / suggested lines) for the month, rounded to 4 decimal places
        """
        api_endpoint = f"/enterprises/{organization}/copilot/metrics"
        url = urljoin(self.base_url, api_endpoint)

        try:
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)

            response.raise_for_status()
            data = response.json()
            # Handle if data is a list or dict
            if isinstance(data, dict):
                entries = data.get('data', [])
            elif isinstance(data, list):
                entries = data
            else:
                entries = []

            target_date_prefix = f"{year}-{month:0>2}"

            total_accepted_lines = 0
            total_suggested_lines = 0
            for entry in entries:
                if entry.get('date', '').startswith(target_date_prefix):
                    completions = entry.get('copilot_ide_code_completions', {})
                    editors = completions.get('editors', [])
                    for editor in editors:
                        for model in editor.get('models', []):
                            for language in model.get('languages', []):
                                total_accepted_lines += language.get('total_code_lines_accepted', 0)
                                total_suggested_lines += language.get('total_code_lines_suggested', 0)
            if total_suggested_lines > 0:
                adoption_rate = total_accepted_lines / total_suggested_lines
            else:
                adoption_rate = 0.0
            return round(adoption_rate, 4)
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error calculating Copilot adoption rate: {e}")
            return 0.0
       
    def get_ai_usage(self, organization, year, month):
        """
        Get the total number of Copilot Chat interactions (total_chats) for an organization.
 
        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
 
        Returns:
            int: Total number of Copilot Chat interactions for the month
        """
        api_endpoint = f"/enterprises/{organization}/copilot/metrics"
        url = urljoin(self.base_url, api_endpoint)
 
        try:
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)
 
            response.raise_for_status()
            data = response.json()
            # Handle if data is a list or dict
            if isinstance(data, dict):
                entries = data.get('data', [])
            elif isinstance(data, list):
                entries = data
            else:
                entries = []
 
            target_date_prefix = f"{year}-{month:0>2}"
 
            total_chats = 0
            for entry in entries:
                if entry.get('date', '').startswith(target_date_prefix):
                    chat = entry.get('copilot_ide_chat', {})
                    editors = chat.get('editors', [])
                    for editor in editors:
                        for model in editor.get('models', []):
                            total_chats += model.get('total_chats', 0)
            return total_chats
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching GitHub Copilot AI usage: {e}")
            return 0  # Return 0 if there's an error

    def get_total_seats(self, organization):
        """
        Get the total number of Copilot seats for an organization (enterprise).

        Args:
            organization (str): GitHub organization/enterprise name

        Returns:
            int: Total number of Copilot seats (total_seats)
        """
        api_endpoint = f"/enterprises/{organization}/copilot/billing/seats"
        url = urljoin(self.base_url, api_endpoint)
        try:
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get('total_seats', 0)
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching GitHub Copilot total seats: {e}")
            return 0