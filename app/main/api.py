from flask import request, jsonify, session, current_app
from app.main import bp
from app.auth.utils import login_required
from app.main.utils import (
    check_and_update_study_status, 
    check_and_update_patient_status,
    STATUS_NOT_ANNOTATED,
    STATUS_PARTIAL,
    STATUS_COMPLETE
)
from app.models.annotation import (
    get_series_annotations, 
    save_series_annotations, 
    add_annotation, 
    delete_annotation, 
    validate_annotation,
    ANNOTATION_TYPES, 
    VERTEBRAL_LEVELS, 
    SIDE_OPTIONS
)

@bp.route('/api/annotations/types', methods=['GET'])
@login_required
def get_annotation_types():
    """Get all available annotation types and options"""
    return jsonify({
        'types': ANNOTATION_TYPES,
        'levels': VERTEBRAL_LEVELS,
        'sides': SIDE_OPTIONS
    })

@bp.route('/api/annotations/<patient_id>/<study_id>/<series_name>', methods=['GET'])
@login_required
def get_annotations(patient_id, study_id, series_name):
    """Get all annotations for a specific series"""
    annotations = get_series_annotations(patient_id, study_id, series_name)
    return jsonify({'annotations': annotations})

@bp.route('/api/annotations/<patient_id>/<study_id>/<series_name>', methods=['POST'])
@login_required
def create_annotations(patient_id, study_id, series_name):
    """Create/update annotations for a specific series"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    annotations = data.get('annotations', [])
    
    # Validate each annotation
    all_errors = []
    for i, annotation in enumerate(annotations):
        errors = validate_annotation(annotation)
        if errors:
            all_errors.append({
                'index': i,
                'errors': errors
            })
    
    if all_errors:
        return jsonify({
            'error': 'Invalid annotation data',
            'validation_errors': all_errors
        }), 400
    
    # Save annotations
    success = save_series_annotations(
        patient_id, 
        study_id, 
        series_name, 
        annotations, 
        session['username']
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Annotations saved successfully'})
    else:
        return jsonify({'error': 'Failed to save annotations'}), 500

@bp.route('/api/annotations/<patient_id>/<study_id>/<series_name>', methods=['PUT'])
@login_required
def add_single_annotation(patient_id, study_id, series_name):
    """Add a single annotation to a series"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate the annotation
    errors = validate_annotation(data)
    if errors:
        return jsonify({
            'error': 'Invalid annotation data',
            'validation_errors': errors
        }), 400
    
    # Add the annotation
    success = add_annotation(
        patient_id, 
        study_id, 
        series_name, 
        data, 
        session['username']
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Annotation added successfully'})
    else:
        return jsonify({'error': 'Failed to add annotation'}), 500

@bp.route('/api/annotations/<patient_id>/<study_id>/<series_name>/<annotation_id>', methods=['DELETE'])
@login_required
def remove_annotation(patient_id, study_id, series_name, annotation_id):
    """Delete a single annotation from a series"""
    success = delete_annotation(
        patient_id, 
        study_id, 
        series_name, 
        annotation_id, 
        session['username']
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Annotation deleted successfully'})
    else:
        return jsonify({'error': 'Failed to delete annotation'}), 500
