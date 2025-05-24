from flask import request, jsonify
from flask_login import current_user, login_required
from . import student_bp
from ..models import db, User, RoleEnum, Assignment, WorksheetProgress
from sqlalchemy.orm import joinedload
import logging

logger = logging.getLogger(__name__)

def student_required(fn):
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != RoleEnum.STUDENT:
            return jsonify(success=False, message="Student access required."), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@student_bp.route('/assignments', methods=['GET'])
@student_required
def get_student_assignments():
    if not current_user.student_class_id:
        return jsonify(success=False, message="Student not assigned to any class."), 404
    assignments = Assignment.query.filter_by(class_id=current_user.student_class_id)\
                                   .options(joinedload(Assignment.worksheet))\
                                   .order_by(Assignment.assigned_date.desc()).all()
    assignments_data = []
    for ass in assignments:
        has_progress = WorksheetProgress.query.filter_by(student_id=current_user.id, assignment_id=ass.id).first() is not None
        assignments_data.append({
            "assignment_id": ass.id, "worksheet_id": ass.worksheet.id, "worksheet_title": ass.worksheet.title,
            "worksheet_component": ass.worksheet.component_identifier, "assigned_date": ass.assigned_date.isoformat(),
            "due_date": ass.due_date.isoformat() if ass.due_date else None,
            "status": "In Progress" if has_progress else "Not Started"
        })
    return jsonify(success=True, assignments=assignments_data)

@student_bp.route('/assignments/<int:assignment_id>/progress', methods=['GET'])
@student_required
def get_student_progress_for_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, class_id=current_user.student_class_id).first_or_404("Assignment not found.")
    progress_records = WorksheetProgress.query.filter_by(student_id=current_user.id, assignment_id=assignment.id).all()
    progress_data = {pr.task_identifier: {"answer_data": pr.answer_data, "score": pr.score} for pr in progress_records}
    return jsonify(success=True, worksheet_id=assignment.worksheet_id, worksheet_title=assignment.worksheet.title,
                   worksheet_component=assignment.worksheet.component_identifier, progress=progress_data)

@student_bp.route('/assignments/<int:assignment_id>/progress', methods=['POST'])
@student_required
def save_student_progress(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, class_id=current_user.student_class_id).first_or_404("Assignment not found.")
    data = request.get_json()
    if not data or 'task_identifier' not in data:
        return jsonify(success=False, message="Task identifier is required."), 400
    task_identifier = data['task_identifier']
    answer_data = data.get('answer_data')
    score = data.get('score')
    try:
        progress_record = WorksheetProgress.query.filter_by(
            student_id=current_user.id, assignment_id=assignment.id, task_identifier=task_identifier
        ).first()
        if progress_record:
            progress_record.answer_data = answer_data
            if score is not None: progress_record.score = score
        else:
            progress_record = WorksheetProgress(
                student_id=current_user.id, assignment_id=assignment.id, task_identifier=task_identifier,
                answer_data=answer_data, score=score
            )
            db.session.add(progress_record)
        db.session.commit()
        logger.info(f"Student {current_user.username} progress saved for task {task_identifier} in assignment {assignment_id}")
        return jsonify(success=True, message="Progress saved.",
                       progress_update={"task_identifier": task_identifier, "answer_data": answer_data, "score": score}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving progress for student {current_user.username}, task {task_identifier}: {str(e)}")
        return jsonify(success=False, message="Failed to save progress."), 500
