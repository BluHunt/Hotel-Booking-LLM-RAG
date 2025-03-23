"""
Database schema reset utility.
This script drops and recreates all database tables.
"""

import os
import sys
import sqlite3

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import Base, engine, get_db
from database.models import Booking, QueryHistory

def verify_tables():
    """
    Verify that all tables have the correct schema.
    """
    # Get database path from engine url
    db_path = engine.url.database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if query_history table has the correct schema
    cursor.execute("PRAGMA table_info(query_history)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # Print current schema
    print("Current query_history table schema:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check if the required columns exist
    required_columns = ['id', 'query_text', 'response_text', 'timestamp', 'relevant_booking_ids']
    missing_columns = [col for col in required_columns if col not in column_names]
    
    if missing_columns:
        print(f"Missing columns: {missing_columns}")
        print("Schema mismatch detected. Will recreate tables.")
        return False
    
    print("All tables have the correct schema.")
    return True

def reset_database():
    """
    Drop and recreate all database tables.
    """
    print("Dropping all tables...")
    Base.metadata.drop_all(engine)
    
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    
    # Verify the schema after creation
    if verify_tables():
        print("Database schema has been reset and verified.")
    else:
        print("ERROR: Database schema verification failed after reset!")

def check_and_reset_database():
    """
    Check the current database schema and reset if necessary.
    """
    # Try to verify tables first
    if not verify_tables():
        # If verification fails, reset the database
        reset_database()
    else:
        print("Database schema is correct. No reset needed.")

if __name__ == "__main__":
    # Ask for confirmation
    print("Warning: This will check and potentially reset all data in the database!")
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    
    if confirm.lower() == "yes":
        check_and_reset_database()
    else:
        print("Operation cancelled.")
