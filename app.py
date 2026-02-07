from flask import Flask, render_template, request, jsonify, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# ==================== DATABASE CONFIGURATION ====================
# Using SQLite (can be changed to PostgreSQL, MySQL, etc.)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///weblogix.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['ENV'] = os.getenv('FLASK_ENV', 'development')

db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

class Trip(db.Model):
    """Trip model for storing trip information"""
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    created_date = db.Column(db.DateTime, default=datetime.now)
    members = db.Column(db.JSON, default=[])  # Store as JSON array
    total_amount = db.Column(db.Float, default=0.0)
    
    # Relationship to expenses
    expenses = db.relationship('Expense', backref='trip', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
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
    id = db.Column(db.String(50), primary_key=True)
    trip_id = db.Column(db.String(50), db.ForeignKey('trip.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_by = db.Column(db.String(100), nullable=False)
    split_among = db.Column(db.JSON, default=[])  # Store as JSON array
    date = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'paid_by': self.paid_by,
            'split_among': self.split_among,
            'date': self.date.isoformat()
        }


# ==================== CREATE DATABASE TABLES ====================
with app.app_context():
    db.create_all()

# ==================== MAIN WEBSITE ROUTES ====================

@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')

@app.route('/team')
def team():
    """Team page"""
    team_members = [
        {
            'name': 'Sarah Chen',
            'position': 'Founder & CEO',
            'bio': 'Visionary leader with 10+ years in tech',
            'image': 'team1.jpg'
        },
        {
            'name': 'Alex Rodriguez',
            'position': 'CTO',
            'bio': 'Full-stack developer passionate about innovation',
            'image': 'team2.jpg'
        },
        {
            'name': 'Emma Wilson',
            'position': 'Product Manager',
            'bio': 'User-centric designer focused on experience',
            'image': 'team3.jpg'
        },
        {
            'name': 'David Park',
            'position': 'Lead Developer',
            'bio': 'Python expert with scalable solutions',
            'image': 'team4.jpg'
        }
    ]
    return render_template('team.html', team=team_members)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

# ==================== TCS (TripContriSplitter) ROUTES ====================

@app.route('/tcs')
def tcs_dashboard():
    """TCS Dashboard - Main page"""
    return render_template('tcs/dashboard.html')

@app.route('/tcs/admin/login', methods=['GET', 'POST'])
def tcs_admin_login():
    """Admin Login - Authenticate with passkey"""
    if request.method == 'POST':
        data = request.get_json()
        passkey = data.get('passkey', '')
        if passkey == 'weblogix2014':
            session['admin_authenticated'] = True
            return jsonify({'status': 'success', 'message': 'Authentication successful'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid passkey'})
    return render_template('tcs/admin_login.html')

@app.route('/tcs/admin/logout')
def tcs_admin_logout():
    """Admin Logout - Clear admin session"""
    session.pop('admin_authenticated', None)
    return redirect(url_for('tcs_dashboard'))

@app.route('/tcs/admin')
def tcs_admin_dashboard():
    """Admin Dashboard - View and manage all trips"""
    # Check if user is authenticated as admin
    if not session.get('admin_authenticated'):
        return redirect(url_for('tcs_admin_login'))
    
    trips = Trip.query.all()
    trips_data = []
    for trip in trips:
        trip_dict = trip.to_dict()
        settlements = calculate_settlements(trip_dict)
        trips_data.append({
            'id': trip.id,
            'name': trip.name,
            'description': trip.description,
            'created_date': trip.created_date.isoformat(),
            'members_count': len(trip.members),
            'expenses_count': len(trip.expenses),
            'total_amount': trip.total_amount,
            'settlements': settlements
        })
    return render_template('tcs/admin_dashboard.html', trips=trips_data)

@app.route('/tcs/trip/new', methods=['GET', 'POST'])
def tcs_create_trip():
    """Create a new trip"""
    if request.method == 'POST':
        data = request.get_json()
        trip_id = f"trip_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        # Create new trip in database
        trip = Trip(
            id=trip_id,
            name=data['name'],
            description=data.get('description', ''),
            members=data.get('members', []),
            total_amount=0
        )
        
        db.session.add(trip)
        db.session.commit()
        
        # Redirect to authorize page where user will see trip ID and enter it
        return jsonify({'status': 'success', 'trip_id': trip_id, 'authorize_url': f'/tcs/trip/{trip_id}/auth'})
    
    return render_template('tcs/create_trip.html')

@app.route('/tcs/trip/<trip_id>')
def tcs_trip_details(trip_id):
    """View trip details and settlement"""
    trip = Trip.query.get(trip_id)
    
    if not trip:
        return render_template('tcs/error.html', message='Trip not found'), 404
    # Use session-based authorization: require user to 'enter' the trip id once
    authorized = session.get('authorized_trips', [])
    is_authorized = trip_id in authorized

    if not is_authorized:
        # render a small authorization prompt where the user must enter the trip id
        return render_template('tcs/authorize.html', trip_id=trip_id)

    trip_dict = trip.to_dict()
    settlements = calculate_settlements(trip_dict)

    # Calculate member balances
    member_balances = calculate_member_balances(trip_dict)

    return render_template('tcs/trip_details.html', trip=trip_dict, settlements=settlements, member_balances=member_balances, is_owner=True)

@app.route('/tcs/trip/<trip_id>/add-expense', methods=['POST'])
def tcs_add_expense(trip_id):
    """Add expense to a trip"""
    trip = Trip.query.get(trip_id)
    
    if not trip:
        return jsonify({'status': 'error', 'message': 'Trip not found'}), 404
    
    # Session-based authorization: ensure the user has entered trip id previously
    authorized = session.get('authorized_trips', [])
    if trip_id not in authorized:
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403
    
    data = request.get_json()
    
    # Create new expense
    expense_id = f"exp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    expense = Expense(
        id=expense_id,
        trip_id=trip_id,
        description=data['description'],
        amount=float(data['amount']),
        paid_by=data['paid_by'],
        split_among=data['split_among']
    )
    
    db.session.add(expense)
    db.session.flush()  # flush to ensure expense is in trip.expenses
    
    # Update trip total amount by summing all expenses
    trip.total_amount = sum([exp.amount for exp in trip.expenses])
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'expense': expense.to_dict()})

@app.route('/tcs/trip/<trip_id>/settlements', methods=['GET'])
def tcs_get_settlements(trip_id):
    """Get settlement details for a trip"""
    trip = Trip.query.get(trip_id)
    
    if not trip:
        return jsonify({'status': 'error', 'message': 'Trip not found'}), 404
    # Session-based check: ensure trip was authorized in session
    authorized = session.get('authorized_trips', [])
    if trip_id not in authorized:
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403

    trip_dict = trip.to_dict()
    settlements = calculate_settlements(trip_dict)

    return jsonify({
        'status': 'success',
        'settlements': settlements,
        'total': trip.total_amount
    })

@app.route('/tcs/summary')
def tcs_summary():
    """View all trips summary"""
    trips = Trip.query.all()
    summary = []
    
    for trip in trips:
        trip_dict = trip.to_dict()
        settlements = calculate_settlements(trip_dict)
        summary.append({
            'id': trip.id,
            'name': trip.name,
            'members_count': len(trip.members),
            'total_amount': trip.total_amount,
            'date_created': trip.created_date.isoformat(),
            'settlements': settlements
        })
    
    return render_template('tcs/summary.html', summary=summary)


# ==================== AUTHORIZATION ROUTES ====================
@app.route('/tcs/trip/<trip_id>/auth')
def tcs_show_authorize(trip_id):
    """Show authorization prompt with trip ID visible"""
    trip = Trip.query.get(trip_id)
    if not trip:
        return render_template('tcs/error.html', message='Trip not found'), 404
    return render_template('tcs/authorize.html', trip_id=trip_id)

@app.route('/tcs/trip/<trip_id>/enter', methods=['POST'])
def tcs_enter_trip(trip_id):
    """User submits trip id to gain access for viewing/editing in this session"""
    trip = Trip.query.get(trip_id)
    if not trip:
        return render_template('tcs/error.html', message='Trip not found'), 404

    entered = request.form.get('entered_id') or (request.get_json(silent=True) and request.get_json().get('entered_id'))
    if not entered:
        return render_template('tcs/authorize.html', trip_id=trip_id, error='Please enter the trip id')

    # simple compare: if entered matches the trip id, authorize in session
    if str(entered).strip() == str(trip_id):
        authorized = session.get('authorized_trips', [])
        if trip_id not in authorized:
            authorized.append(trip_id)
            session['authorized_trips'] = authorized
        return render_template('tcs/trip_details.html', trip=trip.to_dict(), settlements=calculate_settlements(trip.to_dict()), member_balances=calculate_member_balances(trip.to_dict()), is_owner=True)

    return render_template('tcs/authorize.html', trip_id=trip_id, error='Invalid trip id')


# ==================== MEMBER / EXPENSE / TRIP MANAGEMENT ====================
@app.route('/tcs/trip/<trip_id>/add-member', methods=['POST'])
def tcs_add_member(trip_id):
    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({'status': 'error', 'message': 'Trip not found'}), 404
    authorized = session.get('authorized_trips', [])
    if trip_id not in authorized:
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403

    data = request.get_json()
    name = data.get('name') if data else None
    if not name:
        return jsonify({'status': 'error', 'message': 'Name required'}), 400

    members = trip.members or []
    if name in members:
        return jsonify({'status': 'error', 'message': 'Member already exists'}), 400

    members.append(name)
    trip.members = members
    db.session.commit()
    return jsonify({'status': 'success', 'members': trip.members})


@app.route('/tcs/trip/<trip_id>/delete-member', methods=['POST'])
def tcs_delete_member(trip_id):
    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({'status': 'error', 'message': 'Trip not found'}), 404
    authorized = session.get('authorized_trips', [])
    if trip_id not in authorized:
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403

    data = request.get_json()
    name = data.get('name') if data else None
    if not name:
        return jsonify({'status': 'error', 'message': 'Name required'}), 400

    members = trip.members or []
    if name not in members:
        return jsonify({'status': 'error', 'message': 'Member not found'}), 404

    # Remove from members
    members.remove(name)
    trip.members = members

    # Remove member from expense splits and delete expenses they paid
    for exp in list(trip.expenses):
        changed = False
        if name == exp.paid_by:
            # delete expense entirely
            db.session.delete(exp)
            changed = True
        else:
            splits = exp.split_among or []
            if name in splits:
                splits = [s for s in splits if s != name]
                exp.split_among = splits
                changed = True
        if changed:
            pass

    # Recompute total amount
    trip.total_amount = sum([e.amount for e in trip.expenses])
    db.session.commit()
    return jsonify({'status': 'success', 'members': trip.members})


@app.route('/tcs/trip/<trip_id>/delete-expense', methods=['POST'])
def tcs_delete_expense(trip_id):
    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({'status': 'error', 'message': 'Trip not found'}), 404
    authorized = session.get('authorized_trips', [])
    if trip_id not in authorized:
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403

    data = request.get_json()
    exp_id = data.get('expense_id') if data else None
    if not exp_id:
        return jsonify({'status': 'error', 'message': 'expense_id required'}), 400

    exp = Expense.query.get(exp_id)
    if not exp or exp.trip_id != trip_id:
        return jsonify({'status': 'error', 'message': 'Expense not found'}), 404

    db.session.delete(exp)
    db.session.commit()
    # Update total
    trip = Trip.query.get(trip_id)
    trip.total_amount = sum([e.amount for e in trip.expenses])
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/tcs/trip/<trip_id>/delete', methods=['POST'])
def tcs_delete_trip(trip_id):
    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({'status': 'error', 'message': 'Trip not found'}), 404
    authorized = session.get('authorized_trips', [])
    if trip_id not in authorized:
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403

    db.session.delete(trip)
    db.session.commit()
    # remove from session
    authorized = session.get('authorized_trips', [])
    if trip_id in authorized:
        authorized.remove(trip_id)
        session['authorized_trips'] = authorized
    return jsonify({'status': 'success'})

# ==================== HELPER FUNCTIONS ====================

def calculate_member_balances(trip):
    """Calculate balance for each member"""
    balances = {}
    for member in trip.get('members', []):
        balances[member] = 0
    
    # Process each expense
    for expense in trip['expenses']:
        paid_by = expense['paid_by']
        amount = expense['amount']
        split_among = expense['split_among']
        
        if not split_among:
            split_among = trip.get('members', [])
        
        split_amount = amount / len(split_among) if split_among else 0
        
        # Add to payer's balance (they paid more)
        balances[paid_by] = balances.get(paid_by, 0) + amount
        
        # Subtract from everyone's balance
        for person in split_among:
            balances[person] = balances.get(person, 0) - split_amount
    
    return balances

def calculate_settlements(trip):
    """Calculate who owes whom and how much"""
    if not trip['expenses']:
        return []
    
    # Calculate each person's balance
    balances = {}
    for member in trip.get('members', []):
        balances[member] = 0
    
    # Process each expense
    for expense in trip['expenses']:
        paid_by = expense['paid_by']
        amount = expense['amount']
        split_among = expense['split_among']
        
        if not split_among:
            split_among = trip.get('members', [])
        
        split_amount = amount / len(split_among) if split_among else 0
        
        # Add to payer's balance (they paid more)
        balances[paid_by] = balances.get(paid_by, 0) + amount
        
        # Subtract from everyone's balance
        for person in split_among:
            balances[person] = balances.get(person, 0) - split_amount
    
    # Generate settlement list (who owes/receives what)
    settlements = []
    
    # Separate debtors and creditors
    debtors = [(person, amount) for person, amount in balances.items() if amount < 0]
    creditors = [(person, amount) for person, amount in balances.items() if amount > 0]
    
    debtors.sort(key=lambda x: x[1])  # Most negative first
    creditors.sort(key=lambda x: x[1], reverse=True)  # Most positive first
    
    # Match debtors with creditors
    for debtor, debt in debtors:
        debt = abs(debt)
        for i, (creditor, credit) in enumerate(creditors):
            if credit <= 0:
                continue
            
            settlement_amount = min(debt, credit)
            settlements.append({
                'from': debtor,
                'to': creditor,
                'amount': round(settlement_amount, 2),
                'status': 'pending'
            })
            
            debt -= settlement_amount
            creditors[i] = (creditor, credit - settlement_amount)
            
            if debt == 0:
                break
    
    return settlements

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Production: use gunicorn (called externally)
    # Development: use Flask development server
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    port = int(os.getenv('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
