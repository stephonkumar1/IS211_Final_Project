#Stephon Kumar
#Final Project

from flask import Flask, render_template, request, redirect, url_for, flash, session  # Import necessary Flask modules
from flask_sqlalchemy import SQLAlchemy  # Import SQLAlchemy for database management
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user  # Import Flask-Login for user authentication
import requests  # Import requests for making API calls
import os  # Import os for file and directory operations

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'  # Configure SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking to save resources

db = SQLAlchemy(app)  # Initialize SQLAlchemy with Flask app
login_manager = LoginManager(app)  # Initialize Flask-Login with Flask app
login_manager.login_view = 'login'  # Set the login view for unauthenticated access

# Database Models
class User(UserMixin, db.Model):  # User model for storing user data
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    username = db.Column(db.String(150), unique=True, nullable=False)  # Username field
    password = db.Column(db.String(150), nullable=False)  # Password field

class Book(db.Model):  # Book model for storing book details
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key linking to User
    isbn = db.Column(db.String(13), nullable=False)  # ISBN field
    title = db.Column(db.String(255), nullable=False)  # Book title field
    author = db.Column(db.String(255))  # Book author field
    page_count = db.Column(db.Integer)  # Page count field
    average_rating = db.Column(db.Float)  # Average rating field
    thumbnail_url = db.Column(db.String(255))  # Thumbnail URL field

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):  # Function to load user by ID
    return User.query.get(int(user_id))  # Query user by primary key

@app.route('/')
def index():  # Home route
    if current_user.is_authenticated:  # Check if user is logged in
        return redirect(url_for('dashboard'))  # Redirect to dashboard if logged in
    return render_template('index.html')  # Render index page if not logged in

@app.route('/register', methods=['GET', 'POST'])
def register():  # Registration route
    if request.method == 'POST':  # Handle POST requests for registration
        username = request.form['username']  # Get username from form
        password = request.form['password']  # Get password from form
        if User.query.filter_by(username=username).first():  # Check if username already exists
            flash('Username already exists!', 'danger')  # Show error message
        else:
            new_user = User(username=username, password=password)  # Create a new user
            db.session.add(new_user)  # Add user to database
            db.session.commit()  # Commit changes
            flash('Registration successful!', 'success')  # Show success message
            return redirect(url_for('login'))  # Redirect to login page
    return render_template('register.html')  # Render registration page

@app.route('/login', methods=['GET', 'POST'])
def login():  # Login route
    if request.method == 'POST':  # Handle POST requests for login
        username = request.form['username']  # Get username from form
        password = request.form['password']  # Get password from form
        user = User.query.filter_by(username=username, password=password).first()  # Authenticate user
        if user:  # Check if user exists
            login_user(user)  # Log in the user
            return redirect(url_for('dashboard'))  # Redirect to dashboard
        else:
            flash('Invalid credentials!', 'danger')  # Show error message for invalid login
    return render_template('login.html')  # Render login page

@app.route('/logout')
@login_required
def logout():  # Logout route
    logout_user()  # Log out the user
    flash('You have been logged out.', 'info')  # Show logout message
    return redirect(url_for('login'))  # Redirect to login page

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():  # Dashboard route
    if request.method == 'POST':  # Handle POST requests for book search
        isbn = request.form['isbn']  # Get ISBN from form
        response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}')  # Fetch book data from API
        if response.status_code == 200:  # Check if API response is successful
            data = response.json()  # Parse JSON response
            if 'items' in data:  # Check if items exist in response
                book_info = data['items'][0]['volumeInfo']  # Get first book info
                title = book_info.get('title', 'N/A')  # Extract title
                author = ', '.join(book_info.get('authors', ['Unknown']))  # Extract authors
                page_count = book_info.get('pageCount', 0)  # Extract page count
                average_rating = book_info.get('averageRating', 0)  # Extract average rating
                thumbnail_url = book_info.get('imageLinks', {}).get('thumbnail', '')  # Extract thumbnail URL

                new_book = Book(user_id=current_user.id, isbn=isbn, title=title, author=author,
                                page_count=page_count, average_rating=average_rating, thumbnail_url=thumbnail_url)  # Create new book instance
                db.session.add(new_book)  # Add book to database
                db.session.commit()  # Commit changes
                flash(f'Book "{title}" added successfully!', 'success')  # Show success message
            else:
                flash('No results found for the provided ISBN.', 'danger')  # Show error message if no results
        else:
            flash('Error fetching book data. Try again later.', 'danger')  # Show error message for API failure

    books = Book.query.filter_by(user_id=current_user.id).all()  # Fetch all books for the user
    return render_template('dashboard.html', books=books)  # Render dashboard with books

@app.route('/delete/<int:book_id>')
@login_required
def delete_book(book_id):  # Route to delete a book
    book = Book.query.get_or_404(book_id)  # Fetch book by ID or return 404
    if book.user_id != current_user.id:  # Check if user owns the book
        flash('Unauthorized action.', 'danger')  # Show error message for unauthorized action
        return redirect(url_for('dashboard'))  # Redirect to dashboard
    db.session.delete(book)  # Delete book from database
    db.session.commit()  # Commit changes
    flash('Book deleted successfully.', 'info')  # Show success message for deletion
    return redirect(url_for('dashboard'))  # Redirect to dashboard

# Ensure templates are created
if not os.path.exists('templates'):  # Check if templates directory exists
    os.makedirs('templates')  # Create templates directory if not exists

# Sample HTML Templates
with open('templates/index.html', 'w') as f:  # Create index.html template
    f.write("""<html><body><h1>Welcome to the Book Catalogue!</h1><a href='/login'>Login</a> | <a href='/register'>Register</a></body></html>""")

with open('templates/register.html', 'w') as f:  # Create register.html template
    f.write("""<html><body><h1>Register</h1><form method='POST'><label>Username:</label><input type='text' name='username'><br><label>Password:</label><input type='password' name='password'><br><button type='submit'>Register</button></form></body></html>""")

with open('templates/login.html', 'w') as f:  # Create login.html template
    f.write("""<html><body><h1>Login</h1><form method='POST'><label>Username:</label><input type='text' name='username'><br><label>Password:</label><input type='password' name='password'><br><button type='submit'>Login</button></form></body></html>""")

with open('templates/dashboard.html', 'w') as f:  # Create dashboard.html template
    f.write("""<html><body><h1>Your Books</h1><form method='POST'><label>ISBN:</label><input type='text' name='isbn'><button type='submit'>Search</button></form><ul>{% for book in books %}<li><img src='{{ book.thumbnail_url }}' alt='No Image'><b>{{ book.title }}</b> by {{ book.author }} - <a href='/delete/{{ book.id }}'>Delete</a></li>{% endfor %}</ul><a href='/logout'>Logout</a></body></html>""")

# Run the application
if __name__ == '__main__':
    if not os.path.exists('books.db'):  # Check if database exists
        db.create_all()  # Create database tables
    app.run(debug=True)  # Run Flask app in debug mode
