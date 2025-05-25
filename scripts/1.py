# python_updater_script.py
import os
import sys

# --- Configuration ---
# This script will use a predefined backend base path and prompt for the teacher email.

# Helper function to create directories if they don't exist
def ensure_dir(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created directory: {directory_path}")

# Helper function to write content to a file, overwriting if it exists
def write_file_content(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully updated file: {file_path}")
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")
        sys.exit(1)

# --- Updated File Content ---
# This is the full content of the new project/auth/routes.py file.
# It includes the logic to correctly assign the TEACHER role for email/password sign-ins.

def get_updated_auth_routes_content(teacher_email):
    # Ensure the teacher_email is properly escaped if it contains special characters for a string literal
    # (though for an email, this is unlikely to be an issue here)
    # Using .lower() for case-insensitive comparison in the template.
    return fr"""# MGSCompSciHub/backend/project/auth/routes.py
from flask import request, jsonify, current_app, g
from . import auth_bp
from ..models import User, RoleEnum, db
import firebase_admin
from firebase_admin import auth as firebase_auth_admin
import logging

logger = logging.getLogger(__name__)

@auth_bp.route('/firebase/verify_session', methods=['POST'])
def firebase_verify_session():
    '''
    Called by frontend AuthContext after a successful Firebase login (any method).
    Verifies the Firebase ID token and ensures a corresponding user exists in the local DB.
    Creates or updates the local user record. Returns user info for the frontend.
    '''
    data = request.get_json()
    firebase_token = data.get('firebase_token')
    logger.info(f"/auth/firebase/verify_session called.")

    if not firebase_token:
        logger.warning("verify_session: Firebase token missing.")
        return jsonify({{"success": False, "isLoggedIn": False, "message": "Firebase token missing."}}), 400

    try:
        decoded_token = firebase_auth_admin.verify_id_token(firebase_token, app=firebase_admin.get_app(), check_revoked=True)
        firebase_uid = decoded_token['uid']
        email_from_token = decoded_token.get('email')
        name_from_token = decoded_token.get('name') # Firebase display name
        
        logger.info(f"verify_session: Token verified for Firebase UID: {{firebase_uid}}, Email: {{email_from_token}}")

        user = User.query.filter_by(firebase_uid=firebase_uid).first()

        if not user:
            logger.info(f"verify_session: No local user found for Firebase UID {{firebase_uid}}. Creating new local user.")
            user_role = RoleEnum.STUDENT # Default role
            app_username = None
            sign_in_provider = decoded_token.get('firebase', {{}}).get('sign_in_provider')
            logger.info(f"verify_session: New user. Firebase sign_in_provider: {{sign_in_provider}}, Email from token: {{email_from_token}}")

            is_teacher_email = False
            if email_from_token:
                # Check if the email matches the configured teacher email (case-insensitive)
                if email_from_token.lower() == "{teacher_email.lower()}":
                    is_teacher_email = True
                    logger.info(f"verify_session: Email {{email_from_token}} matches known teacher email.")
                # Example for checking a domain (uncomment and modify if needed):
                # elif email_from_token.lower().endswith('@your_teacher_domain.com'):
                #     is_teacher_email = True
                #     logger.info(f"verify_session: Email {{email_from_token}} matches teacher domain.")

            if sign_in_provider == 'microsoft.com' or (sign_in_provider == 'password' and is_teacher_email):
                user_role = RoleEnum.TEACHER
                app_username = email_from_token or firebase_uid
                logger.info(f"verify_session: Assigning TEACHER role to {{email_from_token or firebase_uid}}.")
                if email_from_token:
                    existing_user_by_email = User.query.filter(User.email == email_from_token, User.firebase_uid != firebase_uid).first()
                    if existing_user_by_email:
                        logger.warning(f"verify_session: Email {{email_from_token}} for new Firebase user {{firebase_uid}} already exists for local user {{existing_user_by_email.username}} (UID: {{existing_user_by_email.firebase_uid}}). Account linking conflict.")
                        return jsonify({{"success": False, "isLoggedIn": False, "message": "Email already associated with a different account."}}), 409
            else:
                user_role = RoleEnum.STUDENT
                app_username = name_from_token or firebase_uid
                logger.info(f"verify_session: Assigning STUDENT role to {{app_username}} (Firebase UID: {{firebase_uid}}).")
            
            user = User(
                firebase_uid=firebase_uid,
                username=app_username,
                email=email_from_token,
                role=user_role,
                is_mock_teacher=False
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"verify_session: New local user '{{user.username}}' (UID: {{firebase_uid}}, Role: {{user_role.value}}, Provider: {{sign_in_provider}}) created.")
        else:
            logger.info(f"verify_session: Local user '{{user.username}}' found for Firebase UID {{firebase_uid}}.")
            # Optionally update local DB email/name if they changed in Firebase
            if email_from_token and user.email != email_from_token:
                user.email = email_from_token
                logger.info(f"verify_session: Updated email for user {{user.username}} to {{email_from_token}}")
            
            sign_in_provider_for_existing = decoded_token.get('firebase', {{}}).get('sign_in_provider')
            if sign_in_provider_for_existing == 'password' and email_from_token and email_from_token.lower() == "{teacher_email.lower()}" and user.role != RoleEnum.TEACHER:
                logger.info(f"verify_session: Existing user {{user.username}} (Role: {{user.role.value}}) logged in via password with teacher email {{email_from_token}}. Updating role to TEACHER.")
                user.role = RoleEnum.TEACHER
            
            db.session.commit()

        user_data_for_frontend = {{
            "id": user.id, 
            "firebase_uid": user.firebase_uid,
            "username": user.username, 
            "email": user.email,
            "displayName": name_from_token or user.username, # Use Firebase display name if available
            "role": user.role.value
        }}
        if user.role == RoleEnum.STUDENT:
            user_data_for_frontend["class_id"] = user.student_class_id
            if user.assigned_class:
                 user_data_for_frontend["class_name"] = user.assigned_class.name
        
        logger.info(f"verify_session: Success for Firebase UID {{firebase_uid}}. Returning user data: {{user_data_for_frontend}}")
        return jsonify({{"success": True, "isLoggedIn": True, "user": user_data_for_frontend}})

    except firebase_admin.auth.UserNotFoundError:
        logger.warning(f"verify_session: Firebase user not found for token (should not happen if token verified).")
        return jsonify({{"success": False, "isLoggedIn": False, "message": "Firebase user not found."}}), 404
    except (firebase_admin.auth.InvalidIdTokenError, firebase_admin.auth.ExpiredIdTokenError, firebase_admin.auth.RevokedIdTokenError) as token_error:
        logger.warning(f"verify_session: Firebase token error: {{str(token_error)}}")
        return jsonify({{"success": False, "isLoggedIn": False, "message": f"Authentication token issue: {{str(token_error)}}"}}), 401
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in /auth/firebase/verify_session: {{e}}", exc_info=True)
        return jsonify({{"success": False, "isLoggedIn": False, "message": "Session verification server error."}}), 500

# Ensure other routes from the original file would be here if they existed.
# Based on the provided file, firebase_verify_session is the only route.
"""

# --- Script Logic ---
def apply_teacher_auth_fix():
    # Use the provided file path directly
    backend_base_path = r"C:\Users\Dan Mill\OneDrive - Manchester Grammar School\MGSCompSciHub\backend"
    print(f"Using backend project directory: {backend_base_path}")
    
    default_teacher_email = "dannymill@hotmail.co.uk"
    teacher_email_to_check = input(f"Enter the primary teacher's email address (as registered in Firebase) [default: {default_teacher_email}]: ") or default_teacher_email

    if not os.path.exists(backend_base_path) or not os.path.isdir(backend_base_path):
        print(f"Error: The backend base path '{backend_base_path}' does not exist or is not a directory.")
        sys.exit(1)

    auth_routes_py_path = os.path.join(backend_base_path, "project", "auth", "routes.py")

    if not os.path.exists(auth_routes_py_path):
        print(f"Error: The file '{auth_routes_py_path}' does not exist. Please ensure the path is correct.")
        print("If this is a new setup, this file might not have been created by the main application yet.")
        sys.exit(1)
        
    print(f"\nThis script will overwrite '{auth_routes_py_path}'.")
    print("It will update the teacher role assignment logic for Firebase email/password sign-ins.")
    print(f"The email '{teacher_email_to_check}' will be specifically recognized as a teacher.")
    
    proceed = input("Do you want to proceed? (yes/no): ")
    if proceed.lower() != 'yes':
        print("Operation cancelled by the user.")
        sys.exit(0)

    updated_content = get_updated_auth_routes_content(teacher_email_to_check)
    
    ensure_dir(os.path.dirname(auth_routes_py_path))
    write_file_content(auth_routes_py_path, updated_content)

    print("\nPython script finished applying changes.")
    print(f"'{os.path.basename(auth_routes_py_path)}' has been updated in '{os.path.dirname(auth_routes_py_path)}'.")
    print("\nNext Steps:")
    print(f"  1. Ensure the teacher account '{teacher_email_to_check}' exists in your Firebase Authentication console with an email and password.")
    print(f"  2. Restart your Flask backend server (e.g., python run.py in your backend directory).")
    print(f"  3. Try logging in as the teacher '{teacher_email_to_check}' from your frontend application.")

if __name__ == "__main__":
    apply_teacher_auth_fix()
