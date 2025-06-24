import os
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

        # Read static assets and embed them
        css_path = os.path.join("src", "visualisation", "template.css")
        context["embedded_css"] = open(css_path, encoding="utf-8").read() if os.path.exists(css_path) else ""

        # Load and combine all JavaScript files in the correct order
        js_files = [
            os.path.join("src", "visualisation", "charts", "axisUtils.js"),
            os.path.join("src", "visualisation", "charts", "tooltips.js"),
            os.path.join("src", "visualisation", "charts", "lineChart.js"),
            os.path.join("src", "visualisation", "charts", "barChart.js"),
            os.path.join("src", "visualisation", "charts", "index.js"),
        ]

        combined_js = ""
        for js_file in js_files:
            if os.path.exists(js_file):
                with open(js_file, encoding="utf-8") as f:
                    combined_js += f.read() + "\n"

        context["embedded_js"] = combined_js

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

        print(f"✅ Dashboard generated at {os.path.join(output_dir, 'dashboard.html')}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Starting dashboard generation...")
    generate_dashboard()
    print("Done!")

