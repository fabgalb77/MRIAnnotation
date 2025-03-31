from flask import render_template, redirect, url_for, request, jsonify, current_app, session, abort, flash
from app.main import bp
from app.auth.utils import login_required
from app.utils.spinenet_utils import get_spinenet_findings_for_study, get_finding_description
from app.main.utils import (
    get_random_patients_for_annotation,
    get_patient_studies,
    get_study_series,
    get_patient_annotation_status,
    get_study_annotation_status,
    update_patient_annotation_status,
    update_study_annotation_status,
    check_and_update_study_status,
    check_and_update_patient_status,
    get_dicom_preview,
    get_series_info,
    STATUS_NOT_ANNOTATED,
    STATUS_PARTIAL,
    STATUS_COMPLETE
)

@bp.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login page"""
    if 'username' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing patient list"""
    # Check if we should get new patients (from refresh button)
    refresh = request.args.get('refresh', False, type=bool)
    
    # Number of patients to show
    patient_count = request.args.get('count', 5, type=int)
    
    # Get patients from session if they exist and we're not refreshing
    if 'selected_patients' in session and not refresh:
        patients = session['selected_patients']
    else:
        # Get random patients that need annotation
        patients = get_random_patients_for_annotation(count=patient_count)
        # Store in session for persistence
        session['selected_patients'] = patients
    
    # Get detailed information about each patient
    patient_data = []
    for patient_id in patients:
        status = get_patient_annotation_status(patient_id)
        studies = get_patient_studies(patient_id)
        
        patient_data.append({
            'id': patient_id,
            'status': status['status'],
            'annotated_by': status['annotated_by'],
            'last_updated': status['last_updated'],
            'study_count': len(studies)
        })
    
    return render_template('main/dashboard.html', patients=patient_data)

@bp.route('/patient/<patient_id>')
@login_required
def patient_detail(patient_id):
    """View for patient details showing all MRI studies"""
    # Get all MRI studies for this patient
    studies = get_patient_studies(patient_id)
    
    if not studies:
        flash(f"Patient {patient_id} not found or has no MRI studies.", "warning")
        return redirect(url_for('main.dashboard'))
    
    # Check and update patient status based on actual annotations
    check_and_update_patient_status(patient_id, session['username'])
    
    # Get updated patient status
    patient_status = get_patient_annotation_status(patient_id)
    
    # For each study, get information about series and status
    study_data = []
    for study in studies:
        study_id = study['id']
        
        # Check and update study status based on actual annotations
        check_and_update_study_status(patient_id, study_id, session['username'])
        
        series_list = get_study_series(patient_id, study_id)
        study_status = get_study_annotation_status(patient_id, study_id)
        
        study_data.append({
            'id': study_id,
            'date': study['formatted_date'],
            'status': study_status['status'],
            'annotated_by': study_status['annotated_by'],
            'last_updated': study_status['last_updated'],
            'series_count': len(series_list)
        })
    
    return render_template('main/patient.html', 
                           patient_id=patient_id,
                           studies=study_data,
                           status=patient_status)

@bp.route('/patient/<patient_id>/study/<study_id>')
@login_required
def study_detail(patient_id, study_id):
    """View for detailed study information and annotation"""
    # Get all MRI series for this study
    series_list = get_study_series(patient_id, study_id)
    
    if not series_list:
        flash(f"Study {study_id} not found or has no MRI series.", "warning")
        return redirect(url_for('main.patient_detail', patient_id=patient_id))
    
    # Check and update study status based on actual annotations
    check_and_update_study_status(patient_id, study_id, session['username'])
    
    # Get updated study status
    study_status = get_study_annotation_status(patient_id, study_id)
    
    # Study date information
    studies = get_patient_studies(patient_id)
    study_info = next((s for s in studies if s['id'] == study_id), None)
    
    if not study_info:
        study_date = "Unknown Date"
    else:
        study_date = study_info['formatted_date']
    
    # For each series, get information and sample image
    series_data = []
    
    # Import annotation functions
    from app.models.annotation import get_series_annotations
    
    for series_name in series_list:
        dicom_count, sample_path = get_dicom_preview([patient_id, study_id, series_name])
        series_info = get_series_info(patient_id, study_id, series_name)
        
        # Get number of annotations for this series
        series_annotations = get_series_annotations(patient_id, study_id, series_name)
        annotation_count = len(series_annotations)
        
        series_data.append({
            'name': series_name,
            'description': series_info['description'],
            'clean_description': series_info['clean_description'],
            'sequence_type': series_info['sequence_type'],
            'orientation': series_info['orientation'],
            'dicom_count': dicom_count,
            'sample_image': sample_path,
            'annotation_count': annotation_count
        })
    
    return render_template('main/study.html', 
                           patient_id=patient_id,
                           study_id=study_id,
                           study_date=study_date,
                           series_list=series_data,
                           status=study_status)

@bp.route('/api/update_patient_status', methods=['POST'])
@login_required
def update_patient_status():
    """API endpoint to update the annotation status for a patient"""
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    patient_id = data.get('patient_id')
    status = data.get('status')
    
    if not patient_id or not status:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate status
    if status not in [STATUS_NOT_ANNOTATED, STATUS_PARTIAL, STATUS_COMPLETE]:
        return jsonify({'error': 'Invalid status value'}), 400
    
    update_patient_annotation_status(patient_id, status, session['username'])
    return jsonify({'success': True})

@bp.route('/api/update_study_status', methods=['POST'])
@login_required
def update_study_status():
    """API endpoint to update the annotation status for a study"""
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    patient_id = data.get('patient_id')
    study_id = data.get('study_id')
    status = data.get('status')
    
    if not patient_id or not study_id or not status:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate status
    if status not in [STATUS_NOT_ANNOTATED, STATUS_PARTIAL, STATUS_COMPLETE]:
        return jsonify({'error': 'Invalid status value'}), 400
    
    update_study_annotation_status(patient_id, study_id, status, session['username'])
    return jsonify({'success': True})

@bp.route('/dicom/<path:dicom_path>')
@login_required
def serve_dicom(dicom_path):
    """Serve a DICOM file as a JPEG image"""
    from flask import send_file
    import io
    
    try:
        image_bytes = get_dicom_preview(dicom_path, as_bytes=True)
        if not image_bytes:
            abort(404)
            
        return send_file(
            io.BytesIO(image_bytes),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"{dicom_path.replace('/', '_')}.jpg"
        )
    except Exception as e:
        current_app.logger.error(f"Error serving DICOM image: {e}")
        abort(404)

@bp.route('/api/debug/spinenet')
@login_required
def debug_spinenet():
    """Debug endpoint to check SpineNet data availability"""
    from app.utils.spinenet_utils import load_spinenet_results
    
    spinenet_data = load_spinenet_results()
    
    if not spinenet_data:
        return jsonify({
            'available': False,
            'message': 'SpineNet data could not be loaded from any location',
            'checked_paths': [
                os.path.join(current_app.config.get('ANNOTATION_DATA_DIR', ''), 'spinenet_results.json'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'spinenet_results.json'),
                os.path.join(current_app.instance_path, 'spinenet_results.json'),
                os.path.join(current_app.config.get('MRI_ROOT_DIR', ''), 'spinenet_results.json')
            ]
        })
    
    # Return basic information about the data
    patients = list(spinenet_data.get('patients', {}).keys())
    
    # Get a sample of studies for the first patient (if available)
    sample_studies = []
    if patients:
        first_patient = patients[0]
        sample_studies = list(spinenet_data['patients'][first_patient].keys())
    
    return jsonify({
        'available': True,
        'last_updated': spinenet_data.get('last_updated', 'Unknown'),
        'patient_count': len(patients),
        'patients': patients[:10],  # Show first 10 patients
        'sample_studies': sample_studies
    })


@bp.route('/api/spinenet/<patient_id>/<study_id>')
@login_required
def get_spinenet_results(patient_id, study_id):
    """API endpoint to get SpineNet results for a specific study"""
    current_app.logger.info(f"Fetching SpineNet results for patient {patient_id}, study {study_id}")
    
    findings = get_spinenet_findings_for_study(patient_id, study_id)
    
    if not findings:
        current_app.logger.warning(f"SpineNet annotations not found for patient {patient_id}, study {study_id}")
        return jsonify({
            'available': False,
            'message': 'SpineNet annotations not available for this study'
        })
    
    # Process findings to include human-readable descriptions
    processed_findings = {}
    
    # Get sorted levels
    from app.utils.spinenet_utils import sort_spine_levels
    sorted_levels = sort_spine_levels(findings['findings'].keys())
    
    for level in sorted_levels:
        level_findings = findings['findings'][level]
        level_descriptions = []
        
        # Start with Pfirrmann grade if present
        if 'Pfirrmann' in level_findings:
            level_descriptions.append(get_finding_description('Pfirrmann', level_findings['Pfirrmann']))
        
        # Add other findings
        for key, value in level_findings.items():
            if key != 'Pfirrmann' and value > 0:
                level_descriptions.append(get_finding_description(key, value))
        
        processed_findings[level] = level_descriptions
    
    return jsonify({
        'available': True,
        'study_description': findings['study_description'],
        'series_description': findings['series_description'],
        'processed_on': findings['processed_on'],
        'findings': processed_findings,
        'sorted_levels': sorted_levels  # Include the sorted levels for the frontend
    })

@bp.route('/api/dicom-files/<patient_id>/<study_id>/<series_name>')
@login_required
def get_dicom_files(patient_id, study_id, series_name):
    """API endpoint to get DICOM files for a series"""
    from app.main.utils import get_dicom_files
    
    dicom_files = get_dicom_files(patient_id, study_id, series_name)
    
    if not dicom_files:
        return jsonify({
            'success': False,
            'message': 'No DICOM files found for this series',
            'files': []
        }), 404
    
    return jsonify({
        'success': True,
        'message': f'Found {len(dicom_files)} DICOM files',
        'files': dicom_files
    })