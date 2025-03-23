import os
import numpy as np
import pandas as pd
import random
import time
from pathlib import Path
from datetime import datetime
import pickle
import re
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from sqlalchemy import func, and_, or_
from functools import lru_cache

from database.db import SessionLocal
from database.models import Booking

class BookingVectorStore:
    """
    Enhanced store for hotel booking data with improved search capabilities.
    """
    
    def __init__(self):
        """Initialize the store."""
        self.db_session = SessionLocal()
        self.booking_data = None
        self.index = None  # For compatibility with existing code
        
        # Extracted keywords for various query types
        self.keyword_categories = {
            'cancellation': ['cancel', 'cancellation', 'canceled'],
            'lead_time': ['lead', 'advance', 'booking time', 'booked'],
            'hotel': ['hotel', 'resort', 'property', 'accommodation'],
            'country': ['country', 'nation', 'nationality', 'origin'],
            'revenue': ['revenue', 'income', 'adr', 'money', 'profit', 'earn'],
            'duration': ['stay', 'night', 'duration', 'length'],
            'family': ['family', 'child', 'children', 'baby', 'babies', 'adult'],
            'requests': ['request', 'special', 'requirement', 'needs'],
            'time': ['month', 'year', 'quarter', 'season', 'date', 'period'],
            'room': ['room', 'type', 'assigned', 'reserved'],
            'booking': ['booking', 'reservation']
        }
        
        # Paths for storing data
        self.data_dir = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"))
        self.data_path = self.data_dir / "booking_data.pkl"
        
        # Cache for expensive computations
        self._country_cache = None
        self._hotel_cache = None
        self._requests_cache = None
        
        # Performance metrics
        self.search_times = {}
        
        # Load or create the data
        self.load_or_create_data()
        
        # Precompute common groupings to improve performance
        self._precompute_groupings()
    
    def load_or_create_data(self):
        """Load existing data or create new if it doesn't exist."""
        if self.data_path.exists():
            print("Loading existing booking data...")
            try:
                # Load the booking data
                with open(str(self.data_path), 'rb') as f:
                    self.booking_data = pickle.load(f)
                
                print(f"Loaded data with {len(self.booking_data)} bookings")
                return
            except Exception as e:
                print(f"Error loading data: {e}")
                print("Will create new data")
        
        # Create new data
        self.create_data()
    
    def create_data(self):
        """Create a new data store from the database."""
        print("Creating new booking data store...")
        
        # Get all bookings from the database
        bookings = self.db_session.query(Booking).all()
        
        if not bookings:
            print("No bookings found in the database. Data will be empty.")
            return
        
        # Create a list to store booking data
        self.booking_data = []
        
        # Process each booking
        for booking in bookings:
            # Convert booking to dictionary
            booking_dict = {c.name: getattr(booking, c.name) for c in booking.__table__.columns}
            
            # Add to booking data
            self.booking_data.append(booking_dict)
        
        # Save the data
        self.save_data()
        
        print(f"Created data store with {len(self.booking_data)} bookings")
    
    def save_data(self):
        """Save the current data to disk."""
        print("Saving booking data...")
        
        # Save the booking data
        with open(str(self.data_path), 'wb') as f:
            pickle.dump(self.booking_data, f)
        
        print("Booking data saved successfully")
    
    def _tokenize_query(self, query: str) -> List[str]:
        """
        Tokenize a query into individual words and phrases.
        
        Args:
            query: The search query
            
        Returns:
            List of tokens
        """
        # Convert to lowercase and replace special characters with spaces
        query = re.sub(r'[^\w\s]', ' ', query.lower())
        
        # Split into tokens
        tokens = query.split()
        
        # Remove stopwords
        stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                     'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'of', 'from'}
        tokens = [token for token in tokens if token not in stopwords]
        
        return tokens
    
    def _extract_category(self, query: str) -> str:
        """
        Extract the query category based on keywords.
        
        Args:
            query: The search query
            
        Returns:
            Category name (e.g., 'cancellation', 'lead_time')
        """
        query_lower = query.lower()
        
        # Check for each category's keywords
        category_scores = {}
        
        for category, keywords in self.keyword_categories.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            
            if score > 0:
                category_scores[category] = score
        
        # Return the category with the highest score
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return 'general'
    
    def _extract_time_info(self, query: str) -> Dict[str, Any]:
        """
        Extract time-related information from the query.
        
        Args:
            query: The search query
            
        Returns:
            Dictionary with time-related fields
        """
        query_lower = query.lower()
        time_info = {}
        
        # Extract month
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        for month_name, month_number in months.items():
            if month_name in query_lower:
                time_info['month'] = month_number
                break
        
        # Extract year
        year_pattern = r'\b(20\d{2})\b'
        year_match = re.search(year_pattern, query_lower)
        if year_match:
            time_info['year'] = int(year_match.group(1))
        
        return time_info
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant bookings with enhanced query understanding.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            list: List of relevant booking data
        """
        # Start timing
        start_time = time.time()
        
        # Extract query category
        category = self._extract_category(query)
        
        # Get time info for queries related to specific time periods
        time_info = self._extract_time_info(query)
        
        # Dispatch to specialized search based on category
        if category == 'cancellation':
            results = self._search_cancellation(query, k)
        elif category == 'lead_time':
            results = self._search_lead_time(query, k)
        elif category == 'revenue':
            results = self._search_revenue(query, time_info, k)
        elif category == 'duration':
            results = self._search_duration(query, k)
        elif category == 'family':
            results = self._search_family(query, k)
        elif category == 'hotel':
            results = self._search_hotel(query, k)
        elif category == 'country':
            results = self._search_country(query, k)
        elif category == 'requests':
            results = self._search_requests(query, k)
        else:
            # Default search: basic keyword matching across all bookings
            tokens = self._tokenize_query(query)
            relevant_bookings = []
            
            # Count matching tokens for each booking
            for booking in self.booking_data:
                booking_text = ''
                for key, value in booking.items():
                    if key != 'id':  # Skip ID field
                        booking_text += str(value) + ' '
                
                booking_text = booking_text.lower()
                matches = sum(1 for token in tokens if token in booking_text)
                
                if matches > 0:
                    result = booking.copy()
                    result['relevance_score'] = matches
                    relevant_bookings.append(result)
            
            # Sort by relevance score
            results = sorted(relevant_bookings, key=lambda x: x.get('relevance_score', 0), reverse=True)[:k]
        
        # End timing and store metrics
        end_time = time.time()
        search_time = end_time - start_time
        
        if category not in self.search_times:
            self.search_times[category] = []
        self.search_times[category].append(search_time)
        
        return results
    
    def _search_cancellation(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Special search for cancellation-related queries."""
        # Get all bookings, with a preference for cancelled ones
        cancelled = [b for b in self.booking_data if b.get('is_canceled', False)]
        not_cancelled = [b for b in self.booking_data if not b.get('is_canceled', False)]
        
        # Prioritize cancelled bookings, and add some non-cancelled for comparison
        results = cancelled[:int(k * 0.8)]  # 80% cancelled
        results += not_cancelled[:k - len(results)]  # Fill the rest with non-cancelled
        
        for result in results:
            result['relevance_score'] = 5 if result.get('is_canceled', False) else 3
        
        return results
    
    def _search_lead_time(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Special search for lead time-related queries."""
        # Get a representative sample across different lead time ranges
        lead_time_ranges = [(0, 7), (8, 30), (31, 90), (91, 365), (366, float('inf'))]
        results = []
        
        for min_lt, max_lt in lead_time_ranges:
            range_bookings = [b for b in self.booking_data 
                             if min_lt <= b.get('lead_time', 0) <= max_lt]
            
            # Take a sample from each range
            sample_size = min(int(k / len(lead_time_ranges)) + 1, len(range_bookings))
            if range_bookings:
                results.extend(random.sample(range_bookings, sample_size))
        
        # Limit to k results
        results = results[:k]
        
        # Add relevance score
        for result in results:
            result['relevance_score'] = 5  # All are equally relevant for lead time analysis
        
        return results
    
    def _search_revenue(self, query: str, time_info: Dict[str, Any], k: int) -> List[Dict[str, Any]]:
        """Special search for revenue-related queries."""
        results = []
        
        # Filter by time if provided
        if time_info:
            for booking in self.booking_data:
                matching = True
                
                # Match year if specified
                if 'year' in time_info and booking.get('arrival_date'):
                    arrival_year = booking['arrival_date'].year
                    if arrival_year != time_info['year']:
                        matching = False
                
                # Match month if specified
                if 'month' in time_info and booking.get('arrival_date'):
                    arrival_month = booking['arrival_date'].month
                    if arrival_month != time_info['month']:
                        matching = False
                
                if matching and not booking.get('is_canceled', False):
                    result = booking.copy()
                    result['relevance_score'] = 5
                    results.append(result)
        else:
            # Get top ADR bookings if no time specified
            sorted_bookings = sorted(
                [b for b in self.booking_data if not b.get('is_canceled', False)],
                key=lambda x: x.get('adr', 0),
                reverse=True
            )
            results = sorted_bookings[:k]
            for result in results:
                result['relevance_score'] = 5
        
        return results[:k]
    
    def _search_duration(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Special search for duration of stay queries."""
        results = []
        
        for booking in self.booking_data:
            weekend_nights = booking.get('stays_in_weekend_nights', 0)
            week_nights = booking.get('stays_in_week_nights', 0)
            total_nights = weekend_nights + week_nights
            
            if total_nights > 0:
                result = booking.copy()
                result['total_nights'] = total_nights
                result['relevance_score'] = 5
                results.append(result)
                
                if len(results) >= k * 3:  # Get more than needed for a representative sample
                    break
        
        # Get a diversity of durations
        results.sort(key=lambda x: x.get('total_nights', 0))
        
        # Take elements at regular intervals to get a representative sample
        step = max(1, len(results) // k)
        sampled_results = [results[i] for i in range(0, len(results), step)][:k]
        
        return sampled_results
    
    def _search_family(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Special search for family-related queries."""
        # Get bookings with children or babies
        family_bookings = [b for b in self.booking_data 
                          if b.get('children', 0) > 0 or b.get('babies', 0) > 0]
        
        if len(family_bookings) >= k:
            return family_bookings[:k]
        
        # If we don't have enough family bookings, add some bookings with multiple adults
        multi_adult = [b for b in self.booking_data 
                      if b.get('adults', 0) > 1 and b.get('children', 0) == 0 and b.get('babies', 0) == 0]
        
        results = family_bookings + multi_adult[:k - len(family_bookings)]
        
        # Add relevance score
        for result in results:
            if result.get('children', 0) > 0 or result.get('babies', 0) > 0:
                result['relevance_score'] = 5
            else:
                result['relevance_score'] = 3
        
        return results
    
    def _search_hotel(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Special search for hotel-related queries."""
        # Group bookings by hotel
        hotels = self._get_hotel_groupings()
        results = []
        for hotel, bookings in hotels.items():
            sample_size = min(int(k / len(hotels)) + 1, len(bookings))
            results.extend(random.sample(bookings, sample_size))
        
        # Limit to k results
        results = results[:k]
        
        # Add relevance score
        for result in results:
            result['relevance_score'] = 5
        
        return results
    
    def _search_country(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Special search for country-related queries."""
        # Group bookings by country
        countries = self._get_country_groupings()
        results = []
        top_countries = sorted(countries.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Get top countries by booking count
        countries_to_include = min(5, len(top_countries))  # Include up to 5 countries
        
        for i in range(countries_to_include):
            country, bookings = top_countries[i]
            sample_size = min(int(k / countries_to_include) + 1, len(bookings))
            results.extend(random.sample(bookings, sample_size))
        
        # Limit to k results
        results = results[:k]
        
        # Add relevance score
        for result in results:
            result['relevance_score'] = 5
        
        return results
    
    def _search_requests(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Special search for special requests queries."""
        # Group bookings by number of special requests
        request_groups = self._get_request_groupings()
        results = []
        for request_count in sorted(request_groups.keys()):
            bookings = request_groups[request_count]
            sample_size = min(int(k / len(request_groups)) + 1, len(bookings))
            results.extend(random.sample(bookings, sample_size))
        
        # Limit to k results
        results = results[:k]
        
        # Add relevance score
        for result in results:
            result['relevance_score'] = 5
        
        return results
    
    @lru_cache(maxsize=None)
    def _get_hotel_groupings(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get groupings of bookings by hotel."""
        hotels = {}
        for booking in self.booking_data:
            hotel = booking.get('hotel', 'Unknown')
            if hotel not in hotels:
                hotels[hotel] = []
            hotels[hotel].append(booking)
        return hotels
    
    @lru_cache(maxsize=None)
    def _get_country_groupings(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get groupings of bookings by country."""
        countries = {}
        for booking in self.booking_data:
            country = booking.get('country', 'Unknown')
            if country not in countries:
                countries[country] = []
            countries[country].append(booking)
        return countries
    
    @lru_cache(maxsize=None)
    def _get_request_groupings(self) -> Dict[int, List[Dict[str, Any]]]:
        """Get groupings of bookings by number of special requests."""
        request_groups = {}
        for booking in self.booking_data:
            requests = booking.get('total_of_special_requests', 0)
            if requests not in request_groups:
                request_groups[requests] = []
            request_groups[requests].append(booking)
        return request_groups
    
    def _precompute_groupings(self):
        """Precompute common groupings to improve performance."""
        self._get_hotel_groupings()
        self._get_country_groupings()
        self._get_request_groupings()
    
    @property
    def ntotal(self):
        """Return the total number of bookings for compatibility."""
        return len(self.booking_data) if self.booking_data else 0
    
    def close(self):
        """Close the database session."""
        if self.db_session:
            self.db_session.close()
