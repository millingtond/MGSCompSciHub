# MGSCompSciHub/backend/project/__init__.py
from flask import Flask, jsonify
from .extensions import db, migrate, login_manager, oauth, cors # login_manager kept for now, but less used
from .models import User, Worksheet 
from config import Config
import logging
import os
from sqlalchemy.exc import OperationalError
import firebase_admin # Import firebase_admin
from firebase_admin import credentials

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app) # Initialize for potential non-API session needs or if gradually migrating
    oauth.init_app(app) 
    
    frontend_url_from_env = os.environ.get('FRONTEND_URL', 'http://localhost:5173') # Default to Vite port
    allowed_origins_list = list(set([
        frontend_url_from_env,
        frontend_url_from_env.replace("localhost", "127.0.0.1"), # Add IP version
        # Add other common dev ports if necessary, or rely on FRONTEND_URL from .env
        "http://localhost:3000", "http://127.0.0.1:3000" 
    ]))
    app.logger.info(f"Initializing CORS with allowed origins: {allowed_origins_list}")
    cors.init_app(app, supports_credentials=True, resources={
        r"/api/*": {"origins": allowed_origins_list}, 
        r"/auth/*": {"origins": allowed_origins_list}
    })

    # --- Initialize Firebase Admin SDK ---
    try:
        # Get path from app.config which should load from .env
        cred_path_from_config = app.config.get('FIREBASE_ADMIN_SDK_JSON_PATH')
        
        if cred_path_from_config:
            # Construct absolute path if a relative path (e.g., "./key.json") is given in .env
            if not os.path.isabs(cred_path_from_config):
                # Assumes relative path is from the 'backend' directory (where .env and run.py are)
                # __file__ for __init__.py is project/__init__.py
                # os.path.dirname(__file__) is project/
                # os.path.dirname(os.path.dirname(__file__)) is backend/
                base_dir_for_sdk_key = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) 
                cred_path = os.path.join(base_dir_for_sdk_key, cred_path_from_config)
            else:
                cred_path = cred_path_from_config # Already an absolute path
            
            app.logger.info(f"Attempting to load Firebase Admin SDK key from resolved path: {cred_path}")
            if os.path.exists(cred_path):
                if not firebase_admin._apps: # Check if already initialized to prevent re-initialization error
                    cred_obj = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred_obj)
                    app.logger.info("Firebase Admin SDK initialized successfully.")
                else:
                    app.logger.info("Firebase Admin SDK already initialized (skipped re-init).")
            else:
                app.logger.error(f"Firebase Admin SDK JSON key file NOT FOUND at resolved path: {cred_path}. Backend Firebase features will be disabled.")
        else:
            app.logger.error("FIREBASE_ADMIN_SDK_JSON_PATH not set in app.config (check .env and config.py). Firebase Admin features disabled.")
            
    except Exception as e:
        app.logger.error(f"Error initializing Firebase Admin SDK: {e}", exc_info=True)
    # --- End Firebase Admin SDK Init ---

    @login_manager.user_loader # Still needed if any part of Flask-Login session is used
    def load_user(user_id): # user_id here is the local DB User.id
        return User.query.get(int(user_id))
    # login_manager.login_view = 'auth.some_flask_login_route_if_any' # Update if needed, less relevant for pure token auth

    from .auth import auth_bp
    app.register_blueprint(auth_bp)
    from .teacher import teacher_bp
    app.register_blueprint(teacher_bp)
    from .student import student_bp # Student routes will also need to be updated for token auth
    app.register_blueprint(student_bp)
    from .worksheets import worksheets_bp
    app.register_blueprint(worksheets_bp)

    @app.route('/ping_firebase_mode')
    def ping_firebase_mode():
        return jsonify(message="Pong from MGSCompSciHub Backend (Firebase Auth Mode Active)!")

    with app.app_context():
        try:
            worksheet_count = db.session.query(Worksheet.id).count()
            if worksheet_count == 0:
                app.logger.info("Worksheet table empty, seeding...")
                predefined_worksheets = [
                    {"title": "Structure Diagrams", "description": "Visualising Systems with Structure Diagrams (OCR GCSE J277)", "component_identifier": "StructureDiagramsWorksheet"},
                    {"title": "Binary Logic Gates", "description": "Understanding Boolean logic and logic gates.", "component_identifier": "BinaryLogicWorksheet"},
                    {"title": "Python For Loops", "description": "Introduction to for loops in Python.", "component_identifier": "PythonForLoopsWorksheet"},
                ]
                for ws_data in predefined_worksheets:
                    if not Worksheet.query.filter_by(component_identifier=ws_data["component_identifier"]).first():
                        ws = Worksheet(title=ws_data["title"], description=ws_data["description"], component_identifier=ws_data["component_identifier"])
                        db.session.add(ws)
                db.session.commit()
                app.logger.info(f"Seeded {len(predefined_worksheets)} worksheets.")
            # else: # No need to log this every time if not seeding
            #    app.logger.info(f"Worksheet table has {worksheet_count} records. Skipping seed.")
        except OperationalError:
            app.logger.warning("Could not seed worksheets: tables might not exist yet (normal for initial db setup).")
            db.session.rollback()
        except Exception as e:
            app.logger.error(f"Error during worksheet seeding: {e}")
            db.session.rollback()
               
    return app
