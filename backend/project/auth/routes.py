# MGSCompSciHub/backend/project/auth/routes.py
from flask import request, jsonify, current_app, g
from . import auth_bp
from ..models import User, RoleEnum, db
import firebase_admin
from firebase_admin import auth as firebase_auth_admin # Alias for clarity
import logging
import traceback # For detailed exception printing

logger = logging.getLogger(__name__)

@auth_bp.route('/firebase/verify_session', methods=['POST'])
def firebase_verify_session():
    '''
    Called by frontend AuthContext after a successful Firebase login (any method).
    Verifies the Firebase ID token and ensures a corresponding user exists in the local DB.
    Creates or updates the local user record. Returns user info for the frontend.
    '''
    # --- ADDED FOR FORCED DEBUGGING ---
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("!!! ENTERED /auth/firebase/verify_session backend route !!!")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    # --- END ADDED FOR FORCED DEBUGGING ---

    data = request.get_json()
    if data is None: # Check if get_json() failed (e.g. wrong content type)
        logger.error("verify_session: Failed to parse JSON data from request.")
        print("!!! VERIFY_SESSION ERROR: FAILED TO PARSE JSON DATA FROM REQUEST !!!")
        return jsonify({"success": False, "isLoggedIn": False, "message": "Invalid request format: JSON expected."}), 400
        
    firebase_token = data.get('firebase_token')
    logger.info(f"/auth/firebase/verify_session called. Token received (first 10 chars): {str(firebase_token)[:10] if firebase_token else 'None'}") # Log partial token

    if not firebase_token:
        logger.warning("verify_session: Firebase token missing from request body.")
        print("!!! VERIFY_SESSION ERROR: FIREBASE TOKEN MISSING FROM REQUEST BODY !!!")
        return jsonify({"success": False, "isLoggedIn": False, "message": "Firebase token missing."}), 400

    try:
        logger.debug("Attempting to verify Firebase ID token...")
        print("--- DEBUG: Attempting firebase_auth_admin.verify_id_token ---")
        decoded_token = firebase_auth_admin.verify_id_token(
            firebase_token, 
            app=firebase_admin.get_app(), 
            check_revoked=True
        )
        print(f"--- DEBUG: Token verified. UID: {decoded_token.get('uid')} ---")
        logger.debug(f"Firebase ID token verified successfully. UID: {decoded_token.get('uid')}")
        
        firebase_uid = decoded_token['uid']
        email_from_token = decoded_token.get('email')
        name_from_token = decoded_token.get('name') 
        sign_in_provider = decoded_token.get('firebase', {}).get('sign_in_provider', 'unknown')

        logger.info(f"verify_session: Token processed for Firebase UID: {firebase_uid}, Email: {email_from_token}, Name: {name_from_token}, Provider: {sign_in_provider}")
        print(f"--- DEBUG: Processing user with UID: {firebase_uid}, Email: {email_from_token} ---")

        user = User.query.filter_by(firebase_uid=firebase_uid).first()

        if not user:
            logger.info(f"verify_session: No local user found for Firebase UID {firebase_uid}. Creating new local user.")
            print(f"--- DEBUG: No local user for UID {firebase_uid}. Creating new. ---")
            user_role = RoleEnum.STUDENT 
            app_username = None

            is_teacher_email = False
            if email_from_token:
                if email_from_token.lower() == "dannymill@hotmail.co.uk":
                    is_teacher_email = True
                    logger.info(f"verify_session: Email {email_from_token} matches configured teacher email.")
                    print(f"--- DEBUG: Email {email_from_token} matches teacher email. ---")

            if sign_in_provider == 'microsoft.com' or (sign_in_provider == 'password' and is_teacher_email):
                user_role = RoleEnum.TEACHER
                app_username = email_from_token or firebase_uid 
                logger.info(f"verify_session: Assigning TEACHER role to {app_username}.")
                print(f"--- DEBUG: Assigning TEACHER role to {app_username}. ---")
                if email_from_token: 
                    existing_user_by_email = User.query.filter(User.email == email_from_token, User.firebase_uid != firebase_uid).first()
                    if existing_user_by_email:
                        logger.warning(f"verify_session: Email {email_from_token} for new Firebase user {firebase_uid} already exists for local user {existing_user_by_email.username} (UID: {existing_user_by_email.firebase_uid}). Account conflict.")
                        print(f"--- DEBUG: Email conflict for {email_from_token}. ---")
                        return jsonify({"success": False, "isLoggedIn": False, "message": "Email already associated with a different account."}), 409
            else:
                user_role = RoleEnum.STUDENT
                app_username = name_from_token or firebase_uid 
                logger.info(f"verify_session: Assigning STUDENT role to {app_username} (Firebase UID: {firebase_uid}).")
                print(f"--- DEBUG: Assigning STUDENT role to {app_username}. ---")
            
            user = User(
                firebase_uid=firebase_uid,
                username=app_username,
                email=email_from_token,
                role=user_role,
                is_mock_teacher=False 
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"verify_session: New local user '{user.username}' (Role: {user_role.value}) created and committed for Firebase UID {firebase_uid}.")
            print(f"--- DEBUG: New local user '{user.username}' created. ---")
        else:
            logger.info(f"verify_session: Local user '{user.username}' found for Firebase UID {firebase_uid}. Current role: {user.role.value}.")
            print(f"--- DEBUG: Local user '{user.username}' found. Role: {user.role.value} ---")
            if email_from_token and user.email != email_from_token:
                user.email = email_from_token
                logger.info(f"verify_session: Updated email for user {user.username} to {email_from_token}.")
            
            is_recognized_teacher_email_for_existing = False
            if email_from_token and email_from_token.lower() == "dannymill@hotmail.co.uk":
                 is_recognized_teacher_email_for_existing = True

            if (sign_in_provider == 'microsoft.com' or (sign_in_provider == 'password' and is_recognized_teacher_email_for_existing)) and user.role != RoleEnum.TEACHER:
                logger.warning(f"verify_session: Existing user {user.username} (UID: {user.firebase_uid}, Role: {user.role.value}) is now being recognized as a TEACHER. Updating role.")
                print(f"--- DEBUG: Updating role to TEACHER for existing user {user.username}. ---")
                user.role = RoleEnum.TEACHER
            
            db.session.commit()
            logger.info(f"verify_session: Updates for existing user '{user.username}' committed.")
            print(f"--- DEBUG: Updates for user '{user.username}' committed. ---")

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
        print(f"--- DEBUG: Successfully processed user {firebase_uid}. Returning success. ---")
        return jsonify({"success": True, "isLoggedIn": True, "user": user_data_for_frontend})

    except firebase_admin.auth.UserNotFoundError as e:
        logger.warning(f"verify_session: Firebase user associated with the token was not found (deleted after token issuance?): {str(e)}")
        print(f"!!! VERIFY_SESSION ERROR: Firebase User Not Found: {str(e)} !!!")
        return jsonify({"success": False, "isLoggedIn": False, "message": "Firebase user not found."}), 404
    except firebase_admin.auth.InvalidIdTokenError as e:
        logger.warning(f"verify_session: Firebase ID token is INVALID: {str(e)}")
        print(f"!!! VERIFY_SESSION ERROR: Invalid Firebase ID Token: {str(e)} !!!")
        return jsonify({"success": False, "isLoggedIn": False, "message": f"Authentication token issue: Invalid ID token."}), 401
    except firebase_admin.auth.ExpiredIdTokenError as e:
        logger.warning(f"verify_session: Firebase ID token has EXPIRED: {str(e)}")
        print(f"!!! VERIFY_SESSION ERROR: Expired Firebase ID Token: {str(e)} !!!")
        return jsonify({"success": False, "isLoggedIn": False, "message": f"Authentication token issue: Token expired."}), 401
    except firebase_admin.auth.RevokedIdTokenError as e:
        logger.warning(f"verify_session: Firebase ID token has been REVOKED: {str(e)}")
        print(f"!!! VERIFY_SESSION ERROR: Revoked Firebase ID Token: {str(e)} !!!")
        return jsonify({"success": False, "isLoggedIn": False, "message": f"Authentication token issue: Token revoked."}), 401
    except firebase_admin.auth.CertificateFetchError as e:
        logger.error(f"verify_session: Could not fetch Firebase public keys to verify token signature: {str(e)}. This is often a network or Firebase Admin SDK setup issue.")
        print(f"!!! VERIFY_SESSION ERROR: Certificate Fetch Error: {str(e)} !!!") # This might be a 500
        return jsonify({"success": False, "isLoggedIn": False, "message": "Could not verify token signature (server configuration issue)."}), 500
    except Exception as e:
        db.session.rollback()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! CRITICAL ERROR in /auth/firebase/verify_session !!!")
        print(f"!!! Exception Type: {type(e).__name__}")
        print(f"!!! Exception Args: {e.args}")
        print("!!! Full Traceback (from print_exc):")
        traceback.print_exc() 
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        logger.error(f"CRITICAL error in /auth/firebase/verify_session: {e}", exc_info=True)
        return jsonify({"success": False, "isLoggedIn": False, "message": "An unexpected error occurred during session verification."}), 500
