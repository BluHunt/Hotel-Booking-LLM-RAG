"""
Performance Comparison Tool

This script measures the performance improvements of the QA system API
after implementing optimizations.
"""

import os
import sys
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa.qa_system import QASystem
from qa.qa_singleton import QASystemSingleton

class PerformanceTest:
    """
    Performance test for comparing optimized vs non-optimized QA system.
    """
    
    def __init__(self, iterations=5):
        """
        Initialize the performance test.
        
        Args:
            iterations: Number of times to run each test
        """
        self.iterations = iterations
        
        # Standard test questions covering different categories
        self.test_questions = [
            {"category": "cancellation", "question": "What is the cancellation rate?"},
            {"category": "lead_time", "question": "What is the average lead time for bookings?"},
            {"category": "hotel", "question": "Which hotels have the most bookings?"},
            {"category": "country", "question": "What countries do most guests come from?"},
            {"category": "revenue", "question": "What is the total revenue for July 2017?"}
        ]
        
        self.results = {
            "regular": {},
            "singleton": {},
            "cached": {}
        }
    
    def test_regular_qa(self):
        """Test the regular QA system (creating new instance each time)."""
        print("\nTesting regular QA system (new instance for each query)...")
        
        for test in self.test_questions:
            category = test["category"]
            question = test["question"]
            
            print(f"\nTesting '{category}' query: {question}")
            query_times = []
            
            for i in range(self.iterations):
                # Create a new QA system each time (simulating API calls)
                qa_system = QASystem()
                
                start_time = time.time()
                qa_system.answer_question(question)
                end_time = time.time()
                
                query_time = end_time - start_time
                query_times.append(query_time)
                
                # Clean up
                qa_system.close()
                qa_system = None
                
                print(f"  Iteration {i+1}/{self.iterations}: {query_time:.4f} seconds")
            
            avg_query_time = statistics.mean(query_times)
            print(f"Average time for '{category}': {avg_query_time:.4f} seconds")
            
            self.results["regular"][category] = {
                "question": question,
                "average": avg_query_time,
                "min": min(query_times),
                "max": max(query_times),
                "times": query_times
            }
    
    def test_singleton_qa(self):
        """Test the QA system using the singleton pattern."""
        print("\nTesting singleton QA system...")
        
        # Reset the singleton to ensure a clean state
        QASystemSingleton.reset_instance()
        
        for test in self.test_questions:
            category = test["category"]
            question = test["question"]
            
            print(f"\nTesting '{category}' query: {question}")
            query_times = []
            
            for i in range(self.iterations):
                # Get the singleton instance
                qa_system = QASystemSingleton.get_instance()
                
                start_time = time.time()
                qa_system.answer_question(question)
                end_time = time.time()
                
                query_time = end_time - start_time
                query_times.append(query_time)
                
                print(f"  Iteration {i+1}/{self.iterations}: {query_time:.4f} seconds")
            
            avg_query_time = statistics.mean(query_times)
            print(f"Average time for '{category}': {avg_query_time:.4f} seconds")
            
            self.results["singleton"][category] = {
                "question": question,
                "average": avg_query_time,
                "min": min(query_times),
                "max": max(query_times),
                "times": query_times
            }
        
        # Clean up
        QASystemSingleton.reset_instance()
    
    def test_cached_queries(self):
        """Test the QA system with query caching for repeated questions."""
        print("\nTesting cached queries in singleton QA system...")
        
        # Reset the singleton to ensure a clean state
        QASystemSingleton.reset_instance()
        qa_system = QASystemSingleton.get_instance()
        
        for test in self.test_questions:
            category = test["category"]
            question = test["question"]
            
            print(f"\nTesting cached '{category}' query: {question}")
            
            # First call to populate the cache
            start_time = time.time()
            qa_system.answer_question(question)
            first_time = time.time() - start_time
            print(f"  First call (cache miss): {first_time:.4f} seconds")
            
            # Subsequent calls using the cache
            cached_times = []
            for i in range(self.iterations):
                start_time = time.time()
                qa_system.answer_question(question)
                end_time = time.time()
                
                query_time = end_time - start_time
                cached_times.append(query_time)
                
                print(f"  Cached call {i+1}/{self.iterations}: {query_time:.4f} seconds")
            
            avg_query_time = statistics.mean(cached_times)
            print(f"Average cached time for '{category}': {avg_query_time:.4f} seconds")
            
            self.results["cached"][category] = {
                "question": question,
                "first_call": first_time,
                "average_cached": avg_query_time,
                "min_cached": min(cached_times),
                "max_cached": max(cached_times),
                "times": cached_times
            }
        
        # Clean up
        QASystemSingleton.reset_instance()
    
    def run_tests(self):
        """Run all performance tests."""
        print(f"Starting performance tests at {datetime.now()}")
        print("=" * 80)
        
        # Run tests
        self.test_regular_qa()
        self.test_singleton_qa()
        self.test_cached_queries()
        
        # Print comparison
        self.print_comparison()
    
    def print_comparison(self):
        """Print a comparison of all test results."""
        print("\nPerformance Comparison:")
        print("=" * 80)
        print(f"{'Category':<15} {'Regular (s)':<15} {'Singleton (s)':<15} {'Cached (s)':<15} {'Improvement':<15}")
        print("-" * 80)
        
        for category in self.results["regular"].keys():
            regular_time = self.results["regular"][category]["average"]
            singleton_time = self.results["singleton"][category]["average"]
            cached_time = self.results["cached"][category]["average_cached"]
            
            # Calculate improvement percentage (regular to cached)
            if regular_time > 0:
                improvement = ((regular_time - cached_time) / regular_time) * 100
                improvement_str = f"{improvement:.1f}%"
            else:
                improvement_str = "N/A"
            
            print(f"{category:<15} {regular_time:<15.4f} {singleton_time:<15.4f} {cached_time:<15.4f} {improvement_str:<15}")
        
        print("\nAnalysis:")
        print("1. Regular: New QA system instance for each query")
        print("2. Singleton: Reused QA system instance via singleton pattern")
        print("3. Cached: Singleton with query result caching")
        
        # Calculate overall improvements
        regular_avg = statistics.mean([self.results["regular"][cat]["average"] for cat in self.results["regular"]])
        cached_avg = statistics.mean([self.results["cached"][cat]["average_cached"] for cat in self.results["cached"]])
        
        if regular_avg > 0:
            overall_improvement = ((regular_avg - cached_avg) / regular_avg) * 100
            print(f"\nOverall average improvement: {overall_improvement:.1f}%")
            print(f"Average response time reduced from {regular_avg:.4f}s to {cached_avg:.4f}s")


if __name__ == "__main__":
    performance_test = PerformanceTest(iterations=3)  # Reduced for faster testing
    performance_test.run_tests()
