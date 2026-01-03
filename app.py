from flask import Flask, render_template, Response, jsonify, request
import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import math

app = Flask(__name__)

# --- Configuration ---
CAMERA_ID = 0 # Default webcam
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
PINCH_THRESHOLD_LOW = 30  # Pixel distance for max pinch (volume 0)
PINCH_THRESHOLD_HIGH = 150 # Pixel distance for min pinch (volume 100)

# --- Global State Variables ---
project_state = {
    "is_running": False,
    "current_gesture": "Inactive", # "Open Hand", "Pinch", "Closed"
    "current_volume": 0,
    "finger_distance_mm": 0, # Approximation based on pixels
    "accuracy": 0.0,
    "response_time_ms": 0
}

# --- MediaPipe Setup ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)

cap = cv2.VideoCapture(CAMERA_ID)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# --- Helper Functions ---
def calculate_distance(p1, p2):
    """Calculates Euclidean distance between two 2D points."""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def map_value(value, in_min, in_max, out_min, out_max):
    """Maps a value from one range to another linearly."""
    return np.interp(value, [in_min, in_max], [out_min, out_max])

def determine_gesture(landmarks, dist_pixels):
    """Determines the basic gesture based on landmarks and pinch distance."""
    # Thumb tip: 4, Index tip: 8, Middle tip: 12, Ring tip: 16, Pinky tip: 20
    # Pseudo-logic for open/closed vs pinch
    
    # Check if fingers are folded (tips below middle joints)
    # Joint indices: Index(6), Middle(10), Ring(14), Pinky(18)
    fingers_folded = []
    for tip, joint in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        if landmarks[tip].y > landmarks[joint].y: # y increases downwards
            fingers_folded.append(True)
        else:
            fingers_folded.append(False)

    if all(fingers_folded):
        return "Closed"
    elif dist_pixels < PINCH_THRESHOLD_HIGH and not all(fingers_folded):
         # If distance is small and not a fist, it's likely a pinch preparation or active pinch
        return "Pinch"
    else:
        return "Open Hand"

# --- Main Processing Loop ---
def generate_frames():
    while True:
        start_time = time.time()
        success, frame = cap.read()
        if not success:
            break

        if not project_state["is_running"]:
             # If paused, just show the static frame without processing
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            continue

        # 1. Image Processing
        # Flip horizontally for a mirror view
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        h, w, c = frame.shape
        gesture_detected = "Inactive"
        pinch_dist_px = 0
        accuracy_score = 0

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                accuracy_score = handedness.classification[0].score

                # Get key landmarks coordinates
                thumb_tip = hand_landmarks.landmark[4]
                index_tip = hand_landmarks.landmark[8]
                
                tx, ty = int(thumb_tip.x * w), int(thumb_tip.y * h)
                ix, iy = int(index_tip.x * w), int(index_tip.y * h)

                # 2. Calculate Distance & Gesture
                pinch_dist_px = calculate_distance((tx, ty), (ix, iy))
                gesture_detected = determine_gesture(hand_landmarks.landmark, pinch_dist_px)
                
                # Update global state
                project_state["current_gesture"] = gesture_detected
                # Approx conversion px to mm (highly dependent on camera/distance)
                project_state["finger_distance_mm"] = int(pinch_dist_px * 0.25) 
                project_state["accuracy"] = round(accuracy_score * 100, 1)

                # 3. Volume Control & Drawing Visuals
                if gesture_detected == "Pinch":
                    # Draw line between finger and thumb
                    cv2.line(frame, (tx, ty), (ix, iy), (50, 50, 255), 3) # Red line
                    cv2.circle(frame, (tx, ty), 8, (50, 50, 255), cv2.FILLED)
                    cv2.circle(frame, (ix, iy), 8, (255, 50, 50), cv2.FILLED) # Blue dot on index

                    # Map distance to volume range (0-100)
                    # Invert mapping: smaller distance = higher volume
                    vol = map_value(pinch_dist_px, PINCH_THRESHOLD_LOW, PINCH_THRESHOLD_HIGH, 100, 0)
                    vol = int(np.clip(vol, 0, 100))
                    project_state["current_volume"] = vol
                    
                    # Control system volume (using a try-except block for safety)
                    try:
                        # PyAutoGUI volume control is platform-specific and can be tricky. 
                        # This is a generic approach for Windows/Linux.
                        # It presses the volume up/down keys relative to current position.
                        # A more robust cross-platform solution exists but is complex.
                        # For demonstration, we'll assume the calculated 'vol' is the target percentage.
                        # Note: Direct percentage setting isn't natively supported by simple pyautogui press.
                        # We will simulate pressing keys based on change direction for smoother control in a real app.
                        # For this demo, we just update the UI variable.
                        pass 
                        # To actually change volume (Windows example - careful, can be loud):
                        # current_sys_vol = ... # need external library to get actual system volume
                        # if vol > current_sys_vol: pyautogui.press('volumeup')
                        # elif vol < current_sys_vol: pyautogui.press('volumedown')
                    except Exception as e:
                        print(f"Volume control error: {e}")

                    # Draw "Pinch Gesture" label on top left
                    cv2.rectangle(frame, (20, 20), (160, 60), (16, 112, 235), -1) # Orange box
                    cv2.putText(frame, "Pinch Gesture", (30, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                elif gesture_detected == "Open Hand" or gesture_detected == "Closed":
                     # Draw standard landmarks for non-pinch gestures
                     mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Draw "Good Detection" green badge
                if accuracy_score > 0.8:
                    cv2.rectangle(frame, (w - 170, 20), (w - 20, 60), (80, 172, 55), -1) # Green box
                    cv2.putText(frame, "Good Detection", (w - 160, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Calculate response time
        end_time = time.time()
        project_state["response_time_ms"] = int((end_time - start_time) * 1000)

        # Encode frame for web streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_data')
def get_data():
    """API endpoint for frontend to fetch current state."""
    return jsonify(project_state)

@app.route('/start', methods=['POST'])
def start():
    project_state["is_running"] = True
    return jsonify({"status": "started"})

@app.route('/pause', methods=['POST'])
def pause():
    project_state["is_running"] = False
    project_state["current_gesture"] = "Inactive"
    return jsonify({"status": "paused"})

if __name__ == '__main__':
    # threaded=True is important for smooth streaming alongside API calls
    app.run(debug=True, threaded=True, port=5000)