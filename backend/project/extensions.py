from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
oauth = OAuth()
cors = CORS()

# User loader will be set in create_app to ensure User model is defined
# login_manager.user_loader(lambda user_id: User.query.get(int(user_id)))
login_manager.login_view = 'auth.teacher_microsoft_login' # Default, can be overridden
login_manager.login_message_category = 'info'
login_manager.session_protection = "strong"
