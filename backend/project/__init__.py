# MGSCompSciHub/backend/project/__init__.py
from flask import Flask, jsonify
from .extensions import db, migrate, login_manager, oauth, cors # login_manager kept for now, but less used
from .models import User, Worksheet 
from config import Config
import logging
import os
from sqlalchemy.exc import OperationalError
import firebase_admin # Import firebase_admin
from firebase_admin import credentials, initialize_app, get_app # Import more specifically

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure logging is configured early
    if not app.debug: # Default to INFO if not in debug, otherwise Flask's default might be WARNING
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')
    else: # In debug mode, Flask's logger is already active, can add more specific formatting if needed
        pass
    
    app.logger.info("Flask app created. Initializing extensions...")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    oauth.init_app(app) 
    
    frontend_url_from_env = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    allowed_origins_list = list(set([
        frontend_url_from_env,
        frontend_url_from_env.replace("localhost", "127.0.0.1"),
        "http://localhost:3000", "http://127.0.0.1:3000" 
    ]))
    app.logger.info(f"Initializing CORS with allowed origins: {allowed_origins_list}")
    cors.init_app(app, supports_credentials=True, resources={
        r"/api/*": {"origins": allowed_origins_list}, 
        r"/auth/*": {"origins": allowed_origins_list}
    })

    # --- Initialize Firebase Admin SDK ---
    app.logger.info("Attempting to initialize Firebase Admin SDK...")
    try:
        firebase_admin_app_initialized = False
        try:
            get_app() # Check if an app is already initialized
            firebase_admin_app_initialized = True
            app.logger.info("Firebase Admin SDK was already initialized.")
        except ValueError: # No app exists yet
            app.logger.info("Firebase Admin SDK not yet initialized. Proceeding with initialization.")
            pass # Continue to initialize

        if not firebase_admin_app_initialized:
            cred_path_from_config = app.config.get('FIREBASE_ADMIN_SDK_JSON_PATH')
            
            if cred_path_from_config:
                if not os.path.isabs(cred_path_from_config):
                    base_dir_for_sdk_key = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) 
                    cred_path = os.path.join(base_dir_for_sdk_key, cred_path_from_config)
                else:
                    cred_path = cred_path_from_config
                
                app.logger.info(f"Resolved Firebase Admin SDK key path: {cred_path}")
                if os.path.exists(cred_path):
                    cred_obj = credentials.Certificate(cred_path)
                    initialize_app(cred_obj) # Use the specific import
                    app.logger.info("Firebase Admin SDK initialized SUCCESSFULLY.")
                else:
                    app.logger.error(f"CRITICAL: Firebase Admin SDK JSON key file NOT FOUND at resolved path: {cred_path}. Firebase Admin features WILL FAIL.")
            else:
                app.logger.error("CRITICAL: FIREBASE_ADMIN_SDK_JSON_PATH not set in app.config (check .env and config.py). Firebase Admin features WILL FAIL.")
        
    except Exception as e:
        app.logger.error(f"CRITICAL: Error during Firebase Admin SDK initialization: {e}", exc_info=True)
        app.logger.error("Firebase Admin features WILL LIKELY FAIL due to this error.")
    # --- End Firebase Admin SDK Init ---

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth_bp
    app.register_blueprint(auth_bp)
    from .teacher import teacher_bp
    app.register_blueprint(teacher_bp)
    from .student import student_bp
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
        except OperationalError:
            app.logger.warning("Could not seed worksheets: tables might not exist yet (normal for initial db setup).")
            db.session.rollback()
        except Exception as e:
            app.logger.error(f"Error during worksheet seeding: {e}")
            db.session.rollback()
               
    app.logger.info("Flask app initialization complete.")
    return app
