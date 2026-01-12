Here is a comprehensive `README.md` file tailored to the code you provided. It covers installation, usage, features, and the project structure.

---

# 🖐️ AI Gesture Volume Control

A computer vision application that allows you to control your system's master volume using hand gestures. Built with Python, OpenCV, MediaPipe, and Flask, this project features a modern web interface with real-time feedback and a Windows 11-style volume overlay.

## 🚀 Features

* **Real-time Hand Tracking:** Uses MediaPipe to detect hand landmarks with high accuracy.
* **Gesture Recognition:**
* 👌 **Pinch (Index + Thumb):** Adjust volume linearly based on the distance between fingers.
* 👊 **Closed Fist:** Instantly mutes the system audio.
* ✋ **Open Hand:** Idle mode (tracking active, no volume changes).


* **System Integration:** Uses `PyAutoGUI` to simulate actual media key presses on your operating system.
* **Interactive Web UI:**
* Live video feed.
* Real-time metrics (Volume %, Distance in mm, Accuracy score, Latency).
* Visual feedback cards indicating the current active gesture.
* Custom CSS "Windows 11" style volume slider overlay.



## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Computer Vision:** OpenCV (`cv2`), MediaPipe
* **Automation:** PyAutoGUI
* **Frontend:** HTML5, CSS3, JavaScript
* **Math/Data:** NumPy

## 📂 Project Structure

```text
├── app.py                  # Main Flask application and computer vision logic
├── requirements.txt        # Python dependencies
├── static/
│   ├── script.js           # Frontend logic (polling data, UI updates)
│   └── style.css           # Styling for the web interface
└── templates/
    └── index.html          # Main dashboard HTML structure

```

## ⚙️ Installation

1. **Clone the repository** (or download the files):
```bash
git clone <your-repo-url>
cd volumecontrolwithfingers

```


2. **Set up a Virtual Environment (Recommended):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

```


3. **Install Dependencies:**
```bash
pip install -r requirements.txt

```


*Note: If you have issues with the provided `requirements.txt` being too large, you can install the core packages manually:*
```bash
pip install flask opencv-python mediapipe numpy pyautogui

```



## 🖥️ Usage

1. **Run the Application:**
```bash
python app.py

```


2. **Open the Web Interface:**
Open your web browser and navigate to:
`http://127.0.0.1:5000/`
3. **Start Control:**
* Click the **Start** button on the web page to activate the camera.
* Allow the browser permission to access the camera if prompted (though the app uses the server-side camera).


4. **Control Volume:**
* Ensure your hand is clearly visible in the camera frame.
* **To Change Volume:** Fold your middle, ring, and pinky fingers. Bring your **Thumb** and **Index** finger close together (low volume) or move them apart (high volume).
* **To Mute:** Clench your hand into a fist (all fingers folded).



## ⚠️ Troubleshooting & Notes

* **Lighting:** Ensure you are in a well-lit environment. Poor lighting can affect MediaPipe's ability to track hand landmarks.
* **Camera ID:** The code uses `CAMERA_ID = 0` by default. If you have multiple cameras and the wrong one opens, change this value in `app.py`.
* **Permissions:** `PyAutoGUI` requires permission to control your mouse/keyboard.
* **Mac Users:** You may need to grant Terminal/VSCode "Accessibility" permissions in *System Preferences > Security & Privacy*.
* **Latency:** The interface updates metrics every 50ms for a smooth experience.
