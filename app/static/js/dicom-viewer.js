/**
 * DICOM Viewer Component for MRI Annotation Tool
 * 
 * This lightweight viewer allows for browsing through DICOM images, zooming, and panning.
 */

class DicomViewer {
    constructor(options) {
        this.options = Object.assign({
            containerId: 'dicomContainer', // ID of the container element
            controlsId: 'dicomControls',   // ID of the controls element
            imageWidth: 512,               // Default display width of images
            maxZoom: 5,                    // Maximum zoom level
            minZoom: 0.5,                  // Minimum zoom level
            zoomStep: 0.25,                // Zoom step size
            onImageChange: null,           // Callback when image changes
            onLoad: null                   // Callback when images are loaded
        }, options);

        // State variables
        this.images = [];
        this.currentIndex = 0;
        this.isLoading = false;
        this.zoom = 1;
        this.pan = { x: 0, y: 0 };
        this.isDragging = false;
        this.lastMousePosition = { x: 0, y: 0 };
        
        // Elements
        this.container = document.getElementById(this.options.containerId);
        this.controls = document.getElementById(this.options.controlsId);
        
        // Ensure container exists
        if (!this.container) {
            console.error(`DICOM container with ID "${this.options.containerId}" not found`);
            return;
        }
        
        // Initialize the viewer
        this.init();
    }
    
    /**
     * Initialize the viewer components
     */
    init() {
        // Create canvas element for rendering
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'dicom-canvas';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.cursor = 'grab';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        
        // Loading indicator
        this.loadingIndicator = document.createElement('div');
        this.loadingIndicator.className = 'dicom-loading';
        this.loadingIndicator.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading DICOM images...</p>
        `;
        this.loadingIndicator.style.display = 'none';
        this.container.appendChild(this.loadingIndicator);
        
        // Error message
        this.errorMessage = document.createElement('div');
        this.errorMessage.className = 'dicom-error';
        this.errorMessage.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-circle me-2"></i>
                <span class="error-text">Error loading DICOM images</span>
            </div>
        `;
        this.errorMessage.style.display = 'none';
        this.container.appendChild(this.errorMessage);
        
        // Update the controls if they exist
        this.updateControls();
        
        // Bind event listeners
        this.bindEvents();
        
        // Show placeholder message
        this.showPlaceholder();
    }
    
    /**
     * Bind event listeners for interaction
     */
    bindEvents() {
        // Mouse events for pan/zoom
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.canvas.addEventListener('mouseleave', this.handleMouseUp.bind(this));
        this.canvas.addEventListener('wheel', this.handleWheel.bind(this));
        
        // Touch events for mobile
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this));
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this));
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this));
        
        // Control buttons
        if (this.controls) {
            const prevButton = this.controls.querySelector('#prevImage');
            const nextButton = this.controls.querySelector('#nextImage');
            const zoomInButton = this.controls.querySelector('#zoomIn');
            const zoomOutButton = this.controls.querySelector('#zoomOut');
            const resetButton = this.controls.querySelector('#resetView');
            
            if (prevButton) prevButton.addEventListener('click', this.prevImage.bind(this));
            if (nextButton) nextButton.addEventListener('click', this.nextImage.bind(this));
            if (zoomInButton) zoomInButton.addEventListener('click', this.zoomIn.bind(this));
            if (zoomOutButton) zoomOutButton.addEventListener('click', this.zoomOut.bind(this));
            if (resetButton) resetButton.addEventListener('click', this.resetView.bind(this));
        }
        
        // Window resize event
        window.addEventListener('resize', this.handleResize.bind(this));
    }
    
    /**
     * Show a placeholder when no images are loaded
     */
    showPlaceholder() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = '#f8f9fa';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = '#adb5bd';
        this.ctx.font = '16px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText('No DICOM images loaded', this.canvas.width / 2, this.canvas.height / 2);
    }
    
    /**
     * Load DICOM images from a series
     * @param {string} patientId - Patient ID
     * @param {string} studyId - Study ID
     * @param {string} seriesName - Series name
     */
    loadSeries(patientId, studyId, seriesName) {
        this.isLoading = true;
        this.images = [];
        this.currentIndex = 0;
        this.zoom = 1;
        this.pan = { x: 0, y: 0 };
        
        // Show loading indicator
        this.loadingIndicator.style.display = 'flex';
        this.errorMessage.style.display = 'none';
        
        // Reset canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Fetch list of DICOM files for the series
        fetch(`/api/dicom-files/${patientId}/${studyId}/${seriesName}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch DICOM file list');
                }
                return response.json();
            })
            .then(data => {
                const dicomFiles = data.files || [];
                
                if (dicomFiles.length === 0) {
                    throw new Error('No DICOM files found in series');
                }
                
                // Preload all images
                const imagePromises = dicomFiles.map(file => {
                    return new Promise((resolve, reject) => {
                        const img = new Image();
                        img.onload = () => resolve(img);
                        img.onerror = () => reject(new Error(`Failed to load image: ${file}`));
                        img.src = `/dicom/${patientId}/${studyId}/${seriesName}/${file}`;
                    });
                });
                
                return Promise.all(imagePromises);
            })
            .then(loadedImages => {
                this.images = loadedImages;
                this.isLoading = false;
                this.loadingIndicator.style.display = 'none';
                
                // Update controls
                this.updateControls();
                
                // Render first image
                this.renderCurrentImage();
                
                // Call onLoad callback if provided
                if (typeof this.options.onLoad === 'function') {
                    this.options.onLoad(this.images.length);
                }
            })
            .catch(error => {
                console.error('Error loading DICOM series:', error);
                this.isLoading = false;
                this.loadingIndicator.style.display = 'none';
                this.errorMessage.style.display = 'block';
                this.errorMessage.querySelector('.error-text').textContent = error.message;
            });
    }
    
    /**
     * Update the controls UI
     */
    updateControls() {
        if (!this.controls) return;
        
        const currentImageNum = this.controls.querySelector('#currentImageNum');
        const totalImageNum = this.controls.querySelector('#totalImageNum');
        const prevButton = this.controls.querySelector('#prevImage');
        const nextButton = this.controls.querySelector('#nextImage');
        
        if (currentImageNum) currentImageNum.textContent = this.images.length > 0 ? this.currentIndex + 1 : 0;
        if (totalImageNum) totalImageNum.textContent = this.images.length;
        
        if (prevButton) prevButton.disabled = this.images.length === 0 || this.currentIndex === 0;
        if (nextButton) nextButton.disabled = this.images.length === 0 || this.currentIndex === this.images.length - 1;
    }
    
    /**
     * Render the current image with zoom and pan
     */
    renderCurrentImage() {
        if (this.images.length === 0 || this.currentIndex < 0 || this.currentIndex >= this.images.length) {
            this.showPlaceholder();
            return;
        }
        
        const img = this.images[this.currentIndex];
        
        // Resize canvas to match container
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Calculate scaled dimensions
        const scale = Math.min(
            this.canvas.width / img.width,
            this.canvas.height / img.height
        );
        
        const scaledWidth = img.width * scale * this.zoom;
        const scaledHeight = img.height * scale * this.zoom;
        
        // Calculate centered position with pan
        const x = (this.canvas.width - scaledWidth) / 2 + this.pan.x;
        const y = (this.canvas.height - scaledHeight) / 2 + this.pan.y;
        
        // Draw image
        this.ctx.drawImage(img, x, y, scaledWidth, scaledHeight);
        
        // Update controls
        this.updateControls();
        
        // Call onImageChange callback if provided
        if (typeof this.options.onImageChange === 'function') {
            this.options.onImageChange(this.currentIndex, this.images.length);
        }
    }
    
    /**
     * Go to the next image
     */
    nextImage() {
        if (this.currentIndex < this.images.length - 1) {
            this.currentIndex++;
            this.renderCurrentImage();
        }
    }
    
    /**
     * Go to the previous image
     */
    prevImage() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.renderCurrentImage();
        }
    }
    
    /**
     * Zoom in
     */
    zoomIn() {
        if (this.zoom < this.options.maxZoom) {
            this.zoom = Math.min(this.options.maxZoom, this.zoom + this.options.zoomStep);
            this.renderCurrentImage();
        }
    }
    
    /**
     * Zoom out
     */
    zoomOut() {
        if (this.zoom > this.options.minZoom) {
            this.zoom = Math.max(this.options.minZoom, this.zoom - this.options.zoomStep);
            this.renderCurrentImage();
        }
    }
    
    /**
     * Reset zoom and pan
     */
    resetView() {
        this.zoom = 1;
        this.pan = { x: 0, y: 0 };
        this.renderCurrentImage();
    }
    
    /**
     * Handle mouse down event for panning
     */
    handleMouseDown(event) {
        if (this.images.length === 0) return;
        
        this.isDragging = true;
        this.canvas.style.cursor = 'grabbing';
        this.lastMousePosition = {
            x: event.clientX,
            y: event.clientY
        };
    }
    
    /**
     * Handle mouse move event for panning
     */
    handleMouseMove(event) {
        if (!this.isDragging) return;
        
        const deltaX = event.clientX - this.lastMousePosition.x;
        const deltaY = event.clientY - this.lastMousePosition.y;
        
        this.pan.x += deltaX;
        this.pan.y += deltaY;
        
        this.lastMousePosition = {
            x: event.clientX,
            y: event.clientY
        };
        
        this.renderCurrentImage();
    }
    
    /**
     * Handle mouse up event for panning
     */
    handleMouseUp() {
        this.isDragging = false;
        this.canvas.style.cursor = 'grab';
    }
    
    /**
     * Handle mouse wheel event for zooming
     */
    handleWheel(event) {
        event.preventDefault();
        
        if (this.images.length === 0) return;
        
        // Zoom in or out based on wheel direction
        if (event.deltaY < 0) {
            this.zoomIn();
        } else {
            this.zoomOut();
        }
    }
    
    /**
     * Handle touch start event for mobile
     */
    handleTouchStart(event) {
        if (this.images.length === 0 || event.touches.length !== 1) return;
        
        this.isDragging = true;
        this.lastMousePosition = {
            x: event.touches[0].clientX,
            y: event.touches[0].clientY
        };
    }
    
    /**
     * Handle touch move event for mobile
     */
    handleTouchMove(event) {
        if (!this.isDragging || event.touches.length !== 1) return;
        
        event.preventDefault();
        
        const deltaX = event.touches[0].clientX - this.lastMousePosition.x;
        const deltaY = event.touches[0].clientY - this.lastMousePosition.y;
        
        this.pan.x += deltaX;
        this.pan.y += deltaY;
        
        this.lastMousePosition = {
            x: event.touches[0].clientX,
            y: event.touches[0].clientY
        };
        
        this.renderCurrentImage();
    }
    
    /**
     * Handle touch end event for mobile
     */
    handleTouchEnd() {
        this.isDragging = false;
    }
    
    /**
     * Handle window resize event
     */
    handleResize() {
        this.renderCurrentImage();
    }
}

// Make DicomViewer available globally
window.DicomViewer = DicomViewer;