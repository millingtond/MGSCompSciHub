import os

# --- Configuration ---
BACKEND_BASE_PATH = r"C:\Users\Dan Mill\OneDrive - Manchester Grammar School\MGSCompSciHub\backend"
# --- End Configuration ---

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
        print(f"Updated/Created file: {file_path}")
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")

# --- File Contents ---

manage_mock_user_lite_py_content = r"""# MGSCompSciHub/backend/manage_mock_user_lite.py
from project import create_app, db
from project.models import User, RoleEnum # Make sure RoleEnum is imported

app = create_app()

with app.app_context():
    target_username = "mockteacher@mgs.com"
    target_email = "mockteacher@mgs.com"
    target_password = "safepassword123"  # This password will be hashed by pbkdf2_sha256 by set_password
    target_role = RoleEnum.TEACHER
    target_is_mock = True

    user = User.query.filter_by(username=target_username).first()

    if user:
        print(f"User '{target_username}' found.")
        updated = False
        if user.email != target_email:
            user.email = target_email
            print(f"  Updated email to: {target_email}")
            updated = True
        if user.role != target_role: # Ensure role is TEACHER
            user.role = target_role
            print(f"  Updated role to: {target_role}")
            updated = True
        if not getattr(user, 'is_mock_teacher', False) == target_is_mock: # Ensure is_mock_teacher is True
            user.is_mock_teacher = target_is_mock
            print(f"  Updated is_mock_teacher to: {target_is_mock}")
            updated = True
        
        # We will still set the password to ensure it has a valid hash,
        # even if the ultra-simplified route doesn't check it.
        # This keeps the user record consistent.
        print(f"  Re-setting password for '{target_username}' with current hashing method (pbkdf2_sha256).")
        user.set_password(target_password) # This will use pbkdf2_sha256
        updated = True # Mark as updated because password was re-set

        if updated:
            try:
                db.session.commit()
                print(f"SUCCESS: User '{target_username}' updated/confirmed. Password re-hashed. Role: {user.role}, is_mock_teacher: {user.is_mock_teacher}.")
            except Exception as e:
                db.session.rollback()
                print(f"ERROR: Could not commit updates for '{target_username}': {e}")
        else:
            # This branch might not be hit if we always re-set password now.
            print(f"INFO: User '{target_username}' already correctly configured (though password was re-affirmed).")

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
            print(f"SUCCESS: New mock teacher '{target_username}' created. Role: {target_role}, is_mock_teacher: {target_is_mock}.")
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Could not create new mock teacher '{target_username}': {e}")

    print("\n--- Final Verification from manage_mock_user_lite.py ---")
    verify_user = User.query.filter_by(username=target_username).first()
    if verify_user:
        print(f"User: {verify_user.username}")
        print(f"Email: {verify_user.email}")
        print(f"Role: {verify_user.role}")
        print(f"Is Mock Teacher: {getattr(verify_user, 'is_mock_teacher', False)}")
        print(f"Password Hash (start): {verify_user.password_hash[:20] if verify_user.password_hash else 'None'}")
        print(f"Password Check for '{target_password}': {verify_user.check_password(target_password)}")
    else:
        print(f"User '{target_username}' still not found after script execution.")

    print("\nLite mock user management script finished.")

"""

auth_routes_py_content_simplified_mock = r"""# MGSCompSciHub/backend/project/auth/routes.py
from flask import request, jsonify, current_app, url_for, redirect, session as flask_session
from flask_login import login_user, logout_user, current_user, login_required
from . import auth_bp
from ..models import User, RoleEnum, db # Ensure RoleEnum is imported
from ..extensions import oauth, login_manager
from .utils import generate_unique_student_username, generate_random_password
import logging

logger = logging.getLogger(__name__)

# User loader is now configured in create_app via login_manager.user_loader decorator

# --- Microsoft OAuth Routes for Teachers ---
def configure_ms_oauth(app):
    if 'microsoft' in oauth._clients:
        return
    oauth.register(
        name='microsoft',
        client_id=app.config['MS_CLIENT_ID'],
        client_secret=app.config['MS_CLIENT_SECRET'],
        authorize_url=f"{app.config['MS_AUTHORITY']}/oauth2/v2.0/authorize",
        authorize_params=None,
        access_token_url=f"{app.config['MS_AUTHORITY']}/oauth2/v2.0/token",
        access_token_params=None,
        refresh_token_url=None,
        client_kwargs={'scope': ' '.join(app.config['MS_SCOPE'])},
        server_metadata_url=f"{app.config['MS_AUTHORITY']}/v2.0/.well-known/openid-configuration"
    )

@auth_bp.route('/teacher/microsoft/login')
def teacher_microsoft_login():
    app = current_app._get_current_object()
    configure_ms_oauth(app)
    redirect_uri = f"{app.config['APP_BASE_URL']}{url_for('auth.teacher_microsoft_callback')}"
    next_url = request.args.get('next')
    if next_url:
        flask_session['oauth_next_url'] = next_url
    return oauth.microsoft.authorize_redirect(redirect_uri)

@auth_bp.route('/teacher/microsoft/callback')
def teacher_microsoft_callback():
    app = current_app._get_current_object()
    configure_ms_oauth(app)
    try:
        token = oauth.microsoft.authorize_access_token()
        if not token:
            logger.error("Microsoft OAuth: Access token not obtained.")
            return jsonify({"success": False, "message": "Access token not obtained from Microsoft."}), 400
        resp = oauth.microsoft.get('https://graph.microsoft.com/v1.0/me', token=token)
        resp.raise_for_status()
        profile = resp.json()
        ms_oid = profile.get('id')
        email = profile.get('userPrincipalName') or profile.get('mail')
        if not ms_oid or not email:
            logger.error(f"Microsoft OAuth: OID or email missing. Profile: {profile}")
            return jsonify({"success": False, "message": "OID or email missing from Microsoft profile."}), 400
        user = User.query.filter_by(microsoft_oid=ms_oid).first()
        if not user:
            existing_user_by_email = User.query.filter_by(email=email).first()
            if existing_user_by_email:
                logger.warning(f"Teacher login attempt with email {email} already exists but different OID.")
                return jsonify({"success": False, "message": "Email already associated with another account type."}), 409
            user = User(username=email, email=email, microsoft_oid=ms_oid, role=RoleEnum.TEACHER)
            db.session.add(user)
            db.session.commit()
            logger.info(f"New teacher registered: {email} (OID: {ms_oid})")
        login_user(user, remember=True)
        
        frontend_base = current_app.config.get('FRONTEND_URL') or \
                        (current_app.config.get('APP_BASE_URL', 'http://localhost:5173').replace(':5000', ':5173'))
        frontend_auth_success_url = f"{frontend_base}/auth/success"
        next_url_from_session = flask_session.pop('oauth_next_url', None)
        if next_url_from_session and next_url_from_session.startswith('/'):
            frontend_auth_success_url = f"{frontend_base}{next_url_from_session}"
        return redirect(frontend_auth_success_url)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Microsoft OAuth callback error: {str(e)}", exc_info=True)
        frontend_base = current_app.config.get('FRONTEND_URL') or \
                        (current_app.config.get('APP_BASE_URL', 'http://localhost:5173').replace(':5000', ':5173'))
        frontend_auth_failure_url = f"{frontend_base}/auth/failure"
        return redirect(frontend_auth_failure_url + f"?error_message=AuthenticationFailed")

@auth_bp.route('/student/login', methods=['POST', 'OPTIONS'])
def student_login():
    if request.method == 'OPTIONS':
        return '', 204
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"success": False, "message": "Missing username or password"}), 400
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username, role=RoleEnum.STUDENT).first()

    # Ensure models.py uses pbkdf2_sha256 for check_password
    if user and user.check_password(password):
        login_user(user, remember=True)
        return jsonify({"success": True, "message": "Student login successful.", "user": {"id": user.id, "username": user.username, "role": user.role.value, "class_id": user.student_class_id}})
    else:
        # Add logging for failed student login attempt
        logger.warning(f"Failed student login attempt for username: {username}")
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

@auth_bp.route('/teacher/mock_login', methods=['POST', 'OPTIONS'])
def teacher_mock_login():
    print("--- ULTRA SIMPLIFIED MOCK TEACHER LOGIN ---")
    if request.method == 'OPTIONS':
        print("OPTIONS request received for simplified mock_login. Responding 204.")
        return '', 204

    if not current_app.debug:
        print("ULTRA SIMPLIFIED MOCK LOGIN: Denied (not in debug mode).")
        return jsonify({"success": False, "message": "Mock login is disabled."}), 403

    data = request.get_json()
    username_from_form = data.get('username')
    print(f"ULTRA SIMPLIFIED MOCK LOGIN: Received username: '{username_from_form}'")

    if not username_from_form:
        print("ULTRA SIMPLIFIED MOCK LOGIN: Missing username from form.")
        return jsonify({"success": False, "message": "Missing username"}), 400

    expected_mock_username = "mockteacher@mgs.com"
    print(f"ULTRA SIMPLIFIED MOCK LOGIN: Expecting username: '{expected_mock_username}'")

    if username_from_form == expected_mock_username:
        # Query for the user, ensuring they have the TEACHER role and is_mock_teacher is True
        user = User.query.filter_by(username=expected_mock_username, role=RoleEnum.TEACHER, is_mock_teacher=True).first()

        if user: # No need to check is_mock_teacher again here as it's in the query
            print(f"ULTRA SIMPLIFIED MOCK LOGIN: User '{user.username}' (ID: {user.id}) confirmed as mock teacher (role and flag). Logging in.")
            login_user(user, remember=True)
            return jsonify({
                "success": True,
                "message": "Ultra-Simplified Mock Teacher login successful (NO PASSWORD CHECKED, username & flags only).",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value
                }
            })
        else:
            # This means either the user doesn't exist, or their role isn't TEACHER, or is_mock_teacher is False.
            # Query without the flags to see if the user exists at all for better logging
            debug_user = User.query.filter_by(username=expected_mock_username).first()
            if debug_user:
                 print(f"ULTRA SIMPLIFIED MOCK LOGIN: User '{expected_mock_username}' found, but FAILED role/is_mock_teacher check. DB Role: {debug_user.role}, DB is_mock_teacher: {getattr(debug_user, 'is_mock_teacher', False)}")
                 logger.warning(f"Simplified Mock Login: User '{username_from_form}' not correctly configured as mock teacher (role/flag mismatch).")
                 return jsonify({"success": False, "message": "Mock teacher account in DB not correctly configured (check role/is_mock_teacher flag)."}), 401
            else:
                print(f"ULTRA SIMPLIFIED MOCK LOGIN: User '{expected_mock_username}' NOT FOUND in DB at all.")
                logger.warning(f"Simplified Mock Login: Mock teacher user '{expected_mock_username}' not found in DB.")
                return jsonify({"success": False, "message": "Mock teacher user record not found in database."}), 404 # 404 if user doesn't exist
    else:
        print(f"ULTRA SIMPLIFIED MOCK LOGIN: Submitted username '{username_from_form}' does not match expected '{expected_mock_username}'.")
        return jsonify({"success": False, "message": "Invalid username for simplified mock login."}), 401


@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
@login_required
def logout():
    if request.method == 'OPTIONS':
        return '', 204
    logout_user()
    return jsonify({"success": True, "message": "Logout successful."})

@auth_bp.route('/check_session', methods=['GET'])
def check_session():
    if current_user.is_authenticated:
        user_data = {"id": current_user.id, "username": current_user.username, "role": current_user.role.value}
        if current_user.role == RoleEnum.TEACHER:
            user_data["email"] = current_user.email
        elif current_user.role == RoleEnum.STUDENT:
            user_data["class_id"] = current_user.student_class_id
            if current_user.assigned_class:
                 user_data["class_name"] = current_user.assigned_class.name
        return jsonify({"isLoggedIn": True, "user": user_data})
    else:
        return jsonify({"isLoggedIn": False})

"""

# --- Script Logic ---
def apply_simplified_mock_login_changes():
    # Path to manage_mock_user_lite.py (will create or overwrite)
    manage_script_path = os.path.join(BACKEND_BASE_PATH, "manage_mock_user_lite.py")
    write_file_content(manage_script_path, manage_mock_user_lite_py_content)

    # Path to auth/routes.py
    auth_routes_path = os.path.join(BACKEND_BASE_PATH, "project", "auth", "routes.py")
    # Ensure the directory exists before writing
    ensure_dir(os.path.dirname(auth_routes_path))
    write_file_content(auth_routes_path, auth_routes_py_content_simplified_mock)

    print("\nPython script finished.")
    print(f"1. '{os.path.basename(manage_script_path)}' has been created/updated in '{BACKEND_BASE_PATH}'.")
    print(f"2. 'project/auth/routes.py' has been updated with the ultra-simplified mock teacher login.")
    print("\nNext Steps:")
    print(f"  a. Run from your backend terminal (with venv active & FLASK_APP set): python {os.path.basename(manage_script_path)}")
    print(f"  b. Then, restart your main Flask backend server: python run.py")
    print(f"  c. Try the mock teacher login from your frontend.")

if __name__ == "__main__":
    if not os.path.exists(BACKEND_BASE_PATH) or not os.path.isdir(BACKEND_BASE_PATH):
        print(f"Error: The backend base path '{BACKEND_BASE_PATH}' does not exist or is not a directory.")
    else:
        apply_simplified_mock_login_changes()