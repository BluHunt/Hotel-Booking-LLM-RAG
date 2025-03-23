"""
Single Query Test with Clean Output

Tests a single question against the QA system with proper output handling.
"""

import os
import sys
import time
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa.qa_system import QASystem

def run_test(question, expected_patterns):
    """
    Run a single test with the given question
    
    Args:
        question: The question to test
        expected_patterns: List of patterns expected in the answer
    """
    # Initialize QA system
    qa_system = QASystem()
    
    # Ask the question
    print(f"\nTesting question: \"{question}\"")
    print("-" * 80)
    
    start_time = time.time()
    response = qa_system.answer_question(question)
    end_time = time.time()
    
    # Print answer
    print(f"Answer: {response['answer']}")
    print(f"Response time: {end_time - start_time:.2f} seconds")
    
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
    # Test a single question or all questions
    print(f"QA System Test - {datetime.now()}")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        question = sys.argv[1]
        run_test(question, ["relevant", "information"])
    else:
        # Test all standard questions
        test_cases = [
            {
                "category": "cancellation",
                "question": "What is the cancellation rate?",
                "expected_patterns": ["cancellation rate", "%", "canceled"]
            },
            {
                "category": "lead_time",
                "question": "What is the average lead time for bookings?",
                "expected_patterns": ["lead time", "days"]
            },
            {
                "category": "hotel",
                "question": "Which hotels have the most bookings?",
                "expected_patterns": ["hotel", "resort"]
            },
            {
                "category": "country",
                "question": "What countries do most guests come from?",
                "expected_patterns": ["countr", "national"]
            },
            {
                "category": "revenue",
                "question": "What is the total revenue for July 2017?",
                "expected_patterns": ["revenue", "booking", "found"]
            },
            {
                "category": "stay_duration",
                "question": "What is the average length of stay?",
                "expected_patterns": ["average", "stay", "booking"]
            },
            {
                "category": "family",
                "question": "How many bookings include children?",
                "expected_patterns": ["children", "booking", "found"]
            },
            {
                "category": "special_requests",
                "question": "What is the average number of special requests?",
                "expected_patterns": ["special", "request", "booking"]
            }
        ]
        
        total_score = 0
        max_score = 0
        
        print("Running standard test suite...\n")
        for i, test in enumerate(test_cases):
            print(f"Test {i+1}: {test['category']}")
            score, total, _ = run_test(test['question'], test['expected_patterns'])
            total_score += score
            max_score += total
            print()  # Extra spacing between tests
            
        # Print overall results
        accuracy = (total_score / max_score) * 100 if max_score > 0 else 0
        print("\nTest Suite Results")
        print("=" * 80)
        print(f"Overall Accuracy: {accuracy:.2f}%")
        print(f"Total Score: {total_score}/{max_score}")
