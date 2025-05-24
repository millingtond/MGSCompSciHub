from flask import Blueprint

teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')

from . import routes
