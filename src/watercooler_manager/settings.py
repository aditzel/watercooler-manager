import os
import json
import platform
from typing import Tuple
from .enums import PumpVoltage, RGBState
from os.path import join, basename, splitext
from sys import executable

# Windows-specific imports
if platform.system() == 'Windows':
    try:
        import winshell
    except ImportError:
        winshell = None

class Settings:
    REGISTRY_KEY = r"Software\WaterCooler"
    CONFIG_FILE = os.path.expanduser("~/.watercooler.json")
    SYSTEM_CONFIG_FILE = "/etc/watercooler-manager/config.json"

    def __init__(self):
        self.current_voltage = PumpVoltage.V7
        self.current_fan_speed = 50
        self.pump_is_off = False
        self.fan_is_off = False
        self.rgb_state = RGBState.STATIC
        self.rgb_is_off = False
        self.rgb_color = (255, 0, 0)  # Default red
        self.auto_start = False
        self.auto_connect = False
        self.daemon_mode = os.getenv('WATERCOOLER_DAEMON_MODE', '0') == '1'
        self.config_path = os.getenv('WATERCOOLER_CONFIG_PATH', self._get_default_config_path())
        self.load()

    def _get_default_config_path(self):
        """Get the default configuration file path based on mode and system"""
        if platform.system() == 'Windows':
            return None  # Use registry on Windows
        elif self.daemon_mode and os.path.exists(self.SYSTEM_CONFIG_FILE):
            return self.SYSTEM_CONFIG_FILE
        else:
            return self.CONFIG_FILE

    def load(self):
        if platform.system() == 'Windows':
            self._load_from_registry()
        else:
            self._load_from_file()

    def save(self):
        if platform.system() == 'Windows':
            self._save_to_registry()
        else:
            self._save_to_file()

    def _load_from_registry(self):
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY)
            self.current_voltage = PumpVoltage(winreg.QueryValueEx(key, "current_voltage")[0])
            self.current_fan_speed = winreg.QueryValueEx(key, "current_fan_speed")[0]
            self.pump_is_off = bool(winreg.QueryValueEx(key, "pump_is_off")[0])
            self.fan_is_off = bool(winreg.QueryValueEx(key, "fan_is_off")[0])
            self.rgb_state = RGBState(winreg.QueryValueEx(key, "rgb_state")[0])
            self.rgb_is_off = bool(winreg.QueryValueEx(key, "rgb_is_off")[0])
            self.rgb_color = tuple(winreg.QueryValueEx(key, "rgb_color")[0])
            self.auto_start = bool(winreg.QueryValueEx(key, "auto_start")[0])
            self.auto_connect = bool(winreg.QueryValueEx(key, "auto_connect")[0])
            winreg.CloseKey(key)
        except:
            pass

    def _save_to_registry(self):
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY)
            winreg.SetValueEx(key, "current_voltage", 0, winreg.REG_DWORD, self.current_voltage)
            winreg.SetValueEx(key, "current_fan_speed", 0, winreg.REG_DWORD, self.current_fan_speed)
            winreg.SetValueEx(key, "pump_is_off", 0, winreg.REG_DWORD, int(self.pump_is_off))
            winreg.SetValueEx(key, "fan_is_off", 0, winreg.REG_DWORD, int(self.fan_is_off))
            winreg.SetValueEx(key, "rgb_state", 0, winreg.REG_DWORD, self.rgb_state)
            winreg.SetValueEx(key, "rgb_is_off", 0, winreg.REG_DWORD, int(self.rgb_is_off))
            winreg.SetValueEx(key, "rgb_color", 0, winreg.REG_BINARY, bytes(self.rgb_color))
            winreg.SetValueEx(key, "auto_start", 0, winreg.REG_DWORD, int(self.auto_start))
            winreg.SetValueEx(key, "auto_connect", 0, winreg.REG_DWORD, int(self.auto_connect))
            winreg.CloseKey(key)
        except:
            pass

    def _load_from_file(self):
        config_file = self.config_path or self.CONFIG_FILE
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.current_voltage = PumpVoltage(config.get('current_voltage', self.current_voltage))
                self.current_fan_speed = config.get('current_fan_speed', self.current_fan_speed)
                self.pump_is_off = config.get('pump_is_off', self.pump_is_off)
                self.fan_is_off = config.get('fan_is_off', self.fan_is_off)
                self.rgb_state = RGBState(config.get('rgb_state', self.rgb_state))
                self.rgb_is_off = config.get('rgb_is_off', self.rgb_is_off)
                self.rgb_color = tuple(config.get('rgb_color', self.rgb_color))
                self.auto_start = config.get('auto_start', self.auto_start)
                self.auto_connect = config.get('auto_connect', self.auto_connect)
        except Exception as e:
            if self.daemon_mode:
                print(f"Warning: Could not load config from {config_file}: {e}")
            pass

    def _save_to_file(self):
        config_file = self.config_path or self.CONFIG_FILE
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_file), exist_ok=True)

            config = {
                'current_voltage': self.current_voltage,
                'current_fan_speed': self.current_fan_speed,
                'pump_is_off': self.pump_is_off,
                'fan_is_off': self.fan_is_off,
                'rgb_state': self.rgb_state,
                'rgb_is_off': self.rgb_is_off,
                'rgb_color': self.rgb_color,
                'auto_start': self.auto_start,
                'auto_connect': self.auto_connect
            }
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            if self.daemon_mode:
                print(f"Warning: Could not save config to {config_file}: {e}")
            pass

    def set_autostart(self, autostart: bool):
        self.auto_start = autostart
        
        if platform.system() == 'Windows' and 'winshell' in globals() and winshell:
            startup_dir = winshell.startup()
            shortcut_path = join(startup_dir, f"{splitext(basename(executable))[0]}.lnk")
            
            if autostart:
                winshell.CreateShortcut(
                    Path=shortcut_path,
                    Target=executable,
                    Icon=(executable, 0),
                    Description="Watercooler Manager"
                )
            elif os.path.exists(shortcut_path):
                os.remove(shortcut_path)
        
        self.save() 