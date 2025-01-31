from threading import Lock, Thread, Event
import pyautogui
from typing import Dict, Callable
import speech_recognition as sr
import logging
import time

class VoiceController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.command_lock = Lock()
        self.stop_event = Event()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05  # Reduced pause for faster response

        self.commands: Dict[str, Callable] = {
            "select": self.left_click,
            "right click": pyautogui.rightClick,
            "double click": pyautogui.doubleClick,
            "triple click": pyautogui.tripleClick,
            "drag": self.start_drag,
            "drop": self.end_drag,
            "scroll up": lambda: pyautogui.scroll(200),
            "scroll down": lambda: pyautogui.scroll(-200),
            "page up": lambda: pyautogui.hotkey('pgup'),
            "page down": lambda: pyautogui.hotkey('pgdn'),
            "minimise": lambda: pyautogui.hotkey('win', 'down'),
            "maximize": lambda: pyautogui.hotkey('win', 'up'),
            "close window": lambda: pyautogui.hotkey('alt', 'f4'),
            "switch window": lambda: pyautogui.hotkey('alt', 'tab'),
            "new window": lambda: pyautogui.hotkey('ctrl', 'n'),
            "volume up": lambda: pyautogui.press('volumeup'),
            "volume down": lambda: pyautogui.press('volumedown'),
            # Updated to Win + Ctrl + O
            "keyboard": lambda: pyautogui.hotkey('win', 'ctrl', 'o'),
            "mute": lambda: pyautogui.press('volumemute'),
            "play pause": lambda: pyautogui.press('playpause'),
            "go back": lambda: pyautogui.hotkey('alt', 'left'),
            "go forward": lambda: pyautogui.hotkey('alt', 'right'),
            "refresh": lambda: pyautogui.hotkey('f5'),
            "select all": lambda: pyautogui.hotkey('ctrl', 'a'),
            "copy": lambda: pyautogui.hotkey('ctrl', 'c'),
            "paste": lambda: pyautogui.hotkey('ctrl', 'v'),
            "cut": lambda: pyautogui.hotkey('ctrl', 'x'),
            "undo": lambda: pyautogui.hotkey('ctrl', 'z'),
            "redo": lambda: pyautogui.hotkey('ctrl', 'y'),
            # Added duration for smoother movement
            "move left": lambda: pyautogui.moveRel(-50, 0, duration=0.1),
            "move right": lambda: pyautogui.moveRel(50, 0, duration=0.1),
            "move up": lambda: pyautogui.moveRel(0, -50, duration=0.1),
            "move down": lambda: pyautogui.moveRel(0, 50, duration=0.1),
            "small a": lambda: pyautogui.press('a'),
            "small b": lambda: pyautogui.press('b'),
            "small c": lambda: pyautogui.press('c'),
            "small d": lambda: pyautogui.press('d'),
            "small e": lambda: pyautogui.press('e'),
            "small f": lambda: pyautogui.press('f'),
            "small g": lambda: pyautogui.press('g'),
            "small h": lambda: pyautogui.press('h'),
            "small i": lambda: pyautogui.press('i'),
            "small j": lambda: pyautogui.press('j'),
            "small k": lambda: pyautogui.press('k'),
            "small l": lambda: pyautogui.press('l'),
            "small m": lambda: pyautogui.press('m'),
            "small n": lambda: pyautogui.press('n'),
            "small o": lambda: pyautogui.press('o'),
            "small p": lambda: pyautogui.press('p'),
            "small q": lambda: pyautogui.press('q'),
            "small r": lambda: pyautogui.press('r'),
            "small s": lambda: pyautogui.press('s'),
            "small t": lambda: pyautogui.press('t'),
            "small u": lambda: pyautogui.press('u'),
            "small v": lambda: pyautogui.press('v'),
            "small w": lambda: pyautogui.press('w'),
            "small x": lambda: pyautogui.press('x'),
            "small y": lambda: pyautogui.press('y'),
            "small z": lambda: pyautogui.press('z'),
            "capital A": lambda: pyautogui.press('A'),
            "capital B": lambda: pyautogui.press('B'),
            "capital C": lambda: pyautogui.press('C'),
            "capital D": lambda: pyautogui.press('D'),
            "capital E": lambda: pyautogui.press('E'),
            "capital F": lambda: pyautogui.press('F'),
            "capital G": lambda: pyautogui.press('G'),
            "capital H": lambda: pyautogui.press('H'),
            "capital I": lambda: pyautogui.press('I'),
            "capital J": lambda: pyautogui.press('J'),
            "capital K": lambda: pyautogui.press('K'),
            "capital L": lambda: pyautogui.press('L'),
            "capital M": lambda: pyautogui.press('M'),
            "capital N": lambda: pyautogui.press('N'),
            "capital O": lambda: pyautogui.press('O'),
            "capital P": lambda: pyautogui.press('P'),
            "capital Q": lambda: pyautogui.press('Q'),
            "capital R": lambda: pyautogui.press('R'),
            "capital S": lambda: pyautogui.press('S'),
            "capital T": lambda: pyautogui.press('T'),
            "capital U": lambda: pyautogui.press('U'),
            "capital V": lambda: pyautogui.press('V'),
            "capital W": lambda: pyautogui.press('W'),
            "capital X": lambda: pyautogui.press('X'),
            "capital Y": lambda: pyautogui.press('Y'),
            "capital Z": lambda: pyautogui.press('Z'),
        }
        self.voice_thread = None

    def left_click(self):
        """Execute a left click with error handling."""
        try:
            pyautogui.click()
        except Exception as e:
            logging.error(f"Error during left click: {e}")

    def start_drag(self):
        """Start dragging from current position."""
        try:
            pyautogui.mouseDown()
        except Exception as e:
            logging.error(f"Error starting drag: {e}")

    def end_drag(self):
        """End dragging operation."""
        try:
            pyautogui.mouseUp()
        except Exception as e:
            logging.error(f"Error ending drag: {e}")

    def process_voice_commands(self):
        """
        Main loop for processing voice commands with improved error handling
        and noise reduction.
        """
        while not self.stop_event.is_set():
            with sr.Microphone() as source:
                try:
                    self.recognizer.adjust_for_ambient_noise(
                        source, duration=0.5)
                    logging.info("Listening for commands...")
                    audio = self.recognizer.listen(
                        source, timeout=5, phrase_time_limit=3)

                    with self.command_lock:
                        command = self.recognizer.recognize_google(
                            audio).lower()
                        logging.info(f"Command received: {command}")

                        if  "stop" in command:
                            logging.info("Stopping voice command system...")
                            self.stop_event.set()
                            break

                        for cmd, action in self.commands.items():
                            if cmd in command:
                                logging.info(f"Executing command: {cmd}")
                                action()
                                break
                        else:
                            logging.warning(f"Unknown command: {command}")

                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    logging.debug("Could not understand audio")
                except sr.RequestError as e:
                    logging.error(f"Speech recognition service error: {e}")
                except Exception as e:
                    logging.error(
                        f"Unexpected error in voice command processing: {e}")

                time.sleep(0.05)  # Reduced delay

    def start(self):
        """Start the voice controller in a separate thread."""
        if self.voice_thread is None or not self.voice_thread.is_alive():
            self.stop_event.clear()
            self.voice_thread = Thread(
                target=self.process_voice_commands, name="VoiceControlThread")
            self.voice_thread.daemon = True
            self.voice_thread.start()
            logging.info("Voice control thread started")

    def stop(self):
        """Stop the voice controller thread."""
        self.stop_event.set()
        if self.voice_thread and self.voice_thread.is_alive():
            self.voice_thread.join(timeout=5)
            logging.info("Voice control thread stopped")
