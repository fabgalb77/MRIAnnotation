# MRI Annotation Tool

A web-based Flask application for collaborative annotation of lumbar spine MRIs. This tool allows multiple users to work together to annotate MRI images, making the process more efficient.

## Features

- **User Authentication**: Secure login system with predefined users
- **Dashboard**: View and manage MRI studies that need annotation
- **Patient View**: Browse through patient MRI series
- **Annotation Tracking**: Track the progress of annotations across users
- **DICOM Viewing**: Built-in DICOM image viewing capabilities

## Project Structure

```
mri_annotation_app/
│
├── app/                      # Main application package
│   ├── auth/                 # Authentication functionality
│   ├── main/                 # Main application routes and logic
│   ├── models/               # Data models
│   ├── static/               # Static files (JS, CSS)
│   ├── templates/            # HTML templates
│   └── utils/                # Utility functions
│
├── instance/                 # Instance-specific config
├── mri_data/                 # MRI data directory
├── tests/                    # Unit and integration tests
├── venv/                     # Virtual environment (not in git)
│
├── .gitignore                # Git ignore file
├── README.md                 # Project documentation
├── requirements.txt          # Package dependencies
└── run.py                    # Application entry point
```

## MRI Data Organization

The application expects MRI data to be organized in a specific folder structure:

```
mri_data/
├── PATIENT_ID_1/
│   ├── T1W_axial/
│   │   ├── image1.dcm
│   │   ├── image2.dcm
│   │   └── ...
│   ├── T2W_sagittal/
│   │   ├── image1.dcm
│   │   ├── image2.dcm
│   │   └── ...
│   └── ...
├── PATIENT_ID_2/
│   └── ...
└── ...
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mri-annotation-tool.git
   cd mri-annotation-tool
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   export FLASK_APP=run.py
   export FLASK_ENV=development
   export SECRET_KEY=your-secret-key
   export MRI_ROOT_DIR=/path/to/mri/data
   ```

5. Run the application:
   ```
   flask run
   ```

## Usage

1. Access the application at `http://localhost:5000`
2. Log in with one of the predefined user accounts:
   - Username: `admin`, Password: `admin_password`
   - Username: `user1`, Password: `user1_password`
   - Username: `user2`, Password: `user2_password`
3. The dashboard will display a list of patients that need annotation
4. Click on a patient to view their MRI series and begin the annotation process

## Development

### Adding New Users

To add new users, modify the `USERS` dictionary in `app/auth/utils.py`:

```python
USERS = {
    'username': generate_password_hash('password'),
    # Add more users here
}
```

### Modifying the Annotation Interface

The annotation interface can be customized by modifying the templates in `app/templates/main/patient.html` and the corresponding JavaScript in `app/static/js/main.js`.

## License

[MIT License](LICENSE)
