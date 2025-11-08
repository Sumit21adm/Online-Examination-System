from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///examination_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration (using environment variables)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_USE_TLS'] = True

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Custom template filter for JSON parsing
@app.template_filter('from_json')
def from_json_filter(value):
    if value:
        return json.loads(value)
    return []

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    results = db.relationship('Result', backref='student', lazy=True)

class Examination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, default=0)
    passing_marks = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', backref='exam', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('Result', backref='exam', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('examination.id'), nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # mcq, fill_blank, brief, true_false
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)  # JSON string for MCQ options
    correct_answer = db.Column(db.Text, nullable=False)
    marks = db.Column(db.Integer, default=1)
    order_num = db.Column(db.Integer, default=0)
    
    answers = db.relationship('Answer', backref='question', lazy=True)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_text = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    marks_obtained = db.Column(db.Integer, default=0)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('examination.id'), nullable=False)
    total_marks = db.Column(db.Integer, default=0)
    marks_obtained = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, pass, fail
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_sent = db.Column(db.Boolean, default=False)
    
    answers = db.relationship('Answer', backref='result', lazy=True, cascade='all, delete-orphan')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper function to send email
def send_result_email(user_email, user_name, exam_title, marks_obtained, total_marks, percentage, status):
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        print("Email credentials not configured. Skipping email.")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = user_email
        msg['Subject'] = f'Exam Result - {exam_title}'
        
        body = f"""
Dear {user_name},

Your exam results for "{exam_title}" are ready:

Marks Obtained: {marks_obtained}/{total_marks}
Percentage: {percentage:.2f}%
Status: {status.upper()}

Thank you for taking the examination.

Best regards,
Online Examination System
"""
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        text = msg.as_string()
        server.sendmail(app.config['MAIL_USERNAME'], user_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        # Validation
        if not username or not email or not password or not full_name:
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name
        )
        
        # First user becomes admin
        if User.query.count() == 0:
            new_user.is_admin = True
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        exams = Examination.query.all()
        total_students = User.query.filter_by(is_admin=False).count()
        total_exams = Examination.query.count()
        return render_template('admin_dashboard.html', exams=exams, total_students=total_students, total_exams=total_exams)
    else:
        # Get upcoming exams
        now = datetime.utcnow()
        upcoming_exams = Examination.query.filter(Examination.start_time > now).all()
        
        # Get completed exams with results
        my_results = Result.query.filter_by(user_id=current_user.id).all()
        
        return render_template('student_dashboard.html', upcoming_exams=upcoming_exams, results=my_results)

@app.route('/exam/create', methods=['GET', 'POST'])
@login_required
def create_exam():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        duration_minutes = int(request.form.get('duration_minutes'))
        passing_marks = int(request.form.get('passing_marks', 0))
        
        exam = Examination(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            passing_marks=passing_marks,
            created_by=current_user.id
        )
        
        db.session.add(exam)
        db.session.commit()
        
        flash('Exam created successfully!', 'success')
        return redirect(url_for('add_questions', exam_id=exam.id))
    
    return render_template('create_exam.html')

@app.route('/exam/<int:exam_id>/questions/add', methods=['GET', 'POST'])
@login_required
def add_questions(exam_id):
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    exam = Examination.query.get_or_404(exam_id)
    
    if request.method == 'POST':
        question_type = request.form.get('question_type')
        question_text = request.form.get('question_text')
        marks = int(request.form.get('marks', 1))
        
        options = None
        correct_answer = None
        
        if question_type == 'mcq':
            options_list = [
                request.form.get('option1'),
                request.form.get('option2'),
                request.form.get('option3'),
                request.form.get('option4')
            ]
            options = json.dumps(options_list)
            correct_answer = request.form.get('correct_option')
        elif question_type == 'fill_blank':
            correct_answer = request.form.get('correct_answer')
        elif question_type == 'true_false':
            correct_answer = request.form.get('correct_answer')
        elif question_type == 'brief':
            correct_answer = request.form.get('model_answer', '')
        
        order_num = Question.query.filter_by(exam_id=exam_id).count() + 1
        
        question = Question(
            exam_id=exam_id,
            question_type=question_type,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            marks=marks,
            order_num=order_num
        )
        
        db.session.add(question)
        
        # Update exam total marks
        exam.total_marks = exam.total_marks + marks
        
        db.session.commit()
        
        flash('Question added successfully!', 'success')
        
        if request.form.get('add_another'):
            return redirect(url_for('add_questions', exam_id=exam_id))
        else:
            return redirect(url_for('view_exam', exam_id=exam_id))
    
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_num).all()
    return render_template('add_questions.html', exam=exam, questions=questions)

@app.route('/exam/<int:exam_id>')
@login_required
def view_exam(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_num).all()
    
    # Check if user has already taken this exam
    existing_result = Result.query.filter_by(user_id=current_user.id, exam_id=exam_id).first()
    
    return render_template('view_exam.html', exam=exam, questions=questions, existing_result=existing_result)

@app.route('/exam/<int:exam_id>/admit-card')
@login_required
def admit_card(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    
    # Generate PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add content
    p.setFont("Helvetica-Bold", 20)
    p.drawString(200, height - 50, "ADMIT CARD")
    
    p.setFont("Helvetica", 12)
    y = height - 100
    
    p.drawString(50, y, f"Examination: {exam.title}")
    y -= 30
    p.drawString(50, y, f"Student Name: {current_user.full_name}")
    y -= 30
    p.drawString(50, y, f"Username: {current_user.username}")
    y -= 30
    p.drawString(50, y, f"Email: {current_user.email}")
    y -= 30
    p.drawString(50, y, f"Start Time: {exam.start_time.strftime('%Y-%m-%d %H:%M')}")
    y -= 30
    p.drawString(50, y, f"Duration: {exam.duration_minutes} minutes")
    y -= 30
    p.drawString(50, y, f"Total Marks: {exam.total_marks}")
    y -= 50
    
    p.setFont("Helvetica-Italic", 10)
    p.drawString(50, y, "Please bring this admit card on the day of examination.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'admit_card_{exam_id}.pdf', mimetype='application/pdf')

@app.route('/exam/<int:exam_id>/take', methods=['GET', 'POST'])
@login_required
def take_exam(exam_id):
    if current_user.is_admin:
        flash('Admins cannot take exams!', 'error')
        return redirect(url_for('dashboard'))
    
    exam = Examination.query.get_or_404(exam_id)
    
    # Check if exam is available
    now = datetime.utcnow()
    if now < exam.start_time:
        flash('Exam has not started yet!', 'error')
        return redirect(url_for('view_exam', exam_id=exam_id))
    
    if now > exam.end_time:
        flash('Exam has ended!', 'error')
        return redirect(url_for('view_exam', exam_id=exam_id))
    
    # Check if already taken
    existing_result = Result.query.filter_by(user_id=current_user.id, exam_id=exam_id).first()
    if existing_result:
        flash('You have already taken this exam!', 'error')
        return redirect(url_for('view_result', result_id=existing_result.id))
    
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_num).all()
    
    if request.method == 'POST':
        # Create result
        result = Result(
            user_id=current_user.id,
            exam_id=exam_id,
            total_marks=exam.total_marks
        )
        db.session.add(result)
        db.session.flush()  # Get result ID
        
        total_obtained = 0
        
        for question in questions:
            answer_text = request.form.get(f'question_{question.id}')
            
            # Check answer
            is_correct = False
            marks_obtained = 0
            
            if question.question_type == 'mcq':
                if answer_text and answer_text == question.correct_answer:
                    is_correct = True
                    marks_obtained = question.marks
            elif question.question_type == 'fill_blank':
                if answer_text and answer_text.strip().lower() == question.correct_answer.strip().lower():
                    is_correct = True
                    marks_obtained = question.marks
            elif question.question_type == 'true_false':
                if answer_text and answer_text == question.correct_answer:
                    is_correct = True
                    marks_obtained = question.marks
            # Brief answers need manual checking, so marks_obtained = 0 by default
            
            answer = Answer(
                result_id=result.id,
                question_id=question.id,
                answer_text=answer_text or '',
                is_correct=is_correct,
                marks_obtained=marks_obtained
            )
            db.session.add(answer)
            total_obtained += marks_obtained
        
        # Update result
        result.marks_obtained = total_obtained
        result.percentage = (total_obtained / exam.total_marks * 100) if exam.total_marks > 0 else 0
        result.status = 'pass' if total_obtained >= exam.passing_marks else 'fail'
        
        db.session.commit()
        
        # Send email
        email_sent = send_result_email(
            current_user.email,
            current_user.full_name,
            exam.title,
            total_obtained,
            exam.total_marks,
            result.percentage,
            result.status
        )
        
        if email_sent:
            result.email_sent = True
            db.session.commit()
        
        flash('Exam submitted successfully!', 'success')
        return redirect(url_for('view_result', result_id=result.id))
    
    return render_template('take_exam.html', exam=exam, questions=questions)

@app.route('/result/<int:result_id>')
@login_required
def view_result(result_id):
    result = Result.query.get_or_404(result_id)
    
    # Check access
    if not current_user.is_admin and result.user_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('view_result.html', result=result)

@app.route('/exams')
@login_required
def list_exams():
    now = datetime.utcnow()
    
    if current_user.is_admin:
        exams = Examination.query.all()
    else:
        # Show only upcoming and ongoing exams
        exams = Examination.query.filter(Examination.end_time > now).all()
    
    return render_template('list_exams.html', exams=exams)

@app.route('/results')
@login_required
def list_results():
    if current_user.is_admin:
        results = Result.query.all()
    else:
        results = Result.query.filter_by(user_id=current_user.id).all()
    
    return render_template('list_results.html', results=results)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
