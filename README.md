# Virtual Mouse

Virtual Mouse is a real-time Python project that turns a standard webcam into a gesture-driven mouse controller. It combines MediaPipe hand tracking and face tracking, OpenCV video processing, PyAutoGUI desktop control, and SQLite profile storage so different users can be recognized and load their own sensitivity settings automatically.

## Features

### Hand tracking
- Cursor movement using index finger movement
- Left click with thumb-index pinch
- Right click with thumb-middle pinch
- Double click with index-middle close gesture while thumb stays open
- Drag and text selection using a long thumb-index pinch hold and release
- Scroll up with index and middle fingers raised
- Scroll down with a closed index-middle posture plus raised ring and pinky fingers
- Swipe left and swipe right using open palm motion
- Copy gesture using thumb, index, middle, and pinky raised while ring finger stays down
- Pause and resume gesture control with a closed fist

### Face tracking
- Cursor movement using nose position
- Left click with left-eye wink
- Right click with right-eye wink
- Hand/face mode switch using both eyes closed briefly
- Scroll up by tilting the head upward
- Scroll down by tilting the head downward
- Drag start with mouth open
- Drag stop with mouth close

### Personalization
- SQLite database for profiles and sensitivity settings
- Saved face images per profile
- Automatic face scan on startup
- Face-image matching and automatic settings load
- Dead-zone filtering and cursor smoothing for both hand and face control

## Project structure

- `main.py`: application startup, webcam loop, UI integration, profile auto-load
- `mouse_controller.py`: PyAutoGUI mouse and keyboard actions, dead zone, smoothing
- `hand_trackedr.py`: MediaPipe Hands tracking and hand gesture measurements
- `face_tracker.py`: MediaPipe Face Mesh tracking and facial gesture measurements
- `face_auth.py`: face embedding extraction, profile comparison, face image saving
- `gesture_engine.py`: gesture interpretation, mode switching, debounce logic
- `gesture_utils.py`: geometry utilities and core algorithms
- `control_panel.py`: external Tkinter control panel window
- `profile_manager.py`: profile save/load workflow
- `database.py`: SQLite schema and persistence
- `config.py`: shared configuration and sensitivity models

## Algorithms used

- Hand landmark detection with MediaPipe Hands
- Face landmark detection with MediaPipe Face Mesh
- Pinch-distance gesture detection using normalized fingertip distances
- Finger up/down state detection using tip and joint landmark comparison
- Eye aspect ratio for wink detection
- Mouth opening ratio for drag control
- Nose-position cursor control
- Head-tilt ratio for scrolling
- Dead-zone filtering to reduce jitter
- Exponential cursor smoothing
- Cooldown-based gesture debouncing
- Face-image matching using normalized landmark geometry plus grayscale appearance embedding

## Installation

1. Install Python 3.12 or later.
2. Install the dependencies:

```bash
pip install opencv-python mediapipe pyautogui numpy
```

3. Run the application:

```bash
python main.py
```

## Controls and UI

The project opens two windows:

- A camera window that shows the live webcam feed, hand/face landmarks, mode, profile, and current status
- A separate external control panel with:
  - Mode switch button
  - Save profile button
  - Sensitivity increase/decrease buttons
  - Status, mode, and active profile display

## Notes

- The first run uses default sensitivity values until a face profile is saved.
- Press `q` or `Esc` in the camera window to quit.
- Gesture thresholds may need small tuning depending on webcam angle, lighting, and user distance.
- MediaPipe and PyAutoGUI should be installed in the same Python environment used to run the app.
