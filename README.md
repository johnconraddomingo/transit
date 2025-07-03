# GitHub Copilot Metrics Framework

This Python application collects

1. **baseline/baseline.csv**: The initial set of measurements or data points collected before implementing changes, serving as a reference point to evaluate the impact and effectiveness of subsequent improvements. This is run once, gathering the average for the months of March, April and May.

2. **ongoing/YYYY-MM.csv**: Continuous data collected after GitHub Copilot’s implementation, enabling comparison against the baseline to evaluate the tool’s impact, track trends over time, and identify areas for further improvement. 
This is run on a monthly basis and saved with YYYY-MM format.

They are then visualised to demonstrate the impact of GitHub Copilot in Suncorp.

## Setup

Create and activate a virtual environment, then install the required dependencies:

Windows:
```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
```

Unix/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You'll know the virtual environment is activated when you see `(venv)` at the beginning of your terminal prompt.

1. Configure your projects in `config/projects.json`:
   ```json   
   {
        "organisation": "suncorp",
        "repos": [
            "EPI/github-copilot-training",
            "DPI/mac-motor-bicc-ui",
            "DPI/mac-motor-web-experience-api",
            "DPI/mcm-bicc-ui",
            "DPI/mcm-bicc-web-experience-api"
        ],
        "projects": [
            "SNZPA1"
        ],
        "scans": [
            "mac-motor-bicc-ui"
        ],
        "deployments": [
            "ENV-Management-jobs-NonProd/job/ENV-Management-jobs-NonProd-UAT/job/UAT-Alerting-UI"
        ]
    }
    ```

2. Configure your server URLs and data source availability in `config/servers.json`:

   ```json
   {       
        "servers": {
           "bitbucket": {
               "url": "https://bitbucket.int.corp.sun",
               "enabled": true
           },
           "sonarqube": {
               "url": "https://sonar.int.corp.sun",
               "enabled": true
           },           
           "jira": {
               "url": "https://jira.suncorp.app",
               "enabled": true
           },           
           "jenkins": {
               "url": "https://jenkins.int.corp.sun",
               "enabled": true
           },
           "github": {
               "url": "https://api.github.com",
               "enabled": true
           },
            "excel": {
                "base_path": "",
                "enabled": true
          }
       }
   }
   ```
   
   You can set `enabled` to `false` for any data source you want to disable. The application will skip collecting metrics from disabled data sources.

3. Configure your authentication in `config/tokens.json`:
     You can use either token-based authentication:
   ```json   
   {
       "bitbucket": {
           "token": "YOUR_TOKEN_HERE"
       },
       "sonarqube": {
           "token": "YOUR_SONARQUBE_TOKEN"
       },       
       "jira": {
           "token": "YOUR_JIRA_TOKEN"
       },       
       "jenkins": {
           "token": "YOUR_JENKINS_API_TOKEN",
           "username": "YOUR_JENKINS_USERNAME"
       },
       "github": {
           "token": "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
       }
   }
   ```
     Or username/password authentication:
   ```json
   {
       "bitbucket": {
           "username": "YOUR_USERNAME",
           "password": "YOUR_PASSWORD"
       },
       "sonarqube": {
           "username": "YOUR_SONARQUBE_USERNAME",
           "password": "YOUR_SONARQUBE_PASSWORD"
       },       
       "jira": {
           "username": "YOUR_JIRA_USERNAME",
           "password": "YOUR_JIRA_PASSWORD"
       },       
       "jenkins": {
           "username": "YOUR_JENKINS_USERNAME",
           "password": "YOUR_JENKINS_PASSWORD"
       },
       "github": {
           "username": "YOUR_GITHUB_USERNAME",
           "password": "YOUR_GITHUB_PASSWORD"
       }
   }
   ```
   
  > **Note**: For GitHub, token authentication is strongly recommended as username/password authentication is deprecated for the GitHub API. Use a Personal Access Token with the appropriate scopes.
 
  Create a GitHub personal access token (classic) with the following permissions, see https://github.com/settings/tokens:
  manage_billing:copilot, manage_billing:enterprise, read:audit_log, read:org, read:user

## Metrics Collection Details

The application collects metrics from different data sources using their respective APIs:

### GitHub Metrics (Enterprise)
- `a_active_users`: Uses `/enterprises/{organization}/copilot/metrics` endpoint, gets the maximum `total_active_users` for the month
- `a_code_suggestions`: Uses `/enterprises/{organization}/copilot/metrics` endpoint, sums `total_code_lines_suggested` for the month
- `a_code_accepted`: Uses `/enterprises/{organization}/copilot/metrics` endpoint, sums `total_code_lines_accepted` for the month
- `a_ai_adoption_rate`: Uses `/enterprises/{organization}/copilot/metrics` endpoint, calculates accepted/suggested lines for the month
- `a_ai_usage`: Uses `/enterprises/{organization}/copilot/metrics` endpoint, sums `total_chats` for the month

### Bitbucket Metrics
- `s_merged_prs`: Uses `/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests` with `state=ALL` and checks the status for each Pull Request
- `s_pr_review_time`: Uses pull requests endpoint plus `/activities` to calculate time between creation and approval

### JIRA Metrics
- `s_story_points`: Uses `/rest/api/2/search` with JQL query for completed issues and story points field (customfield_10002)

### SonarQube Metrics
- `q_code_smells`: Uses `/api/issues/search` with type=CODE_SMELL
- `q_bugs`: Uses `/api/issues/search` with type=BUG
- `q_vulnerabilities`: Uses `/api/issues/search` with type=VULNERABILITY
- `q_coverage`: Uses `/api/measures/component` with metricKeys=coverage,new_coverage
### Jenkins Metrics
- `d_deployment_frequency`: Uses builds API to count successful deployments

### Experience Metrics

> The Experience Metrics generates the content based on the exported survey results. Place these GitHub Copilot Experience Feedback file and rename it accordingly based on the YYYY-MM.xlsx format from when it was generated and then place it on the same `ongoing` folder

- `e_user_satisfaction`: Generated from the YYYY-MM.xlsx file survey result using Column Y. Getting the percentage of "Very disappointed"
    - Question: How would you feel if you could no longer use GitHub Copilot? 
- `e_adoption`: Generated from the YYYY-MM.xlsx file survey result using Column G. Getting the percentage of "Almost Always"
    - Question: When you are coding, how often do you use GitHub Copilot? 
- `e_productivity`: Generated from the YYYY-MM.xlsx file survey result using Columns T, U and V. Getting the percentage of "Strongly agree"
    - Question: Complete tasks faster 
    - Question: Learn from suggestions 
    - Question: Save brainpower on repetitive tasks 
    
- `e_use_cases`: Manually added from survey results

All API endpoints support both token-based and username/password authentication. Each request includes appropriate date filters (start/end) based on the specified year and month.

### Executive Summary
At the top of the visualization report, a curated selection of key metrics is prominently displayed to highlight the most relevant insights and trends that are of general interest to stakeholders.

The executive summary includes:
- Key adoption and productivity metrics
- Overall productivity index
- Experience widgets showing survey data from Excel files (Writing New Code, Refactoring Code, Writing Tests)

Inside the ``ongoing/all.csv`` contains a configuration of the total number of employees used to build the Number of Active Users Donut chart
```
a_all_users,5000
```
The Experience widgets are generated using the latest available YYYY-MM.xlsx file on the `ongoing` folder. It extracts survey responses from columns I, J, and K showing distribution of responses:
  - Column I: Experience with writing new code
  - Column J: Experience with refactoring existing code
  - Column K: Experience with writing tests

## Usage

Run the application with a year-month parameter:

```powershell
python collect_metrics.py 2025-05
```

This will collect metrics for May 2025 for all projects defined in the configuration.

## Output

The metrics are saved in CSV format in the `ongoing` directory with the filename matching the year-month parameter and a .csv extension:

```
/ongoing/2025-05.csv
```

Sample contents:
```
a_active_users,1000
a_ai_adoption_rate,0.25
a_ai_usage,250
a_code_suggestions,500
a_code_accepted,600
s_merged_prs,300
s_pr_review_time,1231
s_story_points,210
q_code_smells,3500  
q_coverage,0.30     
q_bugs,480
q_vulnerabilities,92
d_deployment_frequency,2
```

## Adding New Metrics

When you add a new metric to your data collection process, you'll need to register it in the dashboard configuration:

### 1. Add the metric to the appropriate data source class

Add your data collection method in `src/data_sources/` directory:
```python
def collect_new_metric(self, start_date, end_date):
    # Implementation of data collection logic
    return value
```

### 2. Register the metric in the MetricsCollector

In `src/metrics/collector.py`, add your metric to the `metric_mappings` dictionary:
```python
self.metric_mappings = {
    # ... existing mappings
    'new_metric_key': {
        'method': self.data_source.collect_new_metric,
        'args': []
    }
}
```

### 3. Add the metric to the dashboard configuration

In `config/dashboard.json`, add an entry in the `metrics_mapping` object:
```json
"metrics_mapping": {
  // ... existing metrics
  "new_metric_key": {
    "label": "Human-Readable Metric Name",
    "category": "Quality", // Choose an appropriate category
    "format": "number", // or "percentage"
    "inverse": false, // true if lower values are better
    "weight": 0.2 // Set appropriate weight within its category
  }
}
```

Remember to adjust the weights of other metrics in the same category to ensure they still sum to 1.0.

### 4. Verify data collection and visualization

1. Run the data collection for a test month:
   ```powershell
   python collect_metrics.py 2025-10
   ```

2. Generate the updated dashboard:
   ```powershell
   python visualise.py
   ```

3. Check that your new metric appears in the dashboard with correct formatting and categorization.

## Experiences

Experiences metrics are added manually and picked up from the survey results. Open the ongoing content CSV files and add the survey results. They should look like this:

```
a_active_users,1000
a_ai_adoption_rate,0.25
a_ai_usage,250
a_code_suggestions,500
a_code_accepted,600
s_merged_prs,300
s_pr_review_time,1231
s_story_points,210
q_code_smells,3500  
q_coverage,0.30     
q_bugs,480
q_vulnerabilities,92  
e_user_satisfaction,0.60
e_adoption,0.22
e_productivity,0.55
e_use_cases,8
d_deployment_frequency,2
```

The order of metrics in the CSV file does not matter. The visualization tool will properly organize them according to your dashboard configuration.

## Visualization

To visualize the metrics and generate an HTML dashboard, run:

```powershell
python visualise.py
```

By default, this will:
1. Load baseline data from the `baseline` directory
2. Load ongoing metrics from the `ongoing` directory
3. Generate an HTML dashboard in the `reports` directory

You can also specify custom paths:

```powershell
python visualise.py [baseline_dir] [ongoing_dir] [output_dir]
```

For example:
```powershell
python visualise.py baseline data/ongoing custom/reports
```

This allows you to:
- Maintain multiple baseline datasets for different teams or projects
- Separate ongoing metrics by team or project
- Generate dashboards in custom locations for different stakeholders

### Dashboard Features

The generated HTML dashboard includes:

- **Executive Summary**: A concise overview of key metrics and insights
  - Experience pie charts showing developer survey responses (writing new code, refactoring code, writing tests)
  - Data is sourced from the latest Excel file in the ongoing folder (columns I, J, K)
  - Interactive donut charts with clear legends showing response distribution

- **Organized Metric Categories**: Metrics grouped into sections (Adoption, Speed, Quality, Experience, Delivery)
  - Each category is collapsible for better information management
  - Visual color coding to distinguish between categories

- **Comprehensive Metric Cards**: Each metric displayed with:
  - Current value
  - Baseline value
  - New average across all time periods
  - Percentage improvement with visual indicators
    - Green for significant improvements
    - Yellow for modest improvements
    - Red for declining metrics
  - Historical data in collapsible tables
  - Interactive line charts showing trends over time

- **Productivity Analysis**:
  - Overall productivity index prominently displayed
  - Detailed table showing how each metric contributes to the index
  - Weighted calculations based on the configured category and metric weights

- **Visual Comparisons**:
  - Baseline reference lines on all charts for easy comparison
  - Consistent formatting based on metric type (percentage vs. number)
  - Clear trend indicators showing direction and magnitude of change

### Productivity Index Calculation

The productivity index is calculated using weighted contributions from each metric based on the configuration in `config/dashboard.json`:

1. **Individual metric improvement calculation**:
   ```
   Improvement = ((Current - Baseline) / |Baseline|) * 100%
   ```
   - For inverse metrics (where lower is better, marked with `"inverse": true`), the improvement is negated
   - Example: If code smells dropped from 3,500 to 3,000, the improvement is 14.3%

2. **Weighted metric contribution**:
   ```
   Contribution = Improvement * Metric.Weight * Category.Weight
   ```
   - Each metric has its own weight within its category
   - Each category has a weight in the overall index
   - Example: Code smells (14.3% improvement, 0.25 metric weight, 0.4 category weight) = 1.43% contribution

3. **Overall productivity index**:
   ```
   ProductivityIndex = Sum of all metric contributions
   ```

The default category weights are configured as:
- Speed: 38%
- Quality: 40%
- Experience: 12%
- Delivery: 10%
- Adoption: 0% (tracked but not weighted in the index)

This weighting system ensures that improvements in the most critical areas (like code quality and development speed) contribute more significantly to the overall productivity index.

### Customization

You can customize the dashboard by modifying `config/dashboard.json`:
- Metric labels and categories
- Category weights and order
- Chart colors
- Value formatting (percentage/number)

Example dashboard configuration:
```json
{
  "dashboard_title": "GitHub Copilot Metrics Framework",
  "category_order": ["Adoption", "Speed", "Quality", "Experience", "Delivery"],
  "category_weights": {
    "Adoption": 0.0,
    "Speed": 0.38,
    "Quality": 0.4,
    "Experience": 0.12,
    "Delivery": 0.1
  },
  "chart_colors": {
    "Adoption": "#4285F4",
    "Speed": "#4285F4",
    "Quality": "#4285F4",
    "Experience": "#4285F4",
    "Delivery": "#4285F4"
  },
  "metrics_mapping": {
    "a_active_users": {
      "label": "Number of Active Users",
      "category": "Adoption",
      "format": "number",
      "weight": 0.25
    },
    "a_ai_adoption_rate": {
      "label": "AI Adoption Rate",
      "category": "Adoption",
      "format": "percentage",
      "weight": 0.25
    }
    // Other metrics defined similarly
  }
}
```

Each section of the configuration serves a specific purpose:

- `dashboard_title`: Sets the title displayed at the top of the dashboard
- `category_order`: Controls the sequence in which metric categories appear in the dashboard
- `category_weights`: Determines the contribution of each category to the overall productivity index
  - Values should sum to 1.0 (or 0 if the category shouldn't impact the index)
  - Higher weights give more importance to that category
- `chart_colors`: Defines the color scheme for charts in each category
  - Uses hex color codes (e.g., "#4285F4" for blue)
  - Consistent colors help with visual identification
- `metrics_mapping`: Configures individual metrics with the following properties:
  - `label`: Human-readable name displayed in the dashboard
  - `category`: Associates the metric with a category from `category_order`
  - `format`: Presentation format ("number" or "percentage")
  - `inverse`: Optional boolean, set to `true` if lower values are better (like bugs or code smells)
  - `weight`: Relative importance within its category (weights in each category should sum to 1.0)

#### Customizing for Different Reporting Needs

You can modify the dashboard configuration to highlight different aspects of your GitHub Copilot metrics:

1. **To emphasize developer experience**: Increase the weight of the "Experience" category
   ```json
   "category_weights": {
     "Adoption": 0.0,
     "Speed": 0.3,
     "Quality": 0.3,
     "Experience": 0.3,
     "Delivery": 0.1
   }
   ```

2. **To track adoption metrics without affecting productivity index**: Keep "Adoption" weight at 0.0
   - Adoption metrics will still be displayed but won't affect the productivity index calculation

3. **To add new metrics**: Add new entries to the `metrics_mapping` object
   ```json
   "new_metric_key": {
     "label": "New Metric Display Name",
     "category": "Quality",
     "format": "number",
     "weight": 0.2
   }
   ```
   (Remember to adjust other weights in the same category to maintain a sum of 1.0)

4. **To change visualization colors**: Modify the `chart_colors` object
   ```json
   "chart_colors": {
     "Adoption": "#4285F4",  // Blue
     "Speed": "#34A853",     // Green
     "Quality": "#FBBC05",   // Yellow
     "Experience": "#EA4335", // Red
     "Delivery": "#673AB7"   // Purple
   }
   ```

