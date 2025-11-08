# Online Examination System

A comprehensive end-to-end online examination platform built with Flask, featuring user management, exam scheduling, multiple question types, automatic grading, admit card generation, and email notifications.

## Features

### 🔐 User Management
- **User Registration** with validation (username, email, password)
- **User Login/Logout** with secure session management
- **Role-based Access Control** (Admin and Student roles)
- First registered user automatically becomes admin

### 📅 Examination Management
- **Create Examinations** with title, description, and scheduling
- **Flexible Scheduling** with start time, end time, and duration
- **Passing Marks Configuration**
- **Exam Listing** with status indicators (Upcoming, Ongoing, Ended)

### ❓ Question Types Support
1. **Multiple Choice Questions (MCQ)** - 4 options with single correct answer
2. **Fill in the Blanks** - Text-based answers with automatic checking
3. **True/False** - Boolean questions
4. **Brief Answers** - Long-form answers (requires manual grading)

### 🎫 Admit Card Generation
- **PDF Admit Cards** with student and exam details
- **Download functionality** for registered students
- Professional format with exam information

### ✅ Automated Grading
- **Automatic checking** for MCQ, Fill-in-blanks, and True/False questions
- **Case-insensitive matching** for text answers
- **Instant result calculation** with marks and percentage
- **Pass/Fail status** based on passing marks threshold

### 📊 Results Management
- **Detailed result view** with question-wise analysis
- **Answer comparison** showing correct vs submitted answers
- **Results saved to database** for historical tracking
- **Student and Admin dashboards** with result summaries

### 📧 Email Notifications
- **Automatic email notifications** when results are ready
- Configurable SMTP settings via environment variables
- Email includes marks, percentage, and pass/fail status

### 🎨 Minimal UI
- Clean and responsive design using **Bootstrap 5**
- Mobile-friendly interface
- Intuitive navigation and user experience

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/Sumit21adm/Online-Examination-System.git
cd Online-Examination-System
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Email (Optional)**
To enable email notifications, set these environment variables:
```bash
# On Windows
set MAIL_SERVER=smtp.gmail.com
set MAIL_PORT=587
set MAIL_USERNAME=your-email@gmail.com
set MAIL_PASSWORD=your-app-password

# On macOS/Linux
export MAIL_SERVER=smtp.gmail.com
export MAIL_PORT=587
export MAIL_USERNAME=your-email@gmail.com
export MAIL_PASSWORD=your-app-password
```

**Note:** For Gmail, you need to use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

5. **Run the application**
```bash
python app.py
```

6. **Access the application**
Open your web browser and navigate to: `http://localhost:5000`

## Usage Guide

### For First-Time Setup
1. Register a new account (first user becomes admin automatically)
2. Login with your credentials

### For Admins

#### Creating an Exam
1. Go to Dashboard
2. Click "Create New Exam"
3. Fill in exam details:
   - Title and description
   - Start and end times
   - Duration in minutes
   - Passing marks
4. Click "Create Exam"

#### Adding Questions
1. After creating an exam, you'll be redirected to add questions
2. Select question type (MCQ, Fill in the Blanks, True/False, Brief Answer)
3. Enter question text and answer options
4. Set marks for the question
5. Click "Add & Create Another" to add more questions or "Add & Finish" to complete

#### Managing Exams
- View all exams from the Dashboard
- Add more questions to existing exams
- Monitor student results

### For Students

#### Taking an Exam
1. Login to your account
2. View upcoming exams from Dashboard
3. Download admit card before the exam
4. Click "Start Exam" when ready (must be within exam time window)
5. Answer all questions
6. Click "Submit Exam" before timer expires

#### Viewing Results
1. Results are automatically calculated after submission
2. View detailed results from Dashboard or Results page
3. Check your email for result notification (if configured)
4. Review correct answers and your responses

## Project Structure
```
Online-Examination-System/
│
├── app.py                 # Main application file with routes and logic
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore file
│
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── register.html     # Registration page
    ├── login.html        # Login page
    ├── admin_dashboard.html    # Admin dashboard
    ├── student_dashboard.html  # Student dashboard
    ├── create_exam.html        # Exam creation form
    ├── add_questions.html      # Question creation form
    ├── view_exam.html          # Exam details view
    ├── take_exam.html          # Exam taking interface
    ├── view_result.html        # Result details
    ├── list_exams.html         # All exams listing
    └── list_results.html       # All results listing
```

## Database Schema

The application uses SQLite with the following models:

- **User**: User accounts with authentication
- **Examination**: Exam details and scheduling
- **Question**: Questions with multiple types
- **Answer**: Student answers for each question
- **Result**: Exam results and scores

## Security Features

- Password hashing using Werkzeug security
- Session-based authentication with Flask-Login
- CSRF protection with Flask-WTF
- Role-based access control
- SQL injection prevention with SQLAlchemy ORM

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLAlchemy with SQLite
- **Authentication**: Flask-Login
- **PDF Generation**: ReportLab
- **Email**: SMTP with Python smtplib
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Security**: Werkzeug password hashing

## Troubleshooting

### Database Issues
If you encounter database errors, delete the `examination_system.db` file and restart the application. It will create a fresh database.

### Email Not Sending
- Verify MAIL_USERNAME and MAIL_PASSWORD are correctly set
- For Gmail, ensure you're using an App Password, not your regular password
- Check if "Less secure app access" is enabled (if required)
- The application will continue to work without email; results are still saved to database

### Port Already in Use
If port 5000 is already in use, you can change it in `app.py`:
```python
app.run(debug=True, port=5001)  # Change to any available port
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open-source and available for educational purposes.

## Contact

For questions or support, please open an issue on the GitHub repository.
