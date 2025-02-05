**Library Management System**

**Overview**

The Library Management System is a web-based application built using Flask, HTML, and CSS that allows administrators and students to manage book transactions efficiently. The system provides functionalities for adding, updating, and deleting books, as well as borrowing and returning them.

**Technologies Used**

Backend: Python (Flask) 

Frontend: HTML, CSS

Database: SQLite/MySQL 

Virtual Environment: venv

**Features**

**Admin Panel:**

1) Login with librarian as username.

2) Add, update, delete sections and books.

3) View issued and returned books.

4) Revoke issued books.

5) See feedbacks on books.

**Student Portal:**

1) Login with any username.

2) View available sections and books.

3) Borrow and return books.

4) Read and download books and give feedback.

**Installation & Setup**

1. Clone the Repository

       git clone https://github.com/Ayushrana198/library1.git
       cd library1

2. Create and Activate a Virtual Environment

   For Windows:

       python -m venv venv
       venv\Scripts\activate

   For macOS/Linux:

       python3 -m venv venv
       source venv/bin/activate

3. Install Dependencies

       pip install -r requirements.txt

4. Run the Application

       python main.py

5. Access the Application

       Open your browser and go to http://127.0.0.1:5000/

**Contribution**

If you’d like to contribute:

Fork the repository.

Create a new branch.

Make your changes.

Submit a pull request.

