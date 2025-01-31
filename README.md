# The HEV: Head, Eye, and Voice Control Interface

This Python application allows users to control their computer using head movements, eye blinks, and voice commands, and optionally, an on-screen virtual keyboard. It leverages facial landmark detection, speech recognition, and system control libraries to provide a hands-free interaction method. The application is composed of four main Python files: `main.py`, `facecontroller.py`, `voicecontroller.py`, and `virtualkeyboard.py`.  `main.py` orchestrates the interaction between the face, voice, and virtual keyboard controllers. `facecontroller.py` handles head and eye tracking for mouse control, `voicecontroller.py` manages speech recognition and execution of voice commands, and `virtualkeyboard.py` provides an on-screen keyboard controlled by head and eye movements.

## Features

- **Head-controlled mouse:** Move the cursor by tracking head movements.  The sensitivity of this control can be adjusted dynamically.
- **Nod-to-scroll:** Scroll up or down by nodding your head. The scrolling speed is configurable.
- **Blink-to-click:** Perform left or right clicks by blinking your eyes.  The blink detection threshold is adjustable.
- **Voice commands:** Execute various actions using voice commands (e.g., clicking, scrolling, opening applications). A comprehensive list of supported commands is provided below.
- **On-screen virtual keyboard:**  An optional on-screen keyboard allows for text input using head and eye movements.
- **Dynamic threshold adjustments:** Adjust sensitivity and thresholds for head movement, blinking, and virtual keyboard using keyboard shortcuts (detailed below).
- **Configuration saving:** Settings are saved to a JSON file (`face_controller_config.json`) and loaded on startup. This ensures persistent settings between sessions.
- **Error Handling:** Robust error handling is implemented throughout the application to gracefully manage unexpected issues, such as webcam or microphone unavailability.
- **Multithreading:** The application utilizes multithreading to handle face tracking, voice recognition, keyboard input, and virtual keyboard concurrently, improving responsiveness and preventing blocking operations.  This allows for smooth and efficient operation.


## Dependencies

Before running the application, ensure you have the following libraries installed. You can install them using pip:

```bash
pip install opencv-python mediapipe pyautogui SpeechRecognition pynput
```

**Detailed breakdown of dependencies:**

- **opencv-python:** For capturing and processing video from the webcam.
- **mediapipe:** For detecting facial landmarks.
- **pyautogui:** For controlling the mouse and keyboard.
- **SpeechRecognition:** For converting speech to text.
- **pynput:** For capturing keyboard events to adjust settings.

## Installation

1. **Clone the repository (if applicable):**

   ```bash
   git clone [repository_url]
   cd [repository_directory]
   ```

2. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   (Alternatively, install them individually as mentioned in the Dependencies section.)

3. **Setup the project (Optional):**  The provided setup scripts (`setup.sh`, `setup.bat`, `setup.ps1`) are optional and aim to simplify environment setup.  If you prefer a different virtual environment management approach, you can skip this step.

   - **For Linux users:** Run the `setup.sh` script in the project's root directory:
     ```bash
     ./setup.sh
     ```
     This script will create a virtual environment and install the necessary dependencies. Refer to the `setup.sh` file for more details.

   - **For Windows users using Command Prompt:** Run the `setup.bat` script in the project's root directory:

     ```bash
     setup.bat
     ```
     This script will create a virtual environment and install the necessary dependencies. Refer to the `setup.bat` file for more details.

   - **For Windows users using PowerShell:** Run the `setup.ps1` script in the project's root directory:

     ```powershell
     .\setup.ps1
     ```
     This script will create a virtual environment and install the necessary dependencies. Refer to the `setup.ps1` file for more details.


## Usage

1. **Run the application:**

   ```bash
   python main.py
   ```

2. **Head Control:**
   - Move your head to move the mouse cursor on the screen.
   - Nod your head up or down to scroll the active window.

3. **Eye Blink Control:**
   - Single blink: Performs a left mouse click.
   - Double blink: Performs a right mouse click.

4. **Voice Commands:**
   - Speak the defined commands to perform actions.  The voice recognition system will listen continuously until you say "stop listening" or press the Escape key. A list of available commands is provided below.

5. **Virtual Keyboard:**
    - Builtin virtual keyboard to open and close by opening and closing mouth.

6. **Adjusting Settings:**
   - You can dynamically adjust the sensitivity and thresholds using the following keyboard shortcuts\
   \
    **Turn on/off *CAPSLOCK* key first to change the threshold values**
     - **Sensitivity (Head Movement):**
       - `Up Arrow`: Increase sensitivity.
       - `Down Arrow`: Decrease sensitivity.
     - **Blink Threshold:**
       - `Right Arrow`: Increase blink threshold.
       - `Left Arrow`: Decrease blink threshold.
     - **Nod Threshold:**
       - `F1`: Decrease nod threshold.
       - `F2`: Increase nod threshold.
     - **Movement Range (Head Movement):**
       - `F3`: Decrease movement range.
       - `F4`: Increase movement range.
     - **Safe Margin (Head Movement):**
       - `F5`: Decrease safe margin.
       - `F6`: Increase safe margin.
     - **Scroll Amount:**
       - `F7`: Decrease scroll amount.
       - `F8`: Increase scroll amount.
     - **Blink Duration Threshold:**
       - `F9`: Decrease blink duration threshold.
       - `F10`: Increase blink duration threshold.
     - **Click Interval:**
       - `F11`: Decrease click interval.
       - `F12`: Increase click interval.
     - **Smoothing Window Size (Head Movement):**
       - `Page Down`: Decrease smoothing window size.
       - `Page Up`: Increase smoothing window size.
     - **Mouth Open Threshold:**
       - `Ctrl+F1`: Decrease mouth open threshold.
       - `Ctrl+F2`: Increase mouth open threshold.
     - **Mouth Open Duration Threshold:**
       - `Ctrl+F3`: Decrease mouth open duration threshold.
       - `Ctrl+F4`: Increase mouth open duration threshold.
     - **Virtual Keyboard Settings:**  (Specific shortcuts for adjusting virtual keyboard parameters would be listed here if implemented)
     - **Reset to Defaults:**
       - `Ctrl+X`: Resets all settings to their default values.

7. **Stopping the Application:**
   - Press the `Esc` key to stop the application.
   - Say "stop listening" to stop the voice command system.


## Voice Commands

The following voice commands are currently supported:

- **Basic Mouse Actions:**
  - "select" (Left click)
  - "right click"
  - "double click"
  - "triple click"
  - "drag" (Starts dragging; requires a subsequent "drop" command to end dragging)
  - "drop" (Stops dragging)

- **Scrolling:**
  - "scroll up"
  - "scroll down"
  - "page up"
  - "page down"

- **Window Management:**
  - "minimize"
  - "maximize"
  - "close window"
  - "switch window" (switches to the next window)
  - "new window" (opens a new window for the default browser)

- **System Controls:**
  - "volume up"
  - "volume down"
  - "mute"
  - "play pause"
  - "keyboard" (Opens the on-screen keyboard, if available)

- **Navigation (Browser Actions):**
  - "go back"
  - "go forward"
  - "refresh"

- **Text Editing:**
  - "select all"
  - "copy"
  - "paste"
  - "cut"
  - "undo"
  - "redo"

- **Cursor Movement (Small Increments):**
  - "move left"
  - "move right"
  - "move up"
  - "move down"

- **Typing Individual Letters (lowercase and uppercase):**
  - "small a", "small b", "small c", ..., "small z"
  - "capital A", "capital B", "capital C", ..., "capital Z"


## Configuration

The application's configuration, including sensitivity, thresholds, and other parameters, is stored in a file named `face_controller_config.json`. This file is created automatically when the application is run for the first time. You can manually edit this file to adjust the settings, or use the keyboard shortcuts while the application is running. The configuration file is used to persist settings between application runs.


## Troubleshooting

- **Ensure proper lighting conditions:** Good lighting is crucial for accurate facial landmark detection.
- **Webcam access:** Make sure the application has permission to access your webcam.
- **Microphone access:** Ensure the application has permission to access your microphone for voice commands.
- **Background noise:** For better voice command recognition, try to minimize background noise.
- **Performance:** If you experience performance issues, try closing other applications that might be using your webcam or CPU heavily.

