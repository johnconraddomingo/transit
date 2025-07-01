"""
Metrics calculation for Bitbucket data.
Provides functionality for calculating various metrics from Bitbucket PR data.
"""

import calendar
from datetime import datetime
from dateutil import parser
import pytz

class BitbucketMetrics:
    """
    Calculates metrics from Bitbucket pull request data.
    """
    def __init__(self, client, cache):
        """
        Initialize the BitbucketMetrics.
        
        Args:
            client: BitbucketClient instance for making API requests
            cache: BitbucketCache instance for caching data
        """
        self.client = client
        self.cache = cache
        self.logger = client.logger
        
    def _fetch_pr_data(self, project_path, year, month):
        """
        Fetch PR data from cache or API.
        
        Args:
            project_path (str): Project path in format "PROJECT/REPO"
            year (str): Year (e.g. "2025")
            month (str): Month (e.g. "05")
            
        Returns:
            dict: PR data including details and activities
        """
        # Check cache first
        cached_data = self.cache.get(project_path, year, month)
        if cached_data:
            self.logger.info(2, f"Using cached PR data for {project_path} ({year}-{month})")
            # Log cache stats to help diagnose any issues
            self.logger.info(3, f"Cache stats: {len(cached_data.get('prs', []))} PRs, {len(cached_data.get('activities', {}))} PR activity records")
            return cached_data
            
        # If not in cache, fetch from API
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
        
        # Construct API endpoint for pull requests - use maximum allowed page size
        api_endpoint = f"/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests?state=ALL&limit=1000"
        self.logger.info(2, f"Fetching PRs with endpoint: {api_endpoint}")
        
        # Fetch all PRs using concurrent pagination for improved performance
        # Using a larger page size (1000) to minimize the number of API calls needed
        all_prs = self.client.fetch_paginated_data_concurrently(api_endpoint, project_path, page_size=1000)
        self.logger.info(3, f"Total PRs fetched: {len(all_prs)}. Pre-filtering PRs by date range.")
        
        # Convert date strings to timestamps for filtering
        start_timestamp = int(parser.parse(start_date).timestamp() * 1000)
        end_timestamp = int(parser.parse(end_date).timestamp() * 1000)
        
        # Pre-filter PRs by date range to reduce API calls
        filtered_prs = self._pre_filter_prs_by_date_range(all_prs, start_timestamp, end_timestamp)
        pre_filter_percentage = (len(filtered_prs) / len(all_prs) * 100) if all_prs else 0
        self.logger.info(3, f"Pre-filtered to {len(filtered_prs)} PRs (from {len(all_prs)}) for {project_path} ({pre_filter_percentage:.1f}%). Now fetching details.")
        
        # Fetch details and activities for each PR
        pr_data = self.client.fetch_pr_data_concurrently(project, repo, filtered_prs)
        
        # Cache the data
        self.cache.put(project_path, year, month, pr_data)
        
        return pr_data
        
    def _pre_filter_prs_by_date_range(self, prs, start_timestamp, end_timestamp):
        """
        Pre-filter PRs by date range to avoid fetching details for PRs that won't be counted.
        This is an optimization to reduce the number of API calls.
        
        Args:
            prs (list): List of PRs from initial fetch
            start_timestamp (int): Start timestamp in milliseconds
            end_timestamp (int): End timestamp in milliseconds
            
        Returns:
            list: Filtered list of PRs
        """
        # Focus primarily on closed dates since that's what matters for the metrics
        # But still be somewhat conservative to avoid missing PRs that might be relevant
        
        filtered_prs = []
        skipped_count = 0
        
        for pr in prs:
            include_pr = False
            
            # Extract closed date from the PR
            closed_date = pr.get('closedDate')
            
            # PR state (note that initial PR data might not have complete state info)
            state = pr.get('state', '').upper()
            
            # Only include PRs that are MERGED and closed within our date range
            if closed_date and start_timestamp <= closed_date <= end_timestamp and state == 'MERGED':
                include_pr = True
                
            if include_pr:
                filtered_prs.append(pr)
            else:
                skipped_count += 1
                
        self.logger.info(3, f"Pre-filtering skipped {skipped_count} PRs that are not merged or closed outside the date range")
        self.logger.info(3, f"Pre-filtering kept {len(filtered_prs)} PRs that are MERGED and closed within date range")
        return filtered_prs
         
        
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
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API (for filtering and logging)
        start_date_str = f"{year}-{month}-01T00:00:00.000Z"
        end_date_str = f"{year}-{month}-{last_day}T23:59:59.999Z"
        
        # Convert start and end dates to UTC timestamps in milliseconds for comparison
        # Bitbucket API uses UTC timestamps (in milliseconds since epoch)
        
        # Parse ISO format dates with timezone info
        start_dt = parser.parse(start_date_str)
        end_dt = parser.parse(end_date_str)
        
        # Convert to milliseconds timestamp (same format as Bitbucket API)
        start_timestamp = int(start_dt.timestamp() * 1000)
        end_timestamp = int(end_dt.timestamp() * 1000)
        
        # Fetch PR data from cache or API
        pr_data = self._fetch_pr_data(project_path, year, month)
        detailed_prs = pr_data["prs"]
        
        self.logger.info(3, f"Filtering merged PRs between {start_date_str} and {end_date_str} (timestamps: {start_timestamp} - {end_timestamp})")
        
        # Count total merged PRs in dataset
        total_merged_count = len([pr for pr in detailed_prs if pr.get('state', '').upper() == 'MERGED'])
        merged_with_closed_date = len([pr for pr in detailed_prs 
                                      if pr.get('state', '').upper() == 'MERGED' and pr.get('closedDate')])
        
        # Filter PRs by closedDate that fall within our date range AND are in MERGED state
        filtered_prs = [
            pr for pr in detailed_prs
            if pr.get('closedDate') 
            and start_timestamp <= pr.get('closedDate') <= end_timestamp
            and pr.get('state', '').upper() == 'MERGED'
        ]
        
        pr_count = len(filtered_prs)
        self.logger.info(3, f"Found {pr_count} merged PRs in {project_path} for {year}-{month} "
                          f"(out of {total_merged_count} total merged PRs, {merged_with_closed_date} with closed dates)")
        
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
        # Calculate start and end dates for the month
        year_int = int(year)
        month_int = int(month)
        
        # Get the last day of the month
        _, last_day = calendar.monthrange(year_int, month_int)
        
        # Format dates for the API (for filtering and logging)
        start_date_str = f"{year}-{month}-01T00:00:00.000Z"
        end_date_str = f"{year}-{month}-{last_day}T23:59:59.999Z"
        
        # Fetch PR data from cache or API
        pr_data = self._fetch_pr_data(project_path, year, month)
        detailed_prs = pr_data["prs"]
        activities_data = pr_data["activities"]
        
        # Calculate PR review time (creation to approval) for all PRs
        aus_timezone = pytz.timezone('Australia/Sydney')
        start_dt = parser.parse(start_date_str).astimezone(aus_timezone)
        end_dt = parser.parse(end_date_str).astimezone(aus_timezone)
        start_timestamp = int(start_dt.timestamp() * 1000)
        end_timestamp = int(end_dt.timestamp() * 1000)
        
        self.logger.info(3, f"Calculating PR review times between {start_date_str} and {end_date_str} for {len(detailed_prs)} PRs")
        
        total_review_time = 0
        pr_count = 0
        skipped_no_created = 0
        skipped_no_approval = 0
        skipped_outside_range = 0
        
        skipped_not_merged = 0
        
        for pr in detailed_prs:
            # Only consider MERGED PRs
            if pr.get('state', '').upper() != 'MERGED':
                skipped_not_merged += 1
                continue
            
            created_date = pr.get('createdDate')
            pr_id = pr.get('id')
            
            # Skip PRs with no creation date
            if not created_date:
                skipped_no_created += 1
                continue
                
            # Get cached activities for this PR
            activities = activities_data.get(str(pr_id), [])
            approval_date = None
            
            for activity in activities:
                if activity.get('action') == 'APPROVED':
                    approval_date = activity.get('createdDate')
                    break
            
            # Skip PRs with no approval date
            if not approval_date:
                skipped_no_approval += 1
                continue
                
            # Only count PRs approved within our date range
            if start_timestamp <= approval_date <= end_timestamp:
                created_datetime = datetime.fromtimestamp(created_date / 1000)
                approval_datetime = datetime.fromtimestamp(approval_date / 1000)
                review_time = (approval_datetime - created_datetime).total_seconds() / 3600
                total_review_time += review_time
                pr_count += 1
                self.logger.info(4, f"PR #{pr_id} review time: {review_time:.2f} hours")
            else:
                skipped_outside_range += 1
                
        # Log statistics about skipped PRs
        self.logger.info(3, f"PR review time calculation - Skipped PRs: {skipped_not_merged} not merged, "
                           f"{skipped_no_created} no creation date, "
                           f"{skipped_no_approval} no approval, {skipped_outside_range} outside date range")
        
        if pr_count > 0:
            avg_review_time = total_review_time / pr_count
            avg_review_time_rounded = round(avg_review_time, 2)
            self.logger.info(3, f"Average PR review time for {project_path}: {avg_review_time_rounded:.2f} hours "
                              f"based on {pr_count} PRs approved in {year}-{month}")
            return avg_review_time_rounded
        else:
            self.logger.info(3, f"No PRs with approval found for {project_path} in {year}-{month}")
            return 0
