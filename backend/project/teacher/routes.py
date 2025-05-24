# MGSCompSciHub/backend/project/teacher/routes.py
from flask import request, jsonify, current_app, g
from . import teacher_bp
from ..models import db, User, Class, RoleEnum, Worksheet, Assignment
from ..auth.utils import firebase_teacher_required, generate_unique_app_username, generate_random_password
import firebase_admin
from firebase_admin import auth as firebase_auth_admin # Alias
import logging

logger = logging.getLogger(__name__)

@teacher_bp.route('/classes', methods=['POST'])
@firebase_teacher_required # Use the new decorator
def create_class():
    teacher = g.current_user # User object from local DB, authenticated via Firebase token
    data = request.get_json()
    class_name = data.get('name','').strip()
    if not class_name: 
        return jsonify(success=False, message="Class name is required."), 400
    
    if Class.query.filter_by(name=class_name, teacher_id=teacher.id).first(): # Check if this teacher already has a class with this name
        return jsonify(success=False, message=f"You already have a class named '{class_name}'."), 409
    if Class.query.filter(Class.name == class_name, Class.teacher_id != teacher.id).first(): # Check if name is taken by another teacher
        return jsonify(success=False, message=f"A class named '{class_name}' already exists (managed by another teacher)."), 409


    try:
        new_class = Class(name=class_name, teacher_id=teacher.id)
        db.session.add(new_class)
        db.session.commit()
        logger.info(f"Teacher {teacher.username} (Firebase UID: {teacher.firebase_uid}) created class: {new_class.name} (ID: {new_class.id})")
        return jsonify(success=True, message="Class created successfully.", class_details={"id": new_class.id, "name": new_class.name}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating class {class_name} by {teacher.username}: {str(e)}")
        return jsonify(success=False, message="Failed to create class."), 500

@teacher_bp.route('/classes', methods=['GET'])
@firebase_teacher_required
def get_teacher_classes():
    teacher = g.current_user
    classes = Class.query.filter_by(teacher_id=teacher.id).order_by(Class.name).all()
    return jsonify(success=True, classes=[{"id": c.id, "name": c.name, "student_count": c.students.count()} for c in classes])

@teacher_bp.route('/classes/<int:class_id>', methods=['GET'])
@firebase_teacher_required
def get_class_details(class_id):
    teacher = g.current_user
    target_class = Class.query.filter_by(id=class_id, teacher_id=teacher.id).first_or_404("Class not found or not managed by you.")
    # Students in local DB linked to this class
    students_in_db = User.query.filter_by(student_class_id=target_class.id, role=RoleEnum.STUDENT).all()
    students_data = [{"id": s.id, "username": s.username, "firebase_uid": s.firebase_uid, "email": s.email} for s in students_in_db]
    
    assigned_ws = [{
        "assignment_id": a.id, "worksheet_id": a.worksheet.id, "title": a.worksheet.title,
        "assigned_date": a.assigned_date.isoformat(), "due_date": a.due_date.isoformat() if a.due_date else None
    } for a in target_class.assigned_worksheets]
    
    return jsonify(success=True, class_details={
        "id": target_class.id, "name": target_class.name, 
        "students": students_data, "assigned_worksheets": assigned_ws
    })

@teacher_bp.route('/create_firebase_student', methods=['POST'])
@firebase_teacher_required
def create_firebase_student_account_route():
    teacher = g.current_user
    data = request.get_json()
    
    class_id_str = data.get('classId')
    num_students_to_create = data.get('numStudents', 1)
    # desired_display_name_prefix = data.get('usernamePrefix', 'student') # Optional prefix for generated names

    if not class_id_str:
        return jsonify(success=False, message="Class ID is required."), 400
    try:
        class_id = int(class_id_str)
        num_students_to_create = int(num_students_to_create)
        if not (0 < num_students_to_create <= 50): # Limit batch size
             raise ValueError("Number of students must be between 1 and 50.")
    except ValueError:
        return jsonify(success=False, message="Invalid Class ID or number of students."), 400

    target_class = Class.query.filter_by(id=class_id, teacher_id=teacher.id).first()
    if not target_class:
        return jsonify(success=False, message="Class not found or not managed by this teacher."), 404

    created_accounts_info = []
    for i in range(num_students_to_create):
        app_display_username = generate_unique_app_username() # Uses the util
        
        # Construct a unique, non-real email for Firebase. Domain should be controlled by you or a placeholder.
        # Using a count or random element to help ensure uniqueness if app_display_username isn't globally unique enough.
        # This email is primarily an identifier for Firebase Auth.
        firebase_user_count = User.query.count() # Simple way to add a unique number
        firebase_email = f"{app_display_username.replace('_', '')}{firebase_user_count + i + 1}@mgscompscihub-students.firebase".lower() # Example domain
        initial_password = generate_random_password(10)

        try:
            fb_user_record = firebase_auth_admin.create_user(
                email=firebase_email,
                password=initial_password,
                display_name=app_display_username,
                email_verified=False 
            )
            logger.info(f"Teacher {teacher.username} creating Firebase user: {fb_user_record.uid} with email {firebase_email}")

            local_user = User(
                firebase_uid=fb_user_record.uid,
                username=app_display_username, # Store the two-word username here
                email=firebase_email, # Store the generated email used for Firebase login
                role=RoleEnum.STUDENT,
                student_class_id=target_class.id,
                # Set password hash locally if you want a backup, using the User model's method
                # This ensures it's hashed with pbkdf2_sha256 if models.py is set up for that
            )
            local_user.set_password(initial_password) # Hash and store password locally
            db.session.add(local_user)
            # db.session.commit() # Commit per student or batch commit later

            created_accounts_info.append({
                "app_username": app_display_username,
                "firebase_login_email": firebase_email,
                "initial_password": initial_password,
                "firebase_uid": fb_user_record.uid
            })

        except firebase_admin.auth.EmailAlreadyExistsError:
            logger.error(f"Firebase: Email {firebase_email} already exists when creating student by {teacher.username}.")
            # For simplicity, we skip this student. A real app might retry with a new email.
            continue 
        except Exception as e:
            logger.error(f"Error creating one Firebase student for {teacher.username}: {e}", exc_info=True)
            db.session.rollback() # Rollback if a single student creation fails within the loop before batch commit
            continue

    if not created_accounts_info:
        return jsonify(success=False, message="No student accounts were created. Check logs for errors like email conflicts."), 500
        
    try:
        db.session.commit() # Commit all successfully created local DB users
        logger.info(f"Teacher {teacher.username} committed {len(created_accounts_info)} student(s) to local DB for class {target_class.name}.")
        return jsonify({
            "success": True,
            "message": f"{len(created_accounts_info)} student account(s) created successfully.",
            "created_students": created_accounts_info
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error committing local student DB records: {e}", exc_info=True)
        return jsonify(success=False, message="Error saving student records to local database after Firebase creation."), 500

# Update other teacher routes (assign_worksheet, get_assignment_progress_for_class)
# to use @firebase_teacher_required and g.current_user

@teacher_bp.route('/classes/<int:class_id>/assign_worksheet', methods=['POST'])
@firebase_teacher_required
def assign_worksheet_to_class(class_id):
    teacher = g.current_user
    target_class = Class.query.filter_by(id=class_id, teacher_id=teacher.id).first_or_404("Class not found or not managed by you.")
    data = request.get_json(); worksheet_id = data.get('worksheet_id')
    if not worksheet_id: return jsonify(success=False, message="Worksheet ID is required."), 400
    worksheet = Worksheet.query.get(worksheet_id)
    if not worksheet: return jsonify(success=False, message="Worksheet not found."), 404
    if Assignment.query.filter_by(class_id=class_id, worksheet_id=worksheet_id).first():
        return jsonify(success=False, message="Worksheet already assigned to this class."), 409
    try:
        assignment = Assignment(class_id=class_id, worksheet_id=worksheet_id)
        db.session.add(assignment); db.session.commit()
        logger.info(f"Worksheet {worksheet.title} assigned to class {target_class.name} by {teacher.username}")
        return jsonify(success=True, message=f"Worksheet '{worksheet.title}' assigned."), 201
    except Exception as e:
        db.session.rollback(); logger.error(f"Error assigning worksheet: {str(e)}")
        return jsonify(success=False, message="Failed to assign worksheet."), 500

@teacher_bp.route('/classes/<int:class_id>/assignments/<int:assignment_id>/progress', methods=['GET'])
@firebase_teacher_required
def get_assignment_progress_for_class(class_id, assignment_id):
    teacher = g.current_user
    target_class = Class.query.filter_by(id=class_id, teacher_id=teacher.id).first_or_404("Class not found.")
    assignment = Assignment.query.filter_by(id=assignment_id, class_id=target_class.id).first_or_404("Assignment not found.")
    
    students_in_class = User.query.filter_by(student_class_id=target_class.id, role=RoleEnum.STUDENT).all()
    student_progress_data = []
    for student in students_in_class:
        progress_records = [{"task_identifier": pr.task_identifier, "score": pr.score, "last_updated": pr.last_updated.isoformat()}
                            for pr in student.progress_records.filter_by(assignment_id=assignment.id).all()]
        student_progress_data.append({
            "student_db_id": student.id, "student_username": student.username, "firebase_uid": student.firebase_uid,
            "has_progress": bool(progress_records), "progress_details": progress_records
        })
    return jsonify(success=True, assignment_progress=student_progress_data, worksheet_title=assignment.worksheet.title)

