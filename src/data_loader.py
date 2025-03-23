import pandas as pd
import numpy as np
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from database.db import engine, SessionLocal, Base
from database.models import Booking


def load_and_clean_data(file_path):
    """
    Load and clean the hotel booking data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    print(f"Loading data from {file_path}")
    
    # Load data
    df = pd.read_csv(file_path)
    
    # Basic info about the dataset
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Handle missing values
    print("Handling missing values...")
    
    # Fill missing children values with 0
    if 'children' in df.columns:
        df['children'] = df['children'].fillna(0).astype(int)
    
    # Fill missing country values with 'Unknown'
    if 'country' in df.columns:
        df['country'] = df['country'].fillna('Unknown')
    
    # Convert dates if necessary
    if 'arrival_date_year' in df.columns and 'arrival_date_month' in df.columns and 'arrival_date_day_of_month' in df.columns:
        # Map month names to numbers
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
            'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        
        # Create a single date column
        df['arrival_date'] = pd.to_datetime(
            df['arrival_date_year'].astype(str) + '-' + 
            df['arrival_date_month'].map(month_map).astype(str) + '-' + 
            df['arrival_date_day_of_month'].astype(str)
        )
    
    # Create a total_stays column
    if 'stays_in_weekend_nights' in df.columns and 'stays_in_week_nights' in df.columns:
        df['total_stays'] = df['stays_in_weekend_nights'] + df['stays_in_week_nights']
    
    # Calculate total revenue
    if 'adr' in df.columns:
        # ADR (Average Daily Rate) is the average price per day
        if 'total_stays' in df.columns:
            df['total_revenue'] = df['adr'] * df['total_stays']
        else:
            print("Warning: Cannot calculate total_revenue without stays information")
    
    # Convert reservation_status_date to proper format
    if 'reservation_status_date' in df.columns:
        # Try to convert using different date formats
        try:
            # First check if the column is already in a proper date format
            sample_date = df['reservation_status_date'].iloc[0]
            if isinstance(sample_date, str):
                if '/' in sample_date:
                    # Format like MM/DD/YYYY
                    df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'], format='%m/%d/%Y', errors='coerce').dt.date
                elif '-' in sample_date:
                    # Format like YYYY-MM-DD
                    df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'], format='%Y-%m-%d', errors='coerce').dt.date
                else:
                    # Fallback with error handling
                    df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'], errors='coerce').dt.date
            else:
                # Fallback with error handling
                df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'], errors='coerce').dt.date
        except Exception as e:
            print(f"Error converting reservation_status_date: {e}")
            # Fallback with error handling
            df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'], errors='coerce').dt.date
        
        # Fill any NaT values with a default date
        df['reservation_status_date'] = df['reservation_status_date'].fillna(pd.Timestamp('2000-01-01').date())
    
    # Additional cleaning steps can be added here
    
    print("Data cleaning completed.")
    return df


def save_to_database(df, db_session):
    """
    Save the cleaned DataFrame to the database.
    
    Args:
        df: Cleaned DataFrame
        db_session: SQLAlchemy session
    """
    print("Saving data to database...")
    
    # Convert date columns to Python date objects
    if 'arrival_date' in df.columns:
        df['arrival_date'] = pd.to_datetime(df['arrival_date'], format='%Y-%m-%d').dt.date
    
    # Map DataFrame columns to model fields
    count = 0
    for _, row in df.iterrows():
        booking = Booking(
            hotel=row.get('hotel', None),
            is_canceled=row.get('is_canceled', False),
            lead_time=row.get('lead_time', 0),
            arrival_date=row.get('arrival_date', None),
            stays_in_weekend_nights=row.get('stays_in_weekend_nights', 0),
            stays_in_week_nights=row.get('stays_in_week_nights', 0),
            adults=row.get('adults', 0),
            children=row.get('children', 0),
            babies=row.get('babies', 0),
            meal=row.get('meal', None),
            country=row.get('country', None),
            market_segment=row.get('market_segment', None),
            distribution_channel=row.get('distribution_channel', None),
            is_repeated_guest=row.get('is_repeated_guest', False),
            previous_cancellations=row.get('previous_cancellations', 0),
            previous_bookings_not_canceled=row.get('previous_bookings_not_canceled', 0),
            reserved_room_type=row.get('reserved_room_type', None),
            assigned_room_type=row.get('assigned_room_type', None),
            booking_changes=row.get('booking_changes', 0),
            deposit_type=row.get('deposit_type', None),
            agent=row.get('agent', None),
            company=row.get('company', None),
            days_in_waiting_list=row.get('days_in_waiting_list', 0),
            customer_type=row.get('customer_type', None),
            adr=row.get('adr', 0.0),
            required_car_parking_spaces=row.get('required_car_parking_spaces', 0),
            total_of_special_requests=row.get('total_of_special_requests', 0),
            reservation_status=row.get('reservation_status', None),
            reservation_status_date=row.get('reservation_status_date', None)
        )
        db_session.add(booking)
        count += 1
        
        # Commit in batches to avoid memory issues
        if count % 1000 == 0:
            db_session.commit()
            print(f"Committed {count} records")
    
    # Final commit
    db_session.commit()
    print(f"Successfully saved {count} records to database")


def init_db():
    """Initialize the database by creating all tables."""
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


def main():
    """Main function to run the data loading process."""
    # Initialize database
    init_db()
    
    # Path to the dataset
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    file_path = data_dir / "hotel_bookings.csv"
    
    # Check if file exists
    if not file_path.exists():
        print(f"Dataset not found at {file_path}")
        print("Please download the hotel_bookings.csv and place it in the data directory.")
        return
    
    # Load, clean and process data
    df = load_and_clean_data(file_path)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Save to database
        save_to_database(df, db)
        print("Data processing completed successfully!")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
