import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import statistics
from collections import Counter, defaultdict
import re
import logging
import time

from database.db import SessionLocal
from database.models import QueryHistory
from qa.vectorstore import BookingVectorStore

class QASystem:
    """
    Question-answering system for hotel booking data.
    """
    
    def __init__(self):
        """Initialize the QA system."""
        # Create a database session
        self.db_session = SessionLocal()
        
        # Create a vector store
        self.vector_store = BookingVectorStore()
        
        # Cache for repeated questions
        self.query_cache = {}
        
        # For tracking performance
        self.performance_metrics = defaultdict(list)
    
    def answer_question(self, query: str) -> Dict[str, Any]:
        """
        Answer a question based on the hotel booking data.
        
        Args:
            query: The user's question
            
        Returns:
            Dictionary with answer and any supporting data
        """
        # Log the query
        query_id = self._log_query(query)
        
        # Check the query cache
        if query in self.query_cache:
            answer, relevant_bookings, query_category = self.query_cache[query]
        else:
            # Search for relevant bookings
            relevant_bookings = self.vector_store.search(query, k=5)
            
            # Generate an answer
            query_category = self._determine_query_category(query)
            answer = self._generate_answer(query, relevant_bookings, query_category)
            
            # Update the query cache
            self.query_cache[query] = (answer, relevant_bookings, query_category)
        
        # Update the query history with the answer
        self._update_query_history(query_id, answer, relevant_bookings)
        
        # Return the answer
        return {
            "query": query,
            "answer": answer,
            "relevant_bookings": self._format_bookings(relevant_bookings),
            "category": query_category
        }
    
    def _determine_query_category(self, query: str) -> str:
        """
        Determine the category of a query.
        
        Args:
            query: The user's question
            
        Returns:
            Category of the query
        """
        # Use the vector store's category extraction
        if hasattr(self.vector_store, '_extract_category'):
            return self.vector_store._extract_category(query)
        
        # Fallback to basic category detection
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['cancel', 'cancellation']):
            return 'cancellation'
        elif any(word in query_lower for word in ['lead', 'advance']):
            return 'lead_time'
        elif any(word in query_lower for word in ['revenue', 'income', 'money']):
            return 'revenue'
        elif any(word in query_lower for word in ['stay', 'night', 'duration']):
            return 'duration'
        elif any(word in query_lower for word in ['child', 'family', 'baby']):
            return 'family'
        elif any(word in query_lower for word in ['hotel', 'resort']):
            return 'hotel'
        elif any(word in query_lower for word in ['country', 'nationality']):
            return 'country'
        elif any(word in query_lower for word in ['special', 'request']):
            return 'requests'
        
        return 'general'
    
    def _generate_answer(self, query: str, relevant_bookings: List[Dict[str, Any]], category: str) -> str:
        """
        Generate an answer based on the query and relevant bookings.
        
        Args:
            query: The user's question
            relevant_bookings: List of relevant booking data
            category: Category of the query
            
        Returns:
            Generated answer
        """
        if not relevant_bookings:
            return "I don't have any booking information to answer this question."
        
        # Handle different categories of questions
        if category == 'cancellation':
            return self._answer_cancellation(query, relevant_bookings)
        elif category == 'lead_time':
            return self._answer_lead_time(query, relevant_bookings)
        elif category == 'revenue':
            return self._answer_revenue(query, relevant_bookings)
        elif category == 'duration':
            return self._answer_duration(query, relevant_bookings)
        elif category == 'family':
            return self._answer_family(query, relevant_bookings)
        elif category == 'hotel':
            return self._answer_hotel(query, relevant_bookings)
        elif category == 'country':
            return self._answer_country(query, relevant_bookings)
        elif category == 'requests':
            return self._answer_requests(query, relevant_bookings)
        
        # Generic answer for other categories
        return "Based on the booking data, I found some related information, but I'm not sure how to answer your specific question."
    
    def _answer_cancellation(self, query: str, bookings: List[Dict[str, Any]]) -> str:
        """Generate answer for cancellation-related queries."""
        # Count cancelled vs. non-cancelled bookings
        cancelled = sum(1 for b in bookings if b.get('is_canceled', False))
        total = len(bookings)
        
        if 'rate' in query.lower():
            # Calculate overall cancellation rate from all bookings
            all_bookings = self.vector_store.booking_data
            all_cancelled = sum(1 for b in all_bookings if b.get('is_canceled', False))
            all_total = len(all_bookings)
            rate = (all_cancelled / all_total) * 100 if all_total > 0 else 0
            
            return f"I found that the overall cancellation rate is {rate:.2f}%. Out of {all_total} bookings, {all_cancelled} were canceled."
        
        # Look for patterns in cancelled bookings
        if cancelled > 0:
            # Analyze lead times for cancelled bookings
            lead_times = [b.get('lead_time', 0) for b in bookings if b.get('is_canceled', False)]
            avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
            
            # Analyze deposit types for cancelled bookings
            deposit_types = [b.get('deposit_type', 'Unknown') for b in bookings if b.get('is_canceled', False)]
            deposit_counts = Counter(deposit_types)
            most_common_deposit = deposit_counts.most_common(1)[0][0] if deposit_counts else 'Unknown'
            
            return f"I found that out of {total} bookings, {cancelled} were canceled ({(cancelled/total)*100:.2f}%). " \
                   f"The average lead time for canceled bookings was {avg_lead_time:.1f} days. " \
                   f"The most common deposit type for canceled bookings was '{most_common_deposit}'."
        else:
            return "I haven't found any canceled bookings in the sample. This suggests a low cancellation rate, " \
                   "but I would need to analyze more data to give you a precise cancellation rate."
    
    def _answer_lead_time(self, query: str, bookings: List[Dict[str, Any]]) -> str:
        """Generate answer for lead time-related queries."""
        # Extract lead times
        lead_times = [b.get('lead_time', 0) for b in bookings if b.get('lead_time') is not None]
        
        if not lead_times:
            return "I couldn't find any lead time information in the booking data."
        
        # Calculate statistics
        avg_lead_time = sum(lead_times) / len(lead_times)
        median_lead_time = statistics.median(lead_times) if lead_times else 0
        max_lead_time = max(lead_times) if lead_times else 0
        min_lead_time = min(lead_times) if lead_times else 0
        
        if 'average' in query.lower():
            return f"The average lead time for bookings is {avg_lead_time:.1f} days."
        
        # Analyze lead times by hotel type
        hotel_lead_times = defaultdict(list)
        for booking in bookings:
            lead_time = booking.get('lead_time')
            hotel = booking.get('hotel')
            if lead_time is not None and hotel:
                hotel_lead_times[hotel].append(lead_time)
        
        hotel_avg_lead_times = {
            hotel: sum(times) / len(times) if times else 0
            for hotel, times in hotel_lead_times.items()
        }
        
        result = f"Based on the booking data, the average lead time is {avg_lead_time:.1f} days, with a median of {median_lead_time:.1f} days. "
        
        if hotel_avg_lead_times:
            hotel_info = ", ".join(f"{hotel}: {avg:.1f} days" for hotel, avg in hotel_avg_lead_times.items())
            result += f"Average lead times by hotel type: {hotel_info}."
        
        return result
    
    def _answer_revenue(self, query: str, bookings: List[Dict[str, Any]]) -> str:
        """Generate answer for revenue-related queries."""
        # Filter out cancelled bookings
        active_bookings = [b for b in bookings if not b.get('is_canceled', False)]
        
        if not active_bookings:
            return "I couldn't find any revenue information from completed bookings."
        
        # Calculate revenue (ADR * nights)
        revenues = []
        for booking in active_bookings:
            adr = booking.get('adr', 0)
            weekend_nights = booking.get('stays_in_weekend_nights', 0)
            week_nights = booking.get('stays_in_week_nights', 0)
            total_nights = weekend_nights + week_nights
            revenue = adr * total_nights
            revenues.append(revenue)
        
        total_revenue = sum(revenues)
        avg_revenue = total_revenue / len(revenues) if revenues else 0
        
        # Check for time period in query
        query_lower = query.lower()
        time_period = ""
        
        # Look for month names
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        found_month = None
        for month_name, month_num in months.items():
            if month_name in query_lower:
                found_month = month_name
                time_period = f" for {month_name.capitalize()}"
                break
        
        # Look for year
        year_match = re.search(r'\b(20\d{2})\b', query_lower)
        found_year = None
        if year_match:
            found_year = year_match.group(1)
            time_period += f" {found_year}" if found_month else f" for {found_year}"
        
        if 'total' in query_lower:
            return f"The total revenue{time_period} from the analyzed bookings is €{total_revenue:.2f}."
        else:
            return f"Based on {len(active_bookings)} analyzed bookings{time_period}, " \
                   f"the total revenue is €{total_revenue:.2f}, with an average of €{avg_revenue:.2f} per booking."
    
    def _answer_duration(self, query: str, bookings: List[Dict[str, Any]]) -> str:
        """Generate answer for duration of stay-related queries."""
        # Calculate stay durations
        durations = []
        for booking in bookings:
            weekend_nights = booking.get('stays_in_weekend_nights', 0)
            week_nights = booking.get('stays_in_week_nights', 0)
            total_nights = weekend_nights + week_nights
            
            if total_nights > 0:
                durations.append({
                    'total': total_nights,
                    'weekend': weekend_nights,
                    'weekday': week_nights,
                    'hotel': booking.get('hotel', 'Unknown')
                })
        
        if not durations:
            return "I couldn't find any information about stay durations in the booking data."
        
        # Calculate statistics
        avg_total = sum(d['total'] for d in durations) / len(durations)
        avg_weekend = sum(d['weekend'] for d in durations) / len(durations)
        avg_weekday = sum(d['weekday'] for d in durations) / len(durations)
        
        if 'average' in query.lower() or 'mean' in query.lower():
            return f"The average length of stay is {avg_total:.1f} nights, comprising {avg_weekday:.1f} weekday nights and {avg_weekend:.1f} weekend nights."
        
        # Group by hotel type
        hotel_durations = defaultdict(list)
        for d in durations:
            hotel_durations[d['hotel']].append(d['total'])
        
        hotel_avg_durations = {
            hotel: sum(nights) / len(nights)
            for hotel, nights in hotel_durations.items()
        }
        
        # Find most common stay length
        duration_counts = Counter(d['total'] for d in durations)
        most_common_duration = duration_counts.most_common(1)[0][0] if duration_counts else 0
        
        result = f"Based on the booking data, the average length of stay is {avg_total:.1f} nights. " \
                 f"The most common stay duration is {most_common_duration} nights."
        
        if hotel_avg_durations:
            hotel_info = ", ".join(f"{hotel}: {avg:.1f} nights" for hotel, avg in hotel_avg_durations.items())
            result += f" Average stay by hotel type: {hotel_info}."
        
        return result
    
    def _answer_family(self, query: str, bookings: List[Dict[str, Any]]) -> str:
        """Generate answer for family-related queries."""
        # Count bookings with children or babies
        with_children = sum(1 for b in bookings if b.get('children', 0) > 0)
        with_babies = sum(1 for b in bookings if b.get('babies', 0) > 0)
        total = len(bookings)
        
        if 'include children' in query.lower() or 'how many' in query.lower():
            # Get overall statistics from all bookings
            all_bookings = self.vector_store.booking_data
            all_with_children = sum(1 for b in all_bookings if b.get('children', 0) > 0)
            all_with_babies = sum(1 for b in all_bookings if b.get('babies', 0) > 0)
            all_total = len(all_bookings)
            
            children_percent = (all_with_children / all_total) * 100 if all_total > 0 else 0
            babies_percent = (all_with_babies / all_total) * 100 if all_total > 0 else 0
            
            return f"Out of {all_total} bookings, {all_with_children} ({children_percent:.2f}%) include children " \
                   f"and {all_with_babies} ({babies_percent:.2f}%) include babies."
        
        # Analyze family booking patterns
        family_hotels = [b.get('hotel', 'Unknown') for b in bookings if b.get('children', 0) > 0 or b.get('babies', 0) > 0]
        hotel_counts = Counter(family_hotels)
        most_common_hotel = hotel_counts.most_common(1)[0][0] if hotel_counts else 'Unknown'
        
        family_room_types = [b.get('reserved_room_type', 'Unknown') for b in bookings if b.get('children', 0) > 0 or b.get('babies', 0) > 0]
        room_counts = Counter(family_room_types)
        most_common_room = room_counts.most_common(1)[0][0] if room_counts else 'Unknown'
        
        return f"Looking at {total} bookings, {with_children} include children and {with_babies} include babies. " \
               f"Families most commonly stay at '{most_common_hotel}' hotel, and the most popular room type for families is '{most_common_room}'."
    
    def _answer_hotel(self, query: str, bookings: List[Dict[str, Any]]) -> str:
        """Generate answer for hotel-related queries."""
        # Count bookings by hotel
        hotels = [b.get('hotel', 'Unknown') for b in bookings]
        hotel_counts = Counter(hotels)
        
        if 'most bookings' in query.lower():
            # Get overall statistics from all bookings
            all_bookings = self.vector_store.booking_data
            all_hotels = [b.get('hotel', 'Unknown') for b in all_bookings]
            all_hotel_counts = Counter(all_hotels)
            
            top_hotels = all_hotel_counts.most_common(3)
            hotel_info = ", ".join(f"'{hotel}' ({count} bookings)" for hotel, count in top_hotels)
            
            return f"The hotels with the most bookings are {hotel_info}."
        
        # Analyze hotel stay patterns
        hotel_data = defaultdict(lambda: {'total': 0, 'cancelled': 0, 'adr': []})
        
        for booking in bookings:
            hotel = booking.get('hotel', 'Unknown')
            hotel_data[hotel]['total'] += 1
            if booking.get('is_canceled', False):
                hotel_data[hotel]['cancelled'] += 1
            if booking.get('adr') is not None:
                hotel_data[hotel]['adr'].append(booking['adr'])
        
        result = "Here's information about the hotels in the booking data:\n"
        
        for hotel, data in hotel_data.items():
            cancel_rate = (data['cancelled'] / data['total']) * 100 if data['total'] > 0 else 0
            avg_adr = sum(data['adr']) / len(data['adr']) if data['adr'] else 0
            
            result += f"- {hotel}: {data['total']} bookings, {cancel_rate:.2f}% cancellation rate, "
            result += f"average daily rate of €{avg_adr:.2f}\n"
        
        return result.strip()
    
    def _answer_country(self, query: str, bookings: List[Dict[str, Any]]) -> str:
        """Generate answer for country-related queries."""
        # Count bookings by country
        countries = [b.get('country', 'Unknown') for b in bookings]
        country_counts = Counter(countries)
        
        if 'most' in query.lower() or 'top' in query.lower():
            # Get overall statistics from all bookings
            all_bookings = self.vector_store.booking_data
            all_countries = [b.get('country', 'Unknown') for b in all_bookings]
            all_country_counts = Counter(all_countries)
            
            top_countries = all_country_counts.most_common(5)
            country_info = ", ".join(f"{country} ({count} bookings)" for country, count in top_countries)
            
            return f"The top countries of origin for guests are: {country_info}."
        
        # Analyze booking patterns by country
        country_data = defaultdict(lambda: {'total': 0, 'adr': [], 'stay_length': []})
        
        for booking in bookings:
            country = booking.get('country', 'Unknown')
            country_data[country]['total'] += 1
            
            if booking.get('adr') is not None:
                country_data[country]['adr'].append(booking['adr'])
            
            weekend_nights = booking.get('stays_in_weekend_nights', 0)
            week_nights = booking.get('stays_in_week_nights', 0)
            total_nights = weekend_nights + week_nights
            
            if total_nights > 0:
                country_data[country]['stay_length'].append(total_nights)
        
        result = "Here's information about guest countries in the booking data:\n"
        
        for country, data in sorted(country_data.items(), key=lambda x: x[1]['total'], reverse=True):
            avg_adr = sum(data['adr']) / len(data['adr']) if data['adr'] else 0
            avg_stay = sum(data['stay_length']) / len(data['stay_length']) if data['stay_length'] else 0
            
            result += f"- {country}: {data['total']} bookings, average stay of {avg_stay:.1f} nights, "
            result += f"average daily rate of €{avg_adr:.2f}\n"
        
        return result.strip()
    
    def _answer_requests(self, query: str, bookings: List[Dict[str, Any]]) -> str:
        """Generate answer for special requests-related queries."""
        # Extract special requests counts
        request_counts = [b.get('total_of_special_requests', 0) for b in bookings if b.get('total_of_special_requests') is not None]
        
        if not request_counts:
            return "I couldn't find any information about special requests in the booking data."
        
        # Calculate statistics
        avg_requests = sum(request_counts) / len(request_counts) if request_counts else 0
        max_requests = max(request_counts) if request_counts else 0
        
        if 'average' in query.lower() or 'mean' in query.lower():
            # Get overall statistics from all bookings
            all_bookings = self.vector_store.booking_data
            all_request_counts = [b.get('total_of_special_requests', 0) for b in all_bookings if b.get('total_of_special_requests') is not None]
            all_avg_requests = sum(all_request_counts) / len(all_request_counts) if all_request_counts else 0
            
            return f"The average number of special requests per booking is {all_avg_requests:.2f}."
        
        # Analyze request patterns
        request_distribution = Counter(request_counts)
        most_common_count = request_distribution.most_common(1)[0][0] if request_distribution else 0
        
        # Analyze requests by hotel type
        hotel_requests = defaultdict(list)
        for booking in bookings:
            requests = booking.get('total_of_special_requests')
            hotel = booking.get('hotel')
            if requests is not None and hotel:
                hotel_requests[hotel].append(requests)
        
        hotel_avg_requests = {
            hotel: sum(counts) / len(counts) if counts else 0
            for hotel, counts in hotel_requests.items()
        }
        
        result = f"Based on the booking data, the average number of special requests is {avg_requests:.2f} per booking. " \
                 f"The most common number of requests is {most_common_count}, and the maximum is {max_requests}."
        
        if hotel_avg_requests:
            hotel_info = ", ".join(f"{hotel}: {avg:.2f}" for hotel, avg in hotel_avg_requests.items())
            result += f" Average requests by hotel type: {hotel_info}."
        
        return result
    
    def _format_bookings(self, bookings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format booking data for API response.
        
        Args:
            bookings: List of booking data
            
        Returns:
            Formatted booking data
        """
        formatted_bookings = []
        
        for booking in bookings:
            # Create a copy of the booking
            formatted_booking = {}
            
            # Format each field
            for key, value in booking.items():
                # Convert numpy types to Python types
                if isinstance(value, (np.int64, np.int32, np.int16, np.int8)):
                    formatted_booking[key] = int(value)
                elif isinstance(value, (np.float64, np.float32)):
                    formatted_booking[key] = float(value)
                elif isinstance(value, np.bool_):
                    formatted_booking[key] = bool(value)
                else:
                    formatted_booking[key] = value
            
            formatted_bookings.append(formatted_booking)
        
        return formatted_bookings
    
    def _log_query(self, query: str) -> int:
        """
        Log a query to the database.
        
        Args:
            query: The user's question
            
        Returns:
            The query ID
        """
        # Create a new query history record
        query_history = QueryHistory(
            query_text=query,  
            timestamp=datetime.now()
        )
        
        # Add to the database
        self.db_session.add(query_history)
        self.db_session.commit()
        
        # Get the query ID
        query_id = query_history.id
        
        return query_id
    
    def _update_query_history(self, query_id: int, answer: str, relevant_bookings: List[Dict[str, Any]]) -> None:
        """
        Update a query history record with the answer and relevant bookings.
        
        Args:
            query_id: The query ID
            answer: The generated answer
            relevant_bookings: List of relevant booking data
        """
        try:
            # Get the query history record
            query_history = self.db_session.query(QueryHistory).filter(QueryHistory.id == query_id).first()
            
            if query_history:
                # Update with the answer and relevant bookings
                query_history.response_text = answer  
                
                # Store relevant booking IDs as a JSON string
                if relevant_bookings:
                    booking_ids = [booking.get('id', '') for booking in relevant_bookings if booking.get('id')]
                    query_history.relevant_booking_ids = json.dumps(booking_ids)
                
                # Commit the changes
                self.db_session.commit()
        except Exception as e:
            print(f"Error updating query history: {str(e)}")
            self.db_session.rollback()
    
    def get_query_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the query history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of query history records
        """
        # Get query history records
        query_history = self.db_session.query(QueryHistory).order_by(QueryHistory.id.desc()).limit(limit).all()
        
        # Format the records
        history = []
        for qh in query_history:
            history.append({
                "id": qh.id,
                "query": qh.query_text,
                "answer": qh.response_text,
                "timestamp": qh.timestamp.isoformat() if qh.timestamp else None,
                "relevant_booking_ids": json.loads(qh.relevant_booking_ids) if qh.relevant_booking_ids else []
            })
        
        return history
    
    def close(self):
        """Close the database session and vector store."""
        if self.db_session:
            self.db_session.close()
        
        if self.vector_store:
            self.vector_store.close()
