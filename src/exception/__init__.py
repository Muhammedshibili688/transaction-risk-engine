import sys
import os

def error_message_detail(error, error_detail: sys):
    """
    Unpacks the 'sys' module to find the exact location of the crash.
    """
    # exc_tb is the 'Traceback' object - the DNA of the error
    _, _, exc_tb = error_detail.exc_info()
    
    # Extract the file path and line number
    file_name = exc_tb.tb_frame.f_code.co_filename
    line_number = exc_tb.tb_lineno
    
    # Just show the filename, not the entire local C:/Users/... path
    short_file_name = os.path.basename(file_name)

    error_message = (
        f"!! FraudEngine Exception: \n"
        f"   Script: [{short_file_name}] \n"
        f"   Line:   [{line_number}] \n"
        f"   Error:  [{str(error)}]"
    )

    return error_message

class FraudException(Exception):
    """
    Custom Exception class for the Fraud Detection Engine.
    Every time this is raised, it automatically writes to your logs.
    """
    def __init__(self, error_message, error_detail: sys):
        # Initialize the parent class
        super().__init__(error_message)
        
        # Build the surgical error message
        self.error_message = error_message_detail(
            error_message, error_detail=error_detail
        )
        
        # SENIOR MOVE: Import logging here to avoid circular dependency
        from src.logger import logging
        # Every exception is logged automatically to the log file!
        logging.error(self.error_message)

    def __str__(self):
        """
        Ensures that when you run 'print(e)', you see the detailed message.
        """
        return self.error_message