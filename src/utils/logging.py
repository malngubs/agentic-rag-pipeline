"""
Logging configuration for the RAG system.
"""

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
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
        
        return json.dumps(log_entry)


def setup_logging(level: str = "INFO", log_path: str = "./data/logs"):
    """Setup structured logging for the application."""
    # Create logs directory
    Path(log_path).mkdir(parents=True, exist_ok=True)
    
    # Root logger configuration
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.handlers.RotatingFileHandler(
                f"{log_path}/app.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # JSON logging for production
    json_handler = logging.handlers.RotatingFileHandler(
        f"{log_path}/app.json",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    json_handler.setFormatter(JSONFormatter())
    
    # Add JSON handler to root logger
    logging.getLogger().addHandler(json_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logging.info("Logging configured successfully")