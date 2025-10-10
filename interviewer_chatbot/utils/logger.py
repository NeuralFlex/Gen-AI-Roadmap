import logging
import sys

# Create a single shared logger configuration
def setup_logger(name: str = "interview_bot") -> logging.Logger:
    """
    Creates or returns a logger with a standard format across the project.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:  # Avoid duplicate handlers if imported multiple times
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Optional: get a default global logger (usable directly)
logger = setup_logger()
