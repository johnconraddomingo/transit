import os
import shutil
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from src.visualisation.prepare_data import prepare_dashboard_context
from src.loader import load_config, load_all_data

def generate_dashboard(baseline_dir="baseline", ongoing_dir="ongoing", output_dir="reports"):
    try:
        # Load configuration and data
        config = load_config()
        baseline_data, time_series_data, average_data = load_all_data(baseline_dir, ongoing_dir)

        # Prepare dashboard context
        context = prepare_dashboard_context(config, baseline_data, time_series_data, average_data)
        context["generation_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Setup Jinja2 environment and load template
        env = Environment(loader=FileSystemLoader("src/visualisation"))
        try:
            template = env.get_template("template.html")
        except TemplateNotFound:
            print("❌ Error: template.html not found in src/visualisation/")
            return

        # Render and write the HTML output
        html_output = template.render(context)
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "dashboard.html"), "w", encoding="utf-8") as f:
            f.write(html_output)

        # Copy static assets
        for asset in ["template.css", "charts.js"]:
            src_path = os.path.join("src", "visualisation", asset)
            dest_path = os.path.join(output_dir, asset)
            if os.path.exists(src_path):
                shutil.copy(src_path, dest_path)
            else:
                print(f"⚠️ Warning: {asset} not found in src/visualisation")

        print(f"✅ Dashboard generated at {os.path.join(output_dir, 'dashboard.html')}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Starting dashboard generation...")
    generate_dashboard()
    print("Done!")

