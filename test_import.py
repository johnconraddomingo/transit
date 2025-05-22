import os
import sys

# Add the src directory to the path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)
print(f"Python path: {sys.path}")

# Try to import the module
try:
    from src.data_sources.bitbucket import BitbucketDataSource
    print("Import successful!")
    print(f"BitbucketDataSource: {BitbucketDataSource}")
except ImportError as e:
    print(f"Import error: {e}")
