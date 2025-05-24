from flask import jsonify, request
from ..models import Worksheet, db
from ..teacher.routes import teacher_required # Assuming teacher_required is defined in teacher.routes
from . import worksheets_bp
import logging

logger = logging.getLogger(__name__)

@worksheets_bp.route('', methods=['GET'])
@teacher_required
def list_all_worksheets():
    worksheets = Worksheet.query.order_by(Worksheet.title).all()
    return jsonify(success=True, worksheets=[
        {"id": ws.id, "title": ws.title, "description": ws.description, "component_identifier": ws.component_identifier}
        for ws in worksheets
    ])

# Optional: Endpoint to add new worksheet metadata
@worksheets_bp.route('', methods=['POST'])
@teacher_required # Or a more specific admin role if needed
def create_worksheet_metadata():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    component_identifier = data.get('component_identifier')

    if not all([title, component_identifier]):
        return jsonify(success=False, message="Title and component_identifier are required."), 400

    if Worksheet.query.filter_by(title=title).first() or \
       Worksheet.query.filter_by(component_identifier=component_identifier).first():
        return jsonify(success=False, message="Worksheet with this title or component_identifier already exists."), 409
    
    try:
        new_worksheet = Worksheet(
            title=title, 
            description=description, 
            component_identifier=component_identifier
        )
        db.session.add(new_worksheet)
        db.session.commit()
        logger.info(f"New worksheet metadata created: {title} ({component_identifier})")
        return jsonify(success=True, message="Worksheet metadata created successfully.", 
                       worksheet={"id": new_worksheet.id, "title": new_worksheet.title, 
                                  "component_identifier": new_worksheet.component_identifier}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating worksheet metadata {title}: {str(e)}")
        return jsonify(success=False, message="Failed to create worksheet metadata."), 500
