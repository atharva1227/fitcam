// Modal functionality
const modal = document.getElementById('aiCameraModal');
const closeModal = document.querySelector('.close-modal');
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startCameraButton = document.getElementById('startCamera');
const captureButton = document.getElementById('capturePhoto');
const measurementResults = document.getElementById('measurementResults');

function openAICamera() {
    modal.style.display = 'block';
}

closeModal.onclick = function() {
    modal.style.display = 'none';
    stopCamera();
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
        stopCamera();
    }
}

// Camera functionality
let stream = null;

startCameraButton.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
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
    measurementResults.style.display = 'none';
}

captureButton.addEventListener('click', () => {
    // Simulate AI measurement processing
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    // Simulate measurement calculation
    setTimeout(() => {
        // Display random measurements (in a real app, this would be AI-processed)
        document.getElementById('chestSize').textContent = `${Math.floor(90 + Math.random() * 20)} cm`;
        document.getElementById('waistSize').textContent = `${Math.floor(70 + Math.random() * 20)} cm`;
        document.getElementById('hipSize').textContent = `${Math.floor(90 + Math.random() * 20)} cm`;
        
        measurementResults.style.display = 'block';
        stopCamera();
    }, 1500);
});