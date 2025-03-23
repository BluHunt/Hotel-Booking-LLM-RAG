"""
Database management utility.
This script provides functionality to manage the database schema and data.
"""

import os
import sys
import sqlite3
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a clean Base and engine - not reusing the existing ones to avoid any potential issues
DB_PATH = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data" / "hotel_bookings.db"
SQLITE_URL = f"sqlite:///{DB_PATH}"

engine = sa.create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define models directly in this script to ensure they match what we want
class Booking(Base):
    """Model for storing hotel booking data."""
    __tablename__ = "bookings"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    hotel = sa.Column(sa.String, index=True)
    is_canceled = sa.Column(sa.Boolean, index=True)
    lead_time = sa.Column(sa.Integer)
    arrival_date = sa.Column(sa.Date, index=True)
    stays_in_weekend_nights = sa.Column(sa.Integer)
    stays_in_week_nights = sa.Column(sa.Integer)
    adults = sa.Column(sa.Integer)
    children = sa.Column(sa.Integer)
    babies = sa.Column(sa.Integer)
    meal = sa.Column(sa.String)
    country = sa.Column(sa.String, index=True)
    market_segment = sa.Column(sa.String)
    distribution_channel = sa.Column(sa.String)
    is_repeated_guest = sa.Column(sa.Boolean)
    previous_cancellations = sa.Column(sa.Integer)
    previous_bookings_not_canceled = sa.Column(sa.Integer)
    reserved_room_type = sa.Column(sa.String)
    assigned_room_type = sa.Column(sa.String)
    booking_changes = sa.Column(sa.Integer)
    deposit_type = sa.Column(sa.String)
    agent = sa.Column(sa.String)
    company = sa.Column(sa.String)
    days_in_waiting_list = sa.Column(sa.Integer)
    customer_type = sa.Column(sa.String)
    adr = sa.Column(sa.Float)
    required_car_parking_spaces = sa.Column(sa.Integer)
    total_of_special_requests = sa.Column(sa.Integer)
    reservation_status = sa.Column(sa.String)
    reservation_status_date = sa.Column(sa.Date)


class QueryHistory(Base):
    """Model for storing question-answering history."""
    __tablename__ = "query_history"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    query_text = sa.Column(sa.Text)
    response_text = sa.Column(sa.Text, nullable=True)
    timestamp = sa.Column(sa.Date, nullable=True)
    relevant_booking_ids = sa.Column(sa.Text, nullable=True)  # Stored as JSON string


def check_db_exists():
    """Check if the database file exists."""
    return DB_PATH.exists()


def get_db_info():
    """Get information about the database."""
    if not check_db_exists():
        return {
            "exists": False,
            "tables": [],
            "size": 0
        }
    
    # Connect to the database
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    # Get table schemas
    table_schemas = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        table_schemas[table] = [
            {"name": col[1], "type": col[2], "notnull": col[3], "pk": col[5]}
            for col in columns
        ]
    
    # Get table row counts
    table_counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        table_counts[table] = count
    
    # Get database file size
    size_bytes = os.path.getsize(DB_PATH)
    size_mb = size_bytes / (1024 * 1024)
    
    # Close connection
    conn.close()
    
    return {
        "exists": True,
        "tables": tables,
        "schemas": table_schemas,
        "row_counts": table_counts,
        "size": {
            "bytes": size_bytes,
            "mb": round(size_mb, 2)
        }
    }


def create_fresh_db():
    """Create a fresh database with the correct schema."""
    # Remove existing database if it exists
    if DB_PATH.exists():
        os.remove(DB_PATH)
    
    # Create the directory if it doesn't exist
    DB_PATH.parent.mkdir(exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    return get_db_info()


def validate_schema():
    """Validate that the database schema matches the expected schema."""
    if not check_db_exists():
        return {
            "valid": False,
            "error": "Database does not exist"
        }
    
    # Get database info
    db_info = get_db_info()
    
    # Check that all expected tables exist
    expected_tables = {"bookings", "query_history"}
    actual_tables = set(db_info["tables"])
    missing_tables = expected_tables - actual_tables
    
    if missing_tables:
        return {
            "valid": False,
            "error": f"Missing tables: {missing_tables}"
        }
    
    # Check schemas
    for table, schema in db_info["schemas"].items():
        if table == "bookings":
            # Check for key columns in bookings
            column_names = {col["name"] for col in schema}
            essential_columns = {"id", "hotel", "is_canceled", "arrival_date"}
            missing_columns = essential_columns - column_names
            
            if missing_columns:
                return {
                    "valid": False,
                    "error": f"Missing essential columns in {table}: {missing_columns}"
                }
        
        elif table == "query_history":
            # Check for key columns in query_history
            column_names = {col["name"] for col in schema}
            essential_columns = {"id", "query_text", "response_text", "timestamp", "relevant_booking_ids"}
            missing_columns = essential_columns - column_names
            
            if missing_columns:
                return {
                    "valid": False,
                    "error": f"Missing essential columns in {table}: {missing_columns}"
                }
    
    return {
        "valid": True,
        "info": db_info
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Management Utility')
    parser.add_argument('--action', choices=['info', 'validate', 'recreate'], 
                        default='info', help='Action to perform')
    parser.add_argument('--force', action='store_true', 
                        help='Force recreation without confirmation')
    
    args = parser.parse_args()
    
    if args.action == 'info':
        info = get_db_info()
        print("\nDatabase Information:")
        print(f"Exists: {info['exists']}")
        if info['exists']:
            print(f"Size: {info['size']['mb']} MB")
            print(f"Tables: {', '.join(info['tables'])}")
            print("\nTable Row Counts:")
            for table, count in info['row_counts'].items():
                print(f"  {table}: {count} rows")
            
            print("\nTable Schemas:")
            for table, schema in info['schemas'].items():
                print(f"\n  {table}:")
                for column in schema:
                    pk_str = "PRIMARY KEY" if column['pk'] else ""
                    null_str = "NOT NULL" if column['notnull'] else "NULL"
                    print(f"    {column['name']} ({column['type']}) {null_str} {pk_str}")
    
    elif args.action == 'validate':
        result = validate_schema()
        if result['valid']:
            print("\nDatabase schema is valid.")
            print(f"Tables: {', '.join(result['info']['tables'])}")
            print("\nTable Row Counts:")
            for table, count in result['info']['row_counts'].items():
                print(f"  {table}: {count} rows")
        else:
            print(f"\nDatabase schema is INVALID: {result['error']}")
    
    elif args.action == 'recreate':
        if args.force or input("\nThis will DELETE all data and recreate the database. Continue? (y/n): ").lower() == 'y':
            print("Creating fresh database...")
            info = create_fresh_db()
            print("Database created successfully.")
            print(f"Tables: {', '.join(info['tables'])}")
        else:
            print("Operation cancelled.")
