import os
import logging
from datetime import datetime

def setup_logger(name: str, log_to_file: bool = False) -> logging.Logger:
    """
    Sets up a logger with the given name.
    
    :param name: Name of the logger
    :param log_to_file: Whether to log to a file in addition to console
    :return: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Always add console handler
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        logger.addHandler(console_handler)

        if log_to_file:
            # Create logs directory if it doesn't exist
            logs_dir = "logs"
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)

            # Create file handler
            log_file = os.path.join(logs_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)

    return logger
