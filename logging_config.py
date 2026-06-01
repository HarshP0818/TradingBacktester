import logging
import sys
import os
from logging.handlers import RotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s %(name)s %(levelname)s: %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler with rotation (audit trail)
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'backtester.log'),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
