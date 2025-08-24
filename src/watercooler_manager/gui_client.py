#!/usr/bin/env python3
"""
Standalone GUI client for watercooler daemon
This can run independently of the main application to control a running daemon
"""

import sys
import time
import threading
from .daemon_client import DaemonClient
from .tray import SystemTrayIcon
from .settings import Settings
from .enums import PumpVoltage, RGBState


class WatercoolerGUIClient:
    """Standalone GUI client for daemon control"""
    
    def __init__(self, version="1.2.0"):
        self.version = version
        self.daemon_client = DaemonClient()
        self.settings = Settings()  # For GUI preferences only
        self.connected_to_daemon = False
        self.status_update_thread = None
        self.running = True
        
        # Try to connect to daemon
        self.connected_to_daemon = self.daemon_client.connect()
        
        if not self.connected_to_daemon:
            print("❌ Cannot connect to watercooler daemon")
            print("Please ensure the daemon is running:")
            print("  sudo systemctl start watercooler-manager.service")
            print("  or")
            print("  systemctl --user start watercooler-manager.service")
            sys.exit(1)
        
        # Create system tray with daemon-specific callbacks
        self.tray = SystemTrayIcon(
            on_connect=self.connect_device,
            on_disconnect=self.disconnect_device,
            on_pump_settings=self.set_pump_voltage,
            on_fan_settings=self.set_fan_speed,
            on_rgb_settings=self.set_rgb_settings,
            on_autostart_settings=self.handle_autostart_settings,
            on_autoconnect_settings=self.handle_autoconnect_settings,
            on_exit=self.exit_app,
            settings=self.settings,
            version=f"{self.version} (Client)"
        )
        
        # Subscribe to daemon updates
        self.daemon_client.subscribe_to_updates(self.on_daemon_status_update)
        
        # Start status update thread
        self.status_update_thread = threading.Thread(
            target=self._status_update_loop, 
            daemon=True
        )
        self.status_update_thread.start()
    
    def run(self):
        """Run the GUI client"""
        print(f"✅ Watercooler GUI Client v{self.version} connected to daemon")
        
        # Setup and run the system tray
        self.tray.setup()
        self.tray.run()
    
    def connect_device(self):
        """Connect to device via daemon"""
        if self.daemon_client.connect_device():
            print("✅ Device connection requested via daemon")
        else:
            print("❌ Failed to request device connection")
    
    def disconnect_device(self):
        """Disconnect from device via daemon"""
        if self.daemon_client.disconnect_device():
            print("✅ Device disconnection requested via daemon")
        else:
            print("❌ Failed to request device disconnection")
    
    def set_pump_voltage(self, voltage: PumpVoltage):
        """Set pump voltage via daemon"""
        if self.daemon_client.set_pump_voltage(voltage):
            print(f"✅ Pump voltage set to {voltage} via daemon")
        else:
            print(f"❌ Failed to set pump voltage to {voltage}")
    
    def set_fan_speed(self, speed: int):
        """Set fan speed via daemon"""
        if self.daemon_client.set_fan_speed(speed):
            print(f"✅ Fan speed set to {speed}% via daemon")
        else:
            print(f"❌ Failed to set fan speed to {speed}%")
    
    def set_rgb_settings(self, state: RGBState, color: tuple = None):
        """Set RGB settings via daemon"""
        success = True
        
        if not self.daemon_client.set_rgb_state(state):
            print(f"❌ Failed to set RGB state to {state}")
            success = False
        
        if color and not self.daemon_client.set_rgb_color(*color):
            print(f"❌ Failed to set RGB color to {color}")
            success = False
        
        if success:
            color_str = f" and color {color}" if color else ""
            print(f"✅ RGB state set to {state}{color_str} via daemon")
    
    def handle_autostart_settings(self, enabled: bool):
        """Handle autostart settings (local GUI setting)"""
        self.settings.auto_start = enabled
        self.settings.save()
        print(f"✅ GUI autostart {'enabled' if enabled else 'disabled'}")
    
    def handle_autoconnect_settings(self, enabled: bool):
        """Handle autoconnect settings (this affects daemon)"""
        # Note: This would need to be implemented in the daemon service
        print(f"ℹ️  Autoconnect setting change requested: {enabled}")
        print("   (This setting is controlled by the daemon configuration)")
    
    def on_daemon_status_update(self, status: dict):
        """Handle status updates from daemon"""
        try:
            # Update local settings cache for tray display
            if 'pump_voltage' in status:
                self.settings.current_voltage = PumpVoltage(status['pump_voltage'])
            if 'fan_speed' in status:
                self.settings.current_fan_speed = status['fan_speed']
            if 'rgb_color' in status:
                self.settings.rgb_color = tuple(status['rgb_color'])
            if 'rgb_state' in status:
                self.settings.rgb_state = RGBState(status['rgb_state'])
            
            # Update tray icon if needed
            if hasattr(self.tray, 'update_status'):
                self.tray.update_status(status)
                
        except Exception as e:
            print(f"Error processing daemon status update: {e}")
    
    def _status_update_loop(self):
        """Periodically fetch status from daemon"""
        while self.running:
            try:
                if self.daemon_client.is_connected():
                    status = self.daemon_client.get_status()
                    if status:
                        self.on_daemon_status_update(status)
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"Error in status update loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def exit_app(self):
        """Exit the GUI client"""
        print("Shutting down GUI client...")
        self.running = False
        
        if self.daemon_client:
            self.daemon_client.disconnect()
        
        if hasattr(self.tray, 'stop'):
            self.tray.stop()


def main():
    """Main entry point for standalone GUI client"""
    try:
        client = WatercoolerGUIClient()
        client.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
