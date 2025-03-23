import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from pathlib import Path
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc
import json
from typing import Dict, List, Any, Union

from database.models import Booking
from database.db import SessionLocal


class BookingAnalyzer:
    """
    Class for analyzing hotel booking data and generating insights.
    """
    
    def __init__(self, db_session=None):
        """Initialize the analyzer with a database session."""
        self.db = db_session if db_session else SessionLocal()
        self.output_dir = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "charts"))
        self.output_dir.mkdir(exist_ok=True)
    
    def close(self):
        """Close the database session."""
        if self.db:
            self.db.close()
    
    def get_revenue_trends(self, period='monthly'):
        """
        Calculate revenue trends over time.
        
        Args:
            period: Time period for aggregation ('daily', 'weekly', 'monthly', 'yearly')
            
        Returns:
            dict: Revenue trends data
        """
        print(f"Calculating revenue trends by {period}...")
        
        # Query to get bookings that were not canceled
        query = self.db.query(
            Booking.arrival_date,
            Booking.adr,
            (Booking.stays_in_weekend_nights + Booking.stays_in_week_nights).label('total_nights')
        ).filter(Booking.is_canceled == False)
        
        # Execute query and convert to DataFrame
        df = pd.read_sql(query.statement, query.session.bind)
        
        # Calculate revenue for each booking
        df['revenue'] = df['adr'] * df['total_nights']
        
        # Set arrival_date as index
        df['arrival_date'] = pd.to_datetime(df['arrival_date'])
        df.set_index('arrival_date', inplace=True)
        
        # Aggregate by period
        if period == 'daily':
            revenue_by_period = df.resample('D')['revenue'].sum()
        elif period == 'weekly':
            revenue_by_period = df.resample('W')['revenue'].sum()
        elif period == 'monthly':
            revenue_by_period = df.resample('M')['revenue'].sum()
        elif period == 'yearly':
            revenue_by_period = df.resample('Y')['revenue'].sum()
        else:
            raise ValueError(f"Invalid period: {period}")
        
        # Convert to dict for JSON serialization
        result = {
            'period': period,
            'dates': revenue_by_period.index.strftime('%Y-%m-%d').tolist(),
            'revenue': revenue_by_period.tolist()
        }
        
        # Create a visualization
        plt.figure(figsize=(12, 6))
        plt.plot(revenue_by_period.index, revenue_by_period.values)
        plt.title(f'Revenue Trends ({period.capitalize()})')
        plt.xlabel('Date')
        plt.ylabel('Revenue')
        plt.grid(True)
        plt.tight_layout()
        
        # Save visualization
        chart_path = self.output_dir / f"revenue_trends_{period}.png"
        plt.savefig(chart_path)
        plt.close()
        
        # Add chart path to result
        result['chart_path'] = str(chart_path)
        
        return result
    
    def get_cancellation_rates(self):
        """
        Calculate cancellation rate as percentage of total bookings.
        
        Returns:
            dict: Cancellation rate data
        """
        print("Calculating cancellation rates...")
        
        # Get total bookings and canceled bookings count
        total_bookings = self.db.query(func.count(Booking.id)).scalar()
        canceled_bookings = self.db.query(func.count(Booking.id)).filter(Booking.is_canceled == True).scalar()
        
        # Calculate cancellation rate
        cancellation_rate = (canceled_bookings / total_bookings) * 100 if total_bookings > 0 else 0
        
        # Create result dict
        result = {
            'total_bookings': total_bookings,
            'canceled_bookings': canceled_bookings,
            'cancellation_rate': cancellation_rate
        }
        
        # Create a visualization
        labels = ['Confirmed', 'Canceled']
        sizes = [total_bookings - canceled_bookings, canceled_bookings]
        colors = ['#4CAF50', '#F44336']
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title('Booking Cancellation Rate')
        plt.tight_layout()
        
        # Save visualization
        chart_path = self.output_dir / "cancellation_rate.png"
        plt.savefig(chart_path)
        plt.close()
        
        # Add chart path to result
        result['chart_path'] = str(chart_path)
        
        return result
    
    def get_geographical_distribution(self):
        """
        Calculate geographical distribution of users doing the bookings.
        
        Returns:
            dict: Geographical distribution data
        """
        print("Calculating geographical distribution...")
        
        # Query to get bookings by country
        query = self.db.query(
            Booking.country,
            func.count(Booking.id).label('booking_count')
        ).group_by(Booking.country).order_by(desc('booking_count'))
        
        # Execute query and convert to DataFrame
        df = pd.read_sql(query.statement, query.session.bind)
        
        # Calculate percentage
        total = df['booking_count'].sum()
        df['percentage'] = (df['booking_count'] / total) * 100
        
        # Get top 10 and aggregate others
        top_10 = df.head(10)
        others = pd.DataFrame({
            'country': ['Others'],
            'booking_count': [df.iloc[10:]['booking_count'].sum() if len(df) > 10 else 0],
            'percentage': [df.iloc[10:]['percentage'].sum() if len(df) > 10 else 0]
        })
        
        # Combine top 10 and others
        result_df = pd.concat([top_10, others])
        
        # Create result dict
        result = {
            'countries': result_df['country'].tolist(),
            'booking_counts': result_df['booking_count'].tolist(),
            'percentages': result_df['percentage'].tolist()
        }
        
        # Create a visualization
        plt.figure(figsize=(12, 8))
        sns.barplot(x='booking_count', y='country', data=result_df)
        plt.title('Geographical Distribution of Bookings')
        plt.xlabel('Number of Bookings')
        plt.ylabel('Country')
        plt.tight_layout()
        
        # Save visualization
        chart_path = self.output_dir / "geographical_distribution.png"
        plt.savefig(chart_path)
        plt.close()
        
        # Add chart path to result
        result['chart_path'] = str(chart_path)
        
        return result
    
    def get_lead_time_distribution(self):
        """
        Calculate booking lead time distribution.
        
        Returns:
            dict: Lead time distribution data
        """
        print("Calculating lead time distribution...")
        
        # Query to get lead times
        query = self.db.query(Booking.lead_time)
        
        # Execute query and convert to DataFrame
        df = pd.read_sql(query.statement, query.session.bind)
        
        # Define bins for lead time
        bins = [0, 7, 30, 90, 180, 365, float('inf')]
        labels = ['0-7 days', '8-30 days', '31-90 days', '91-180 days', '181-365 days', '365+ days']
        
        # Create lead time categories
        df['lead_time_category'] = pd.cut(df['lead_time'], bins=bins, labels=labels)
        
        # Count bookings in each category
        lead_time_counts = df['lead_time_category'].value_counts().sort_index()
        
        # Calculate statistics
        stats = {
            'mean': df['lead_time'].mean(),
            'median': df['lead_time'].median(),
            'min': df['lead_time'].min(),
            'max': df['lead_time'].max()
        }
        
        # Create result dict
        result = {
            'categories': lead_time_counts.index.tolist(),
            'counts': lead_time_counts.tolist(),
            'statistics': stats
        }
        
        # Create a visualization
        plt.figure(figsize=(12, 6))
        sns.histplot(df['lead_time'], bins=20, kde=True)
        plt.title('Booking Lead Time Distribution')
        plt.xlabel('Lead Time (days)')
        plt.ylabel('Number of Bookings')
        plt.axvline(stats['mean'], color='r', linestyle='--', label=f'Mean: {stats["mean"]:.1f} days')
        plt.axvline(stats['median'], color='g', linestyle='--', label=f'Median: {stats["median"]:.1f} days')
        plt.legend()
        plt.tight_layout()
        
        # Save visualization
        chart_path = self.output_dir / "lead_time_distribution.png"
        plt.savefig(chart_path)
        plt.close()
        
        # Add chart path to result
        result['chart_path'] = str(chart_path)
        
        return result
    
    def get_additional_analytics(self):
        """
        Generate additional analytics insights.
        
        Returns:
            dict: Additional analytics data
        """
        print("Generating additional analytics...")
        
        # 1. Average daily rate by hotel type
        adr_by_hotel_query = self.db.query(
            Booking.hotel,
            func.avg(Booking.adr).label('avg_adr')
        ).group_by(Booking.hotel)
        
        adr_by_hotel_df = pd.read_sql(adr_by_hotel_query.statement, adr_by_hotel_query.session.bind)
        
        # 2. Bookings by market segment
        market_segment_query = self.db.query(
            Booking.market_segment,
            func.count(Booking.id).label('booking_count')
        ).group_by(Booking.market_segment).order_by(desc('booking_count'))
        
        market_segment_df = pd.read_sql(market_segment_query.statement, market_segment_query.session.bind)
        
        # 3. Repeated guest statistics
        repeated_guest_query = self.db.query(
            Booking.is_repeated_guest,
            func.count(Booking.id).label('booking_count')
        ).group_by(Booking.is_repeated_guest)
        
        repeated_guest_df = pd.read_sql(repeated_guest_query.statement, repeated_guest_query.session.bind)
        
        # Compile results
        result = {
            'adr_by_hotel': {
                'hotel_types': adr_by_hotel_df['hotel'].tolist(),
                'avg_adr': adr_by_hotel_df['avg_adr'].tolist()
            },
            'market_segments': {
                'segments': market_segment_df['market_segment'].tolist(),
                'booking_counts': market_segment_df['booking_count'].tolist()
            },
            'repeated_guests': {
                'is_repeated': repeated_guest_df['is_repeated_guest'].tolist(),
                'booking_counts': repeated_guest_df['booking_count'].tolist()
            }
        }
        
        # Create visualizations for market segments
        plt.figure(figsize=(12, 8))
        sns.barplot(x='booking_count', y='market_segment', data=market_segment_df)
        plt.title('Bookings by Market Segment')
        plt.xlabel('Number of Bookings')
        plt.ylabel('Market Segment')
        plt.tight_layout()
        
        # Save visualization
        chart_path = self.output_dir / "market_segments.png"
        plt.savefig(chart_path)
        plt.close()
        
        # Add chart path to result
        result['market_segments']['chart_path'] = str(chart_path)
        
        return result
    
    def get_all_analytics(self):
        """
        Generate all analytics reports.
        
        Returns:
            dict: All analytics data
        """
        try:
            analytics = {
                'revenue_trends': self.get_revenue_trends(),
                'cancellation_rates': self.get_cancellation_rates(),
                'geographical_distribution': self.get_geographical_distribution(),
                'lead_time_distribution': self.get_lead_time_distribution(),
                'additional_analytics': self.get_additional_analytics()
            }
            # Convert NumPy types to Python native types before returning
            return convert_numpy_types(analytics)
        except Exception as e:
            print(f"Error generating analytics: {e}")
            return {"error": str(e)}
        finally:
            self.close()


# Function to convert a matplotlib figure to base64 encoded image
def fig_to_base64(fig):
    """Convert a matplotlib figure to base64 encoded string."""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return img_str


# Utility function to convert NumPy types to Python native types
def convert_numpy_types(obj: Any) -> Any:
    """
    Convert NumPy types to Python native types for JSON serialization.
    
    Args:
        obj: Object that may contain NumPy types
        
    Returns:
        Object with NumPy types converted to Python native types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [convert_numpy_types(item) for item in obj]
    elif hasattr(obj, 'tolist'):
        # For other NumPy types with tolist method
        return obj.tolist()
    else:
        return obj
