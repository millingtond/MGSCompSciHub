# MGSCompSciHub/backend/manage_mock_user_lite.py
from project import create_app, db
from project.models import User, RoleEnum, Class # Make sure RoleEnum and Class are imported

app = create_app()

with app.app_context():
    # --- Mock Teacher Setup ---
    target_teacher_username = "mockteacher@mgs.com"
    target_teacher_email = "mockteacher@mgs.com"
    # Password will be hashed by pbkdf2_sha256 by set_password, 
    # but not checked by the "trust mode" teacher_mock_login route
    target_teacher_password = "safepassword123" 
    target_teacher_role = RoleEnum.TEACHER
    target_teacher_is_mock = True

    teacher_user = User.query.filter_by(username=target_teacher_username).first()

    if teacher_user:
        print(f"User '{target_teacher_username}' found. Updating attributes and re-setting password...")
        teacher_user.email = target_teacher_email
        teacher_user.role = target_teacher_role
        teacher_user.is_mock_teacher = target_teacher_is_mock
        # Always set/reset password to ensure it's hashed with current models.py method (pbkdf2_sha256)
        teacher_user.set_password(target_teacher_password) 
        try:
            db.session.commit()
            print(f"SUCCESS: User '{target_teacher_username}' updated/confirmed. Password re-hashed. Role: {teacher_user.role}, is_mock_teacher: {teacher_user.is_mock_teacher}.")
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Could not commit updates for '{target_teacher_username}': {e}")
    else:
        print(f"User '{target_teacher_username}' NOT found. Creating new mock teacher...")
        teacher_user = User(
            username=target_teacher_username,
            email=target_teacher_email,
            role=target_teacher_role,
            is_mock_teacher=target_teacher_is_mock
        )
        teacher_user.set_password(target_teacher_password)
        db.session.add(teacher_user)
        try:
            db.session.commit()
            print(f"SUCCESS: New mock teacher '{target_teacher_username}' created. Role: {target_teacher_role}, is_mock_teacher: {target_teacher_is_mock}.")
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Could not create new mock teacher '{target_teacher_username}': {e}")

    # --- Test Student Setup (ensure a class exists for the student) ---
    if teacher_user: # Proceed only if mock teacher exists to assign as class teacher
        target_class_name = "Test Class 101"
        # Ensure class is associated with the mock teacher
        test_class = Class.query.filter_by(name=target_class_name, teacher_id=teacher_user.id).first()
        if not test_class:
            print(f"Class '{target_class_name}' not found for mock teacher '{teacher_user.username}'. Creating it...")
            test_class = Class(name=target_class_name, teacher_id=teacher_user.id)
            db.session.add(test_class)
            try:
                db.session.commit()
                print(f"SUCCESS: Created class '{test_class.name}' with id {test_class.id} for teacher '{teacher_user.username}'.")
            except Exception as e:
                db.session.rollback()
                print(f"ERROR: Could not create class '{target_class_name}': {e}")
        
        if test_class: # Proceed only if class exists or was created
            target_student_username = "test_student_01"
            target_student_role = RoleEnum.STUDENT
            # Password will be hashed by pbkdf2_sha256, but not checked by the "trust mode" student login route
            target_student_password = "studentpass123" 

            student_user = User.query.filter_by(username=target_student_username).first()
            if student_user:
                print(f"Student '{target_student_username}' found. Updating attributes and re-setting password...")
                student_user.role = target_student_role
                student_user.student_class_id = test_class.id # Assign to the test class
                student_user.set_password(target_student_password)
                try:
                    db.session.commit()
                    print(f"SUCCESS: Student '{target_student_username}' updated. Role: {student_user.role}, Class ID: {student_user.student_class_id}.")
                except Exception as e:
                    db.session.rollback()
                    print(f"ERROR: Could not commit updates for student '{target_student_username}': {e}")
            else:
                print(f"Student '{target_student_username}' NOT found. Creating new test student...")
                student_user = User(
                    username=target_student_username,
                    role=target_student_role,
                    student_class_id=test_class.id # Assign to the test class
                )
                student_user.set_password(target_student_password)
                db.session.add(student_user)
                try:
                    db.session.commit()
                    print(f"SUCCESS: New student '{target_student_username}' created. Role: {target_student_role}, Class ID: {student_user.student_class_id}.")
                except Exception as e:
                    db.session.rollback()
                    print(f"ERROR: Could not create new student '{target_student_username}': {e}")
        else:
            print(f"INFO: Could not create/find class '{target_class_name}', so test student creation was skipped.")
    else:
        print("INFO: Mock teacher not found/created, so class and student setup was skipped.")


    # --- Final Verification ---
    print("\n--- Final Verification from manage_mock_user_lite.py ---")
    verify_teacher = User.query.filter_by(username=target_teacher_username).first()
    if verify_teacher:
        print(f"Teacher: {verify_teacher.username}, Role: {verify_teacher.role}, IsMock: {getattr(verify_teacher, 'is_mock_teacher', False)}, PwdCheck('{target_teacher_password}'): {verify_teacher.check_password(target_teacher_password)}")
    else:
        print(f"Mock Teacher '{target_teacher_username}' NOT VERIFIED (not found).")
    
    verify_student = User.query.filter_by(username="test_student_01").first()
    if verify_student:
        print(f"Student: {verify_student.username}, Role: {verify_student.role}, ClassID: {verify_student.student_class_id}, PwdCheck('{target_student_password}'): {verify_student.check_password(target_student_password)}")
    else:
        print(f"Test Student 'test_student_01' NOT VERIFIED (not found).")

    print("\nLite mock user management script finished.")

