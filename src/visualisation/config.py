"""
Configuration for visualizing metrics data.
Maps data fields to user-friendly labels and categories.
"""

# Mapping of data fields to user-friendly labels and their categories
METRICS_MAPPING = {
    # Adoption metrics
    "a_active_users": {
        "label": "Active Users",
        "category": "Adoption",
        "format": "number"
    },
    "a_ai_adoption_rate": {
        "label": "AI Adoption Rate",
        "category": "Adoption",
        "format": "percentage"
    },
    "a_ai_usage": {
        "label": "AI Usage",
        "category": "Adoption",
        "format": "percentage"
    },
    "a_code_suggestions": {
        "label": "Code Suggestions",
        "category": "Adoption",
        "format": "number"
    },
    "a_code_accepted": {
        "label": "Code Accepted",
        "category": "Adoption",
        "format": "number"
    },
    
    # Speed metrics
    "s_merged_prs": {
        "label": "Merged PRs",
        "category": "Speed",
        "format": "number"
    },    "s_pr_review_time": {
        "label": "PR Review Time (minutes)",
        "category": "Speed",
        "format": "number",
        "inverse": True  # Lower is better
    },
    "s_story_points": {
        "label": "Story Points Completed",
        "category": "Speed",
        "format": "number"
    },
    
    # Quality metrics
    "q_code_smells": {
        "label": "Code Smells",
        "category": "Quality",
        "format": "number",
        "inverse": True  # Lower is better
    },
    "q_coverage": {
        "label": "Code Coverage",
        "category": "Quality",
        "format": "percentage"
    },
    "q_bugs": {
        "label": "Bugs",
        "category": "Quality",
        "format": "number",
        "inverse": True  # Lower is better
    },
    "q_vulnerabilities": {
        "label": "Vulnerabilities",
        "category": "Quality",
        "format": "number",
        "inverse": True  # Lower is better
    },
    
    # Experience metrics
    "e_user_satisfaction": {
        "label": "User Satisfaction",
        "category": "Experience",
        "format": "percentage"
    },
    "e_adoption": {
        "label": "Team Adoption",
        "category": "Experience",
        "format": "percentage"
    },
    "e_productivity": {
        "label": "Perceived Productivity",
        "category": "Experience",
        "format": "percentage"
    },
    "e_use_cases": {
        "label": "Use Cases",
        "category": "Experience",
        "format": "number"
    },
    
    # Delivery metrics
    "d_deployment_frequency": {
        "label": "Deployment Frequency (per week)",
        "category": "Delivery",
        "format": "number"
    }
}

# Define category display order
CATEGORY_ORDER = ["Adoption", "Speed", "Quality", "Experience", "Delivery"]

# Define color scheme for charts
CHART_COLORS = {
    "Adoption": "#4285F4",  # Blue
    "Speed": "#EA4335",     # Red
    "Quality": "#34A853",   # Green
    "Experience": "#FBBC05", # Yellow
    "Delivery": "#8334A4"    # Purple
}

# Dashboard title
DASHBOARD_TITLE = "GitHub Copilot Metrics Framework"
