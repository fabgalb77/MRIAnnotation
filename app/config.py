import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # MRI data directory - absolute path to the root directory containing patient folders
    MRI_ROOT_DIR = os.environ.get('MRI_ROOT_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mri_data')
     
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # Path to annotation status JSON file
    ANNOTATION_STATUS_FILE = os.path.join(MRI_ROOT_DIR, 'annotation_status.json')
    
    # Annotations data directory
    ANNOTATION_DATA_DIR = os.environ.get('ANNOTATION_DATA_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'annotations_data')
    
    # SpineNet results file
    SPINENET_RESULTS_FILE = os.environ.get('SPINENET_RESULTS_FILE') or os.path.join(ANNOTATION_DATA_DIR, 'spinenet_results.json')
    
    # Session configuration
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    MRI_ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests', 'test_data')
    ANNOTATION_STATUS_FILE = os.path.join(MRI_ROOT_DIR, 'annotation_status.json')
    ANNOTATION_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests', 'test_annotations')

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # In production, SECRET_KEY should be set as an environment variable