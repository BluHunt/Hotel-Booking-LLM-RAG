# LLM-Powered Booking Analytics & QA System

A system that processes hotel booking data, extracts insights, and enables retrieval-augmented question answering (RAG).

## Features

1. **Data Processing**
   - Data cleaning and preprocessing
   - Database integration

2. **Analytics & Reporting**
   - Revenue trends
   - Cancellation rates
   - Geographical distribution
   - Booking lead time distribution

3. **Question Answering with RAG**
   - Natural language queries about booking data
   - Vector database for efficient retrieval
   - History tracking for questions
   - Optimized performance with caching

4. **Performance Optimizations**
   - Singleton pattern for QA system to avoid repeated initialization
   - Query result caching for faster responses to repeated questions
   - Precomputed groupings for common analytics operations
   - Performance metrics tracking

## Getting Started

### Prerequisites

- Python 3.8+
- Required packages in `requirements.txt`

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the data loader to initialize the database:
   ```
   python src/data_loader.py
   ```

4. Start the API server:
   ```
   python src/main.py
   ```

## API Endpoints

- `POST /analytics` - Returns analytics reports
- `POST /ask` - Answers booking-related questions
- `GET /query_history` - Retrieves recent query history
- `GET /health` - Checks system status

## Project Structure

- `src/` - Source code
  - `analytics/` - Analytics and reporting functions
  - `database/` - Database models and utilities
  - `qa/` - Question answering with RAG
  - `api/` - FastAPI endpoints
  - `data_loader.py` - Data preprocessing script
  - `main.py` - API server entry point
  - `tests/` - Test scripts and benchmarking tools

## Performance

The system includes several performance optimizations:

- **API Response Time**: Reduced through singleton pattern implementation
- **Retrieval Speed**: Enhanced with precomputed groupings and LRU caching
- **Query Caching**: Previously answered questions return immediately
- **Monitoring**: Built-in performance metrics help identify bottlenecks

For detailed benchmarks and implementation details, see [IMPLEMENTATION.md](IMPLEMENTATION.md).
