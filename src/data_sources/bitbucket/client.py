"""
Bitbucket HTTP client implementation.
Provides functionality for making API requests to a Bitbucket server.
"""

import requests
import time
import concurrent.futures
from urllib.parse import urljoin
from src.utils.logger import get_logger

class BitbucketClient:
    """
    Client for making HTTP requests to a Bitbucket server.
    Handles authentication, rate limiting, and concurrent requests.
    """
    def __init__(self, base_url, token=None, username=None, password=None, max_workers=10, requests_per_second=5):
        """
        Initialize the BitbucketClient.
       
        Args:
            base_url (str): Base URL of the Bitbucket server
            token (str, optional): Authentication token for API access
            username (str, optional): Username for basic authentication
            password (str, optional): Password for basic authentication
            max_workers (int, optional): Maximum number of concurrent API requests
            requests_per_second (int, optional): Maximum number of requests per second (rate limit)
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.username = username
        self.password = password
        self.logger = get_logger("bitbucket_client")
        self.max_workers = max_workers
        self.request_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self.last_request_time = 0
       
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
            
    def rate_limited_request(self, url, auth=None):
        """
        Make a rate-limited HTTP request.
        
        Args:
            url (str): URL to request
            auth (tuple, optional): Auth tuple for basic auth
            
        Returns:
            Response: HTTP response object
        """
        # Apply rate limiting
        now = time.time()
        time_since_last_request = now - self.last_request_time
        if time_since_last_request < self.request_interval:
            sleep_time = self.request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        # Make the request
        if auth:
            response = requests.get(url, headers=self.headers, auth=auth)
        else:
            response = requests.get(url, headers=self.headers)
            
        self.last_request_time = time.time()
        return response
        
    def fetch_paginated_data(self, endpoint, project_path, page_size=100):
        """
        Fetch paginated data from Bitbucket API.
        
        Args:
            endpoint (str): API endpoint to fetch data from
            project_path (str): Project path for logging
            page_size (int, optional): Size of each page. Defaults to 100.
            
        Returns:
            list: List of items from all pages
        """
        url = urljoin(self.base_url, endpoint)
        all_items = []
        start = 0
        total_count = None
        pages_fetched = 0
        
        while True:
            paged_url = f"{url}&start={start}&limit={page_size}"
            self.logger.info(3, f"Fetching page starting at {start} for {project_path}")
            try:
                response = self.rate_limited_request(paged_url, self.auth)
                response.raise_for_status()
                data = response.json()
                
                # Get the total count if this is the first page
                if total_count is None:
                    total_count = data.get('total', 0)
                    self.logger.info(3, f"Total items reported by API: {total_count}")
                
                page_items = data.get('values', [])
                pages_fetched += 1
                
                if not page_items:
                    self.logger.info(3, f"No items returned on page, stopping pagination")
                    break
                    
                all_items.extend(page_items)
                
                # Log detailed pagination information
                is_last_page = data.get('isLastPage', True)
                next_start = data.get('nextPageStart')
                self.logger.info(3, f"Page {pages_fetched}: got {len(page_items)} items, " 
                                  f"isLastPage={is_last_page}, nextPageStart={next_start}, "
                                  f"total so far: {len(all_items)}/{total_count}")
                
                if is_last_page:
                    self.logger.info(3, f"Reached last page as reported by API")
                    break
                    
                # Get the next page start index directly from the API response
                if next_start is not None:
                    start = next_start
                else:
                    # If no nextPageStart is provided, use current position + items count
                    start = start + len(page_items)
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(3, f"Error fetching page: {e}")
                break
                
        # Log summary of pagination
        if total_count and len(all_items) < total_count:
            self.logger.warning(3, f"Expected {total_count} items but only fetched {len(all_items)} "
                               f"items from {project_path} in {pages_fetched} pages")
        else:
            self.logger.info(3, f"Fetched {len(all_items)} items from {project_path} in {pages_fetched} pages")
                
        return all_items
                
        return all_items
        
    def fetch_pr_details(self, project, repo, pr_id):
        """
        Fetch details for a single PR.
        
        Args:
            project (str): Project name
            repo (str): Repository name
            pr_id (int): Pull request ID
            
        Returns:
            dict: PR details or None if error
        """
        pr_detail_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests/{pr_id}"
        pr_detail_url = urljoin(self.base_url, pr_detail_endpoint)
        self.logger.info(4, f"Fetching details for PR #{pr_id}")
        
        try:
            response = self.rate_limited_request(pr_detail_url, self.auth)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching details for PR {pr_id}: {e}")
            return None
    
    def fetch_pr_activities(self, project, repo, pr_id):
        """
        Fetch activities for a single PR.
        
        Args:
            project (str): Project name
            repo (str): Repository name
            pr_id (int): Pull request ID
            
        Returns:
            list: List of activities or empty list if error
        """
        pr_activities_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests/{pr_id}/activities"
        pr_activities_url = urljoin(self.base_url, pr_activities_endpoint)
        
        try:
            response = self.rate_limited_request(pr_activities_url, self.auth)
            response.raise_for_status()
            return response.json().get('values', [])
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching activities for PR {pr_id}: {e}")
            return []
            
    def fetch_pr_data_concurrently(self, project, repo, prs):
        """
        Fetch details and activities for multiple PRs concurrently.
        
        Args:
            project (str): Project name
            repo (str): Repository name
            prs (list): List of PRs to fetch details for
            
        Returns:
            dict: Dictionary with PR details and activities
        """
        pr_data = {
            "prs": [],
            "activities": {}
        }
        
        # Use concurrent futures to fetch PR details and activities in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all detail and activity fetches
            detail_futures = {}
            activity_futures = {}
            
            for pr in prs:
                pr_id = pr.get('id')
                if not pr_id:
                    continue
                
                # Submit detail fetch
                detail_futures[executor.submit(self.fetch_pr_details, project, repo, pr_id)] = pr_id
                
                # Submit activity fetch
                activity_futures[executor.submit(self.fetch_pr_activities, project, repo, pr_id)] = pr_id
            
            # Process detail futures
            completed_details = 0
            total_details = len(detail_futures)
            for future in concurrent.futures.as_completed(detail_futures):
                completed_details += 1
                if completed_details % 10 == 0 or completed_details == total_details:
                    self.logger.info(3, f"Completed {completed_details}/{total_details} PR detail requests")
                
                pr_id = detail_futures[future]
                try:
                    pr_detail = future.result()
                    if pr_detail:
                        pr_data["prs"].append(pr_detail)
                except Exception as e:
                    self.logger.error(3, f"Error fetching details for PR {pr_id}: {e}")
            
            # Process activity futures
            completed_activities = 0
            total_activities = len(activity_futures)
            for future in concurrent.futures.as_completed(activity_futures):
                completed_activities += 1
                if completed_activities % 10 == 0 or completed_activities == total_activities:
                    self.logger.info(3, f"Completed {completed_activities}/{total_activities} PR activity requests")
                
                pr_id = activity_futures[future]
                try:
                    activities = future.result()
                    pr_data["activities"][str(pr_id)] = activities
                except Exception as e:
                    self.logger.error(3, f"Error fetching activities for PR {pr_id}: {e}")
        
        return pr_data
    
    def fetch_paginated_data_concurrently(self, endpoint, project_path, page_size=100):
        """
        Fetch paginated data from Bitbucket API using concurrent requests.
        
        This method first requests the initial page to get the total count,
        then makes concurrent requests for all required pages.
        
        Args:
            endpoint (str): API endpoint to fetch data from
            project_path (str): Project path for logging
            page_size (int, optional): Size of each page. Defaults to 100.
            
        Returns:
            list: List of items from all pages
        """
        url = urljoin(self.base_url, endpoint)
        
        # Make initial request to get total count
        initial_url = f"{url}&limit={page_size}"
        self.logger.info(3, f"Fetching initial page to determine pagination for {project_path}")
        try:
            initial_response = self.rate_limited_request(initial_url, self.auth)
            initial_response.raise_for_status()
            initial_data = initial_response.json()
            
            # Extract initial items
            all_items = initial_data.get('values', [])
            
            # If this is the only page, return immediately
            if initial_data.get('isLastPage', True):
                self.logger.info(3, f"Only one page needed for {project_path}")
                return all_items
                
            # Calculate total number of pages needed
            size = initial_data.get('size', 0)  # Items per page
            total_count = initial_data.get('total', 0)  # Total items
            
            if size == 0:
                self.logger.warning(3, f"Unable to determine page size for {project_path}")
                return all_items
                
            # Get first page start index
            next_page_start = initial_data.get('nextPageStart', 0)
            
            # Calculate additional pages needed
            remaining_items = total_count - len(all_items)
            self.logger.info(3, f"Need to fetch {remaining_items} more items from {project_path} (total count: {total_count})")
            
            # Prepare page starts for concurrent fetching
            # For safety, we'll fetch one page at a time sequentially to respect the nextPageStart
            # This ensures we're following Bitbucket's pagination properly
            
            # First, add the initial next page start
            next_starts = [next_page_start]
            
            # Prefetch some page starts to determine the pagination pattern
            current_start = next_page_start
            
            # We'll fetch a few pages sequentially first to understand the pagination pattern
            self.logger.info(3, f"Prefetching up to 5 pages to determine pagination pattern")
            
            # Maximum number of pages to prefetch
            max_prefetch = min(5, total_count // page_size + (1 if total_count % page_size > 0 else 0) - 1)
            
            for i in range(max_prefetch):
                paged_url = f"{url}&start={current_start}&limit={page_size}"
                try:
                    response = self.rate_limited_request(paged_url, self.auth)
                    response.raise_for_status()
                    data = response.json()
                    
                    # If this is the last page, break
                    if data.get('isLastPage', True):
                        self.logger.info(3, f"Reached last page during prefetch at index {current_start}")
                        break
                    
                    # Get the next page start
                    next_start = data.get('nextPageStart')
                    if next_start is not None:
                        next_starts.append(next_start)
                        current_start = next_start
                    else:
                        # If no nextPageStart is provided, use estimated position
                        current_start += page_size
                        next_starts.append(current_start)
                        
                    self.logger.info(4, f"Prefetched page with nextPageStart: {next_start}")
                    
                except requests.exceptions.RequestException as e:
                    self.logger.error(3, f"Error prefetching page: {e}")
                    break
            
            # Now that we've learned the pagination pattern, we can fetch the remaining pages
            page_starts = next_starts
                
            self.logger.info(3, f"Preparing to fetch {len(page_starts)} additional pages concurrently for {project_path}")
            
            # Define function to fetch a single page
            def fetch_page(start_index):
                paged_url = f"{url}&start={start_index}&limit={page_size}"
                try:
                    response = self.rate_limited_request(paged_url, self.auth)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Get the page items
                    page_items = data.get('values', [])
                    
                    # Add detailed logging about the pagination
                    is_last_page = data.get('isLastPage', True)
                    next_start = data.get('nextPageStart')
                    self.logger.info(4, f"Page at index {start_index}: got {len(page_items)} items, " 
                                      f"isLastPage={is_last_page}, nextPageStart={next_start}")
                    
                    return page_items
                except requests.exceptions.RequestException as e:
                    self.logger.error(3, f"Error fetching page at index {start_index}: {e}")
                    return []
                    
            # Fetch all pages concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all page fetches
                future_to_start = {executor.submit(fetch_page, start): start for start in page_starts}
                
                # Process results as they complete
                completed = 0
                total_pages = len(future_to_start)
                
                for future in concurrent.futures.as_completed(future_to_start):
                    completed += 1
                    if completed % 5 == 0 or completed == total_pages:
                        self.logger.info(3, f"Completed {completed}/{total_pages} page fetches for {project_path}")
                        
                    try:
                        page_items = future.result()
                        all_items.extend(page_items)
                    except Exception as e:
                        start_index = future_to_start[future]
                        self.logger.error(3, f"Error processing page at index {start_index}: {e}")
                        
            # If we didn't get all the items we expected, try sequential fetching
            if len(all_items) < total_count:
                self.logger.warning(3, f"Expected {total_count} items but only fetched {len(all_items)} items. " 
                                   f"Attempting sequential fetch to ensure we get all items.")
                
                # Store existing items in a set for quick lookup
                existing_ids = set()
                for item in all_items:
                    if 'id' in item:
                        existing_ids.add(item['id'])
                
                # Do a complete sequential fetch to ensure we get everything
                seq_items = self.fetch_paginated_data(endpoint, project_path, page_size)
                
                # Add any items we didn't already get
                new_items_count = 0
                for item in seq_items:
                    if 'id' in item and item['id'] not in existing_ids:
                        all_items.append(item)
                        existing_ids.add(item['id'])
                        new_items_count += 1
                
                self.logger.info(3, f"Sequential fetch added {new_items_count} new items")
            
            self.logger.info(3, f"Fetched a total of {len(all_items)} items from {project_path} (expected: {total_count})")
            return all_items
            
        except requests.exceptions.RequestException as e:
            self.logger.error(3, f"Error fetching initial page: {e}")
            return []
