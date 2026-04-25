import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from src.constants import PROJECT_ROOT

# 1. Project-relative path handling (bulletproof)
LOG_DIR = "logs"
LOG_FILE = f"{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.log"

# Ensures the logs directory is created at the root regardless of where script is called
logs_path = os.path.join(PROJECT_ROOT, LOG_DIR)
os.makedirs(logs_path, exist_ok=True)

LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

def configure_logger():
    """
    Sets up the global logging rules.
    Best Practice: 
    - File = DEBUG level (Store every tiny detail for forensics)
    - Console = INFO level (Keep the terminal clean for monitoring)
    """
    
    # Create the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) # Gatekeeper: allow all through

    # Clean up any existing handlers (prevents double logging on restart)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Define the professional format
    formatter = logging.Formatter(
        "[ %(asctime)s ] - %(name)s - %(levelname)s - %(message)s"
    )

    # 2. FILE HANDLER (Forensic Black-Box)
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, 
        maxBytes=5*1024*1024, # 5MB
        backupCount=3,         # Keep 3 files (15MB total)
        encoding='utf-8'       # Handle global currency symbols safely
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # 3. CONSOLE HANDLER (Real-time Dashboard)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO) # Only show high-level info on screen

    # Add handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 4. SILENCE THE NOISE (The "Senior Developer" touch)
    # Stop internal AWS and Network logs from cluttering your data
    # logging.getLogger("botocore").setLevel(logging.WARNING)
    # logging.getLogger("boto3").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)
    # logging.getLogger("s3transfer").setLevel(logging.WARNING)
    # logging.getLogger("httpx").setLevel(logging.WARNING) # For Dagshub/MLflow

# Initialize immediately
configure_logger()