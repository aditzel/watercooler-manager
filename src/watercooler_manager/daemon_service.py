"""
D-Bus service interface for the watercooler daemon
"""

import json
import asyncio
from typing import Dict, Any

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    import gi
    gi.require_version('GLib', '2.0')
    from gi.repository import GLib
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False
    dbus = None
    GLib = None


if DBUS_AVAILABLE:
    class WatercoolerDaemonService(dbus.service.Object):
        """D-Bus service for watercooler daemon"""

        SERVICE_NAME = "org.watercooler.Manager"
        OBJECT_PATH = "/org/watercooler/Manager"
        INTERFACE_NAME = "org.watercooler.Manager"

        def __init__(self, watercooler_manager):
            self.watercooler_manager = watercooler_manager
            self.device = watercooler_manager.device
            self.settings = watercooler_manager.settings

            # Initialize D-Bus
            DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SessionBus()

            # Request service name
            bus_name = dbus.service.BusName(self.SERVICE_NAME, self.bus)
            super().__init__(bus_name, self.OBJECT_PATH)

            print(f"✅ D-Bus service started: {self.SERVICE_NAME}")

        @dbus.service.method(INTERFACE_NAME, out_signature='s')
        def ping(self):
            """Ping method for connection testing"""
            return "pong"
    
    @dbus.service.method(INTERFACE_NAME, out_signature='s')
    def get_status(self):
        """Get current device status"""
        try:
            status = {
                'connected': self.device.is_connected if hasattr(self.device, 'is_connected') else False,
                'device_name': getattr(self.device, 'device_name', 'Unknown'),
                'pump_voltage': int(self.settings.current_voltage),
                'fan_speed': self.settings.current_fan_speed,
                'pump_is_off': self.settings.pump_is_off,
                'fan_is_off': self.settings.fan_is_off,
                'rgb_state': int(self.settings.rgb_state),
                'rgb_is_off': self.settings.rgb_is_off,
                'rgb_color': list(self.settings.rgb_color),
                'auto_connect': self.settings.auto_connect,
                'daemon_mode': self.settings.daemon_mode,
            }
            return json.dumps(status)
        except Exception as e:
            return json.dumps({'error': str(e)})
    
    @dbus.service.method(INTERFACE_NAME, out_signature='s')
    def get_settings(self):
        """Get current settings"""
        try:
            settings = {
                'current_voltage': int(self.settings.current_voltage),
                'current_fan_speed': self.settings.current_fan_speed,
                'pump_is_off': self.settings.pump_is_off,
                'fan_is_off': self.settings.fan_is_off,
                'rgb_state': int(self.settings.rgb_state),
                'rgb_is_off': self.settings.rgb_is_off,
                'rgb_color': list(self.settings.rgb_color),
                'auto_start': self.settings.auto_start,
                'auto_connect': self.settings.auto_connect,
            }
            return json.dumps(settings)
        except Exception as e:
            return json.dumps({'error': str(e)})
    
    @dbus.service.method(INTERFACE_NAME, in_signature='i')
    def set_pump_voltage(self, voltage):
        """Set pump voltage"""
        try:
            from .enums import PumpVoltage
            self.settings.current_voltage = PumpVoltage(voltage)
            self.settings.save()
            
            # Apply to device if connected
            if hasattr(self.device, 'is_connected') and self.device.is_connected:
                # Schedule async operation
                asyncio.create_task(self._apply_pump_voltage())
            
            self._emit_status_changed()
        except Exception as e:
            print(f"Error setting pump voltage: {e}")
    
    @dbus.service.method(INTERFACE_NAME, in_signature='i')
    def set_fan_speed(self, speed):
        """Set fan speed"""
        try:
            self.settings.current_fan_speed = max(0, min(100, speed))
            self.settings.save()
            
            # Apply to device if connected
            if hasattr(self.device, 'is_connected') and self.device.is_connected:
                # Schedule async operation
                asyncio.create_task(self._apply_fan_speed())
            
            self._emit_status_changed()
        except Exception as e:
            print(f"Error setting fan speed: {e}")
    
    @dbus.service.method(INTERFACE_NAME, in_signature='iii')
    def set_rgb_color(self, r, g, b):
        """Set RGB color"""
        try:
            self.settings.rgb_color = (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b))
            )
            self.settings.save()
            
            # Apply to device if connected
            if hasattr(self.device, 'is_connected') and self.device.is_connected:
                # Schedule async operation
                asyncio.create_task(self._apply_rgb_color())
            
            self._emit_status_changed()
        except Exception as e:
            print(f"Error setting RGB color: {e}")
    
    @dbus.service.method(INTERFACE_NAME, in_signature='i')
    def set_rgb_state(self, state):
        """Set RGB state"""
        try:
            from .enums import RGBState
            self.settings.rgb_state = RGBState(state)
            self.settings.save()
            
            # Apply to device if connected
            if hasattr(self.device, 'is_connected') and self.device.is_connected:
                # Schedule async operation
                asyncio.create_task(self._apply_rgb_state())
            
            self._emit_status_changed()
        except Exception as e:
            print(f"Error setting RGB state: {e}")
    
    @dbus.service.method(INTERFACE_NAME)
    def connect_device(self):
        """Connect to device"""
        try:
            # Schedule async operation
            asyncio.create_task(self._connect_device())
        except Exception as e:
            print(f"Error connecting device: {e}")
    
    @dbus.service.method(INTERFACE_NAME)
    def disconnect_device(self):
        """Disconnect from device"""
        try:
            # Schedule async operation
            asyncio.create_task(self._disconnect_device())
        except Exception as e:
            print(f"Error disconnecting device: {e}")
    
    @dbus.service.signal(INTERFACE_NAME, signature='s')
    def StatusChanged(self, status_json):
        """Signal emitted when status changes"""
        pass
    
    def _emit_status_changed(self):
        """Emit status changed signal"""
        try:
            status = self.get_status()
            self.StatusChanged(status)
        except Exception as e:
            print(f"Error emitting status change: {e}")
    
    # Async helper methods
    async def _apply_pump_voltage(self):
        """Apply pump voltage to device"""
        try:
            if hasattr(self.device, 'set_pump_voltage'):
                await self.device.set_pump_voltage(self.settings.current_voltage)
        except Exception as e:
            print(f"Error applying pump voltage: {e}")
    
    async def _apply_fan_speed(self):
        """Apply fan speed to device"""
        try:
            if hasattr(self.device, 'set_fan_speed'):
                await self.device.set_fan_speed(self.settings.current_fan_speed)
        except Exception as e:
            print(f"Error applying fan speed: {e}")
    
    async def _apply_rgb_color(self):
        """Apply RGB color to device"""
        try:
            if hasattr(self.device, 'set_rgb_color'):
                await self.device.set_rgb_color(*self.settings.rgb_color)
        except Exception as e:
            print(f"Error applying RGB color: {e}")
    
    async def _apply_rgb_state(self):
        """Apply RGB state to device"""
        try:
            if hasattr(self.device, 'set_rgb_state'):
                await self.device.set_rgb_state(self.settings.rgb_state)
        except Exception as e:
            print(f"Error applying RGB state: {e}")
    
    async def _connect_device(self):
        """Connect to device"""
        try:
            if hasattr(self.device, 'connect'):
                await self.device.connect()
                self._emit_status_changed()
        except Exception as e:
            print(f"Error connecting to device: {e}")
    
    async def _disconnect_device(self):
        """Disconnect from device"""
        try:
            if hasattr(self.device, 'disconnect'):
                await self.device.disconnect()
                self._emit_status_changed()
        except Exception as e:
            print(f"Error disconnecting from device: {e}")

else:
    # Fallback class when D-Bus is not available
    class WatercoolerDaemonService:
        """Fallback daemon service without D-Bus"""

        def __init__(self, watercooler_manager):
            print("D-Bus not available, daemon will run without D-Bus interface")
            self.watercooler_manager = watercooler_manager


def start_glib_main_loop():
    """Start GLib main loop for D-Bus in a separate thread"""
    if DBUS_AVAILABLE and GLib:
        try:
            loop = GLib.MainLoop()
            loop.run()
        except KeyboardInterrupt:
            pass
