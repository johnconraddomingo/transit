"""
Cache implementation for Bitbucket API data.
Provides functionality for caching PR data in memory and on disk.
"""

import os
import json
import tempfile

class BitbucketCache:
    """
    Cache for Bitbucket data to avoid redundant API calls.
    Supports both in-memory caching and disk-based caching.
    """
    def __init__(self, logger):
        """
        Initialize the BitbucketCache.
        
        Args:
            logger: Logger instance for logging cache operations
        """
        self.cache_file = None
        self.pr_cache = {}  # In-memory cache mapping project_path/year/month to PR data
        self.logger = logger
        
    def create_cache_key(self, project_path, year, month):
        """
        Create a unique key for caching PR data.
        
        Args:
            project_path (str): Project path
            year (str): Year
            month (str): Month
            
        Returns:
            str: Cache key
        """
        return f"{project_path}_{year}_{month}"
        
    def get(self, project_path, year, month):
        """
        Get data from cache.
        
        Args:
            project_path (str): Project path
            year (str): Year
            month (str): Month
            
        Returns:
            dict: Cached data or None if not in cache
        """
        cache_key = self.create_cache_key(project_path, year, month)
        
        # Check if we already have this data in memory cache
        if cache_key in self.pr_cache:
            self.logger.info(3, f"Using in-memory cached PR data for {project_path} ({year}-{month})")
            return self.pr_cache[cache_key]
            
        # Check if we have a cache file and try to load from it
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    if cache_key in cache_data:
                        self.logger.info(3, f"Using file cached PR data for {project_path} ({year}-{month})")
                        self.pr_cache[cache_key] = cache_data[cache_key]
                        return self.pr_cache[cache_key]
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(3, f"Error reading cache file: {e}")
                
        return None
        
    def put(self, project_path, year, month, data):
        """
        Store data in cache.
        
        Args:
            project_path (str): Project path
            year (str): Year
            month (str): Month
            data (dict): Data to cache
            
        Returns:
            dict: The cached data
        """
        cache_key = self.create_cache_key(project_path, year, month)
        self.pr_cache[cache_key] = data
        self._update_cache_file()
        return data
        
    def _update_cache_file(self):
        """Update the cache file with current in-memory cache data."""
        if not self.cache_file:
            # Create a temporary file for caching if it doesn't exist
            fd, self.cache_file = tempfile.mkstemp(prefix="bitbucket_pr_cache_", suffix=".json")
            os.close(fd)
            self.logger.info(3, f"Created cache file at {self.cache_file}")
            
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.pr_cache, f)
        except IOError as e:
            self.logger.error(3, f"Error writing to cache file: {e}")
            
    def cleanup(self):
        """Clean up temporary cache file when done."""
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
                self.logger.info(3, f"Removed cache file {self.cache_file}")
            except OSError as e:
                self.logger.error(3, f"Error removing cache file: {e}")
            self.cache_file = None
        self.pr_cache = {}  # Clear memory cache
