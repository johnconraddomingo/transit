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
        api_endpoint = f"/orgs/{organization}/settings/billing/copilot"
        
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

    def get_copilot_suggested_lines(self, organization, year, month):
        """
        Get the number of code lines suggested by GitHub Copilot for an organization.
        
        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
            
        Returns:
            dict: A dictionary containing timeseries data of Copilot suggested lines
                  Format: {"timestamp": ISO8601 date, "suggested_lines": int}
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API in ISO format
        start_date = f"{year}-{month}-01T00:00:00Z"
        end_date = f"{year}-{month}-{last_day}T23:59:59Z"
        
        # Construct API endpoint for Copilot usage metrics
        # This endpoint is available for enterprise customers
        api_endpoint = f"/orgs/{organization}/copilot/usage"
        
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "granularity": "day"  # Keep daily granularity for detailed data
        }
        
        url = urljoin(self.base_url, api_endpoint)
        
        try:
            # Query the GitHub API for Copilot metrics
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
            else:
                response = requests.get(url, headers=self.headers, params=params)
                
            response.raise_for_status()
            data = response.json()
            
            # Extract suggested lines data from the response
            # The actual structure depends on GitHub's API response format
            results = []
            
            for entry in data.get('data', []):
                suggested_lines = entry.get('suggested_lines', 0)
                timestamp = entry.get('date')
                
                if timestamp and suggested_lines is not None:
                    results.append({
                        "timestamp": timestamp,
                        "suggested_lines": suggested_lines
                    })
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching GitHub Copilot suggested lines: {e}")
            
            # Try alternative approach with GraphQL API if REST API fails
            try:
                graphql_query = """
                query CopilotMetrics($org: String!, $startDate: String!, $endDate: String!) {
                  enterprise(slug: $org) {
                    copilotMetrics(startDate: $startDate, endDate: $endDate) {
                      suggestedLines
                      date
                    }
                  }
                }
                """
                
                variables = {
                    "org": organization,
                    "startDate": start_date,
                    "endDate": end_date
                }
                
                # GraphQL endpoint is typically at /api/graphql
                graphql_url = urljoin(self.base_url, "/api/graphql")
                
                # Update headers for GraphQL
                graphql_headers = self.headers.copy()
                graphql_headers['Content-Type'] = 'application/json'
                
                payload = {
                    "query": graphql_query,
                    "variables": variables
                }
                
                if self.auth:
                    response = requests.post(graphql_url, headers=graphql_headers, auth=self.auth, json=payload)
                else:
                    response = requests.post(graphql_url, headers=graphql_headers, json=payload)
                
                response.raise_for_status()
                graphql_data = response.json()
                
                # Extract data from GraphQL response
                metrics = graphql_data.get('data', {}).get('enterprise', {}).get('copilotMetrics', [])
                
                results = []
                for metric in metrics:
                    results.append({
                        "timestamp": metric.get('date'),
                        "suggested_lines": metric.get('suggestedLines', 0)
                    })
                
                return results
            except Exception as graphql_error:
                print(f"GraphQL fallback also failed: {graphql_error}")
                return []
            
    def get_copilot_accepted_lines(self, organization, year, month):
        """
        Get the number of code lines accepted from GitHub Copilot suggestions for an organization.
        
        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
            
        Returns:
            list: A list of dictionaries containing timeseries data of Copilot accepted lines
                Format: [{"timestamp": ISO8601 date, "accepted_lines": int}]
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API in ISO format
        start_date = f"{year}-{month}-01T00:00:00Z"
        end_date = f"{year}-{month}-{last_day}T23:59:59Z"
        
        # Construct API endpoint for Copilot usage metrics
        # This endpoint is available for enterprise customers
        api_endpoint = f"/orgs/{organization}/copilot/usage"
        
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "granularity": "day"  # Keep daily granularity for detailed data
        }
        
        url = urljoin(self.base_url, api_endpoint)
        
        try:
            # Query the GitHub API for Copilot metrics
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
            else:
                response = requests.get(url, headers=self.headers, params=params)
                
            response.raise_for_status()
            data = response.json()
            
            # Extract accepted lines data from the response
            # The actual structure depends on GitHub's API response format
            results = []
            
            for entry in data.get('data', []):
                accepted_lines = entry.get('accepted_lines', 0)
                timestamp = entry.get('date')
                
                if timestamp and accepted_lines is not None:
                    results.append({
                        "timestamp": timestamp,
                        "accepted_lines": accepted_lines
                    })
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching GitHub Copilot accepted lines: {e}")
            
            # Try alternative approach with GraphQL API if REST API fails
            try:
                graphql_query = """
                query CopilotMetrics($org: String!, $startDate: String!, $endDate: String!) {
                enterprise(slug: $org) {
                    copilotMetrics(startDate: $startDate, endDate: $endDate) {
                    acceptedLines
                    date
                    }
                }
                }
                """
                
                variables = {
                    "org": organization,
                    "startDate": start_date,
                    "endDate": end_date
                }
                
                # GraphQL endpoint is typically at /api/graphql
                graphql_url = urljoin(self.base_url, "/api/graphql")
                
                # Update headers for GraphQL
                graphql_headers = self.headers.copy()
                graphql_headers['Content-Type'] = 'application/json'
                
                payload = {
                    "query": graphql_query,
                    "variables": variables
                }
                
                if self.auth:
                    response = requests.post(graphql_url, headers=graphql_headers, auth=self.auth, json=payload)
                else:
                    response = requests.post(graphql_url, headers=graphql_headers, json=payload)
                
                response.raise_for_status()
                graphql_data = response.json()
                
                # Extract data from GraphQL response
                metrics = graphql_data.get('data', {}).get('enterprise', {}).get('copilotMetrics', [])
                
                results = []
                for metric in metrics:
                    results.append({
                        "timestamp": metric.get('date'),
                        "accepted_lines": metric.get('acceptedLines', 0)
                    })
                
                return results
            except Exception as graphql_error:
                print(f"GraphQL fallback also failed: {graphql_error}")
                return []
            
    def get_copilot_adoption_rate(self, organization, year, month):
        """
        Calculate the GitHub Copilot adoption rate for an organization.
        
        The adoption rate is calculated as: 
        - Primary method: Active Copilot users / Total organization users
        - Secondary method: Accepted lines / Suggested lines (if user counts unavailable)
        
        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
            
        Returns:
            list: A list of dictionaries containing timeseries data of Copilot adoption metrics
                Format: [{"timestamp": ISO8601 date, "adoption_rate": float, "method": str}]
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API in ISO format
        start_date = f"{year}-{month}-01T00:00:00Z"
        end_date = f"{year}-{month}-{last_day}T23:59:59Z"
        
        # Construct API endpoint for organization members count
        api_endpoint = f"/orgs/{organization}/members"
        url = urljoin(self.base_url, api_endpoint)
        
        try:
            # First try to calculate adoption rate based on active users vs total users
            # Get total number of users in the organization
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth)
            else:
                response = requests.get(url, headers=self.headers)
                
            response.raise_for_status()
            org_data = response.json()
            total_users = org_data.get('total_count', 0)
            
            if not total_users:
                raise ValueError("Could not determine total user count")
                
            # Now get active Copilot users using the get_active_users method which already takes year and month
            active_users = self.get_active_users(organization, year, month)
            
            # Calculate adoption rate
            adoption_rate = active_users / total_users if total_users > 0 else 0
            
            # Format as a data point with the last day of the month as timestamp
            timestamp = f"{year}-{month}-{last_day}T23:59:59Z"
            results = [{
                "timestamp": timestamp,
                "adoption_rate": adoption_rate,
                "active_users": active_users,
                "total_users": total_users,
                "method": "user_count"
            }]
            
            return results
            
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Error calculating adoption rate from user counts: {e}")
            print("Falling back to accepted/suggested lines method")
            
            # Fallback method: Calculate adoption as ratio of accepted to suggested lines
            try:
                # Get suggested lines using the updated methods that take year and month
                suggested_lines_data = self.get_copilot_suggested_lines(organization, year, month)
                
                # Get accepted lines using the updated method that takes year and month
                accepted_lines_data = self.get_copilot_accepted_lines(organization, year, month)
                
                # Match up the data points by timestamp and calculate rates
                results = []
                suggested_dict = {item["timestamp"]: item["suggested_lines"] for item in suggested_lines_data}
                
                for accepted_item in accepted_lines_data:
                    timestamp = accepted_item["timestamp"]
                    accepted_lines = accepted_item["accepted_lines"]
                    suggested_lines = suggested_dict.get(timestamp, 0)
                    
                    if suggested_lines > 0:
                        adoption_rate = accepted_lines / suggested_lines
                        results.append({
                            "timestamp": timestamp,
                            "adoption_rate": adoption_rate,
                            "accepted_lines": accepted_lines,
                            "suggested_lines": suggested_lines,
                            "method": "line_ratio"
                        })
                
                return results
                
            except Exception as fallback_error:
                print(f"Fallback method also failed: {fallback_error}")
                return []
            
    def get_ai_usage(self, organization, year, month):
        """
        Get AI usage metrics based on the total number of GitHub Copilot Chat interactions.
        
        Args:
            organization (str): GitHub organization name
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
            
        Returns:
            dict: Dictionary containing AI usage metrics with the format:
                {"timestamp": ISO8601 date, "total_chats": int}
        """
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API in ISO format
        start_date = f"{year}-{month}-01T00:00:00Z"
        end_date = f"{year}-{month}-{last_day}T23:59:59Z"
        
        # Construct API endpoint for Copilot Chat statistics
        api_endpoint = f"/orgs/{organization}/copilot/chat-stats"
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        url = urljoin(self.base_url, api_endpoint)
        
        try:
            # Query the GitHub API for Copilot Chat statistics
            if self.auth:
                response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
            else:
                response = requests.get(url, headers=self.headers, params=params)
                
            response.raise_for_status()
            data = response.json()
            
            # Format the response with timestamp
            timestamp = f"{year}-{month}-{last_day}T23:59:59Z"
            return {
                "timestamp": timestamp,
                "total_chats": data.get('total_chats', 0)
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching GitHub Copilot Chat usage: {e}")
            
            # Try alternative approach with GraphQL API
            try:
                graphql_query = """
                query CopilotChatUsage($org: String!, $startDate: String!, $endDate: String!) {
                enterprise(slug: $org) {
                    copilotChat(startDate: $startDate, endDate: $endDate) {
                    totalChats
                    }
                }
                }
                """
                
                variables = {
                    "org": organization,
                    "startDate": start_date,
                    "endDate": end_date
                }
                
                graphql_url = urljoin(self.base_url, "/api/graphql")
                
                graphql_headers = self.headers.copy()
                graphql_headers['Content-Type'] = 'application/json'
                
                payload = {
                    "query": graphql_query,
                    "variables": variables
                }
                
                if self.auth:
                    response = requests.post(graphql_url, headers=graphql_headers, auth=self.auth, json=payload)
                else:
                    response = requests.post(graphql_url, headers=graphql_headers, json=payload)
                
                response.raise_for_status()
                graphql_data = response.json()
                
                total_chats = graphql_data.get('data', {}).get('enterprise', {}).get('copilotChat', {}).get('totalChats', 0)
                
                # Format the response with timestamp
                timestamp = f"{year}-{month}-{last_day}T23:59:59Z"
                return {
                    "timestamp": timestamp,
                    "total_chats": total_chats
                }
                
            except Exception as graphql_error:
                print(f"GraphQL fallback for chat metrics also failed: {graphql_error}")
                timestamp = f"{year}-{month}-{last_day}T23:59:59Z"
                return {
                    "timestamp": timestamp,
                    "total_chats": 0
                }