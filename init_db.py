#!/usr/bin/env python
"""
Database initialization script for Mantra WebLogix
Run this script to initialize or reset the database
"""

from app import app, db, Trip, Expense
import os


def init_db():
    """Initialize the database"""
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Check if database file exists
        db_path = 'weblogix.db'
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path) / 1024  # Size in KB
            print(f"📁 Database file: {db_path} ({db_size:.2f} KB)")


def reset_db():
    """Reset the database (delete all data)"""
    with app.app_context():
        print("⚠️  Warning: This will delete all data in the database!")
        confirm = input("Are you sure? (yes/no): ")
        
        if confirm.lower() == 'yes':
            print("Dropping all tables...")
            db.drop_all()
            print("Creating new tables...")
            db.create_all()
            print("✅ Database reset successfully!")
        else:
            print("❌ Reset cancelled")


def add_sample_data():
    """Add sample data for testing"""
    with app.app_context():
        # Check if data already exists
        if Trip.query.first():
            print("Database already contains data. Skipping sample data.")
            return
        
        print("Adding sample data...")
        
        # Create sample trip
        trip = Trip(
            id='trip_sample_001',
            name='Sample Trip to Bali',
            description='Test trip for expense management',
            members=['Alice Johnson', 'Bob Smith', 'Charlie Brown'],
            total_amount=0
        )
        db.session.add(trip)
        db.session.commit()
        
        # Create sample expenses
        expenses = [
            Expense(
                id='exp_sample_001',
                trip_id='trip_sample_001',
                description='Hotel booking',
                amount=300.00,
                paid_by='Alice Johnson',
                split_among=['Alice Johnson', 'Bob Smith', 'Charlie Brown']
            ),
            Expense(
                id='exp_sample_002',
                trip_id='trip_sample_001',
                description='Restaurant dinner',
                amount=120.00,
                paid_by='Bob Smith',
                split_among=['Alice Johnson', 'Bob Smith', 'Charlie Brown']
            ),
            Expense(
                id='exp_sample_003',
                trip_id='trip_sample_001',
                description='Transportation',
                amount=80.00,
                paid_by='Charlie Brown',
                split_among=['Alice Johnson', 'Bob Smith', 'Charlie Brown']
            )
        ]
        
        for expense in expenses:
            db.session.add(expense)
        
        # Update trip total
        trip.total_amount = sum(exp.amount for exp in expenses)
        
        db.session.commit()
        
        print("✅ Sample data added successfully!")
        print(f"   - Trip: {trip.name}")
        print(f"   - Expenses: {len(expenses)}")
        print(f"   - Total Amount: ${trip.total_amount:.2f}")


def show_stats():
    """Display database statistics"""
    with app.app_context():
        trip_count = Trip.query.count()
        expense_count = Expense.query.count()
        
        print("\n📊 Database Statistics:")
        print(f"   - Total Trips: {trip_count}")
        print(f"   - Total Expenses: {expense_count}")
        
        if trip_count > 0:
            total_amount = sum(trip.total_amount for trip in Trip.query.all())
            print(f"   - Total Amount Tracked: ${total_amount:.2f}")


if __name__ == '__main__':
    import sys
    
    print("=" * 50)
    print("Mantra WebLogix - Database Management")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'init':
            init_db()
        elif command == 'reset':
            reset_db()
        elif command == 'sample':
            init_db()
            add_sample_data()
        elif command == 'stats':
            show_stats()
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  init    - Initialize the database")
            print("  reset   - Reset the database (delete all data)")
            print("  sample  - Initialize and add sample data")
            print("  stats   - Show database statistics")
    else:
        # Default: initialize
        init_db()
        show_stats()
