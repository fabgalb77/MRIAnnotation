import os
import json
from datetime import datetime
from flask import current_app

# Define the constants for annotation types
ANNOTATION_TYPES = {
    'disc_herniation': {
        'name': 'Disc Herniation',
        'options': ['mild', 'moderate', 'severe']
    },
    'central_stenosis': {
        'name': 'Central Stenosis',
        'options': ['mild', 'moderate', 'severe']
    },
    'foraminal_stenosis': {
        'name': 'Foraminal Stenosis',
        'options': ['mild', 'moderate', 'severe']
    },
    'recess_stenosis': {
        'name': 'Recess Stenosis',
        'options': ['mild', 'moderate', 'severe']
    },
    'spondylolisthesis': {
        'name': 'Spondylolisthesis',
        'options': ['mild', 'moderate', 'severe']
    },
    'signal': {
        'name': 'Signal Alteration',
        'options': ['hyperintense', 'hypointense']
    },
    'endplate_lesion': {
        'name': 'Endplate Lesion',
        'options': ['small_defect', 'schmorls_node', 'completely_damaged']
    },
    'degenerated_disc': {
        'name': 'Degenerated Disc',
        'options': ['I', 'II', 'III', 'IV', 'V']
    },
    'fracture': {
        'name': 'Fracture',
        'options': ['osteoporotic', 'traumatic']
    },
    'other': {
        'name': 'Other',
        'options': []
    }
}

# Define the vertebral levels
VERTEBRAL_LEVELS = [
    'L1', 'L1-L2', 'L2', 'L2-L3', 'L3', 'L3-L4', 'L4', 'L4-L5', 'L5', 'L5-S1', 'S1'
]

# Define the side options
SIDE_OPTIONS = ['left', 'right', 'bilateral']

def get_annotations_file_path(patient_id, study_id, series_name):
    """Get the path to the annotations JSON file for a specific series"""
    # Create a nested structure: patient_id/study_id/series_name.json
    annotations_dir = os.path.join(current_app.config['ANNOTATION_DATA_DIR'], patient_id, study_id)
    
    # Create directory if it doesn't exist
    os.makedirs(annotations_dir, exist_ok=True)
    
    # Return the path to the series-specific annotations file
    return os.path.join(annotations_dir, f"{series_name}.json")

def get_series_annotations(patient_id, study_id, series_name):
    """Get all annotations for a specific series"""
    file_path = get_annotations_file_path(patient_id, study_id, series_name)
    
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        current_app.logger.error(f"Error loading annotations from {file_path}: {e}")
        return []

def save_series_annotations(patient_id, study_id, series_name, annotations, username):
    """Save annotations for a specific series"""
    file_path = get_annotations_file_path(patient_id, study_id, series_name)
    
    # Add metadata to each annotation if not present
    for annotation in annotations:
        if 'created_by' not in annotation:
            annotation['created_by'] = username
        if 'created_at' not in annotation:
            annotation['created_at'] = datetime.now().isoformat()
        
        annotation['updated_by'] = username
        annotation['updated_at'] = datetime.now().isoformat()
    
    try:
        with open(file_path, 'w') as f:
            json.dump(annotations, f, indent=2)
        return True
    except IOError as e:
        current_app.logger.error(f"Error saving annotations to {file_path}: {e}")
        return False

def add_annotation(patient_id, study_id, series_name, annotation_data, username):
    """Add a single annotation to a series"""
    annotations = get_series_annotations(patient_id, study_id, series_name)
    
    # Add metadata
    annotation_data['created_by'] = username
    annotation_data['created_at'] = datetime.now().isoformat()
    annotation_data['updated_by'] = username
    annotation_data['updated_at'] = datetime.now().isoformat()
    
    # Add a unique ID for this annotation
    annotation_data['id'] = str(len(annotations) + 1)
    
    # Add to list
    annotations.append(annotation_data)
    
    # Save updated list
    saved = save_series_annotations(patient_id, study_id, series_name, annotations, username)
    
    if saved:
        # Update study status to partially annotated
        from app.main.utils import update_study_annotation_status, STATUS_PARTIAL
        update_study_annotation_status(patient_id, study_id, STATUS_PARTIAL, username)
    
    return saved

def delete_annotation(patient_id, study_id, series_name, annotation_id, username):
    """Delete a single annotation from a series"""
    annotations = get_series_annotations(patient_id, study_id, series_name)
    
    # Find and remove the annotation with the given ID
    annotations = [a for a in annotations if a.get('id') != annotation_id]
    
    # Save updated list
    saved = save_series_annotations(patient_id, study_id, series_name, annotations, username)
    
    if saved:
        # Check if there are any annotations left and update study status
        from app.main.utils import check_and_update_study_status
        check_and_update_study_status(patient_id, study_id, username)
    
    return saved

def get_all_patient_annotations(patient_id):
    """Get all annotations for a patient across all studies and series"""
    annotations_dir = os.path.join(current_app.config['ANNOTATION_DATA_DIR'], patient_id)
    
    if not os.path.exists(annotations_dir):
        return {}
    
    all_annotations = {}
    
    # Traverse the directory structure
    for study_id in os.listdir(annotations_dir):
        study_dir = os.path.join(annotations_dir, study_id)
        
        if os.path.isdir(study_dir):
            all_annotations[study_id] = {}
            
            # Get annotations for each series
            for filename in os.listdir(study_dir):
                if filename.endswith('.json'):
                    series_name = os.path.splitext(filename)[0]
                    file_path = os.path.join(study_dir, filename)
                    
                    try:
                        with open(file_path, 'r') as f:
                            all_annotations[study_id][series_name] = json.load(f)
                    except (json.JSONDecodeError, IOError) as e:
                        current_app.logger.error(f"Error loading annotations from {file_path}: {e}")
                        all_annotations[study_id][series_name] = []
    
    return all_annotations


def validate_annotation(annotation_data):
    """Validate annotation data against defined schemas"""
    errors = []
    
    # Check required fields
    required_fields = ['finding', 'level']
    for field in required_fields:
        if field not in annotation_data or not annotation_data[field]:
            errors.append(f"Missing required field: {field}")
            
    # Set default for relevant_to_decision if not present
    if 'relevant_to_decision' not in annotation_data:
        annotation_data['relevant_to_decision'] = True
    
    # If we have required fields
    if 'finding' in annotation_data and annotation_data['finding']:
        finding = annotation_data['finding']
        
        # Check if finding type is valid
        if finding not in ANNOTATION_TYPES:
            errors.append(f"Invalid finding type: {finding}")
        
        # Check if value is valid for this finding type
        if 'value' in annotation_data and annotation_data['value']:
            value = annotation_data['value']
            valid_options = ANNOTATION_TYPES.get(finding, {}).get('options', [])
            
            if valid_options and value not in valid_options:
                errors.append(f"Invalid value '{value}' for finding type '{finding}'. Valid options: {', '.join(valid_options)}")
    
    # Check if level is valid
    if 'level' in annotation_data and annotation_data['level']:
        level = annotation_data['level']
        if level not in VERTEBRAL_LEVELS:
            errors.append(f"Invalid vertebral level: {level}")
    
    # Check if side is valid (if provided)
    if 'side' in annotation_data and annotation_data['side']:
        side = annotation_data['side']
        if side not in SIDE_OPTIONS:
            errors.append(f"Invalid side: {side}")
    
    return errors