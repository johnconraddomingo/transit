"""
Bitbucket data source for retrieving metrics from a Bitbucket server.

This module is a compatibility shim that imports and re-exports the BitbucketDataSource
from the refactored bitbucket package. This maintains backward compatibility with
existing imports while allowing the codebase to use the new modular structure.
"""

# Import from the refactored package
from src.data_sources.bitbucket import BitbucketDataSource

# Keep the original class name for backward compatibility
# BitbucketDataSource is now imported from the package