import os
import json
from flask import current_app

def load_spinenet_results():
    """Load SpineNet results from JSON file"""
    # Try multiple potential locations for the SpineNet results file
    potential_locations = [
        # Config-specified location
        current_app.config.get('SPINENET_RESULTS_FILE'),
        
        # In annotation data directory
        os.path.join(current_app.config.get('ANNOTATION_DATA_DIR', ''), 'spinenet_results.json'),
        
        # In root directory
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'spinenet_results.json'),
        
        # In instance directory
        os.path.join(current_app.instance_path, 'spinenet_results.json'),
        
        # Same directory as MRI data
        os.path.join(current_app.config.get('MRI_ROOT_DIR', ''), 'spinenet_results.json'),
        
    ]
    
    # Log attempt to load file
    current_app.logger.info(f"Attempting to load SpineNet results from multiple locations")
    
    # Try each location
    for location in potential_locations:
        if location and os.path.exists(location):
            try:
                current_app.logger.info(f"Found SpineNet results file at: {location}")
                with open(location, 'r') as f:
                    data = json.load(f)
                    current_app.logger.info(f"Successfully loaded SpineNet results with {len(data.get('patients', {}))} patients")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                current_app.logger.error(f"Error loading SpineNet results from {location}: {e}")
                continue
        elif location:
            current_app.logger.debug(f"SpineNet file not found at: {location}")
    
    # If we get here, no valid file was found
    current_app.logger.warning("SpineNet results file not found in any expected location")
    return None


def get_spinenet_findings_for_study(patient_id, study_id):
    """Get relevant SpineNet findings for a specific study"""
    current_app.logger.info(f"Fetching SpineNet findings for patient {patient_id}, study {study_id}")
    
    spinenet_data = load_spinenet_results()
    if not spinenet_data:
        current_app.logger.warning("No SpineNet data available at all")
        return None
    
    # Check if patient exists in SpineNet data
    if patient_id not in spinenet_data.get('patients', {}):
        current_app.logger.warning(f"Patient {patient_id} not found in SpineNet data")
        current_app.logger.debug(f"Available patients: {', '.join(spinenet_data.get('patients', {}).keys())}")
        return None
    
    # Check if study exists for the patient
    patient_data = spinenet_data['patients'][patient_id]
    current_app.logger.debug(f"Available studies for patient {patient_id}: {', '.join(patient_data.keys())}")
    
    # Try different formats of study ID (with/without leading zeros or suffixes)
    original_study_id = study_id
    if study_id in patient_data:
        current_app.logger.info(f"Found exact match for study ID: {study_id}")
    else:
        # Try to normalize the study ID (remove potential date format differences)
        try:
            # Case 1: Remove _MR suffix if present
            if study_id.endswith('_MR'):
                date_part = study_id.replace('_MR', '')
                if date_part in patient_data:
                    current_app.logger.info(f"Found match after removing _MR suffix: {date_part}")
                    study_id = date_part
            
            # Case 2: Handle YYYYMMDD format
            elif len(study_id) == 8 and study_id.isdigit():
                if study_id in patient_data:
                    current_app.logger.info(f"Found matching date part: {study_id}")
                else:
                    # Try to find prefix matches
                    for existing_id in patient_data.keys():
                        if existing_id.startswith(study_id):
                            study_id = existing_id
                            current_app.logger.info(f"Found matching study by prefix: {study_id}")
                            break
            
            # Case 3: Try matching only the date part
            elif '_' in study_id:
                date_part = study_id.split('_')[0]
                if date_part in patient_data:
                    study_id = date_part
                    current_app.logger.info(f"Found matching study by date part: {study_id}")
        except Exception as e:
            current_app.logger.error(f"Error while trying to normalize study ID: {e}")
    
    if study_id not in patient_data:
        current_app.logger.warning(f"Study {study_id} not found for patient {patient_id} after normalization attempts")
        return None
    
    # Now we have a valid study_id that exists in patient_data
    study_data = patient_data[study_id]
    if not study_data.get('series', []):
        current_app.logger.warning(f"No series data found for patient {patient_id}, study {study_id}")
        return None
    
    # Get the first series (SpineNet results are per study, not per series)
    series_data = study_data['series'][0]
    if 'spine_results' not in series_data:
        current_app.logger.warning(f"No spine_results found in series data for patient {patient_id}, study {study_id}")
        return None
    
    # Process and filter the findings
    filtered_findings = {}
    
    for level, findings in series_data['spine_results'].items():
        level_findings = {}
        
        # Include Pfirrmann grade only if 4 or 5
        if findings.get('Pfirrmann', 0) >= 4:
            level_findings['Pfirrmann'] = findings['Pfirrmann']
        
        # Include other findings only if they are positive (value > 0)
        for key, value in findings.items():
            if key != 'Pfirrmann' and value > 0:
                level_findings[key] = value
        
        # Add level to filtered findings if there are any relevant findings
        if level_findings:
            filtered_findings[level] = level_findings
    
    result = {
        'study_description': study_data.get('study_description', ''),
        'series_description': series_data.get('description', ''),
        'processed_on': series_data.get('processed_on', ''),
        'findings': filtered_findings
    }
    
    current_app.logger.info(f"Successfully retrieved SpineNet findings for patient {patient_id}, study {original_study_id} (normalized to {study_id})")
    current_app.logger.debug(f"Found {len(filtered_findings)} levels with relevant findings")
    
    return result

def get_finding_description(finding_key, value):
    """Get a human-readable description for a finding"""
    descriptions = {
        'Pfirrmann': {
            4: 'Moderate disc degeneration (Grade IV)',
            5: 'Severe disc degeneration (Grade V)'
        },
        'Narrowing': {
            1: 'Mild disc narrowing',
            2: 'Moderate disc narrowing',
            3: 'Severe disc narrowing',
            4: 'Extreme disc narrowing'
        },
        'CentralCanalStenosis': {
            1: 'Mild central canal stenosis',
            2: 'Moderate central canal stenosis',
            3: 'Severe central canal stenosis',
            4: 'Extreme central canal stenosis'
        },
        'Spondylolisthesis': {
            1: 'Spondylolisthesis present'
        },
        'UpperEndplateDefect': {
            1: 'Upper endplate defect'
        },
        'LowerEndplateDefect': {
            1: 'Lower endplate defect'
        },
        'UpperMarrow': {
            1: 'Upper vertebral marrow changes'
        },
        'LowerMarrow': {
            1: 'Lower vertebral marrow changes'
        },
        'ForaminalStenosisLeft': {
            1: 'Left foraminal stenosis'
        },
        'ForaminalStenosisRight': {
            1: 'Right foraminal stenosis'
        },
        'Herniation': {
            1: 'Disc herniation present'
        }
    }
    
    # Get description based on finding and value
    if finding_key in descriptions and value in descriptions[finding_key]:
        return descriptions[finding_key][value]
    
    # Generic description for binary findings
    if value == 1 and finding_key not in ['Pfirrmann', 'Narrowing', 'CentralCanalStenosis']:
        return f"{finding_key} present"
    
    # Default description
    return f"{finding_key}: {value}"

def sort_spine_levels(levels):
    """
    Sort spine levels in cranio-caudal order (top to bottom)
    
    Order: T* levels first, then L* levels, then S* levels
    """
    def level_key(level):
        # Split the level into parts (e.g., "L4-L5" -> ["L4", "L5"])
        parts = level.split('-')
        
        # Parse the first part to determine primary sorting
        primary = parts[0]
        
        # Main section (T, L, S)
        if primary.startswith('T'):
            section_value = 0
        elif primary.startswith('L'):
            section_value = 1
        elif primary.startswith('S'):
            section_value = 2
        else:
            # Unknown format, put at the end
            return (3, 99)
        
        # Extract the number part (e.g., "L4" -> 4)
        try:
            number = int(primary[1:])
        except ValueError:
            number = 99  # Invalid format, put at the end
        
        return (section_value, number)
    
    return sorted(levels, key=level_key)