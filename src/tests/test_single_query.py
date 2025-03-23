"""
Single Query Test

This script tests a single query against the QA system to verify its functionality.
"""

import os
import sys
import json
from typing import Dict, Any
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa.qa_system import QASystem

def test_single_query(query: str):
    """
    Test a single query against the QA system
    
    Args:
        query: The question to test
    """
    print(f"Testing query: {query}")
    print("-" * 80)
    
    qa_system = QASystem()
    
    try:
        response = qa_system.answer_question(query)
        print(f"Answer: {response['answer']}")
        print("-" * 80)
    except Exception as e:
        print(f"Error: {str(e)}")
        
if __name__ == "__main__":
    # Test with different query categories
    queries = [
        "What is the cancellation rate?",
        "What is the average lead time for bookings?",
        "Which hotels have the most bookings?", 
        "What countries do most guests come from?",
        "What is the total revenue for July 2017?",
        "What is the average length of stay?",
        "How many bookings include children?",
        "What is the average number of special requests?"
    ]
    
    for query in queries:
        test_single_query(query)
        print("\n")
