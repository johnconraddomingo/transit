# Project Metrics Collector

This Python application collects various metrics for a specified month across predefined projects.

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
   ```json   {
       "projects": [
           "EPI/github-copilot-training",
           "PROJECT2/REPO2"
       ],
       "deployments": [
           "EPI/github-copilot-training/main",
           "EPI/github-copilot-training/deploy-prod"
       ]
   }
   ```

2. Configure your server URLs and data source availability in `config/servers.json`:
   ```json
   {       "servers": {
           "bitbucket": {
               "url": "https://bitbucket.int.corp.sun",
               "enabled": true
           },
           "sonarqube": {
               "url": "https://sonar.int.corp.sun",
               "enabled": true
           },           "jira": {
               "url": "https://jira.int.corp.sun",
               "enabled": true
           },           "jenkins": {
               "url": "https://jenkins.int.corp.sun",
               "enabled": true
           },
           "github": {
               "url": "https://api.github.com",
               "enabled": true
           }
       }
   }
   ```
   
   You can set `enabled` to `false` for any data source you want to disable. The application will skip collecting metrics from disabled data sources.

3. Configure your authentication in `config/tokens.json`:
     You can use either token-based authentication:
   ```json   {
       "bitbucket": {
           "token": "YOUR_TOKEN_HERE"
       },
       "sonarqube": {
           "token": "YOUR_SONARQUBE_TOKEN"
       },       
       "jira": {
           "token": "YOUR_JIRA_TOKEN"
       },       "jenkins": {
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
       },       "jira": {
           "username": "YOUR_JIRA_USERNAME",
           "password": "YOUR_JIRA_PASSWORD"
       },       "jenkins": {
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

## Usage

Run the application with a year-month parameter:

```powershell
python main.py 2025-05
```

This will collect metrics for May 2025 for all projects defined in the configuration.

## Output

The metrics are saved in CSV format in the `ongoing` directory with the filename matching the year-month parameter and a .csv extension:

```
/ongoing/2025-05.csv
```

Sample contents:
```
s_merged_prs,123
q_bugs,45
s_story_points,89
d_deployment_frequency,12
a_active_users,35
```

## Adding New Metrics

To add a new metric:

1. Implement the data collection method in the appropriate data source class.
2. Register the metric in the `MetricsCollector` class by adding an entry to the `metric_mappings` dictionary.

## Adding New Data Sources

To add a new data source:

1. Create a new class in the `src/data_sources` directory.
2. Implement the necessary methods to collect metrics.
3. Register the data source with the `MetricsCollector` instance in `main.py`.
