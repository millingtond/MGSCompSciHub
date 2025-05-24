from flask import Blueprint

worksheets_bp = Blueprint('worksheets', __name__, url_prefix='/api/worksheets')

from . import routes
