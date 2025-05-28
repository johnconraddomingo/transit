#!/usr/bin/env python3
"""
GitHub Copilot Metrics Framework Visualization Tool

This script generates a dashboard visualization of GitHub Copilot metrics
by comparing baseline data with ongoing monthly metrics data.
"""
import os
import sys
import argparse
from pathlib import Path
import webbrowser

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to use the full visualization module if available, otherwise fall back to basic
try:
    from src.visualisation import create_dashboard
    HAS_FULL_VISUALIZATION = True
except ImportError:
    from basic_dashboard import generate_simple_dashboard
    HAS_FULL_VISUALIZATION = False


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate visualizations for GitHub Copilot Metrics Framework"
    )
    parser.add_argument(
        "--baseline", 
        default="baseline",
        help="Directory containing baseline metrics data (default: 'baseline')"
    )
    parser.add_argument(
        "--ongoing", 
        default="ongoing",
        help="Directory containing ongoing metrics data (default: 'ongoing')"
    )
    parser.add_argument(
        "--output", 
        default="reports",
        help="Directory to save generated visualizations and dashboard (default: 'reports')"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the dashboard in browser after generation"
    )
    parser.add_argument(
        "--basic",
        action="store_true",
        help="Force the use of the basic dashboard generator (no external dependencies)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the dashboard generation."""
    args = parse_arguments()
    
    print(f"🚀 Generating GitHub Copilot Metrics Framework dashboard...")
    
    # Resolve paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    baseline_dir = os.path.join(current_dir, args.baseline)
    ongoing_dir = os.path.join(current_dir, args.ongoing)
    output_dir = os.path.join(current_dir, args.output)
    
    # Check if required directories exist
    if not os.path.exists(baseline_dir):
        print(f"⚠️  Warning: Baseline directory '{baseline_dir}' not found.")
    
    if not os.path.exists(ongoing_dir):
        print(f"⚠️  Warning: Ongoing data directory '{ongoing_dir}' not found.")
        
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Check if full visualization is available and not forced to use basic
        if HAS_FULL_VISUALIZATION and not args.basic:
            # Generate the dashboard with full visualization
            output_file = create_dashboard(
                output_path=output_dir,
                baseline_folder=baseline_dir,
                ongoing_folder=ongoing_dir            )
            print("Using full visualization module with charts and advanced features")
        else:
            # Generate the basic dashboard
            if args.basic:
                print("Using basic dashboard generator as requested")
            else:
                print("Full visualization module not available, falling back to basic dashboard")
              # Pass the appropriate directories to the function
            output_file = generate_simple_dashboard(
                baseline_dir=baseline_dir,
                ongoing_dir=ongoing_dir,
                output_dir=output_dir
            )
        
        print(f"✅ Dashboard generated successfully: {output_file}")
        
        # Open the dashboard if requested
        if args.open and os.path.exists(output_file):
            file_url = f"file://{os.path.abspath(output_file)}"
            print(f"🌐 Opening dashboard in browser...")
            webbrowser.open(file_url)
            
    except Exception as e:
        print(f"❌ Error generating dashboard: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
