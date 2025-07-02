import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.visualisation.render import generate_dashboard
from src.visualisation.experience_widgets import add_experience_widgets
import os

def add_experience_widgets_to_dashboard():
    """Add experience widgets showing survey data from Excel files to the dashboard"""
    # First generate the dashboard normally
    print("Starting dashboard generation...")
    generate_dashboard()
    
    # Now add the experience widgets using the modular function
    output_path = os.path.join("reports", "dashboard.html")
    if os.path.exists(output_path):
        # Read the current HTML content
        with open(output_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Add experience widgets to the HTML content
        modified_content, success = add_experience_widgets(html_content)
        
        if success:
            # Write the modified content back to the file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(modified_content)
            print("✅ Experience widgets added to dashboard")
        else:
            print("❌ Failed to add experience widgets to dashboard")
    else:
        print("❌ Dashboard file not found")
    
    print("Done!")

if __name__ == "__main__":
    add_experience_widgets_to_dashboard()