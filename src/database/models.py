from sqlalchemy import Column, Integer, Float, String, Date, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Booking(Base):
    """Model representing a hotel booking record."""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    hotel = Column(String(50))  # Resort Hotel or City Hotel
    is_canceled = Column(Boolean, default=False)
    lead_time = Column(Integer)  # Number of days between booking and arrival
    arrival_date = Column(Date)
    stays_in_weekend_nights = Column(Integer)
    stays_in_week_nights = Column(Integer)
    adults = Column(Integer)
    children = Column(Integer, nullable=True)
    babies = Column(Integer, nullable=True)
    meal = Column(String(20))  # BB, HB, FB, etc.
    country = Column(String(50), nullable=True)
    market_segment = Column(String(50))  # Direct, Corporate, Online TA, etc.
    distribution_channel = Column(String(50))
    is_repeated_guest = Column(Boolean, default=False)
    previous_cancellations = Column(Integer)
    previous_bookings_not_canceled = Column(Integer)
    reserved_room_type = Column(String(10))
    assigned_room_type = Column(String(10))
    booking_changes = Column(Integer)
    deposit_type = Column(String(20))  # No Deposit, Non Refund, Refundable
    agent = Column(String(20), nullable=True)
    company = Column(String(20), nullable=True)
    days_in_waiting_list = Column(Integer)
    customer_type = Column(String(20))  # Transient, Contract, etc.
    adr = Column(Float)  # Average Daily Rate
    required_car_parking_spaces = Column(Integer)
    total_of_special_requests = Column(Integer)
    reservation_status = Column(String(20))
    reservation_status_date = Column(Date)
    
    def __repr__(self):
        return f"<Booking(id={self.id}, hotel={self.hotel}, adr={self.adr})>"


class QueryHistory(Base):
    """Model for storing question-answering history."""
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text)  # Changed from 'query' to match the actual DB schema
    response_text = Column(Text, nullable=True)  # Changed from 'answer' to match the actual DB schema
    timestamp = Column(Date, nullable=True)
    relevant_booking_ids = Column(Text, nullable=True)  # Stored as JSON string

    def __repr__(self):
        return f"<QueryHistory(id={self.id}, query_text={self.query_text[:20]}...)>"
