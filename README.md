# Project Metrics Collector

This Python application collects various metrics for a specified month across predefined projects.

## Setup

1. Configure your projects in `config/projects.json`:
   ```json
   {
       "projects": [
           "EPI/github-copilot-training",
           "PROJECT2/REPO2"
       ]
   }
   ```

2. Configure your server URLs in `config/servers.json`:
   ```json
   {
       "servers": {
           "bitbucket": "https://bitbucket.int.corp.sun"
       }
   }
   ```

3. Configure your access tokens in `config/tokens.json`:
   ```json
   {
       "tokens": {
           "bitbucket": "YOUR_TOKEN_HERE"
       }
   }
   ```

## Usage

Run the application with a year-month parameter:

```powershell
python main.py 2025-05
```

This will collect metrics for May 2025 for all projects defined in the configuration.

## Output

The metrics are saved in CSV format in the `ongoing` directory with the filename matching the year-month parameter:

```
/ongoing/2025-05
```

Sample contents:
```
merged_pr,123
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
