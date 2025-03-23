"""
Q&A Accuracy Testing Framework

This script evaluates the accuracy of the QA system responses by comparing them
against expected answers for a set of test questions.
"""

import os
import sys
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa.qa_system import QASystem
from database.db import SessionLocal


class QAAccuracyTester:
    """
    Test framework for evaluating the accuracy of the QA system.
    """
    
    def __init__(self):
        """Initialize the tester."""
        self.qa_system = QASystem()
        self.test_cases = self._get_test_cases()
        self.results = []
        
    def _get_test_cases(self) -> List[Dict[str, Any]]:
        """
        Define test cases with questions and expected answer patterns.
        
        Returns:
            List of test cases with questions and expected answer patterns
        """
        return [
            {
                "id": 1,
                "category": "cancellation",
                "question": "What is the cancellation rate?",
                "expected_patterns": ["cancellation rate", "%", "canceled"]
            },
            {
                "id": 2,
                "category": "lead_time",
                "question": "What is the average lead time for bookings?",
                "expected_patterns": ["lead time", "days"]
            },
            {
                "id": 3,
                "category": "hotel",
                "question": "Which hotels have the most bookings?",
                "expected_patterns": ["hotel", "resort"]
            },
            {
                "id": 4,
                "category": "country",
                "question": "What countries do most guests come from?",
                "expected_patterns": ["countr", "national"]
            },
            {
                "id": 5,
                "category": "revenue",
                "question": "What is the total revenue for July 2017?",
                "expected_patterns": ["revenue", "booking", "found"]
            },
            {
                "id": 6,
                "category": "stay_duration",
                "question": "What is the average length of stay?",
                "expected_patterns": ["average", "stay", "booking"]
            },
            {
                "id": 7,
                "category": "family",
                "question": "How many bookings include children?",
                "expected_patterns": ["children", "booking", "found"]
            },
            {
                "id": 8,
                "category": "special_requests",
                "question": "What is the average number of special requests?",
                "expected_patterns": ["special", "request", "booking"]
            }
        ]
    
    def run_tests(self) -> None:
        """
        Run all test cases and evaluate the responses.
        """
        print(f"Starting QA accuracy evaluation at {datetime.now()}")
        print(f"Running {len(self.test_cases)} test cases...")
        
        total_score = 0
        max_score = 0
        
        # First collect all results
        for test_case in self.test_cases:
            result = self._evaluate_test_case(test_case)
            self.results.append(result)
            
            total_score += result["score"]
            max_score += len(test_case["expected_patterns"])
        
        # Then print them in a clean way
        print("\nResults:\n")
        for result in self.results:
            print(f"{'=' * 80}")
            print(f"Test {result['test_id']} - {result['category']}:")
            print(f"  Question: {result['question']}")
            print(f"  Answer: {result['answer']}")
            print(f"  Score: {result['score']}/{len(result['expected_patterns'])}")
            print(f"  Matched patterns: {result['matched_patterns']}")
            print(f"  Missing patterns: {result['missing_patterns']}")
            print(f"{'=' * 80}\n")
        
        overall_accuracy = (total_score / max_score) * 100 if max_score > 0 else 0
        print(f"Overall accuracy: {overall_accuracy:.2f}%")
        print(f"Total score: {total_score}/{max_score}\n")
        
        self._save_results(overall_accuracy)
    
    def _evaluate_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single test case.
        
        Args:
            test_case: Test case to evaluate
            
        Returns:
            Test result with score and matched patterns
        """
        question = test_case["question"]
        expected_patterns = test_case["expected_patterns"]
        
        try:
            # Get response from the QA system
            response = self.qa_system.answer_question(question)
            answer = response["answer"]
            
            # Check for expected patterns in the answer
            matched_patterns = []
            missing_patterns = []
            
            for pattern in expected_patterns:
                if pattern.lower() in answer.lower():
                    matched_patterns.append(pattern)
                else:
                    missing_patterns.append(pattern)
            
            score = len(matched_patterns)
            
            return {
                "test_id": test_case["id"],
                "category": test_case["category"],
                "question": question,
                "answer": answer,
                "expected_patterns": expected_patterns,
                "matched_patterns": matched_patterns,
                "missing_patterns": missing_patterns,
                "score": score
            }
            
        except Exception as e:
            print(f"Error evaluating test case {test_case['id']}: {str(e)}")
            return {
                "test_id": test_case["id"],
                "category": test_case["category"],
                "question": question,
                "answer": f"ERROR: {str(e)}",
                "expected_patterns": expected_patterns,
                "matched_patterns": [],
                "missing_patterns": expected_patterns,
                "score": 0
            }
    
    def _save_results(self, overall_accuracy: float) -> None:
        """
        Save the test results to a file.
        
        Args:
            overall_accuracy: Overall accuracy percentage
        """
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "test_results")
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"qa_accuracy_{timestamp}.json")
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_accuracy": overall_accuracy,
            "test_cases": len(self.test_cases),
            "results": self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"Test results saved to {output_file}")
    
    def generate_improvement_recommendations(self) -> List[str]:
        """
        Generate recommendations for improving the QA system based on test results.
        
        Returns:
            List of improvement recommendations
        """
        if not self.results:
            return ["Run tests first to generate recommendations."]
        
        recommendations = []
        categories_needing_improvement = {}
        
        for result in self.results:
            category = result["category"]
            score = result["score"]
            max_score = len(result["expected_patterns"])
            
            if score < max_score:
                if category not in categories_needing_improvement:
                    categories_needing_improvement[category] = []
                
                categories_needing_improvement[category].append({
                    "question": result["question"],
                    "missing_patterns": result["missing_patterns"]
                })
        
        # General recommendations
        recommendations.append("General QA System Improvement Recommendations:")
        
        if not categories_needing_improvement:
            recommendations.append("- The QA system is performing well across all tested categories.")
        else:
            # Add category-specific recommendations
            for category, issues in categories_needing_improvement.items():
                recommendations.append(f"\nCategory: {category}")
                recommendations.append("Issues:")
                
                for issue in issues:
                    recommendations.append(f"- Question: '{issue['question']}'")
                    recommendations.append(f"  Missing patterns: {', '.join(issue['missing_patterns'])}")
                
                # Add specific recommendations based on category
                if category == "cancellation":
                    recommendations.append("Recommendation: Enhance pattern matching for cancellation queries.")
                elif category == "lead_time":
                    recommendations.append("Recommendation: Improve lead time calculation and presentation in responses.")
                elif category == "hotel" or category == "country":
                    recommendations.append(f"Recommendation: Expand the {category} information included in responses.")
                elif category == "revenue":
                    recommendations.append("Recommendation: Add specific revenue calculation capabilities to the QA system.")
                elif category == "stay_duration":
                    recommendations.append("Recommendation: Add logic to calculate and report on stay duration metrics.")
                elif category == "family":
                    recommendations.append("Recommendation: Include family-specific booking patterns in responses.")
                elif category == "special_requests":
                    recommendations.append("Recommendation: Enhance special requests analysis in the QA system.")
        
        # Advanced recommendations
        recommendations.append("\nAdvanced Improvement Recommendations:")
        recommendations.append("1. Consider implementing a true LLM-based QA system rather than pattern matching.")
        recommendations.append("2. Expand the vectorstore capability to better match questions to relevant bookings.")
        recommendations.append("3. Add more sophisticated analytics for specialized queries (e.g., revenue forecasting).")
        recommendations.append("4. Implement confidence scores for answers to indicate reliability.")
        recommendations.append("5. Create a feedback mechanism to improve responses over time.")
        
        return recommendations


if __name__ == "__main__":
    # Create the test directory if it doesn't exist
    test_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(test_dir, exist_ok=True)
    
    # Run the tests
    tester = QAAccuracyTester()
    tester.run_tests()
    
    # Generate and print recommendations
    print("\nImprovement Recommendations:")
    recommendations = tester.generate_improvement_recommendations()
    for recommendation in recommendations:
        print(recommendation)
