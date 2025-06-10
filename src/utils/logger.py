"""
Custom Logger Module
 
This module provides a custom logger that supports indentation levels
for better log readability.
"""
 
import logging
from functools import wraps
 
class IndentLogger:
    """A logger wrapper that provides indentation support."""
    def __init__(self, logger_name=None, indent_char="   "):
        """
        Initialize the IndentLogger.
       
        Args:
            logger_name: Name for the logger (optional)
            indent_char: Character(s) used for indentation (default is three spaces)
        """
        if logger_name:
            self.logger = logging.getLogger(logger_name)
        else:
            self.logger = logging.getLogger()
        self.indent_char = indent_char
        
        # Change WARNING level name to WARN for more concise logging
        logging.addLevelName(logging.WARNING, "WARN ")
 
    def _log_with_indent(self, level_func, level, message, *args, **kwargs):
        """
        Log a message with the specified indentation level.
       
        Args:
            level_func: The logging function to use (info, warning, error, etc.)
            level: The indentation level (0 = no indent, 1 = one indent, etc.)
            message: The message to log
            *args, **kwargs: Additional arguments to pass to the logger
        """
        indent = self.indent_char * level
       
        # Add a newline before level 0 messages to visually separate main sections
        if level == 0:
            level_func("")  # Empty log line
            # Make level 0 messages bright green
            bright_green = "\033[92m"
            reset_color = "\033[0m"
            message = f"{bright_green}{message}{reset_color}"
           
        level_func(f"{indent}{message}", *args, **kwargs)
   
    def info(self, level, message, *args, **kwargs):
        """Log an info message with indentation."""
        if isinstance(level, int):
            self._log_with_indent(self.logger.info, level, message, *args, **kwargs)
        else:
            # For backwards compatibility, if first arg is not an int, assume it's part of the message
            self.logger.info(level, *([message] + list(args)), **kwargs)
   
    def warning(self, level, message, *args, **kwargs):
        """Log a warning message with indentation, a warning icon, and orange color."""
        warning_icon = "⚠️  "
        grey_color = "\033[90m"  
        reset_color = "\033[0m"
        
        logging.addLevelName(logging.WARNING, "WARN ")
        
        if isinstance(level, int):
            message = f"{grey_color}{warning_icon}{message}{reset_color}"
            self._log_with_indent(self.logger.warning, level, message, *args, **kwargs)
        else:
            level = f"{grey_color}{warning_icon}{level}{reset_color}"
            self.logger.warning(level, *([message] + list(args)), **kwargs)         
   
    def error(self, level, message, *args, **kwargs):
        """Log an error message with indentation, an X icon, and red color."""
        error_icon = "❌  "
        red_color = "\033[31m"
        reset_color = "\033[0m"
        if isinstance(level, int):
            message = f"{red_color}{error_icon}{message}{reset_color}"
            self._log_with_indent(self.logger.error, level, message, *args, **kwargs)
        else:
            level = f"{red_color}{error_icon}{level}{reset_color}"
            self.logger.error(level, *([message] + list(args)), **kwargs)
   
    def debug(self, level, message, *args, **kwargs):
        """Log a debug message with indentation."""
        if isinstance(level, int):
            self._log_with_indent(self.logger.debug, level, message, *args, **kwargs)
        else:
            self.logger.debug(level, *([message] + list(args)), **kwargs)
   
    def critical(self, level, message, *args, **kwargs):
        """Log a critical message with indentation, an X icon, and bright red color."""
        critical_icon = " "
        bright_red_color = "\033[91m"  # Bright red for critical to distinguish from regular errors
        reset_color = "\033[0m"
        if isinstance(level, int):
            message = f"{bright_red_color}{critical_icon}{message}{reset_color}"
            self._log_with_indent(self.logger.critical, level, message, *args, **kwargs)
        else:
            level = f"{bright_red_color}{critical_icon}{level}{reset_color}"
            self.logger.critical(level, *([message] + list(args)), **kwargs)
   
    # Provide compatibility with regular logger
    def setLevel(self, level):
        """Set the logging level."""
        self.logger.setLevel(level)
   
    def addHandler(self, handler):
        """Add a handler to the logger."""
        self.logger.addHandler(handler)
   
    def removeHandler(self, handler):
        """Remove a handler from the logger."""
        self.logger.removeHandler(handler)
 
# Create a function to get or create an IndentLogger
def get_logger(name=None):
    """
    Get an IndentLogger instance.
   
    Args:
        name: The name for the logger.
       
    Returns:
        An IndentLogger instance.
    """
    return IndentLogger(name)