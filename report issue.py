from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///disaster_reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)

    def repr(self):
        return f"<Contact(name='{self.name}', phone='{self.phone}', category='{self.category}')>"
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)





class DisasterReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50), nullable=False)
    photo = db.Column(db.String(100), nullable=True)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    reports = DisasterReport.query.all()
    return render_template('index.html', reports=reports)

# Modify the emergency_contacts route to pass the correct data to the template
@app.route('/emergency_contacts')
@login_required
def emergency_contacts():
    # Retrieve emergency contacts from the database
    emergency_contacts = Contact.query.all()
    return render_template('emergency_contacts.html', contacts=emergency_contacts)


@app.route('/add_contact', methods=['POST'])
@login_required
def add_contact():
    if request.method == 'POST':
        # Retrieve data from the form
        name = request.form['name']
        phone = request.form['phone']
        category = request.form['category']
        
        # Create a new Contact object
        new_contact = Contact(name=name, phone=phone, category=category)
        
        # Add the new contact to the database
        db.session.add(new_contact)
        db.session.commit()
        
        # Retrieve all contacts from the database
        contacts = Contact.query.all()
        
        # Redirect to the index page after adding the contact
        return render_template('emergency_contacts.html', contacts=contacts)
    else:
        # Handle other HTTP methods (GET, etc.) if needed
        pass

# Add route for deleting a contact
@app.route('/delete_contact/<int:id>', methods=['POST'])
@login_required
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('emergency_contacts'))


@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        location = request.form['location']
        description = request.form['description']
        category = request.form['category']
        subcategory = request.form['subcategory']
        photo = None

        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file:
                photo = photo_file.filename
                photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo))

        new_report = DisasterReport(location=location, description=description, category=category, subcategory=subcategory, photo=photo)
        db.session.add(new_report)
        db.session.commit()
        flash('Disaster report submitted successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('report.html')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    report = DisasterReport.query.get_or_404(id)
    if request.method == 'POST':
        report.location = request.form['location']
        report.description = request.form['description']
        report.category = request.form['category']
        report.subcategory = request.form['subcategory']
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file:
                report.photo = photo_file.filename
                photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], report.photo))
        db.session.commit()
        flash('Disaster report updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('update.html', report=report)



@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    report = DisasterReport.query.get_or_404(id)
    db.session.delete(report)
    db.session.commit()
    flash('Disaster report deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# New route for dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# New route for resource management page
@app.route('/resources_page')
@login_required
def resources_page():
    return render_template('resources.html', resources=resources, allocations=allocations)

# Routes and logic for resource management
resources = [
    {"id": 1, "name": "Food", "quantity": 100},
    {"id": 2, "name": "Medical Supplies", "quantity": 50},
    {"id": 3, "name": "Shelter", "quantity": 20}
]

locations = []
allocations = []

@app.route("/allocate", methods=["POST"])
@login_required
def allocate():
    resource_id = int(request.form["resource_id"])
    location_name = request.form["location_name"]
    quantity = int(request.form["quantity"])

    resource = next((r for r in resources if r["id"] == resource_id), None)
    location = next((l for l in locations if l["name"].lower() == location_name.lower()), None)

    if not location:
        location = {"id": len(locations) + 1, "name": location_name}
        locations.append(location)

    if resource and resource["quantity"] >= quantity:
        resource["quantity"] -= quantity
        allocations.append({
            "resource_id": resource_id, 
            "resource_name": resource["name"], 
            "location_id": location["id"], 
            "location_name": location_name, 
            "quantity": quantity
        })
    else:
        flash("Resource not available or insufficient quantity", "error")
    
    return redirect(url_for('resources_page'))

@app.route("/remove_allocation/<int:allocation_index>", methods=["POST"])
@login_required
def remove_allocation(allocation_index):
    if 0 <= allocation_index < len(allocations):
        allocation = allocations.pop(allocation_index)
        resource = next((r for r in resources if r["id"] == allocation["resource_id"]), None)
        if resource:
            resource["quantity"] += allocation["quantity"]
    
    return redirect(url_for('resources_page'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)