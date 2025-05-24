# MGSCompSciHub/backend/project/models.py
from .extensions import db
from flask_login import UserMixin
from passlib.hash import pbkdf2_sha256 # Keep for student password generation if needed by Admin SDK
import enum
from sqlalchemy import func

class RoleEnum(enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    # Firebase UID will be the primary link to Firebase Auth.
    # It should be unique.
    firebase_uid = db.Column(db.String(128), unique=True, nullable=True, index=True) 
    
    # This 'username' can now store the two-word student username or teacher's display name/email.
    # Ensure it's unique if used for lookups other than firebase_uid.
    username = db.Column(db.String(80), unique=True, nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=True) # Store verified email from Firebase
    
    # password_hash is no longer the primary method for user login if Firebase handles all auth.
    # However, it's needed if teachers set initial passwords for students via Firebase Admin SDK,
    # as Firebase Admin SDK's createUser can take a password.
    password_hash = db.Column(db.String(128), nullable=True) 
    
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    is_mock_teacher = db.Column(db.Boolean, default=False) # This flag may become less relevant or repurposed
    
    # This was for direct Microsoft OAuth via Flask, may be deprecated if all MS auth goes via Firebase
    microsoft_oid = db.Column(db.String(100), unique=True, nullable=True) 
    
    student_class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)

    classes_managed = db.relationship('Class', backref='managing_teacher', lazy='dynamic', foreign_keys='Class.teacher_id')
    
    def __repr__(self):
        return f'<User {self.username} (Firebase UID: {self.firebase_uid}, Role: {self.role.value})>'

    def set_password(self, password):
        # This method will be used by Firebase Admin SDK when creating users with passwords
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        # This method is less likely to be called if logins are purely via Firebase token verification.
        # Kept for completeness or if some local password check is ever needed.
        if not self.password_hash:
            return False
        return pbkdf2_sha256.verify(password, self.password_hash)

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    students = db.relationship('User', backref='assigned_class', lazy='dynamic', foreign_keys='User.student_class_id')
    assigned_worksheets = db.relationship('Assignment', back_populates='class_assigned', cascade="all, delete-orphan")
    def __repr__(self): return f'<Class {self.name}>'

class Worksheet(db.Model):
    __tablename__ = 'worksheets'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    component_identifier = db.Column(db.String(100), nullable=False, unique=True) 
    assignments = db.relationship('Assignment', back_populates='worksheet', cascade="all, delete-orphan")
    def __repr__(self): return f'<Worksheet {self.title}>'

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    worksheet_id = db.Column(db.Integer, db.ForeignKey('worksheets.id'), nullable=False)
    assigned_date = db.Column(db.DateTime, server_default=func.now())
    due_date = db.Column(db.DateTime, nullable=True)
    class_assigned = db.relationship('Class', back_populates='assigned_worksheets')
    worksheet = db.relationship('Worksheet', back_populates='assignments')
    progress_records = db.relationship('WorksheetProgress', back_populates='assignment', cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('class_id', 'worksheet_id', name='_class_worksheet_uc'),)
    def __repr__(self): return f'<Assignment of {self.worksheet.title} to {self.class_assigned.name}>'

class WorksheetProgress(db.Model):
    __tablename__ = 'worksheet_progress'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # This will be the local DB User ID
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    task_identifier = db.Column(db.String(100), nullable=False) 
    answer_data = db.Column(db.JSON, nullable=True)
    score = db.Column(db.Float, nullable=True)
    last_updated = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    student = db.relationship('User', backref=db.backref('progress_records', lazy='dynamic'))
    assignment = db.relationship('Assignment', back_populates='progress_records')
    __table_args__ = (db.UniqueConstraint('student_id', 'assignment_id', 'task_identifier', name='_student_assignment_task_uc'),)
    def __repr__(self): return f'<Progress by Student ID {self.student_id} on Task {self.task_identifier}>'
