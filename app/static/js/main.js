/**
 * MRI Annotation Tool - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Enable clickable table rows
    const clickableRows = document.querySelectorAll('.clickable-row');
    clickableRows.forEach(row => {
        row.addEventListener('click', function() {
            window.location = this.dataset.href;
        });
    });
    
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.querySelector('.btn-close')) {
                alert.querySelector('.btn-close').click();
            }
        }, 5000);
    });
    
    // Initialize any tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
    
    // Initialize any popovers
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popovers.forEach(popover => {
        new bootstrap.Popover(popover);
    });
});

/**
 * Update patient annotation status
 * @param {string} patientId - The patient ID
 * @param {string} status - The new status (not_annotated, partially_annotated, completed)
 * @returns {Promise} - Promise that resolves when the update is complete
 */
function updatePatientStatus(patientId, status) {
    return fetch('/api/update_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            patient_id: patientId,
            status: status
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Reload the page to reflect the new status
            location.reload();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
        alert('Failed to update status. Please try again.');
    });
}

/**
 * Handle DICOM viewer interactions (placeholder)
 * In a real implementation, this would interact with a DICOM viewer library
 */
class DicomViewer {
    constructor(elementId) {
        this.element = document.getElementById(elementId);
        if (!this.element) {
            console.error(`Element with ID ${elementId} not found`);
            return;
        }
        
        this.currentSeries = null;
        this.currentIndex = 0;
        this.images = [];
    }
    
    /**
     * Load a series of DICOM images
     * @param {string} patientId - The patient ID
     * @param {string} seriesName - The series name
     */
    loadSeries(patientId, seriesName) {
        this.currentSeries = seriesName;
        
        // In a real implementation, you would fetch the DICOM images from the server
        // and load them into the viewer
        console.log(`Loading series ${seriesName} for patient ${patientId}`);
        
        // Simulate loading images
        this.element.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading DICOM series...</p>
            </div>
        `;
        
        // In a real implementation, you would fetch the images and render them
        // For now, just show a placeholder
        setTimeout(() => {
            this.element.innerHTML = `
                <div class="dicom-viewer-container">
                    <div class="dicom-controls mb-2">
                        <button class="btn btn-sm btn-outline-secondary" id="prevImage" disabled>
                            <i class="fas fa-chevron-left"></i> Previous
                        </button>
                        <span class="mx-2">Image 1 of 1</span>
                        <button class="btn btn-sm btn-outline-secondary" id="nextImage" disabled>
                            Next <i class="fas fa-chevron-right"></i>
                        </button>
                        <div class="float-end">
                            <button class="btn btn-sm btn-outline-secondary" id="zoomIn">
                                <i class="fas fa-search-plus"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" id="zoomOut">
                                <i class="fas fa-search-minus"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" id="resetView">
                                <i class="fas fa-sync-alt"></i> Reset
                            </button>
                        </div>
                    </div>
                    <div class="dicom-image-container border rounded">
                        <div class="d-flex align-items-center justify-content-center h-100">
                            <p class="text-muted">DICOM Viewer Placeholder</p>
                        </div>
                    </div>
                </div>
            `;
        }, 1000);
    }
    
    /**
     * Navigate to the next image in the series
     */
    nextImage() {
        if (this.currentIndex < this.images.length - 1) {
            this.currentIndex++;
            this.renderCurrentImage();
        }
    }
    
    /**
     * Navigate to the previous image in the series
     */
    previousImage() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.renderCurrentImage();
        }
    }
    
    /**
     * Render the current image
     */
    renderCurrentImage() {
        // In a real implementation, you would render the current DICOM image
        console.log(`Rendering image ${this.currentIndex + 1} of ${this.images.length}`);
    }
}