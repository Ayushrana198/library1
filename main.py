from flask import Flask, request, redirect, url_for, render_template, flash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy.orm import joinedload
from flask import send_file, abort
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.units import inch
from models import Book
from textwrap import wrap

app = Flask(__name__)

# Set configuration before initializing the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///libmgmt.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '21f1005671'

# Initialize database
db = SQLAlchemy()

# Initialize login manager
login_manager = LoginManager()

# Function to initialize the app with the SQLAlchemy and LoginManager
def create_app():
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = '/'

    with app.app_context():
        db.create_all()  # Create the database and tables

    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from models import *

# Correct the path setting for the upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/images')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Routes
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return 'User already exists'

        # Assign role based on the username
        if username.lower() == 'librarian':
            role = 'librarian'
        else:
            role = 'student'

        # Create a new user with the assigned role
        new_user = User(username=username, role=role)
        new_user.set_password(password)

        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        # Redirect to login page after successful signup
        return redirect('/login')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Query user from database
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Use Flask-Login to login the user
            login_user(user)

            # Redirect based on role
            if user.role == 'librarian':
                return redirect('/librarian_dashboard')
            else:
                return redirect('/student_dashboard')
        else:
            return 'Invalid credentials'

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('welcome'))

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/librarian_dashboard')
@login_required
def librarian_dashboard():
    if current_user.role != 'librarian':
        return redirect('/student_dashboard')
    sections = Section.query.all()
    return render_template('librarian_dashboard.html', sections=sections)


@app.route('/add_section', methods=['POST'])
def add_section():
    sec_name = request.form.get('sec_name')
    description = request.form.get('sec_description')
    sec_image = request.files['sec_image']

    # Save the image to the static folder
    filename = secure_filename(sec_image.filename)
    sec_image.save(os.path.join('static/images', filename))

    new_section = Section(user_id= current_user.user_id, sec_name=sec_name, description=description, sec_image=filename)
    db.session.add(new_section)
    db.session.commit()

    return redirect(url_for('librarian_dashboard'))


@app.route('/edit_section/<int:sec_id>', methods=['GET', 'POST'])
@login_required
def edit_section(sec_id):
    section = Section.query.get_or_404(sec_id)

    if request.method == 'POST':
        section.sec_name = request.form.get('sec_name')
        section.description = request.form.get('sec_description')

        # If a new image is uploaded, replace the old one
        if 'sec_image' in request.files and request.files['sec_image'].filename:
            sec_image = request.files['sec_image']
            filename = secure_filename(sec_image.filename)
            sec_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            section.sec_image = filename

        db.session.commit()
        return redirect(url_for('librarian_dashboard'))

    # Load the section details to be edited
    sections = Section.query.all()
    return render_template('librarian_dashboard.html', sections=sections, section_to_edit=section)


@app.route('/delete_section/<int:sec_id>', methods=['POST'])
def delete_section(sec_id):
    section = Section.query.get_or_404(sec_id)
    db.session.delete(section)
    db.session.commit()

    return redirect(url_for('librarian_dashboard'))


@app.route('/section/<int:sec_id>')
@login_required
def view_books(sec_id):
    section = Section.query.get_or_404(sec_id)
    books = Book.query.filter_by(sec_id=sec_id).all()
    return render_template('books.html', section=section, books=books)


@app.route('/add_book', methods=['POST'])
@login_required
def add_book():
    sec_id = request.form.get('sec_id')
    title = request.form.get('book_title')
    author = request.form.get('book_author')
    description = request.form.get('book_description')
    price = request.form.get('book_price')
    book_image = request.files['book_image']

    # Save the image to the static folder
    filename = secure_filename(book_image.filename)
    book_image.save(os.path.join('static/images', filename))

    new_book = Book(user_id= current_user.user_id,sec_id=sec_id, title=title, author=author, description=description, price=price, book_image=filename)
    db.session.add(new_book)
    db.session.commit()

    return redirect(url_for('view_books', sec_id=sec_id))


@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        book.title = request.form.get('book_title')
        book.author = request.form.get('book_author')
        book.description = request.form.get('book_description')
        book.price = request.form.get('book_price')

        # Check if a new image is uploaded, otherwise keep the existing one
        if 'book_image' in request.files and request.files['book_image'].filename:
            book_image = request.files['book_image']
            filename = secure_filename(book_image.filename)
            book_image.save(os.path.join('static/images', filename))
            book.book_image = filename

        db.session.commit()
        return redirect(url_for('view_books', sec_id=book.sec_id))

    section = Section.query.get(book.sec_id)
    books = Book.query.filter_by(sec_id=book.sec_id).all()
    return render_template('books.html', section=section, books=books, book=book)  # Pass the book to prefill the form


@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    sec_id = book.sec_id
    db.session.delete(book)
    db.session.commit()

    return redirect(url_for('view_books', sec_id=sec_id))

@app.route('/book_issue')
@login_required
def book_issue():
    # Fetch all issued books (requests) from the database
    issued_books = Request.query.options(joinedload(Request.user), joinedload(Request.book)).all()
    current_time = datetime.now()
    
    return render_template('book_issue.html', issued_books=issued_books, current_time=current_time)

@app.route('/revoke_book/<int:book_id>/<int:user_id>', methods=['POST'])
@login_required
def revoke_book(book_id, user_id):
    # Find the book request to revoke
    book_request = Request.query.filter_by(book_id=book_id, user_id=user_id).first()

    if book_request:
        db.session.delete(book_request)
        db.session.commit()
    
    return redirect(url_for('book_issue'))

@app.route('/view_all_feedback')
@login_required
def view_all_feedback():
    # Fetch all feedbacks, join with book data, and group them by book title
    feedbacks = db.session.query(Feedback).join(Book, Feedback.book_id == Book.book_id).order_by(Book.title.asc()).all()

    # Group feedbacks by book
    feedback_dict = {}
    for feedback in feedbacks:
        if feedback.book not in feedback_dict:
            feedback_dict[feedback.book] = []
        feedback_dict[feedback.book].append(feedback)

    return render_template('feedback.html', feedbacks=feedback_dict)


@app.route('/student_dashboard')
@login_required
def student_dashboard():
    sections = Section.query.all()  # Fetch all sections
    return render_template('student_dashboard.html', sections=sections)

@app.route('/sections/<int:sec_id>')
@login_required
def see_books(sec_id):
    section = Section.query.get_or_404(sec_id)
    books = Book.query.filter_by(sec_id=sec_id).all()

    # Check if the student has already requested 2 books
    def book_already_requested(book_id):
        user_books_count = Request.query.filter_by(user_id=current_user.user_id).count()
        if user_books_count >= 2:
            return True
        # Check if the book has been requested by the user
        requested_book = Request.query.filter_by(user_id=current_user.user_id, book_id=book_id).first()
        return bool(requested_book)

    return render_template('books_list.html', section=section, books=books, book_already_requested=book_already_requested)

@app.route('/request_book/<int:book_id>', methods=['POST'])
@login_required
def request_book(book_id):
    # Fetch the book details
    book = Book.query.get_or_404(book_id)
    
    # Check if the user already has 2 requests or has requested this book
    if Request.query.filter_by(user_id=current_user.user_id).count() >= 2:
        return redirect(url_for('see_books', sec_id=book.sec_id))

    # Check if the user has already requested this book
    existing_request = Request.query.filter_by(user_id=current_user.user_id, book_id=book_id).first()
    if existing_request:
        return redirect(url_for('see_books', sec_id=book.sec_id))

    # Create a new request
    new_request = Request(
        book_id=book_id,
        title=book.title,  # Add the book title here
        user_id=current_user.user_id,
        request_date=datetime.now(),
        expiry_date=datetime.now() + timedelta(days=7)
    )

    # Add the request to the database
    db.session.add(new_request)
    db.session.commit()

    return redirect(url_for('my_books'))


@app.route('/my_books')
@login_required
def my_books():
    requests = Request.query.filter_by(user_id=current_user.user_id).all()  # Fetch all requested books for the user
    return render_template('my_books.html', requests=requests)

@app.route('/return_book/<int:req_id>', methods=['POST'])
@login_required
def return_book(req_id):
    request_to_delete = Request.query.get_or_404(req_id)
    db.session.delete(request_to_delete)
    db.session.commit()

    return redirect(url_for('my_books'))

@app.route('/read_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def read_book(book_id):
    # Fetch the book
    book = Book.query.get_or_404(book_id)

    # Fetch the request to calculate time left for return
    request_record = Request.query.filter_by(user_id=current_user.user_id, book_id=book_id).first()

    if not request_record:
        return "You do not have this book on loan.", 403

    # Calculate how much time is left
    current_time = datetime.now()
    time_left = request_record.expiry_date - current_time

    # Render the read_book template
    return render_template('read_book.html', book=book, time_left=time_left)


@app.route('/submit_feedback/<int:book_id>', methods=['POST'])
@login_required
def submit_feedback(book_id):
    # Get the feedback from the form
    feedback_text = request.form.get('feedback')

    # Fetch the book to get the title
    book = Book.query.get_or_404(book_id)

    # Create the feedback entry
    feedback_entry = Feedback(
        user_id=current_user.user_id,
        book_id=book_id,
        title=book.title,
        feedback=feedback_text
    )

    # Add the feedback to the database
    db.session.add(feedback_entry)
    db.session.commit()

    return redirect(url_for('read_book', book_id=book_id))

@app.route('/download_pdf/<int:book_id>', methods=['GET'])
@login_required
def download_book_pdf(book_id):
    # Fetch the book from the database
    book = Book.query.get(book_id)
    if not book:
        abort(404, description="Book not found")

    # Create a PDF in memory
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)

    # Set up the canvas and fonts
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, 750, f"Title: {book.title}")
    
    pdf.setFont("Helvetica", 14)
    pdf.drawString(100, 730, f"Author: {book.author}")
    
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(100, 700, "Description:")
    
    # Adjust line spacing and start position for the description
    pdf.setFont("Helvetica", 12)
    y_position = 680
    line_height = 14  # The height of each line of text

    # Wrap and print the description text, splitting into multiple lines
    description_lines = wrap(book.description, width=80)  # Wrap text at 80 characters per line
    
    for line in description_lines:
        if y_position <= 50:  # If the text reaches near the bottom of the page
            pdf.showPage()    # Create a new page
            pdf.setFont("Helvetica", 12)  # Reset the font for the new page
            y_position = 750  # Reset the Y position for the new page
        
        pdf.drawString(100, y_position, line)
        y_position -= line_height

    # Save the PDF
    pdf.showPage()
    pdf.save()

    # Set the buffer's position to the beginning
    pdf_buffer.seek(0)

    # Send the PDF to the user for download
    return send_file(pdf_buffer, as_attachment=True, download_name=f"{book.title}.pdf", mimetype='application/pdf')


# Run the application
if __name__ == '__main__':
    create_app()  # Initialize app with db and login manager
    app.run(debug=True)
