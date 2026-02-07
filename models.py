"""
Database models for Mantra WebLogix TCS Application
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Trip(db.Model):
    """Trip model for storing trip information"""
    
    __tablename__ = 'trips'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    created_date = db.Column(db.DateTime, default=datetime.now)
    members = db.Column(db.JSON, default=[])  # Store as JSON array
    total_amount = db.Column(db.Float, default=0.0)
    
    # Relationship to expenses
    expenses = db.relationship('Expense', backref='trip', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Trip {self.id}: {self.name}>'
    
    def to_dict(self):
        """Convert trip object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_date': self.created_date.isoformat(),
            'members': self.members,
            'total_amount': self.total_amount,
            'expenses': [expense.to_dict() for expense in self.expenses]
        }


class Expense(db.Model):
    """Expense model for storing expense information"""
    
    __tablename__ = 'expenses'
    
    id = db.Column(db.String(50), primary_key=True)
    trip_id = db.Column(db.String(50), db.ForeignKey('trips.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_by = db.Column(db.String(100), nullable=False)
    split_among = db.Column(db.JSON, default=[])  # Store as JSON array
    date = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Expense {self.id}: {self.description}>'
    
    def to_dict(self):
        """Convert expense object to dictionary"""
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'paid_by': self.paid_by,
            'split_among': self.split_among,
            'date': self.date.isoformat()
        }
