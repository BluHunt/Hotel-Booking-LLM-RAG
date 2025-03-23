"""
QA System Singleton

This module provides a singleton implementation of the QA system
to avoid repeated initializations and improve performance.
"""

from .qa_system import QASystem

class QASystemSingleton:
    """
    Singleton implementation of the QA system.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of the QA system.
        
        Returns:
            QASystem: The singleton instance
        """
        if cls._instance is None:
            cls._instance = QASystem()
        
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """
        Reset the singleton instance.
        This is useful for testing and when configuration changes.
        """
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
