import cv2
import mediapipe as mp
import pyautogui
import signal
import sys
import os
import time
import logging
from threading import Lock, Thread, Event
from contextlib import contextmanager
from pynput import keyboard
import json
from typing import List, Optional

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure environment variables to suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Import custom controllers
from facecontroller import FaceController
from voicecontroller import VoiceController

class ApplicationController:
    def __init__(self):
        self.capslock = False
        self.face_controller: Optional[FaceController] = None
        self.voice_controller: Optional[VoiceController] = None
        self.active_controllers: List = []
        self.keyboard_listener: Optional[keyboard.Listener] = None

    def on_press(self, key: keyboard.Key) -> None:
        """Handle keyboard press events."""
        try:
            logger.debug(f"Key pressed: {key}")
            if key == keyboard.Key.caps_lock:
                self.capslock = not self.capslock
            if self.capslock and self.face_controller:
                self.face_controller.update_thresholds(key)
        except Exception as e:
            logger.error(f"Error handling key press: {e}")

    def on_release(self, key: keyboard.Key) -> bool:
        """Handle keyboard release events."""
        if key == keyboard.Key.esc:
            self.stop_all_controllers()
            return False
        return True

    def stop_all_controllers(self) -> None:
        """Stop all active controllers."""
        for controller in self.active_controllers:
            if hasattr(controller, 'stop_event'):
                controller.stop_event.set()
            if hasattr(controller, 'stop'):
                controller.stop()

    def signal_handler(self, signum: int, frame: object) -> None:
        """Handle system signals for clean shutdown."""
        logger.info(f"Received shutdown signal: {signum}")
        self.stop_all_controllers()
        sys.exit(0)

    def initialize_controllers(self, choice: int) -> None:
        """Initialize controllers based on user choice."""
        self.face_controller = FaceController()
        self.voice_controller = VoiceController()

        if choice == 1:
            self.active_controllers = [self.face_controller]
        elif choice == 2:
            self.active_controllers = [self.voice_controller]
        elif choice == 3:
            self.active_controllers = [self.voice_controller, self.face_controller]
        else:
            raise ValueError("Invalid choice. Please select 1, 2, or 3.")

    def run(self) -> None:
        """Run the application."""
        try:
            print("How do you want to use the HEV:")
            print("1. Only face controller")
            print("2. Only voice controller")
            print("3. Both face and voice controller")
            
            choice = int(input("Enter your choice (1-3): "))
            self.initialize_controllers(choice)

            # Set up keyboard listener
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.keyboard_listener.start()

            # Set up signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            # Start active controllers
            for controller in self.active_controllers:
                controller.start()

            logger.info("Main thread monitoring controllers")

            # Monitor controllers
            while all(not controller.stop_event.is_set() 
                     for controller in self.active_controllers):
                time.sleep(0.1)

        except ValueError as ve:
            logger.error(f"Invalid input: {ve}")
        except KeyboardInterrupt:
            logger.info("Program terminated by user.")
        except Exception as e:
            logger.critical(f"Critical error in main: {e}")
        finally:
            self.stop_all_controllers()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            logger.info("Application shutting down.")

def main():
    app = ApplicationController()
    app.run()

if __name__ == "__main__":
    main()