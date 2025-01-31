import pyautogui
from threading import Thread, Event,Lock
import mediapipe as mp
from contextlib import contextmanager
import time
from pynput import keyboard
import json
import os
import cv2
import logging
import win32api
import win32con
from virtualkeyboard import VirtualKeyboard
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



SENSITIVITY_DEFAULT = 2.7
MOVEMENT_RANGE_DEFAULT = 0.8
NOD_THRESHOLD_DEFAULT = 0.03
BLINK_THRESHOLD_DEFAULT = 0.047
SAFE_MARGIN = 10
SCROLL_AMOUNT = 850
BLINK_DURATION_THRESHOLD_DEFAULT = 0.1
CLICK_INTERVAL_DEFAULT = 0.5
SMOOTHING_WINDOW_SIZE = 1
MOUTH_OPEN_THRESHOLD=0.5
MOUTH_OPEN_DURATION=1.0
class FaceController:
    def __init__(self):
        # Path for the config file
        self.config_path = "face_controller_config.json"
        self.left_eye_closed_start = None
        self.right_eye_closed_start = None
        self.is_dragging = False
        self.drag_start_pos = None
        self.eyes_closed_start_time = None
        self.RIGHT_CLICK_DURATION = 2.0 
        self.drag_cooldown=0.5
        # Default values
        self.default_config = {
            "sensitivity": SENSITIVITY_DEFAULT,
            "movement_range": MOVEMENT_RANGE_DEFAULT,
            "nod_threshold": NOD_THRESHOLD_DEFAULT,
            "blink_threshold": BLINK_THRESHOLD_DEFAULT,
            "safe_margin": SAFE_MARGIN,
            "scroll_amount": SCROLL_AMOUNT,
            "blink_duration_threshold": BLINK_DURATION_THRESHOLD_DEFAULT,
            "left_click_interval": CLICK_INTERVAL_DEFAULT,
            "smoothing_window": SMOOTHING_WINDOW_SIZE,
            "mouth_open_threshold":MOUTH_OPEN_THRESHOLD,
            "mouth_open_duration_threshold":MOUTH_OPEN_DURATION,
            "right_click_duration": 2.0
        }

        # Load saved config or use deaults
        self.load_config()
        self.drag_duration=0.3
        # Initialize other attributes
        self.stop_event = Event()
        self.lock=Lock()
        self.virtual_keyboard=VirtualKeyboard()
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.keyboard_process=None
        self.screen_w, self.screen_h = pyautogui.size()
        self.prev_nose_y = None
        self.scroll_direction = None
        self.face_thread = None
        self.frame_skip = 2
        self.frame_count = 0
        self.last_click_time = time.time()
        self.left_eye_closed = False
        self.right_eye_closed = False
        self.both_eyes_closed = False
        self.blink_start_time = 0
        self.mouth_open_start_time = None
        self.keyboard_opened = False
        self.waiting_for_mouth_close = False  # Track if we're waiting for mouth to close
        self.mouth_cycle_complete = False
        self.eye_distances = {'left': [], 'right': []}

    @contextmanager
    def camera_context(self):
        """Context manager for camera handling."""
        for index in range(2): # Try both CAP_DSHOW and default
           camera = cv2.VideoCapture(0, cv2.CAP_DSHOW if index == 0 else 0)
           if camera.isOpened():
               try:
                   yield camera
               finally:
                   camera.release()
               return 
        logger.error("Failed to open camera. Please check your camera connection.")

    def click(self,x, y):
        """
        Perform a mouse click at specified coordinates using win32api
        """
        try:
            win32api.SetCursorPos((int(x), int(y)))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            time.sleep(0.1)  # Small delay between down and up
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        except Exception as e:
            logger.error(f"Error performing click: {e}")
    def cursor_movement(self, landmarks):
        """
        Calculate cursor position based on nose landmark position and move the cursor accordingly.

        Args:
            landmarks: Facial landmarks detected by MediaPipe.
        """
        nose = landmarks[1]  # Get nose tip coordinates
        nose_x, nose_y = nose.x, nose.y

        # Convert nose position to screen coordinates
        cursor_x = (nose_x - 0.5) * self.sensitivity * \
            self.screen_w / self.movement_range
        cursor_y = (nose_y - 0.5) * self.sensitivity * \
            self.screen_h / self.movement_range

        # Ensure cursor stays within screen bounds and away from edges
        cursor_x = max(SAFE_MARGIN, min(self.screen_w -
                       SAFE_MARGIN, cursor_x + self.screen_w / 2))
        cursor_y = max(SAFE_MARGIN, min(self.screen_h -
                       SAFE_MARGIN, cursor_y + self.screen_h / 2))

        # Update cursor position
        pyautogui.moveTo(cursor_x, cursor_y)

    def head_nod_scrolling(self, nose_y: float):
        """
        Detect head nods and trigger scrolling based on vertical head movement.

        Args:
            nose_y: Vertical position of nose landmark.
        """
        if self.prev_nose_y is not None:
            # Calculate vertical movement
            nod_movement = nose_y - self.prev_nose_y

            # Trigger scrolling based on movement direction
            if nod_movement > self.nod_threshold:
                self.scroll_direction = "down"
                pyautogui.scroll(-SCROLL_AMOUNT)  # Scroll down
            elif nod_movement < -self.nod_threshold:
                self.scroll_direction = "up"
                pyautogui.scroll(SCROLL_AMOUNT)  # Scroll up

        self.prev_nose_y = nose_y  # Update previous position
    def blink_detection(self, landmarks):
        # 1. Landmark assignments
        LEFT_EYE_TOP, LEFT_EYE_BOTTOM = 145, 159
        RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM = 374, 386
        FACE_LEFT, FACE_RIGHT = 234, 454
        
        current_time = time.time()
        
        try:
            # 2. Calculate dynamic threshold
            face_width = abs(landmarks[FACE_RIGHT].x - landmarks[FACE_LEFT].x)
            dynamic_blink_threshold = self.blink_threshold * face_width
            
            # 3. Calculate eye distances
            left_eye_distance = abs(landmarks[LEFT_EYE_TOP].y - landmarks[LEFT_EYE_BOTTOM].y)
            right_eye_distance = abs(landmarks[RIGHT_EYE_TOP].y - landmarks[RIGHT_EYE_BOTTOM].y)
            
            # Determine eye states
            left_eye_closed = left_eye_distance < dynamic_blink_threshold
            right_eye_closed = right_eye_distance < dynamic_blink_threshold
            both_eyes_closed = left_eye_closed and right_eye_closed
            
            # 4. Main logic
            # a) Both eyes closed - start timer
            if both_eyes_closed:
                if self.eyes_closed_start_time is None:
                    self.eyes_closed_start_time = current_time
            
            # b) Both eyes opened - process clicks based on duration
            elif not left_eye_closed and not right_eye_closed:
                if self.eyes_closed_start_time is not None:
                    elapsed_time = current_time - self.eyes_closed_start_time
                    
                    # d) Check for right click first
                    if elapsed_time >= self.RIGHT_CLICK_DURATION:
                        pyautogui.rightClick()
                        logger.info("Right click triggered")
                    # c) Then check for left click
                    elif elapsed_time < self.left_click_interval:
                        pyautogui.click()
                        logger.info("Left click triggered")
                    
                    # Reset timer after processing click
                    self.eyes_closed_start_time = None
                    self.last_click_time = current_time
                
                # f) Stop dragging if active
                if self.is_dragging:
                    self.handle_drag(False, current_time)
                    self.is_dragging = False
            
            # e) Left eye closed, right eye open - handle dragging
            elif left_eye_closed and not right_eye_closed:
                if self.left_eye_closed_start is None:
                    self.left_eye_closed_start = current_time
                elif (current_time - self.left_eye_closed_start >= self.drag_duration):
                    self.handle_drag(True, current_time)
            
            # Reset drag timer if conditions not met
            else:
                self.left_eye_closed_start = None
                
        except Exception as e:
            logger.error(f"Error in blink detection: {e}")
            self.eyes_closed_start_time = None
            self.left_eye_closed_start = None   
    def handle_drag(self, should_drag, current_time):
        """Handle drag operations based on left eye state."""
        try:
            # Start drag
            if should_drag and not self.is_dragging:
                if self.left_eye_closed_start is None:
                    self.left_eye_closed_start = current_time
                    self.drag_start_pos = win32api.GetCursorPos()
                elif current_time - self.left_eye_closed_start > 0.3:  # Short delay to confirm intentional drag
                    pyautogui.mouseDown(button='left')
                    self.is_dragging = True
                    logger.info("Started dragging")
            
            # End drag
            elif not should_drag and self.is_dragging:
                pyautogui.mouseUp(button='left')
                self.is_dragging = False
                self.left_eye_closed_start = None
                self.drag_start_pos = None
                self.last_click_time = current_time  # Prevent immediate clicks after drag
                logger.info("Stopped dragging")
            
            # Reset if eye opens before drag starts
            elif not should_drag:
                self.left_eye_closed_start = None
                self.drag_start_pos = None
    
        except Exception as e:
            logger.error(f"Error in drag handling: {e}")
            # Ensure drag state is reset on error
            self.is_dragging = False
            self.left_eye_closed_start = None
            self.drag_start_pos = None
            pyautogui.mouseUp(button='left')

    def calculate_mouth_aspect_ratio(self, landmarks):
        """
        Calculate mouth aspect ratio using facial landmarks.
        Uses the ratio of the vertical distance to horizontal distance of the mouth.
        """
        upper_lip = landmarks[13]  
        lower_lip = landmarks[14]  
        left_mouth = landmarks[78]   
        right_mouth = landmarks[308] 
    
        vertical_dist = abs(upper_lip.y - lower_lip.y)
        horizontal_dist = abs(left_mouth.x - right_mouth.x)
        
        if horizontal_dist==0:
            logger.warning("mouth horizontal distance is 0.skipping MaR calculations")
            return 0
        mar = vertical_dist / (horizontal_dist + 1e-6)  # Adding small value to prevent division by zero
        
        return mar
    
    def detect_mouth_opening(self, landmarks, current_time):
        """
        Detect if mouth is open and handle virtual keyboard.
        """
        try:
            # Calculate mouth aspect ratio
            mar = self.calculate_mouth_aspect_ratio(landmarks)
            
            # Debug logging
            logger.debug(f"Mouth Aspect Ratio: {mar:.3f}")
    
            # Check if mouth is open (MAR exceeds threshold)
            if mar > self.mouth_open_threshold:
                if self.mouth_open_start_time is None:
                    self.mouth_open_start_time = current_time
                    logger.debug("Mouth opening detected")
                
                # If mouth has been open for sufficient duration
                elif (current_time - self.mouth_open_start_time) > self.mouth_open_duration_threshold:
                     self.waiting_for_mouth_close=True
                     logger.debug("waiting for mouth to close")
            elif mar< self.mouth_open_threshold:
                if self.waiting_for_mouth_close:
                    if self.keyboard_opened:
                        self.virtual_keyboard.stop()
                        self.keyboard_opened=False
                        logger.info("virtual keyboard closed")
                    else:
                        self.virtual_keyboard.start()
                        self.keyboard_opened = True
                        logger.info("Virtual keyboard opened")
                    self.waiting_for_mouth_close = False
                    self.mouth_cycle_complete = True
                self.mouth_open_start_time = None
    
        except Exception as e:
            logger.error(f"Error in mouth detection: {e}")
    
    def process_face_tracking(self):
        """Main face tracking loop."""
        with self.camera_context() as cam:
            while not self.stop_event.is_set():
                try:
                    success, frame = cam.read()
                    self.frame_count += 1

                    if self.frame_count % self.frame_skip != 0:
                        continue

                    if not success:
                        logging.error("Failed to read frame from camera")
                        break

                    frame = cv2.flip(frame, 1)  # Mirror image
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    output = self.face_mesh.process(rgb_frame)
                    landmark_points = output.multi_face_landmarks
                    # frame_h, frame_w, _ = frame.shape

                    if landmark_points:
                        with self.lock:
                            landmarks = landmark_points[0].landmark
                            self.cursor_movement(landmarks)
                            nose_y = landmarks[1].y
                            self.head_nod_scrolling(nose_y)
                            self.blink_detection(landmarks)
                            current_time = time.time() #moved this line inside the if statement to avoid unnecessary calls
                            self.detect_mouth_opening(landmarks, current_time)
                            if self.is_dragging:
                                cv2.putText(frame, "Dragging...", 
                                          (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 
                                          1, (0, 255, 0), 2)
                            for landmark in landmarks:
                                pos = (int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0]))
                                cv2.circle(frame, pos, 1, (0, 255, 0), -1)
                    else:
                        logger.warning("No face detected in this frame. Skipping.")
                        cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    if self.eyes_closed_start_time is not None:
                        duration = time.time() - self.eyes_closed_start_time
                        if duration < self.RIGHT_CLICK_DURATION:
                            cv2.putText(frame, f"Hold for right-click: {duration:.1f}s",
                                      (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    # Add visual feedback
                    cv2.putText(frame, f"Scroll: {self.scroll_direction or 'None'}",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, "Press 'ESC' to exit.",
                                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow('Head, Eye, and Voice Control', frame)

                    if self.stop_event.isSet() or cv2.waitKey(1)==27:
                        break

                    time.sleep(0.03)

                except Exception as e:
                    logging.error(f"Error in face tracking loop: {e}")
                finally:
                    try:
                        for i in range(5):
                            cv2.waitKey(1)
                    except:
                        pass

    def start(self):
        """Start the face tracking in a separate thread."""
        if self.face_thread is None or not self.face_thread.is_alive():
            self.stop_event.clear()
            self.face_thread = Thread(target=self.process_face_tracking,
                                      name="FaceTrackingThread")
            self.face_thread.daemon = True
            self.face_thread.start()
            logging.info("Face tracking thread started")

    def stop(self):
        """Stop the face tracking thread."""
        self.stop_event.set()
        if self.face_thread and self.face_thread.is_alive():
            self.face_thread.join(timeout=5)
            logging.info("Face tracking thread stopped")
        cv2.destroyAllWindows()

    def load_config(self):
        """Load configuration from JSON file or create with defaults if not exists."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    try:
                        saved_config = json.load(f)
                        self.default_config.update(saved_config)
                        logging.info("Configuration loaded successfully")
                    except json.JSONDecodeError as e:
                        logging.error(f"Error decoding JSON configuration :{e}.Using default settings.")
            else:
                self.save_config()
                logging.info("New configuration file created with defaults")

            # Set instance attributes from config
            for key, value in self.default_config.items():
                setattr(self, key, value)

        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            # Set defaults if loading fails
            for key, value in self.default_config.items():
                setattr(self, key, value)

    def save_config(self):
        """Save current configuration to JSON file."""
        try:
            config = {
                "sensitivity": self.sensitivity,
                "movement_range": self.movement_range,
                "nod_threshold": self.nod_threshold,
                "blink_threshold": self.blink_threshold,
                "safe_margin": self.safe_margin,
                "scroll_amount": self.scroll_amount,
                "blink_duration_threshold": self.blink_duration_threshold,
                "left_click_interval": self.left_click_interval,
                "smoothing_window": self.smoothing_window,
                "mouth_open_threshold":self.mouth_open_threshold,
                "mouth_open_duration_threshold":self.mouth_open_duration_threshold
            }

            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logging.info("Configuration saved successfully")

        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
    def activate(self):
        print("hotkey used")
    def update_thresholds(self, key: keyboard.Key):
        """
        Dynamically update thresholds based on key presses and save to config file.
        """
        
        value_changed = True  # Flag to track if any value was changed

        if key == keyboard.Key.up:
            self.sensitivity += 0.1
            print(
                f"Sensitivity increased to: {self.sensitivity:.2f} (Default: {SENSITIVITY_DEFAULT})")
        elif key == keyboard.Key.down:
            self.sensitivity = max(0.1, self.sensitivity - 0.1)
            print(
                f"Sensitivity decreased to: {self.sensitivity:.2f} (Default: {SENSITIVITY_DEFAULT})")
        elif key == keyboard.Key.right:
            self.blink_threshold += 0.001
            print(
                f"Blink threshold increased to: {self.blink_threshold:.3f} (Default: {BLINK_THRESHOLD_DEFAULT})")
        elif key == keyboard.Key.left:
            self.blink_threshold = max(0.001, self.blink_threshold - 0.001)
            print(
                f"Blink threshold decreased to: {self.blink_threshold:.3f} (Default: {BLINK_THRESHOLD_DEFAULT})")
        elif key == keyboard.Key.f2:
            self.nod_threshold += 0.001
            print(
                f"Nod threshold increased to: {self.nod_threshold:.3f} (Default: {NOD_THRESHOLD_DEFAULT})")
        elif key == keyboard.Key.f1:
            self.nod_threshold = max(0.001, self.nod_threshold - 0.001)
            print(
                f"Nod threshold decreased to: {self.nod_threshold:.3f} (Default: {NOD_THRESHOLD_DEFAULT})")
        elif key == keyboard.Key.f4:
            self.movement_range += 0.01
            print(
                f"Movement range increased to: {self.movement_range:.2f} (Default: {MOVEMENT_RANGE_DEFAULT})")
        elif key == keyboard.Key.f3:
            self.movement_range = max(0.01, self.movement_range - 0.01)
            print(
                f"Movement range decreased to: {self.movement_range:.2f} (Default: {MOVEMENT_RANGE_DEFAULT})")
        elif key == keyboard.Key.f5:
            self.safe_margin = max(1, self.safe_margin - 1)
            print(
                f"Safe margin decreased to: {self.safe_margin} (Default: {SAFE_MARGIN})")
        elif key == keyboard.Key.f6:
            self.safe_margin += 1
            print(
                f"Safe margin increased to: {self.safe_margin} (Default: {SAFE_MARGIN})")
        elif key == keyboard.Key.f7:
            self.scroll_amount = max(50, self.scroll_amount - 50)
            print(
                f"Scroll amount decreased to: {self.scroll_amount} (Default: {SCROLL_AMOUNT})")
        elif key == keyboard.Key.f8:
            self.scroll_amount += 50
            print(
                f"Scroll amount increased to: {self.scroll_amount} (Default: {SCROLL_AMOUNT})")
        elif key == keyboard.Key.f9:
            self.blink_duration_threshold = max(
                0.01, self.blink_duration_threshold - 0.01)
            print(
                f"Blink duration threshold decreased to: {self.blink_duration_threshold:.2f} (Default: {BLINK_DURATION_THRESHOLD_DEFAULT})")
        elif key == keyboard.Key.f10:
            self.blink_duration_threshold += 0.01
            print(
                f"Blink duration threshold increased to: {self.blink_duration_threshold:.2f} (Default: {BLINK_DURATION_THRESHOLD_DEFAULT})")
        elif key == keyboard.Key.f11:
            self.left_click_interval = max(0.1, self.left_click_interval - 0.1)
            print(
                f"Click interval decreased to: {self.left_click_interval:.1f} (Default: {CLICK_INTERVAL_DEFAULT})")
        elif key == keyboard.Key.f12:
                self.left_click_interval += 0.1
                print(f"Click interval increased to: {self.left_click_interval:.1f} (Default: {CLICK_INTERVAL_DEFAULT})")
        elif key == keyboard.Key.page_up:
            self.smoothing_window = min(10, self.smoothing_window + 1)
            print(
                f"Smoothing window size increased to: {self.smoothing_window} (Default: {SMOOTHING_WINDOW_SIZE})")
        elif key == keyboard.Key.page_down:
            self.smoothing_window = max(1, self.smoothing_window - 1)
            print(
                f"Smoothing window size decreased to: {self.smoothing_window} (Default: {SMOOTHING_WINDOW_SIZE})")
        elif key == keyboard.HotKey(['ctrl','f1'],self.activate):
            self.mouth_open_threshold = max(0.1, self.mouth_open_threshold - 0.1)
            print(
                f"Mouth open threshold decreased to: {self.mouth_open_threshold:.1f} (Default: {MOUTH_OPEN_THRESHOLD})")
        elif key == keyboard.HotKey(['ctrl','f2'],self.activate):
            self.mouth_open_threshold = min(1, self.mouth_open_threshold + 0.1)
            print(
                f"Mouth open threshold increased to: {self.mouth_open_threshold:.1f} (Default: {MOUTH_OPEN_THRESHOLD})")
        elif key == keyboard.HotKey(['ctrl','f3'],self.activate):
            self.mouth_open_duration_threshold = max(0.1, self.mouth_open_duration_threshold - 0.1)
            print(
                f"Mouth open duration threshold decreased to: {self.mouth_open_duration_threshold:.1f} (Default: {MOUTH_OPEN_DURATION})")
        elif key == keyboard.HotKey(['ctrl','f4'],self.activate):
            self.mouth_open_duration_threshold = min(2, self.mouth_open_duration_threshold + 0.1)
            print(
                f"Mouth open duration threshold increased to: {self.mouth_open_duration_threshold:.1f} (Default: {MOUTH_OPEN_DURATION})")
        
        elif key == keyboard.HotKey(('ctrl','x'),self.activate): 
            # Reset all values to defaults
            self.__init__()
            print("All values reset to defaults")
        else:
            value_changed = False

        # Save configuration if any value was changed
        if value_changed:
            self.save_config()
