import tkinter as tk
from tkinter import ttk
import logging
import atexit
import threading
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
import pyautogui

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VirtualKeyboardConfig:
    """Configuration management for Virtual Keyboard"""
    # [Previous config code remains the same...]
    DEFAULT_CONFIG = {
        'window': {
            'width': 1300,
            'height': 350,
            'title': "Virtual Keyboard",
            'padding': 10,
            'font': ('Arial', 10),
        },
        'button': {
            'width': 5,
            'height': 2,
            'borderwidth': 1,
            'relief': 'raised',
            'padx': 2,
            'pady': 2
        },
        'special_buttons': {
            'Backspace': {'width': 8},
            'Tab': {'width': 8},
            'Caps': {'width': 8},
            'Enter': {'width': 8},
            'Shift': {'width': 8},
            'Space': {'width': 30}
        },
        'keyboard_layout': [
            ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
            ['Tab', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
            ['Caps', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", 'Enter'],
            ['Shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 'Shift'],
            ['Space']
        ]
    }

    def __init__(self, config_path: Optional[Path] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config_path and config_path.exists():
            self.load_config(config_path)

    def load_config(self, config_path: Path) -> None:
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                self.config = self._deep_update(self.config, user_config)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")

    @staticmethod
    def _deep_update(d: Dict, u: Dict) -> Dict:
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = VirtualKeyboardConfig._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

class VirtualKeyboard:
    """Virtual Keyboard with proper thread management"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, config_path: Optional[Path] = None):
        if not hasattr(self, '_initialized'):
            self.config = VirtualKeyboardConfig(config_path)
            self.root = None
            self.main_frame = None
            self.is_caps = False
            self.is_shift = False
            self._is_running = False
            self._drag_data = {"x": 0, "y": 0}
            self.buttons = {}
            self.keyboard_thread = None
            atexit.register(self.cleanup)
            self._initialized = True

    def start(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Start the virtual keyboard in a separate thread"""
        if self._is_running:
            self.show()
            return

        def create_keyboard():
            self.root = tk.Tk()
            self._setup_window(x, y)
            self._create_widgets()
            self._bind_events()
            self._is_running = True
            self.root.mainloop()

        self.keyboard_thread = threading.Thread(target=create_keyboard)
        self.keyboard_thread.daemon = True
        self.keyboard_thread.start()

    def stop(self) -> None:
        """Stop the virtual keyboard"""
        try:
            if self._is_running and self.root:
               self.root.after(0, self.root.quit)
               self.root.after(100, self.root.destroy)
               self._is_running = False
            if self.keyboard_thread:
                self.keyboard_thread.join(timeout=1.0)
        except:
            logger.info("virtual keyboard stoped succesfully")

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self._is_running:
                self.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    # [Rest of the methods remain the same...]
    def _setup_window(self, x: Optional[int], y: Optional[int]) -> None:
        """Set up the main window"""
        cfg = self.config.config['window']
        self.root.title(cfg['title'])
        self.root.attributes('-topmost', True)
        
        # Calculate position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        if x is None:
            x = (screen_width - cfg['width']) // 2
        if y is None:
            y = screen_height - cfg['height'] - 50
            
        # Validate coordinates
        x = max(0, min(x, screen_width - cfg['width']))
        y = max(0, min(y, screen_height - cfg['height']))
        
        self.root.geometry(f"{cfg['width']}x{cfg['height']}+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create all widgets"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(padx=self.config.config['window']['padding'], 
                           pady=self.config.config['window']['padding'],
                           fill='both',
                           expand=True)
        
        self._create_title_bar()
        self._create_keyboard()

    def _create_title_bar(self) -> None:
        """Create the title bar"""
        title_bar = ttk.Frame(self.main_frame)
        title_bar.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(title_bar, 
                              text=self.config.config['window']['title'],
                              font=self.config.config['window']['font'])
        title_label.pack(side='left', padx=5)
        
        ttk.Button(title_bar, text="−", width=3, command=self.hide).pack(side='right')
        ttk.Button(title_bar, text="×", width=3, command=self.destroy).pack(side='right')

    def _create_keyboard(self) -> None:
        """Create the keyboard layout"""
        layout = self.config.config['keyboard_layout']
        button_cfg = self.config.config['button']
        special_cfg = self.config.config['special_buttons']

        keyboard_frame = ttk.Frame(self.main_frame)
        keyboard_frame.pack(fill='both', expand=True)

        for row_idx, row in enumerate(layout):
            keyboard_frame.grid_rowconfigure(row_idx, weight=1)
            for col_idx, key in enumerate(row):
                keyboard_frame.grid_columnconfigure(col_idx, weight=1)
                
                cfg = button_cfg.copy()
                if key in special_cfg:
                    cfg.update(special_cfg[key])

                button = tk.Button(
                    keyboard_frame,
                    text=key,
                    width=cfg['width'],
                    height=cfg['height'],
                    borderwidth=cfg['borderwidth'],
                    relief=cfg['relief'],
                    command=lambda k=key: self.safe_button_click(k)
                )
                button.grid(
                    row=row_idx,
                    column=col_idx,
                    padx=cfg['padx'],
                    pady=cfg['pady'],
                    sticky='nsew'
                )
                self.buttons[key] = button

    def hide(self) -> None:
        if self.root and self.root.winfo_exists():
            self.root.withdraw()
    
    def show(self) -> None:
        if self.root and self.root.winfo_exists():
            self.root.deiconify()
    
    def destroy(self) -> None:
        self.cleanup()
        VirtualKeyboard._instance = None

    @staticmethod
    def return_focus_to_last_window(event: Optional[tk.Event] = None) -> str:
        try:
            pyautogui.hotkey('alt', 'tab')
        except Exception as e:
            logger.error(f"Error returning focus to last window: {e}")
        return 'break'

    def _bind_events(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        
        title_bar = self.main_frame.winfo_children()[0]
        title_bar.bind('<Button-1>', self._start_drag)
        title_bar.bind('<B1-Motion>', self._drag)
        
        for button in self.buttons.values():
            button.bind('<FocusIn>', self.return_focus_to_last_window)
            button.bind('<Tab>', lambda e: 'break')
            button.bind('<Shift-Tab>', lambda e: 'break')

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
    
    def _drag(self, event: tk.Event) -> None:
        try:
            dx = event.x - self._drag_data["x"]
            dy = event.y - self._drag_data["y"]
            new_x = self.root.winfo_x() + dx
            new_y = self.root.winfo_y() + dy
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            new_x = max(0, min(new_x, screen_width - self.root.winfo_width()))
            new_y = max(0, min(new_y, screen_height - self.root.winfo_height()))
            
            self.root.geometry(f"+{new_x}+{new_y}")
        except Exception as e:
            logger.error(f"Error during drag operation: {e}")

    def safe_button_click(self, key: str) -> None:
        try:
            self._handle_key_press(key)
        except Exception as e:
            logger.error(f"Error handling button click for key '{key}': {e}")

    def _handle_key_press(self, key: str) -> None:
        self.return_focus_to_last_window()
    
        if key == 'Caps':
            self.is_caps = not self.is_caps
            return
        elif key == 'Shift':
            self.is_shift = not self.is_shift
            return
        elif key in {'Space', 'Tab', 'Enter', 'Backspace'}:
            pyautogui.press(key.lower())
            return
    
        if self.is_caps or self.is_shift:
            if key.isalpha():
                pyautogui.press(key.upper())
            else:
                shifted_symbols = {
                    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
                    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
                    ';': ':', "'": '"', ',': '<', '.': '>', '/': '?',
                    '`': '~'
                }
                char = shifted_symbols.get(key, key)
                pyautogui.write(char)
        else:
            pyautogui.write(key)
    
        if self.is_shift:
            self.is_shift = False

