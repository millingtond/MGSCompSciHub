import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess-change-this'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'mgscompsci.db') # Path relative to backend dir
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Microsoft OAuth Configuration
    MS_CLIENT_ID = os.environ.get('MS_CLIENT_ID')
    MS_CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET')
    MS_AUTHORITY = os.environ.get('MS_AUTHORITY', 'https://login.microsoftonline.com/common')
    MS_REDIRECT_PATH = "/auth/teacher/microsoft/callback" # Relative to app base URL
    MS_SCOPE = ["User.Read"]

    APP_BASE_URL = os.environ.get('APP_BASE_URL') or 'http://localhost:5000'
