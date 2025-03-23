"""
Clean Test for QA System

This script tests the QA system with a cleaner output approach
"""

import os
import sys
import json
from typing import Dict, Any
from datetime import datetime
import io
import contextlib

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa.qa_system import QASystem

def test_qa_system():
    """Test the QA system with multiple queries"""
    
    # Initialize QA system (only load data once)
    print("Initializing QA system...")
    qa_system = QASystem()
    print("QA system initialized.\n")
    
    # Define test cases
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
    
    # Run tests
    results = []
    for i, test_case in enumerate(test_cases):
        # Capture output to avoid interleaving
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            response = qa_system.answer_question(test_case["question"])
        
        # Calculate score
        score = 0
        matched = []
        missing = []
        for pattern in test_case["expected_patterns"]:
            if pattern.lower() in response["answer"].lower():
                score += 1
                matched.append(pattern)
            else:
                missing.append(pattern)
        
        # Store result
        results.append({
            "id": i+1,
            "category": test_case["category"],
            "question": test_case["question"],
            "answer": response["answer"],
            "score": score,
            "total": len(test_case["expected_patterns"]),
            "matched": matched,
            "missing": missing
        })
    
    # Calculate overall statistics
    total_score = sum(r["score"] for r in results)
    max_score = sum(r["total"] for r in results)
    accuracy = (total_score / max_score) * 100 if max_score > 0 else 0
    
    # Print results
    print(f"QA System Accuracy Test - {datetime.now()}")
    print("=" * 80)
    
    for result in results:
        print(f"\nTest {result['id']} - {result['category']}:")
        print(f"  Question: {result['question']}")
        print(f"  Answer: {result['answer']}")
        print(f"  Score: {result['score']}/{result['total']}")
        print(f"  Matched patterns: {result['matched']}")
        print(f"  Missing patterns: {result['missing']}")
        print("-" * 80)
    
    print(f"\nOverall Accuracy: {accuracy:.2f}%")
    print(f"Total Score: {total_score}/{max_score}")
    
    # Print recommendations for improvement
    print("\nImprovement Recommendations:")
    for result in results:
        if result["missing"]:
            print(f"\nCategory: {result['category']}")
            print(f"  Question: '{result['question']}'")
            print(f"  Missing patterns: {', '.join(result['missing'])}")
            print(f"  Recommendation: Enhance {result['category']} analysis logic.")

if __name__ == "__main__":
    test_qa_system()
