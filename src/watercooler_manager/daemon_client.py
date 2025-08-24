"""
Daemon client for communicating with the watercooler daemon via D-Bus
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, Callable
from .enums import PumpVoltage, RGBState

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False
    dbus = None


class DaemonClient:
    """Client for communicating with the watercooler daemon"""
    
    DBUS_SERVICE_NAME = "org.watercooler.Manager"
    DBUS_OBJECT_PATH = "/org/watercooler/Manager"
    DBUS_INTERFACE = "org.watercooler.Manager"
    
    def __init__(self):
        self.bus = None
        self.daemon_proxy = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to the daemon via D-Bus"""
        if not DBUS_AVAILABLE:
            print("D-Bus not available, falling back to direct mode")
            return False
            
        try:
            # Initialize D-Bus
            DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SessionBus()
            
            # Get daemon proxy
            self.daemon_proxy = self.bus.get_object(
                self.DBUS_SERVICE_NAME, 
                self.DBUS_OBJECT_PATH
            )
            
            # Test connection
            self.daemon_proxy.ping(dbus_interface=self.DBUS_INTERFACE)
            self.connected = True
            print("✅ Connected to watercooler daemon")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to daemon: {e}")
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to daemon"""
        return self.connected
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current device status from daemon"""
        if not self.connected:
            return None
            
        try:
            status_json = self.daemon_proxy.get_status(dbus_interface=self.DBUS_INTERFACE)
            return json.loads(status_json)
        except Exception as e:
            print(f"Error getting status: {e}")
            return None
    
    def get_settings(self) -> Optional[Dict[str, Any]]:
        """Get current settings from daemon"""
        if not self.connected:
            return None
            
        try:
            settings_json = self.daemon_proxy.get_settings(dbus_interface=self.DBUS_INTERFACE)
            return json.loads(settings_json)
        except Exception as e:
            print(f"Error getting settings: {e}")
            return None
    
    def set_pump_voltage(self, voltage: PumpVoltage) -> bool:
        """Set pump voltage via daemon"""
        if not self.connected:
            return False
            
        try:
            self.daemon_proxy.set_pump_voltage(
                int(voltage), 
                dbus_interface=self.DBUS_INTERFACE
            )
            return True
        except Exception as e:
            print(f"Error setting pump voltage: {e}")
            return False
    
    def set_fan_speed(self, speed: int) -> bool:
        """Set fan speed via daemon"""
        if not self.connected:
            return False
            
        try:
            self.daemon_proxy.set_fan_speed(
                speed, 
                dbus_interface=self.DBUS_INTERFACE
            )
            return True
        except Exception as e:
            print(f"Error setting fan speed: {e}")
            return False
    
    def set_rgb_color(self, r: int, g: int, b: int) -> bool:
        """Set RGB color via daemon"""
        if not self.connected:
            return False
            
        try:
            self.daemon_proxy.set_rgb_color(
                r, g, b, 
                dbus_interface=self.DBUS_INTERFACE
            )
            return True
        except Exception as e:
            print(f"Error setting RGB color: {e}")
            return False
    
    def set_rgb_state(self, state: RGBState) -> bool:
        """Set RGB state via daemon"""
        if not self.connected:
            return False
            
        try:
            self.daemon_proxy.set_rgb_state(
                int(state), 
                dbus_interface=self.DBUS_INTERFACE
            )
            return True
        except Exception as e:
            print(f"Error setting RGB state: {e}")
            return False
    
    def connect_device(self) -> bool:
        """Connect to device via daemon"""
        if not self.connected:
            return False
            
        try:
            self.daemon_proxy.connect_device(dbus_interface=self.DBUS_INTERFACE)
            return True
        except Exception as e:
            print(f"Error connecting device: {e}")
            return False
    
    def disconnect_device(self) -> bool:
        """Disconnect device via daemon"""
        if not self.connected:
            return False
            
        try:
            self.daemon_proxy.disconnect_device(dbus_interface=self.DBUS_INTERFACE)
            return True
        except Exception as e:
            print(f"Error disconnecting device: {e}")
            return False
    
    def subscribe_to_updates(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to status updates from daemon"""
        if not self.connected:
            return
            
        try:
            # Connect to D-Bus signals
            self.bus.add_signal_receiver(
                lambda data: callback(json.loads(data)),
                signal_name="StatusChanged",
                dbus_interface=self.DBUS_INTERFACE,
                path=self.DBUS_OBJECT_PATH
            )
        except Exception as e:
            print(f"Error subscribing to updates: {e}")
    
    def disconnect(self):
        """Disconnect from daemon"""
        self.connected = False
        self.daemon_proxy = None
        self.bus = None
