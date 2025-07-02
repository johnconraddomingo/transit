"""
Experience widgets module for displaying survey data in the dashboard.
This module handles the creation and insertion of experience widgets
with pie charts showing survey data from Excel files.
"""

import os
import json
import re

from src.loader import load_survey_data

def add_experience_widgets(html_content):
    """
    Add experience widgets to the dashboard HTML content.
    
    Args:
        html_content (str): The HTML content of the dashboard
        
    Returns:
        str: The modified HTML content with experience widgets added
        bool: True if widgets were successfully added, False otherwise
    """
    # Look for the executive-summary div
    if '<div class="executive-summary">' in html_content:
        # Prepare the experience widgets HTML
        survey_data = load_survey_data('ongoing')
        
        if survey_data:
            pie_colors = ["#4E9896", "#FFCD05", "#3498db", "#e67e22", "#9b59b6", "#34495e"]
            
            # Create widget HTML
            widgets_html = []
            
            # Add Writing New Code widget
            if 'writing_new_code' in survey_data:
                writing_new_code_data = [
                    {"label": label, "value": value} 
                    for label, value in survey_data['writing_new_code'].items()
                ]
                widgets_html.append(create_widget_html(
                    "Experience: Writing New Code", 
                    "pie_writing_new_code", 
                    writing_new_code_data,
                    pie_colors
                ))
            
            # Add Refactoring Code widget
            if 'refactoring_code' in survey_data:
                refactoring_code_data = [
                    {"label": label, "value": value} 
                    for label, value in survey_data['refactoring_code'].items()
                ]
                widgets_html.append(create_widget_html(
                    "Experience: Refactoring Code", 
                    "pie_refactoring_code", 
                    refactoring_code_data,
                    pie_colors
                ))
            
            # Add Writing Tests widget
            if 'writing_tests' in survey_data:
                writing_tests_data = [
                    {"label": label, "value": value} 
                    for label, value in survey_data['writing_tests'].items()
                ]
                widgets_html.append(create_widget_html(
                    "Experience: Writing Tests", 
                    "pie_writing_tests", 
                    writing_tests_data,
                    pie_colors
                ))
            
            # Combine all widgets
            all_widgets_html = "\n    <!-- Experience survey data from " + survey_data.get('source_file', '') + " -->\n"
            all_widgets_html += "\n    ".join(widgets_html)
            
            # Use a direct approach: split the content at the end of the executive summary
            exec_summary_start = html_content.find('<div class="executive-summary">')
            if exec_summary_start != -1:
                # Find the first category section which comes right after the executive summary
                first_category = html_content.find('<details class="category-section"', exec_summary_start)
                
                if first_category != -1:
                    # Find the last closing div before the first category (this is the end of exec summary)
                    closing_div_pos = html_content.rfind('</div>', exec_summary_start, first_category)
                    
                    if closing_div_pos != -1:
                        # Split the content and insert our widgets just before the closing div
                        first_part = html_content[:closing_div_pos]
                        second_part = html_content[closing_div_pos:]
                        new_content = first_part + all_widgets_html + second_part
                        return new_content, True
            
            return html_content, False
        else:
            print("❌ No survey data available")
            return html_content, False
    else:
        print("❌ Could not find executive summary section")
        return html_content, False

def create_widget_html(title, chart_id, data, colors):
    """
    Create HTML for a single experience widget.
    
    Args:
        title (str): The title of the widget
        chart_id (str): The ID for the chart canvas
        data (list): The data for the pie chart
        colors (list): The colors for the pie chart segments
        
    Returns:
        str: The HTML for the widget
    """
    html = f'''
    <div class="executive-summary-metric experience-widget">
        <div class="metric-title">{title}</div>
        <div class="donut-chart-container">
            <canvas id="{chart_id}" class="chart-canvas" 
                data-chart='{json.dumps(data)}'
                data-options='{json.dumps({"type": "donut", "colors": colors, "isInteger": True})}' style="border: none !important;"
                data-type="donut"></canvas>
        </div>
        <div class="chart-legend donut-legend">'''
    
    for i, item in enumerate(data):
        color = colors[i % len(colors)]
        html += f'''
            <div class="legend-item">
                <div style="width: 10px; height: 10px; background-color: {color}; border-radius: 50%; margin-right: 5px;"></div>
                <span>{item["label"]} ({item["value"]})</span>
            </div>'''
    
    html += '''
        </div>
    </div>'''
    
    return html
