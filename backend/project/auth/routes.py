# MGSCompSciHub/backend/project/auth/routes.py
from flask import request, jsonify, current_app, g # Added g
# from flask_login import login_user, logout_user # Flask-Login's login_user/logout_user not directly used for token auth
from . import auth_bp
from ..models import User, RoleEnum, db
# from ..extensions import oauth # Keep if you had other direct OAuth, otherwise can remove
from .utils import token_required # Import your new decorator
import firebase_admin
from firebase_admin import auth as firebase_auth_admin # Alias
import logging

logger = logging.getLogger(__name__)

# Old Flask-Login based routes (e.g., /student/login, /teacher/mock_login, /teacher/microsoft/*)
# should be REMOVED or heavily adapted if they serve any purpose beyond what Firebase handles.
# The frontend now uses Firebase SDK for login initiation.

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
        return jsonify({"success": False, "isLoggedIn": False, "message": "Firebase token missing."}), 400

    try:
        decoded_token = firebase_auth_admin.verify_id_token(firebase_token, app=firebase_admin.get_app(), check_revoked=True)
        firebase_uid = decoded_token['uid']
        email_from_token = decoded_token.get('email')
        name_from_token = decoded_token.get('name') # Firebase display name
        sign_in_provider = decoded_token.get('firebase', {}).get('sign_in_provider')

        logger.info(f"verify_session: Token verified for Firebase UID: {firebase_uid}, Email: {email_from_token}, Provider: {sign_in_provider}")

        user = User.query.filter_by(firebase_uid=firebase_uid).first()

        if not user:
            logger.info(f"verify_session: No local user found for Firebase UID {firebase_uid}. Creating new local user.")
            # User authenticated with Firebase, but not in our local DB. Create them.
            user_role = RoleEnum.STUDENT # Default role
            app_username = None # This will be the two-word username for students, or email for teachers

            if sign_in_provider == 'microsoft.com':
                user_role = RoleEnum.TEACHER
                app_username = email_from_token or firebase_uid # Use email if available, else UID
                # Check for existing user by email to prevent duplicates if a teacher re-auths with a new FB account but same MS email
                if email_from_token:
                    existing_user_by_email = User.query.filter(User.email == email_from_token, User.firebase_uid != firebase_uid).first()
                    if existing_user_by_email:
                        logger.warning(f"verify_session: Email {email_from_token} for new Firebase user {firebase_uid} already exists for local user {existing_user_by_email.username}. Linking attempt or conflict.")
                        # Decide on linking strategy or return error. For now, let's error if email is taken by another firebase_uid.
                        return jsonify({"success": False, "isLoggedIn": False, "message": "Email already associated with a different account."}), 409
            else: # Assumed student if not Microsoft (or other specific teacher providers)
                user_role = RoleEnum.STUDENT
                # For students created by teachers, their 'username' (two-word name)
                # should have been set as Firebase display_name.
                app_username = name_from_token or firebase_uid # Fallback to UID if display name not set
            
            user = User(
                firebase_uid=firebase_uid,
                username=app_username, # Store Firebase display name or generated username here
                email=email_from_token, # Store email from Firebase
                role=user_role,
                is_mock_teacher=False # Real Firebase users are not mock
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"verify_session: New local user '{user.username}' (UID: {firebase_uid}, Role: {user_role}) created.")
        else:
            logger.info(f"verify_session: Local user '{user.username}' found for Firebase UID {firebase_uid}.")
            # Optionally update local DB email/name if they changed in Firebase
            if email_from_token and user.email != email_from_token:
                user.email = email_from_token
                logger.info(f"verify_session: Updated email for user {user.username} to {email_from_token}")
            # If Firebase display name is our source for User.username for students
            if user.role == RoleEnum.STUDENT and name_from_token and user.username != name_from_token:
                # Be careful with this if User.username must be unique and name_from_token isn't guaranteed unique
                # user.username = name_from_token 
                # logger.info(f"verify_session: Updated username for student {user.firebase_uid} to {name_from_token}")
                pass # Decide on username update strategy
            db.session.commit()


        # login_user(user, remember=True) # Optional: if you want to create a Flask-Login session cookie too

        user_data_for_frontend = {
            "id": user.id, 
            "firebase_uid": user.firebase_uid,
            "username": user.username, 
            "email": user.email,
            "displayName": name_from_token or user.username,
            "role": user.role.value
        }
        if user.role == RoleEnum.STUDENT:
            user_data_for_frontend["class_id"] = user.student_class_id
            if user.assigned_class:
                user_data_for_frontend["class_name"] = user.assigned_class.name
        
        logger.info(f"verify_session: Success for Firebase UID {firebase_uid}. Returning user data: {user_data_for_frontend}")
        return jsonify({"success": True, "isLoggedIn": True, "user": user_data_for_frontend})

    except firebase_admin.auth.UserNotFoundError:
        logger.warning(f"verify_session: Firebase user not found for token (should not happen if token verified).")
        return jsonify({"success": False, "isLoggedIn": False, "message": "Firebase user not found."}), 404
    except (firebase_admin.auth.InvalidIdTokenError, firebase_admin.auth.ExpiredIdTokenError, firebase_admin.auth.RevokedIdTokenError) as token_error:
        logger.warning(f"verify_session: Firebase token error: {str(token_error)}")
        return jsonify({"success": False, "isLoggedIn": False, "message": f"Authentication token issue: {str(token_error)}"}), 401
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in /auth/firebase/verify_session: {e}", exc_info=True)
        return jsonify({"success": False, "isLoggedIn": False, "message": "Session verification server error."}), 500

# This route is effectively replaced by frontend Firebase SDK + /auth/firebase/verify_session
# @auth_bp.route('/logout', methods=['POST', 'OPTIONS']) ...
# Frontend will call Firebase SDK's signOut. If backend session needs clearing, frontend can notify.
