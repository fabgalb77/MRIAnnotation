import os
import json
import random
from datetime import datetime
from flask import current_app
import pydicom

# Status constants
STATUS_NOT_ANNOTATED = 'not_annotated'
STATUS_PARTIAL = 'partially_annotated'
STATUS_COMPLETE = 'completed'

def get_annotation_status():
    """Load the annotation status from JSON file"""
    status_file = current_app.config['ANNOTATION_STATUS_FILE']
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
    
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            current_app.logger.error(f"Error decoding JSON from {status_file}")
            return {}
    return {}

def save_annotation_status(status_data):
    """Save the annotation status to JSON file"""
    status_file = current_app.config['ANNOTATION_STATUS_FILE']
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
    
    with open(status_file, 'w') as f:
        json.dump(status_data, f, indent=2)

def get_patient_list():
    """Get a list of all patient IDs from the MRI root directory"""
    mri_root = current_app.config['MRI_ROOT_DIR']
    
    if not os.path.exists(mri_root):
        current_app.logger.warning(f"MRI root directory does not exist: {mri_root}")
        return []
    
    return [d for d in os.listdir(mri_root) 
            if os.path.isdir(os.path.join(mri_root, d)) and 
            not d.startswith('.') and
            d != os.path.basename(os.path.dirname(current_app.config['ANNOTATION_STATUS_FILE']))]

def get_patient_studies(patient_id):
    """Get all MRI studies for a specific patient (folders named YYYYMMDD_MR)"""
    patient_dir = os.path.join(current_app.config['MRI_ROOT_DIR'], patient_id)
    
    if not os.path.exists(patient_dir):
        current_app.logger.warning(f"Patient directory does not exist: {patient_dir}")
        return []
    
    # Get folders matching the pattern YYYYMMDD_MR
    studies = []
    for d in os.listdir(patient_dir):
        study_path = os.path.join(patient_dir, d)
        if os.path.isdir(study_path) and is_valid_study_folder(d):
            study_date = parse_study_date(d)
            studies.append({
                'id': d,
                'path': study_path,
                'date': study_date,
                'formatted_date': format_study_date(study_date)
            })
    
    # Sort studies by date (newest first)
    return sorted(studies, key=lambda x: x['date'], reverse=True)

def is_valid_study_folder(folder_name):
    """Check if folder name matches YYYYMMDD_MR pattern"""
    if len(folder_name) < 9:  # At least YYYYMMDD_
        return False
    
    date_part = folder_name[:8]
    suffix = folder_name[8:]
    
    # Check date format
    try:
        datetime.strptime(date_part, '%Y%m%d')
        return suffix.startswith('_')
    except ValueError:
        return False

def parse_study_date(folder_name):
    """Extract date from study folder name"""
    try:
        date_part = folder_name[:8]
        return datetime.strptime(date_part, '%Y%m%d')
    except (ValueError, IndexError):
        # Return a far-past date for invalid formats
        return datetime(1900, 1, 1)

def format_study_date(date_obj):
    """Format a study date for display"""
    return date_obj.strftime('%B %d, %Y')

def get_study_series(patient_id, study_id):
    """Get all MRI series for a specific study"""
    study_dir = os.path.join(current_app.config['MRI_ROOT_DIR'], patient_id, study_id)
    
    if not os.path.exists(study_dir):
        current_app.logger.warning(f"Study directory does not exist: {study_dir}")
        return []
    
    return [d for d in os.listdir(study_dir) 
            if os.path.isdir(os.path.join(study_dir, d))]

def get_dicom_files(patient_id, study_id, series_name):
    """Get list of DICOM files for a specific series in a study"""
    series_dir = os.path.join(current_app.config['MRI_ROOT_DIR'], patient_id, study_id, series_name)
    
    if not os.path.exists(series_dir):
        current_app.logger.warning(f"Series directory does not exist: {series_dir}")
        return []
    
    return [f for f in os.listdir(series_dir) if f.lower().endswith('.dcm')]

def get_random_patients_for_annotation(count=5):
    """Get a list of random patients that need annotation"""
    status_data = get_annotation_status()
    patient_list = get_patient_list()
    
    # Filter patients that need annotation (not annotated or partially annotated)
    patients_needing_work = [p for p in patient_list 
                            if p not in status_data or 
                            status_data[p]['status'] != STATUS_COMPLETE]
    
    # If we have fewer patients than requested, return all of them
    if len(patients_needing_work) <= count:
        return patients_needing_work
    
    # Otherwise, return a random selection
    return random.sample(patients_needing_work, count)

def get_patient_annotation_status(patient_id):
    """Get the annotation status for a specific patient"""
    status_data = get_annotation_status()
    
    if patient_id not in status_data:
        return {
            'status': STATUS_NOT_ANNOTATED,
            'annotated_by': None,
            'last_updated': None,
            'studies': {}
        }
    
    return status_data[patient_id]

def update_patient_annotation_status(patient_id, status, username):
    """Update the annotation status for a specific patient"""
    status_data = get_annotation_status()
    
    # If this is a new patient entry, initialize with empty studies dict
    if patient_id not in status_data:
        status_data[patient_id] = {
            'status': status,
            'annotated_by': username,
            'last_updated': datetime.now().isoformat(),
            'studies': {}
        }
    else:
        # Update existing entry
        status_data[patient_id]['status'] = status
        status_data[patient_id]['annotated_by'] = username
        status_data[patient_id]['last_updated'] = datetime.now().isoformat()
        
        # Ensure studies dict exists
        if 'studies' not in status_data[patient_id]:
            status_data[patient_id]['studies'] = {}
    
    save_annotation_status(status_data)

def update_study_annotation_status(patient_id, study_id, status, username):
    """Update the annotation status for a specific study"""
    status_data = get_annotation_status()
    
    # Make sure patient exists in status data
    if patient_id not in status_data:
        status_data[patient_id] = {
            'status': STATUS_PARTIAL,
            'annotated_by': username,
            'last_updated': datetime.now().isoformat(),
            'studies': {}
        }
    
    # Make sure studies dict exists
    if 'studies' not in status_data[patient_id]:
        status_data[patient_id]['studies'] = {}
    
    # Update the study status
    status_data[patient_id]['studies'][study_id] = {
        'status': status,
        'annotated_by': username,
        'last_updated': datetime.now().isoformat()
    }
    
    # Update overall patient status based on studies
    if all(study['status'] == STATUS_COMPLETE for study in status_data[patient_id]['studies'].values()):
        status_data[patient_id]['status'] = STATUS_COMPLETE
    elif any(study['status'] in [STATUS_PARTIAL, STATUS_COMPLETE] for study in status_data[patient_id]['studies'].values()):
        status_data[patient_id]['status'] = STATUS_PARTIAL
    else:
        status_data[patient_id]['status'] = STATUS_NOT_ANNOTATED
    
    # Update last modified
    status_data[patient_id]['last_updated'] = datetime.now().isoformat()
    status_data[patient_id]['annotated_by'] = username
    
    save_annotation_status(status_data)
    return True

def check_and_update_study_status(patient_id, study_id, username):
    """Check if study has any annotations and update its status accordingly"""
    from app.models.annotation import get_all_patient_annotations
    
    # Get all annotations for the patient
    all_annotations = get_all_patient_annotations(patient_id)
    
    # Check if this study has any annotations
    study_has_annotations = False
    if study_id in all_annotations and all_annotations[study_id]:
        for series_name, annotations in all_annotations[study_id].items():
            if annotations and len(annotations) > 0:
                study_has_annotations = True
                break
    
    # Update status based on annotation presence
    if study_has_annotations:
        new_status = STATUS_PARTIAL
    else:
        new_status = STATUS_NOT_ANNOTATED
    
    # Update the study status
    return update_study_annotation_status(patient_id, study_id, new_status, username)

def check_and_update_patient_status(patient_id, username):
    """Check all studies for a patient and update patient status"""
    status_data = get_annotation_status()
    
    if patient_id not in status_data or 'studies' not in status_data[patient_id]:
        # No status data, nothing to update
        return False
    
    # Get study statuses
    studies = status_data[patient_id]['studies']
    
    # Determine patient status based on studies
    if all(study['status'] == STATUS_COMPLETE for study in studies.values()):
        new_status = STATUS_COMPLETE
    elif any(study['status'] in [STATUS_PARTIAL, STATUS_COMPLETE] for study in studies.values()):
        new_status = STATUS_PARTIAL
    else:
        new_status = STATUS_NOT_ANNOTATED
    
    # Update patient status
    status_data[patient_id]['status'] = new_status
    status_data[patient_id]['last_updated'] = datetime.now().isoformat()
    status_data[patient_id]['annotated_by'] = username
    
    save_annotation_status(status_data)
    return True

def get_study_annotation_status(patient_id, study_id):
    """Get the annotation status for a specific study"""
    patient_status = get_patient_annotation_status(patient_id)
    
    if 'studies' not in patient_status or study_id not in patient_status['studies']:
        return {
            'status': STATUS_NOT_ANNOTATED,
            'annotated_by': None,
            'last_updated': None
        }
    
    return patient_status['studies'][study_id]

def get_dicom_preview(path_components, as_bytes=False):
    """
    Get a preview image from a DICOM file
    
    Args:
        path_components: List or string with path components [patient_id, study_id, series_name, dicom_file]
                        or a path string relative to MRI_ROOT_DIR
        as_bytes: If True, return JPEG bytes, otherwise return DICOM count and sample path
        
    Returns:
        If as_bytes=False: tuple of (dicom_count, sample_path)
        If as_bytes=True: JPEG binary data
    """
    import tempfile
    from pydicom.errors import InvalidDicomError
    
    try:
        # Handle different input formats
        if isinstance(path_components, str):
            # Full path string - split it
            rel_path = path_components
            path_parts = rel_path.split('/')
            
            if len(path_parts) < 3:
                raise ValueError(f"Invalid path format: {rel_path}. Expected patient/study/series/file.")
                
            patient_id = path_parts[0]
            study_id = path_parts[1]
            series_name = path_parts[2]
            
            if len(path_parts) > 3:
                dicom_file = path_parts[3]
                # Specific DICOM file
                full_path = os.path.join(current_app.config['MRI_ROOT_DIR'], rel_path)
                if not os.path.exists(full_path):
                    raise FileNotFoundError(f"DICOM file not found: {full_path}")
                
                # Read the DICOM file
                ds = pydicom.dcmread(full_path)
                
                if as_bytes:
                    # Convert to an image and return as JPEG bytes
                    return _dicom_to_jpg(ds)
                else:
                    return 1, rel_path
            else:
                # Series only - need to get a sample DICOM file
                series_dir = os.path.join(current_app.config['MRI_ROOT_DIR'], patient_id, study_id, series_name)
                dicom_files = get_dicom_files(patient_id, study_id, series_name)
        elif len(path_components) >= 3:
            # List of components
            patient_id = path_components[0]
            study_id = path_components[1]
            series_name = path_components[2]
            
            if len(path_components) > 3:
                dicom_file = path_components[3]
                full_path = os.path.join(current_app.config['MRI_ROOT_DIR'], patient_id, study_id, series_name, dicom_file)
                if not os.path.exists(full_path):
                    raise FileNotFoundError(f"DICOM file not found: {full_path}")
                
                # Read the DICOM file
                ds = pydicom.dcmread(full_path)
                
                if as_bytes:
                    # Convert to an image and return as JPEG bytes
                    return _dicom_to_jpg(ds)
                else:
                    return 1, os.path.join(patient_id, study_id, series_name, dicom_file)
            else:
                # Series only - need to get a sample DICOM file
                series_dir = os.path.join(current_app.config['MRI_ROOT_DIR'], patient_id, study_id, series_name)
                dicom_files = get_dicom_files(patient_id, study_id, series_name)
        else:
            raise ValueError("Invalid path components format")
        
        # For series without specific DICOM file specified
        if not dicom_files:
            if as_bytes:
                # Return a placeholder image
                return b''  # Empty bytes, will be handled as 404 in the route
            else:
                return 0, None
        
        # Choose a middle slice for the preview (typically more informative)
        middle_index = len(dicom_files) // 2
        sample_file = dicom_files[middle_index]
        sample_path = os.path.join(patient_id, study_id, series_name, sample_file)
        
        if as_bytes:
            # Read the DICOM file and convert to JPEG
            ds = pydicom.dcmread(os.path.join(series_dir, sample_file))
            return _dicom_to_jpg(ds)
        else:
            return len(dicom_files), sample_path
    
    except (FileNotFoundError, InvalidDicomError, Exception) as e:
        current_app.logger.error(f"Error creating DICOM preview: {e}")
        if as_bytes:
            return b''
        return 0, None

def get_series_info(patient_id, study_id, series_name):
    """Extract series information from DICOM tags"""
    series_dir = os.path.join(current_app.config['MRI_ROOT_DIR'], patient_id, study_id, series_name)
    
    if not os.path.exists(series_dir):
        current_app.logger.warning(f"Series directory does not exist: {series_dir}")
        return {
            'name': series_name,
            'description': series_name,
            'modality': 'Unknown',
            'sequence_type': 'Unknown',
            'orientation': 'Unknown'
        }
    
    # Get the first DICOM file to extract tags
    dicom_files = get_dicom_files(patient_id, study_id, series_name)
    if not dicom_files:
        return {
            'name': series_name,
            'description': series_name,
            'modality': 'Unknown',
            'sequence_type': 'Unknown',
            'orientation': 'Unknown'
        }
    
    try:
        # Read the first DICOM file
        dicom_path = os.path.join(series_dir, dicom_files[0])
        ds = pydicom.dcmread(dicom_path)
        
        # Extract common tags
        series_description = getattr(ds, 'SeriesDescription', series_name)
        modality = getattr(ds, 'Modality', 'Unknown')
        
        # Try to determine sequence type (T1W, T2W, etc.)
        sequence_type = 'Unknown'
        try:
            # Look for sequence type in various tags
            if hasattr(ds, 'ScanningSequence') and hasattr(ds, 'SequenceVariant'):
                scan_seq = getattr(ds, 'ScanningSequence', '')
                seq_var = getattr(ds, 'SequenceVariant', '')
                
                # Common sequence mappings
                if 'SE' in scan_seq and 'IR' not in seq_var:
                    if hasattr(ds, 'EchoTime') and hasattr(ds, 'RepetitionTime'):
                        echo_time = float(ds.EchoTime)
                        if echo_time < 30:  # Typical threshold
                            sequence_type = 'T1-weighted'
                        else:
                            sequence_type = 'T2-weighted'
                elif 'IR' in seq_var:
                    sequence_type = 'STIR'
                elif 'GR' in scan_seq:
                    sequence_type = 'Gradient Echo'
            
            # Check sequence name in series description
            desc_lower = series_description.lower()
            if 't1' in desc_lower:
                sequence_type = 'T1-weighted'
            elif 't2' in desc_lower:
                sequence_type = 'T2-weighted'
            elif 'stir' in desc_lower:
                sequence_type = 'STIR'
            elif 'flair' in desc_lower:
                sequence_type = 'FLAIR'
        except Exception as e:
            current_app.logger.warning(f"Error determining sequence type: {e}")
        
        # Try to determine orientation
        orientation = 'Unknown'
        try:
            if hasattr(ds, 'ImageOrientationPatient'):
                # Simplified orientation detection
                iop = getattr(ds, 'ImageOrientationPatient', [])
                if len(iop) >= 6:
                    # Extract row and column vectors
                    row_x, row_y, row_z = iop[0], iop[1], iop[2]
                    col_x, col_y, col_z = iop[3], iop[4], iop[5]
                    
                    # Determine orientation using the largest component
                    row_max_idx = [abs(row_x), abs(row_y), abs(row_z)].index(max([abs(row_x), abs(row_y), abs(row_z)]))
                    col_max_idx = [abs(col_x), abs(col_y), abs(col_z)].index(max([abs(col_x), abs(col_y), abs(col_z)]))
                    
                    # Map indices to orientations
                    orientations = ['Sagittal', 'Coronal', 'Axial']
                    if row_max_idx != col_max_idx:
                        orientation = orientations[3 - row_max_idx - col_max_idx]
            
            # Check orientation in series description
            desc_lower = series_description.lower()
            if 'sag' in desc_lower:
                orientation = 'Sagittal'
            elif 'cor' in desc_lower:
                orientation = 'Coronal'
            elif 'ax' in desc_lower or 'tra' in desc_lower:
                orientation = 'Axial'
        except Exception as e:
            current_app.logger.warning(f"Error determining orientation: {e}")
        
        # Create a clean, user-friendly description
        clean_description = f"{sequence_type} {orientation}".strip()
        if clean_description == "Unknown Unknown":
            clean_description = series_description
        
        return {
            'name': series_name,
            'description': series_description,
            'clean_description': clean_description,
            'modality': modality,
            'sequence_type': sequence_type,
            'orientation': orientation
        }
    
    except Exception as e:
        current_app.logger.error(f"Error extracting DICOM tags: {e}")
        return {
            'name': series_name,
            'description': series_name,
            'modality': 'Unknown',
            'sequence_type': 'Unknown',
            'orientation': 'Unknown'
        }

def _dicom_to_jpg(ds, width=300):
    """Convert DICOM dataset to JPEG bytes"""
    import numpy as np
    from PIL import Image
    import io
    
    # Extract pixel array (image data) from the DICOM
    try:
        # Get the pixel array
        pixel_array = ds.pixel_array
        
        # Normalize to 0-255 for display
        if pixel_array.dtype != np.uint8:
            pixel_min = pixel_array.min()
            pixel_max = pixel_array.max()
            if pixel_max == pixel_min:
                pixel_array = np.zeros_like(pixel_array)
            else:
                pixel_array = (((pixel_array - pixel_min) / (pixel_max - pixel_min)) * 255).astype(np.uint8)
        
        # Create PIL Image
        if len(pixel_array.shape) == 3 and pixel_array.shape[2] == 3:
            # Color image
            img = Image.fromarray(pixel_array)
        else:
            # Grayscale image
            img = Image.fromarray(pixel_array).convert('L')
        
        # Resize to specified width
        if width:
            height = int(width * img.height / img.width)
            img = img.resize((width, height), Image.LANCZOS)
        
        # Convert to JPEG in memory
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=90)
        return img_byte_arr.getvalue()
    
    except Exception as e:
        current_app.logger.error(f"Error converting DICOM to JPEG: {e}")
        # Return empty bytes
        return b''