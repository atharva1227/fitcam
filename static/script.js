const modal = document.getElementById('aiCameraModal');
const closeModal = document.querySelector('.close-modal');
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startCameraButton = document.getElementById('startCamera');
const captureButton = document.getElementById('capturePhoto');
const measurementResults = document.getElementById('measurementResults');

// Socket.io connection
let socket;
let isProcessing = false;
let processingInterval;

function openAICamera() {
    modal.style.display = 'block';
    
    // Initialize socket connection when modal opens
    if (!socket) {
        socket = io();
        
        socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            stopProcessing();
        });
        
        socket.on('processed_image', (data) => {
            // Display the processed image if you want to show it
            // For example, you could create an image element to display it
            // const processedImageElement = document.getElementById('processedImage');
            // processedImageElement.src = data.image;
            
            // Update measurements
            document.getElementById('chestSize').textContent = data.measurements.chest;
            document.getElementById('waistSize').textContent = data.measurements.waist;
            document.getElementById('hipSize').textContent = data.measurements.hip;
            
            // Show measurement results
            measurementResults.style.display = 'block';
            
            // Continue processing is enabled
            isProcessing = false;
        });
        
        socket.on('error', (data) => {
            console.error('Error from server:', data.message);
            isProcessing = false;
        });
    }
}

closeModal.onclick = function() {
    modal.style.display = 'none';
    stopCamera();
    stopProcessing();
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
        stopCamera();
        stopProcessing();
    }
}

// Camera functionality
let stream = null;

startCameraButton.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        });
        video.srcObject = stream;
        startCameraButton.disabled = true;
        captureButton.disabled = false;
    } catch (err) {
        console.error('Error accessing camera:', err);
        alert('Unable to access camera. Please ensure you have granted camera permissions.');
    }
});

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        stream = null;
    }
    startCameraButton.disabled = false;
    captureButton.disabled = true;
}

function stopProcessing() {
    if (processingInterval) {
        clearInterval(processingInterval);
        processingInterval = null;
    }
}

captureButton.addEventListener('click', () => {
    // If we're already in continuous capture mode, stop it
    if (processingInterval) {
        stopProcessing();
        captureButton.textContent = 'Start Real-Time Analysis';
        return;
    }
    
    // Start continuous capture and processing
    captureButton.textContent = 'Stop Real-Time Analysis';
    
    // Create a function to capture and send frames
    const captureAndSend = () => {
        if (!isProcessing && stream) {
            isProcessing = true;
            
            // Capture frame
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            // Convert to base64
            const imageData = canvas.toDataURL('image/jpeg', 0.7); // Lower quality for better performance
            
            // Send to server
            socket.emit('image', { image: imageData });
        }
    };
    
    // Start capturing frames at regular intervals
    processingInterval = setInterval(captureAndSend, 500); // Adjust interval as needed
    
    // Capture the first frame immediately
    captureAndSend();
});









// Update the modal content in the HTML to include a display for the processed image
document.addEventListener('DOMContentLoaded', function() {
    // Create the processed image element if it doesn't exist
    const modalContent = document.querySelector('.modal-content');
    if (modalContent) {
        const cameraPreview = document.getElementById('cameraPreview');
        
        // Check if the processed image container already exists
        let processedImageContainer = document.getElementById('processedImageContainer');
        if (!processedImageContainer) {
            processedImageContainer = document.createElement('div');
            processedImageContainer.id = 'processedImageContainer';
            processedImageContainer.className = 'processed-image-container';
            
            const processedImage = document.createElement('img');
            processedImage.id = 'processedImage';
            processedImage.className = 'processed-image';
            processedImage.style.display = 'none';
            processedImage.style.maxWidth = '100%';
            
            processedImageContainer.appendChild(processedImage);
            
            // Insert the processed image container after the camera preview
            if (cameraPreview && cameraPreview.nextSibling) {
                cameraPreview.parentNode.insertBefore(processedImageContainer, cameraPreview.nextSibling);
            } else if (cameraPreview) {
                cameraPreview.parentNode.appendChild(processedImageContainer);
            }
        }
    }
});

// Modify the processed_image socket event handler to display the image
socket.on('processed_image', (data) => {
    // Update status to actively processing
    updateConnectionStatus('processing');
    
    // Display the processed image
    const processedImageElement = document.getElementById('processedImage');
    if (processedImageElement) {
        processedImageElement.src = data.image;
        processedImageElement.style.display = 'block';
    }
    
    // Update measurements
    document.getElementById('chestSize').textContent = data.measurements.chest;
    document.getElementById('waistSize').textContent = data.measurements.waist;
    document.getElementById('hipSize').textContent = data.measurements.hip;
    
    // Show measurement results
    measurementResults.style.display = 'block';
    
    // Continue processing is enabled
    isProcessing = false;
});

// Update the capture button behavior
captureButton.addEventListener('click', () => {
    // If we're already in continuous capture mode, stop it
    if (processingInterval) {
        stopProcessing();
        captureButton.textContent = 'Start MediaPipe Analysis';
        
        // Hide the processed image and show the video
        const processedImageElement = document.getElementById('processedImage');
        if (processedImageElement) {
            processedImageElement.style.display = 'none';
        }
        video.style.display = 'block';
        
        return;
    }
    
    // Start continuous capture and processing
    captureButton.textContent = 'Stop MediaPipe Analysis';
    
    // Hide video and show processed image
    video.style.display = 'none';
    const processedImageElement = document.getElementById('processedImage');
    if (processedImageElement) {
        processedImageElement.style.display = 'block';
    }
    
    // Create a function to capture and send frames
    const captureAndSend = () => {
        if (!isProcessing && stream) {
            isProcessing = true;
            
            // Capture frame
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            // Convert to base64
            const imageData = canvas.toDataURL('image/jpeg', 0.8); // Adjust quality as needed
            
            // Send to server
            socket.emit('image', { image: imageData });
        }
    };
    
    // Start capturing frames at regular intervals
    processingInterval = setInterval(captureAndSend, 200); // Adjust for smoother capture
    
    // Capture the first frame immediately
    captureAndSend();
});