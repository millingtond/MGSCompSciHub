# MGSCompSciHub/backend/project/auth/utils.py
from functools import wraps
from flask import request, jsonify, current_app, g
import firebase_admin
from firebase_admin import auth as firebase_auth_admin # Renamed to avoid conflicts
from ..models import User, RoleEnum, db # To find/create user in your DB
import random
import string

# --- Username/Password Generation Utilities (still useful for student creation) ---
ADJECTIVES = ["sunny", "clever", "brave", "quick", "happy", "bright", "gentle", "lucky", "proud", "calm", "eager", "fancy", "jolly", "kind", "merry", "nice", "open", "sharp", "tidy", "witty"]
NOUNS = ["dolphin", "badger", "eagle", "tiger", "river", "mountain", "forest", "ocean", "meadow", "comet", "apple", "berry", "cloud", "diamond", "engine", "flower", "guitar", "harbor", "island", "jacket"]

def _check_app_username_exists(app_username):
    # This checks if the two-word username already exists in your local User.username field
    return User.query.filter_by(username=app_username).first() is not None

def generate_unique_app_username():
    '''Generates a unique two-word username for app display/internal reference.'''
    max_attempts = 100 
    for _ in range(max_attempts):
        adj = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        username = f"{adj}_{noun}"
        if not _check_app_username_exists(username):
            return username
    # Fallback if unique username not found
    return f"user{random.randint(10000, 99999)}"

def generate_random_password(length=10):
    '''Generates a random password with letters, digits, and a special character.'''
    if length < 4: length = 4
    characters = string.ascii_letters + string.digits
    password_list = [
        random.choice(string.ascii_lowercase), random.choice(string.ascii_uppercase),
        random.choice(string.digits), random.choice("!@#$%^&*()-_=+")
    ]
    for _ in range(length - len(password_list)):
        password_list.append(random.choice(characters))
    random.shuffle(password_list)
    return "".join(password_list)

# --- Firebase Token Verification Decorator ---
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]

        if not token:
            current_app.logger.debug("Firebase ID Token is missing from Authorization header.")
            return jsonify({'success': False, 'message': 'Authentication token is missing.'}), 401

        try:
            # Verify the ID token while checking if the token is revoked by passing check_revoked=True.
            # This requires the Firebase Admin SDK to be initialized.
            decoded_token = firebase_auth_admin.verify_id_token(token, app=firebase_admin.get_app(), check_revoked=True)
            
            g.firebase_uid = decoded_token['uid']
            g.firebase_token_info = decoded_token # Store full decoded token if needed by route

            # Find user in your local DB based on Firebase UID
            user = User.query.filter_by(firebase_uid=g.firebase_uid).first()
            
            if not user:
                # This case means the Firebase token is valid, but we don't have a corresponding user
                # in our local database. The /auth/firebase/verify_session endpoint is responsible
                # for creating this local user record upon first login.
                # If we reach here for other API calls, it means the user isn't fully provisioned.
                current_app.logger.warning(f"No local user record found for Firebase UID: {g.firebase_uid}. Token was valid.")
                return jsonify({'success': False, 'message': 'User not fully provisioned in application. Please ensure login process completed.'}), 403

            g.current_user = user # Make your local User object available via Flask's g

        except firebase_admin.auth.InvalidIdTokenError:
            current_app.logger.warning("Invalid Firebase ID Token received.")
            return jsonify({'success': False, 'message': 'Invalid authentication token.'}), 401
        except firebase_admin.auth.ExpiredIdTokenError:
            current_app.logger.warning("Expired Firebase ID Token received.")
            return jsonify({'success': False, 'message': 'Authentication token has expired.'}), 401
        except firebase_admin.auth.RevokedIdTokenError:
            current_app.logger.warning("Revoked Firebase ID Token received.")
            return jsonify({'success': False, 'message': 'Authentication token has been revoked.'}), 401
        except firebase_admin.auth.UserDisabledError:
            current_app.logger.warning(f"Firebase user account disabled for UID: {g.firebase_uid if 'g' in globals() and hasattr(g, 'firebase_uid') else 'Unknown UID'}")
            return jsonify({'success': False, 'message': 'User account has been disabled.'}), 403
        except Exception as e:
            current_app.logger.error(f"Error verifying Firebase token: {e}", exc_info=True)
            return jsonify({'success': False, 'message': f'Token verification failed: {str(e)}'}), 500
        
        return f(*args, **kwargs)
    return decorated_function

def firebase_teacher_required(fn):
    @token_required # First, ensure valid Firebase token and g.current_user is set
    def wrapper(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user or g.current_user.role != RoleEnum.TEACHER:
            return jsonify(success=False, message="Teacher access required."), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__ # Preserve original function name for Flask
    return wrapper

def firebase_student_required(fn):
    @token_required # First, ensure valid Firebase token and g.current_user is set
    def wrapper(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user or g.current_user.role != RoleEnum.STUDENT:
            return jsonify(success=False, message="Student access required."), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__ # Preserve original function name for Flask
    return wrapper
