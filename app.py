from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import io
from PIL import Image
import os
import time
import mediapipe as mp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Create upload folder if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize MediaPipe pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('test_connection')
def handle_test_connection(data):
    """
    Handle test connection requests from the client
    This verifies that the Python backend is receiving and processing messages
    """
    print("Test connection request received:", data)
    
    try:
        # Test if MediaPipe is available
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        test_img[:] = (255, 255, 255)  # White image
        results = pose.process(cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB))
        
        # Return success response
        emit('python_test_response', {
            'status': 'success',
            'message': 'Python backend with MediaPipe is working correctly',
            'timestamp': time.time()
        })
    except Exception as e:
        # Return error if something went wrong
        print(f"Error in test connection: {e}")
        emit('python_test_response', {
            'status': 'error',
            'message': str(e),
            'timestamp': time.time()
        })

@socketio.on('image')
def handle_image(data):
    """
    Handle incoming image frames from the client
    Process them with MediaPipe and send back the measurements
    """
    # Get the image data
    image_data = data.get('image')
    
    # Remove the data URL prefix
    if 'base64,' in image_data:
        image_data = image_data.split('base64,')[1]
    
    # Decode the base64 string
    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert PIL Image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Process the image with MediaPipe
        processed_image, measurements = process_image_with_mediapipe(cv_image)
        
        # Convert processed image back to base64 for sending
        _, buffer = cv2.imencode('.jpg', processed_image)
        processed_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Send back the processed image and measurements
        emit('processed_image', {
            'image': f'data:image/jpeg;base64,{processed_base64}',
            'measurements': measurements
        })
        
    except Exception as e:
        print(f"Error processing image: {e}")
        emit('error', {'message': str(e)})

def process_image_with_mediapipe(image):
    """
    Process the image using MediaPipe Pose to detect body landmarks
    Calculate body measurements based on these landmarks
    """
    # Convert to RGB for MediaPipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Process the image with MediaPipe Pose
    results = pose.process(image_rgb)
    
    # Create a copy of the image to draw on
    annotated_image = image.copy()
    
    # Dictionary to store measurements
    measurements = {
        'chest': 'Not detected',
        'waist': 'Not detected',
        'hip': 'Not detected',
        'timestamp': time.time()
    }
    
    # Process landmarks if detected
    if results.pose_landmarks:
        # Draw the pose landmarks on the image
        mp_drawing.draw_landmarks(
            annotated_image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        # Get image dimensions for scaling
        height, width, _ = image.shape
        
        # Extract landmarks
        landmarks = results.pose_landmarks.landmark
        
        # Calculate chest width (between shoulders)
        if hasattr(mp_pose.PoseLandmark, 'LEFT_SHOULDER') and hasattr(mp_pose.PoseLandmark, 'RIGHT_SHOULDER'):
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            
            if left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5:
                shoulder_distance = calculate_distance(
                    (left_shoulder.x * width, left_shoulder.y * height),
                    (right_shoulder.x * width, right_shoulder.y * height)
                )
                # Approximate chest measurement (typically chest is wider than shoulder distance)
                chest_measurement = shoulder_distance * 1.2  # Scaling factor
                measurements['chest'] = f"{chest_measurement:.1f} cm"
                
                # Draw measurement line
                cv2.line(annotated_image, 
                         (int(left_shoulder.x * width), int(left_shoulder.y * height)),
                         (int(right_shoulder.x * width), int(right_shoulder.y * height)),
                         (0, 255, 0), 2)
                cv2.putText(annotated_image, f"Chest: {chest_measurement:.1f} cm", 
                           (int(width/2 - 50), int(left_shoulder.y * height) - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Calculate waist width
        if hasattr(mp_pose.PoseLandmark, 'LEFT_HIP') and hasattr(mp_pose.PoseLandmark, 'RIGHT_HIP'):
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
            
            if left_hip.visibility > 0.5 and right_hip.visibility > 0.5:
                hip_distance = calculate_distance(
                    (left_hip.x * width, left_hip.y * height),
                    (right_hip.x * width, right_hip.y * height)
                )
                # Waist is typically above the hips
                waist_y = (left_hip.y + right_hip.y) * height / 2 - 30  # Approximate waist position
                waist_measurement = hip_distance * 1.05  # Scaling factor
                measurements['waist'] = f"{waist_measurement:.1f} cm"
                
                # Draw measurement line
                waist_left_x = int(left_hip.x * width)
                waist_right_x = int(right_hip.x * width)
                cv2.line(annotated_image, 
                         (waist_left_x, int(waist_y)),
                         (waist_right_x, int(waist_y)),
                         (0, 255, 0), 2)
                cv2.putText(annotated_image, f"Waist: {waist_measurement:.1f} cm", 
                           (int(width/2 - 50), int(waist_y) - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Calculate hip width
        if hasattr(mp_pose.PoseLandmark, 'LEFT_HIP') and hasattr(mp_pose.PoseLandmark, 'RIGHT_HIP'):
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
            
            if left_hip.visibility > 0.5 and right_hip.visibility > 0.5:
                hip_distance = calculate_distance(
                    (left_hip.x * width, left_hip.y * height),
                    (right_hip.x * width, right_hip.y * height)
                )
                hip_measurement = hip_distance * 1.4  # Scaling factor for hip width
                measurements['hip'] = f"{hip_measurement:.1f} cm"
                
                # Draw measurement line
                cv2.line(annotated_image, 
                         (int(left_hip.x * width), int(left_hip.y * height)),
                         (int(right_hip.x * width), int(right_hip.y * height)),
                         (0, 255, 0), 2)
                cv2.putText(annotated_image, f"Hip: {hip_measurement:.1f} cm", 
                           (int(width/2 - 50), int(left_hip.y * height) + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    else:
        # If no pose detected, add text to the image
        cv2.putText(annotated_image, "No person detected", (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    return annotated_image, measurements

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points and convert to cm"""
    # This is a simplified conversion - in a real app you would need proper calibration
    pixels_per_cm = 5  # This is an approximation - would need real calibration
    return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2) / pixels_per_cm

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)