from flask import Flask, render_template, Response, jsonify, request
import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import math

app = Flask(__name__)


CAMERA_ID = 0 
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
PINCH_THRESHOLD_LOW = 20   
PINCH_THRESHOLD_HIGH = 180 


project_state = {
    "is_running": False,
    "current_gesture": "Inactive", 
    "current_volume": 0,
    "finger_distance_mm": 0, 
    "accuracy": 0.0,
    "response_time_ms": 0
}


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


def calculate_distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def map_value(value, in_min, in_max, out_min, out_max):
    return np.interp(value, [in_min, in_max], [out_min, out_max])

def is_finger_folded(landmarks, tip_idx, pip_idx, wrist_idx=0):
    wrist = landmarks[wrist_idx]
    tip = landmarks[tip_idx]
    pip = landmarks[pip_idx]
    
    d_tip_wrist = math.sqrt((tip.x - wrist.x)**2 + (tip.y - wrist.y)**2)
    d_pip_wrist = math.sqrt((pip.x - wrist.x)**2 + (pip.y - wrist.y)**2)
    
    return d_tip_wrist < d_pip_wrist

def determine_gesture_robust(landmarks, pinch_dist_px):
   
    index_folded = is_finger_folded(landmarks, 8, 6)
    middle_folded = is_finger_folded(landmarks, 12, 10)
    ring_folded = is_finger_folded(landmarks, 16, 14)
    pinky_folded = is_finger_folded(landmarks, 20, 18)

   
    back_fingers_folded = 0
    if middle_folded: back_fingers_folded += 1
    if ring_folded: back_fingers_folded += 1
    if pinky_folded: back_fingers_folded += 1

    
    if back_fingers_folded >= 2: 
        if index_folded:
            return "Closed"  
        else:
            return "Pinch"   
    
   
    if pinch_dist_px < 30:
        return "Pinch"

    
    return "Open Hand"


def generate_frames():
    vol_history = []
    
    while True:
        start_time = time.time()
        success, frame = cap.read()
        if not success:
            break

        if not project_state["is_running"]:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            continue

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


                thumb_tip = hand_landmarks.landmark[4]
                index_tip = hand_landmarks.landmark[8]
                
                tx, ty = int(thumb_tip.x * w), int(thumb_tip.y * h)
                ix, iy = int(index_tip.x * w), int(index_tip.y * h)


                pinch_dist_px = calculate_distance((tx, ty), (ix, iy))
                

                gesture_detected = determine_gesture_robust(hand_landmarks.landmark, pinch_dist_px)
                

                project_state["current_gesture"] = gesture_detected
                project_state["finger_distance_mm"] = int(pinch_dist_px * 0.25)
                project_state["accuracy"] = round(accuracy_score * 100, 1)

                if gesture_detected == "Pinch":

                    cv2.line(frame, (tx, ty), (ix, iy), (50, 50, 255), 3) 
                    cv2.circle(frame, (tx, ty), 10, (50, 50, 255), cv2.FILLED)
                    cv2.circle(frame, (ix, iy), 10, (255, 50, 50), cv2.FILLED)



                    vol = map_value(pinch_dist_px, PINCH_THRESHOLD_LOW, PINCH_THRESHOLD_HIGH, 0, 100)
                    vol = int(np.clip(vol, 0, 100))
                    

                    vol_history.append(vol)
                    if len(vol_history) > 5: vol_history.pop(0)
                    smooth_vol = int(np.mean(vol_history))
                    
                    project_state["current_volume"] = smooth_vol
                    

                    print(f"Dist: {int(pinch_dist_px)} | Vol: {smooth_vol}")




                    try:
                        
                        pass 
                    except Exception as e:
                        pass


                    mid_x, mid_y = (tx+ix)//2, (ty+iy)//2
                    cv2.putText(frame, f"{smooth_vol}%", (mid_x, mid_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 50, 255), 2)

                elif gesture_detected == "Closed":
                     cx, cy = int(hand_landmarks.landmark[9].x * w), int(hand_landmarks.landmark[9].y * h)
                     cv2.circle(frame, (cx, cy), 30, (0, 0, 255), 2)
                     cv2.putText(frame, "CLOSED", (cx-30, cy-40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                elif gesture_detected == "Open Hand":
                     mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)


                if accuracy_score > 0.8:
                    cv2.rectangle(frame, (w - 170, 20), (w - 20, 60), (80, 172, 55), -1)
                    cv2.putText(frame, "Good Detection", (w - 160, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        else:
             project_state["current_gesture"] = "Inactive"

        end_time = time.time()
        project_state["response_time_ms"] = int((end_time - start_time) * 1000)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_data')
def get_data():
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
    app.run(debug=True, threaded=True, port=5000)