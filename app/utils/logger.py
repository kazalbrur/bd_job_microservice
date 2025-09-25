# =============================================================================
# 22. Utility Functions (app/utils/logger.py)
# =============================================================================

import logging
import json
from datetime import datetime
from typing import Dict, Any
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in log_entry and not key.startswith('_'):
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    # Setup centralized logging configuration
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Context manager for structured logging
class LogContext:
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"Error in context: {exc_val}", extra=self.context)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra={**self.context, **kwargs})
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra={**self.context, **kwargs})
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra={**self.context, **kwargs})