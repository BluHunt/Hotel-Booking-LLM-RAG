"""
API Performance Benchmarking Tool

This script measures the performance of the QA system API, identifies bottlenecks,
and provides recommendations for optimization.
"""

import os
import sys
import time
import statistics
import json
from datetime import datetime
from typing import Dict, List, Any
import cProfile
import pstats
from io import StringIO

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa.qa_system import QASystem
from qa.vectorstore import BookingVectorStore
from database.db import SessionLocal


class APIBenchmark:
    """
    Benchmark the performance of the QA system API.
    """
    
    def __init__(self, iterations=10):
        """
        Initialize the benchmark tool.
        
        Args:
            iterations: Number of times to run each benchmark
        """
        self.iterations = iterations
        self.qa_system = None
        self.results = {}
        
        # Standard test questions covering different categories
        self.test_questions = [
            {"category": "cancellation", "question": "What is the cancellation rate?"},
            {"category": "lead_time", "question": "What is the average lead time for bookings?"},
            {"category": "hotel", "question": "Which hotels have the most bookings?"},
            {"category": "country", "question": "What countries do most guests come from?"},
            {"category": "revenue", "question": "What is the total revenue for July 2017?"},
            {"category": "stay_duration", "question": "What is the average length of stay?"},
            {"category": "family", "question": "How many bookings include children?"},
            {"category": "special_requests", "question": "What is the average number of special requests?"}
        ]
    
    def benchmark_initialization(self):
        """Benchmark the initialization time of the QA system."""
        print("Benchmarking QA system initialization...")
        
        init_times = []
        for i in range(self.iterations):
            start_time = time.time()
            qa_system = QASystem()
            end_time = time.time()
            
            init_time = end_time - start_time
            init_times.append(init_time)
            
            # Clean up to prevent memory issues
            qa_system.close()
            
            print(f"  Iteration {i+1}/{self.iterations}: {init_time:.4f} seconds")
        
        avg_init_time = statistics.mean(init_times)
        self.results["initialization"] = {
            "average": avg_init_time,
            "min": min(init_times),
            "max": max(init_times),
            "median": statistics.median(init_times),
            "stddev": statistics.stdev(init_times) if len(init_times) > 1 else 0
        }
        
        print(f"Average initialization time: {avg_init_time:.4f} seconds")
        print("-" * 80)
    
    def benchmark_query_processing(self):
        """Benchmark the query processing time of the QA system."""
        print("Benchmarking query processing...")
        
        # Initialize QA system once for all queries
        self.qa_system = QASystem()
        
        results_by_category = {}
        
        for test in self.test_questions:
            category = test["category"]
            question = test["question"]
            
            print(f"\nTesting '{category}' query: {question}")
            query_times = []
            
            for i in range(self.iterations):
                start_time = time.time()
                self.qa_system.answer_question(question)
                end_time = time.time()
                
                query_time = end_time - start_time
                query_times.append(query_time)
                
                print(f"  Iteration {i+1}/{self.iterations}: {query_time:.4f} seconds")
            
            avg_query_time = statistics.mean(query_times)
            results_by_category[category] = {
                "question": question,
                "average": avg_query_time,
                "min": min(query_times),
                "max": max(query_times),
                "median": statistics.median(query_times),
                "stddev": statistics.stdev(query_times) if len(query_times) > 1 else 0
            }
            
            print(f"Average '{category}' query time: {avg_query_time:.4f} seconds")
        
        self.results["query_processing"] = results_by_category
        
        # Clean up
        self.qa_system.close()
        self.qa_system = None
        print("-" * 80)
    
    def profile_bottlenecks(self):
        """Profile the QA system to identify bottlenecks."""
        print("Profiling QA system to identify bottlenecks...")
        
        self.qa_system = QASystem()
        
        # Choose a representative query
        question = "What is the cancellation rate?"
        
        # Profile the query execution
        pr = cProfile.Profile()
        pr.enable()
        
        # Execute the query
        self.qa_system.answer_question(question)
        
        pr.disable()
        
        # Analyze the profile data
        s = StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Print top 20 bottlenecks
        
        self.results["profile"] = s.getvalue()
        
        # Clean up
        self.qa_system.close()
        self.qa_system = None
        
        print("Profiling complete")
        print("-" * 80)
    
    def run_benchmarks(self):
        """Run all benchmarks."""
        print(f"Starting API benchmarks at {datetime.now()}")
        print("=" * 80)
        
        # Run benchmarks
        self.benchmark_initialization()
        self.benchmark_query_processing()
        self.profile_bottlenecks()
        
        # Save results
        self._save_results()
        
        # Print summary
        self._print_summary()
    
    def _save_results(self):
        """Save benchmark results to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "benchmark_results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Save all results except profile data which might be too large
        results_to_save = {k: v for k, v in self.results.items() if k != "profile"}
        
        results_file = os.path.join(results_dir, f"benchmark_{timestamp}.json")
        with open(results_file, 'w') as f:
            json.dump(results_to_save, f, indent=2)
        
        # Save profile data separately
        if "profile" in self.results:
            profile_file = os.path.join(results_dir, f"profile_{timestamp}.txt")
            with open(profile_file, 'w') as f:
                f.write(self.results["profile"])
        
        print(f"Results saved to {results_file}")
    
    def _print_summary(self):
        """Print a summary of the benchmark results."""
        print("\nPerformance Summary:")
        print("=" * 80)
        
        # Initialization summary
        if "initialization" in self.results:
            init_data = self.results["initialization"]
            print(f"QA System Initialization: {init_data['average']:.4f} seconds")
        
        # Query processing summary
        if "query_processing" in self.results:
            query_data = self.results["query_processing"]
            print("\nQuery Processing Times:")
            
            # Sort categories by average time (slowest first)
            sorted_categories = sorted(
                query_data.items(),
                key=lambda x: x[1]["average"],
                reverse=True
            )
            
            for category, data in sorted_categories:
                print(f"  {category}: {data['average']:.4f} seconds")
        
        print("\nRecommendations for Optimization:")
        print("1. Consider caching frequently asked questions")
        print("2. Optimize data loading and vector store initialization")
        print("3. Review the profiling results to address specific bottlenecks")


if __name__ == "__main__":
    benchmark = APIBenchmark(iterations=5)  # Reduced iterations for faster testing
    benchmark.run_benchmarks()
