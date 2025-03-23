"""
Cancellation Query Test

Tests the cancellation rate query with proper expected patterns.
"""

import os
import sys
import time
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa.qa_system import QASystem

def test_cancellation_query():
    """Test the cancellation rate query specifically"""
    question = "What is the cancellation rate?"
    expected_patterns = ["cancellation rate", "%", "canceled", "found"]
    
    # Initialize QA system
    qa_system = QASystem()
    
    # Ask the question
    print(f"\nTesting question: \"{question}\"")
    print("-" * 80)
    
    response = qa_system.answer_question(question)
    
    # Print answer
    print(f"Answer: {response['answer']}")
    
    # Check for expected patterns
    matched = []
    missing = []
    for pattern in expected_patterns:
        if pattern.lower() in response['answer'].lower():
            matched.append(pattern)
        else:
            missing.append(pattern)
    
    # Print results
    score = len(matched)
    total = len(expected_patterns)
    print(f"Score: {score}/{total} ({(score/total)*100:.2f}%)")
    print(f"Matched patterns: {matched}")
    print(f"Missing patterns: {missing}")
    print("-" * 80)
    
    return score, total, response['answer']

if __name__ == "__main__":
    print(f"Cancellation Query Test - {datetime.now()}")
    print("=" * 80)
    test_cancellation_query()
