#!/usr/bin/env python3
"""
Database migration script to update the extractions table with extracted_by field
"""

from database import create_tables

def main():
    """Run database migrations"""
    print("Running database migrations...")
    try:
        create_tables()
        print("Database migrations completed successfully!")
    except Exception as e:
        print(f"Error running migrations: {e}")

if __name__ == "__main__":
    main()
