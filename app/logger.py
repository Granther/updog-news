import os
import logging

from app.config import DevelopmentConfig, ProductionConfig

def create_logger(name, config=DevelopmentConfig) -> logging.Logger:
    """Returns instantiated logger using environment settings"""

    logger = logging.getLogger(name)
    log_level = config.LOG_LEVEL
    logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(config.LOGS_DIR)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger