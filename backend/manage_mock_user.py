# MGSCompSciHub/backend/manage_mock_user.py

from project import create_app, db
from project.models import User, RoleEnum # Make sure RoleEnum is imported

app = create_app()

with app.app_context():
    target_username = "mockteacher@mgs.com"
    target_email = "mockteacher@mgs.com"
    target_password = "safepassword123"  # This password will be hashed by pbkdf2_sha256
    target_role = RoleEnum.TEACHER
    target_is_mock = True

    user = User.query.filter_by(username=target_username).first()

    if user:
        print(f"User '{target_username}' found. Updating attributes and re-setting password to ensure consistency...")
        
        user.email = target_email
        user.role = target_role
        user.is_mock_teacher = target_is_mock
        user.set_password(target_password) # This will use pbkdf2_sha256 from your models.py
        
        try:
            db.session.commit()
            print(f"SUCCESS: User '{target_username}' updated. Password re-hashed with current algorithm ({user.password_hash[:20]}...). Role set to TEACHER. is_mock_teacher set to True.")
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Could not commit updates for '{target_username}': {e}")

    else:
        print(f"User '{target_username}' NOT found. Creating new mock teacher...")
        new_user = User(
            username=target_username,
            email=target_email,
            role=target_role,
            is_mock_teacher=target_is_mock
        )
        new_user.set_password(target_password) # This will use pbkdf2_sha256
        db.session.add(new_user)
        try:
            db.session.commit()
            print(f"SUCCESS: New mock teacher '{target_username}' created with password '{target_password}' (hash: {new_user.password_hash[:20]}...). Role: TEACHER, is_mock_teacher: True.")
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Could not create new mock teacher '{target_username}': {e}")

    # Final verification
    print("\n--- Final Verification from manage_mock_user.py ---")
    verify_user = User.query.filter_by(username=target_username).first()
    if verify_user:
        print(f"User: {verify_user.username}")
        print(f"Email: {verify_user.email}")
        print(f"Role: {verify_user.role}") # Should be RoleEnum.TEACHER
        print(f"Is Mock Teacher: {getattr(verify_user, 'is_mock_teacher', False)}") # Should be True
        print(f"Password Hash (start): {verify_user.password_hash[:20] if verify_user.password_hash else 'None'}")
        print(f"Password Check for '{target_password}': {verify_user.check_password(target_password)}") # Should be True with pbkdf2_sha256
    else:
        print(f"User '{target_username}' still not found after script execution.")

    print("\nMock user management script finished.")