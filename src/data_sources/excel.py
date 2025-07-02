"""
Excel Data Source

This module provides functionality for reading data from Excel files.
"""

import os
import pandas as pd
from datetime import datetime

class ExcelDataSource:
    """
    Data source for Excel files, primarily for processing survey results.
    """
    
    def __init__(self, base_path=None, **auth_args):
        """
        Initialize the Excel data source.
        
        Args:
            base_path (str, optional): Base path where Excel files are stored.
                                      Defaults to the 'ongoing' directory in the project root.
            **auth_args: Additional authentication arguments (not used for Excel)
        """
        self.base_path = base_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ongoing')
    
    def get_survey_results(self, project, year, month, **kwargs):
        """Process survey results from Excel file for a given year and month.
        
        Args:
            project (str): Project identifier (not used for survey data)
            year (str): Year for the survey data
            month (str): Month for the survey data
            **kwargs: Additional arguments
            
        Returns:
            dict: Dictionary with survey metrics as percentages
        """
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        
        year_month = f"{year}-{month}"
        excel_path = os.path.join(self.base_path, f"{year_month}.xlsx")
        
        if not os.path.exists(excel_path):
            logger.warning(2, f"Survey results file not found: {excel_path}")
            return {
                'user_satisfaction': 0,
                'adoption': 0,
                'productivity': 0
            }
        
        try:
            logger.info(2, f"Processing survey results from {excel_path}")
            df = pd.read_excel(excel_path)
            
            # Get total number of responses (rows in the dataframe)
            total_responses = len(df)
            if total_responses == 0:
                logger.warning(3, "Survey file contains no responses")
                return {
                    'user_satisfaction': 0,
                    'adoption': 0,
                    'productivity': 0
                }
            
            logger.info(3, f"Total survey responses: {total_responses}")
            
            # Excel uses 0-based indices internally, so we need to convert letter-based column references
            # Map Excel column letters to 0-based indices
            col_to_idx = {
                'G': 6, # Column G is the 7th column (0-indexed)
                'T': 19, # Column T is the 20th column (0-indexed)
                'U': 20, # Column U is the 21st column (0-indexed)
                'V': 21, # Column V is the 22nd column (0-indexed)
                'Y': 24, # Column Y is the 25th column (0-indexed)
            }
            
            # Count fields in column Y that contain "Very disappointed" for user_satisfaction
            user_satisfaction_count = 0
            y_idx = col_to_idx['Y']
            if y_idx < len(df.columns):
                user_satisfaction_count = df.iloc[:, y_idx].astype(str).str.contains('Very disappointed', case=False, na=False).sum()
                logger.info(3, f"Found {user_satisfaction_count} 'Very disappointed' responses in column Y (index {y_idx})")
            else:
                logger.warning(3, f"Column Y (index {y_idx}) not found in survey results with {len(df.columns)} columns")
            
            # Count fields in column G that contain "Almost always" for adoption
            adoption_count = 0
            g_idx = col_to_idx['G']
            if g_idx < len(df.columns):
                adoption_count = df.iloc[:, g_idx].astype(str).str.contains('Almost always', case=False, na=False).sum()
                logger.info(3, f"Found {adoption_count} 'Almost always' responses in column G (index {g_idx})")
            else:
                logger.warning(3, f"Column G (index {g_idx}) not found in survey results with {len(df.columns)} columns")
            
            # Count fields in columns T, U and V that contain "Strongly agree" for productivity
            productivity_count = 0
            for col, idx in {'T': col_to_idx['T'], 'U': col_to_idx['U'], 'V': col_to_idx['V']}.items():
                if idx < len(df.columns):
                    col_count = df.iloc[:, idx].astype(str).str.contains('Strongly agree', case=False, na=False).sum()
                    productivity_count += col_count
                    logger.info(3, f"Found {col_count} 'Strongly agree' responses in column {col} (index {idx})")
                else:
                    logger.warning(3, f"Column {col} (index {idx}) not found in survey results with {len(df.columns)} columns")
            
            # Convert counts to percentages
            user_satisfaction_pct = round((user_satisfaction_count / total_responses), 4) if total_responses > 0 else 0
            adoption_pct = round((adoption_count / total_responses), 4) if total_responses > 0 else 0

            # For productivity, we need to consider that there are 3 columns, so the maximum count could be 3 * total_responses
            # We'll calculate as a percentage of total possible responses across all 3 columns
            total_productivity_responses = total_responses * 3  # Three columns: T, U, V
            productivity_pct = round((productivity_count / total_productivity_responses), 4) if total_productivity_responses > 0 else 0
            
            logger.info(2, f"User Satisfaction Percentage: {round(user_satisfaction_pct * 100,4)}%")
            logger.info(2, f"Adoption Percentage: {round(adoption_pct * 100,4)}%")
            logger.info(2, f"Productivity Percentage: {round(productivity_pct * 100,4)}%")

            return {
                'user_satisfaction': user_satisfaction_pct,
                'adoption': adoption_pct,
                'productivity': productivity_pct
            }
            
        except Exception as e:
            logger.error(1, f"Error processing survey results: {str(e)}")
            return {
                'user_satisfaction': 0,
                'adoption': 0,
                'productivity': 0
            }
    
    def cleanup_cache(self):
        """Clean up any temporary cache files."""
        # No cache files for Excel data source
        pass
