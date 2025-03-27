import logging

def setup_logging(logging_on):
    """Configure logging level based on logging_on parameter.
    
    Args:
        logging_on (bool): If True, enables full logging. If False, enables minimal logging.
    """
    level = logging.DEBUG if logging_on else logging.INFO
    logging.basicConfig(level=level, format='%(message)s')

def log_full(msg):
    """Log a detailed message that should only appear in full logging mode.
    
    Args:
        msg (str): The message to log
    """
    logging.debug(msg)

def log_minimal(msg):
    """Log an important message that should appear in both full and minimal logging modes.
    
    Args:
        msg (str): The message to log
    """
    logging.info(msg) 