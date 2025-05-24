from project import create_app, db
from flask_migrate import upgrade
import os
import logging # Added for logging

# Configure logging for the run script itself if needed, or rely on app's logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s : %(message)s')


# Determine the absolute path to the backend directory for SQLite URI
backend_dir = os.path.abspath(os.path.dirname(__file__))
if 'DATABASE_URL' not in os.environ or 'sqlite' in os.environ.get('DATABASE_URL',''):
    # If DATABASE_URL is not set or is for sqlite, ensure the path is correct
    # This is especially important if run.py is in backend/ and db is also in backend/
    default_db_path = os.path.join(backend_dir, 'mgscompsci.db')
    os.environ['DATABASE_URL'] = f'sqlite:///{default_db_path}'
    logger.info(f"Defaulting SQLite DATABASE_URL to: {os.environ['DATABASE_URL']}")


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        migrations_dir = os.path.join(backend_dir, 'migrations')
        if not os.path.exists(migrations_dir):
            logger.warning("Migrations directory not found. Database might not be initialized.")
            logger.warning("If this is the first run, execute these commands in your terminal (in the 'backend' folder with venv activated):")
            logger.warning("1. flask db init")
            logger.warning("2. flask db migrate -m \"Initial database setup\"")
            logger.warning("3. flask db upgrade")
        else:
            try:
                logger.info("Attempting to apply database migrations...")
                upgrade()
                logger.info("Database migrations applied successfully (if any were pending).")
            except Exception as e:
                logger.error(f"Error applying database migrations: {e}", exc_info=True)
                logger.error("Ensure your database is running and accessible, and migrations are up to date.")
                logger.error("If 'flask db upgrade' fails, resolve issues then restart the app.")

    # For production, use Gunicorn: gunicorn --bind 0.0.0.0:5000 "run:app"
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
