import asyncio
import threading
import os
import signal
import sys
import time
from .device import WaterCoolingDevice
from .settings import Settings
from .tray import SystemTrayIcon
from .enums import PumpVoltage, RGBState
from .daemon_service import WatercoolerDaemonService, start_glib_main_loop, DBUS_AVAILABLE
from .daemon_client import DaemonClient
import pystray

class WaterCoolerManager:
    def __init__(self, version=None):
        self.settings = Settings()
        self.device = WaterCoolingDevice()
        self.loop = asyncio.new_event_loop()
        self.daemon_mode = self.settings.daemon_mode
        self.running = True
        self.version = version if version is not None else "v1.2.0"
        self.daemon_service = None
        self.daemon_client = None

        # Setup based on mode
        if self.daemon_mode:
            # Daemon mode: Setup D-Bus service and signal handlers
            self.tray = None
            if DBUS_AVAILABLE:
                self.daemon_service = WatercoolerDaemonService(self)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        else:
            # GUI mode: Try to connect to daemon first, fallback to direct control
            self.daemon_client = DaemonClient()
            daemon_connected = self.daemon_client.connect()

            if daemon_connected:
                print("✅ Connected to daemon, GUI will control via D-Bus")
                self.tray = SystemTrayIcon(
                    on_connect=self.connect_menu_via_daemon,
                    on_disconnect=self.disconnect_menu_via_daemon,
                    on_pump_settings=self.handle_pump_settings_via_daemon,
                    on_fan_settings=self.handle_fan_settings_via_daemon,
                    on_rgb_settings=self.handle_rgb_settings_via_daemon,
                    on_autostart_settings=self.handle_autostart_settings,
                    on_autoconnect_settings=self.handle_autoconnect_settings,
                    on_exit=self.exit_app,
                    settings=self.settings,
                    version=self.version
                )
            else:
                print("ℹ️  No daemon found, GUI will control device directly")
                self.tray = SystemTrayIcon(
                    on_connect=self.connect_menu,
                    on_disconnect=self.disconnect_menu,
                    on_pump_settings=self.handle_pump_settings,
                    on_fan_settings=self.handle_fan_settings,
                    on_rgb_settings=self.handle_rgb_settings,
                    on_autostart_settings=self.handle_autostart_settings,
                    on_autoconnect_settings=self.handle_autoconnect_settings,
                    on_exit=self.exit_app,
                    settings=self.settings,
                    version=self.version
                )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals in daemon mode"""
        print(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)

    def run(self):
        if self.daemon_mode:
            self._run_daemon()
        else:
            self._run_gui()

    def _run_gui(self):
        """Run in GUI mode with system tray"""
        # Setup and start the event loop in a separate thread
        def run_event_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        loop_thread = threading.Thread(target=run_event_loop, daemon=True)
        loop_thread.start()

        # Setup and run the system tray
        self.tray.setup()

        # Auto connect on startup
        if self.settings.auto_connect:
            asyncio.run_coroutine_threadsafe(self.connect_and_run(), self.loop)

        self.tray.run()

    def _run_daemon(self):
        """Run in daemon mode without GUI"""
        print(f"Starting Watercooler Manager daemon v{self.version}")
        print(f"Configuration: {self.settings.config_path}")
        print(f"D-Bus service: {'Available' if DBUS_AVAILABLE else 'Not available'}")

        # Setup and start the event loop
        asyncio.set_event_loop(self.loop)

        # Start D-Bus main loop in separate thread if available
        if DBUS_AVAILABLE and self.daemon_service:
            dbus_thread = threading.Thread(target=start_glib_main_loop, daemon=True)
            dbus_thread.start()
            print("✅ D-Bus service thread started")

        # Auto connect on startup
        if self.settings.auto_connect:
            self.loop.create_task(self.connect_and_run())

        # Start monitoring loop
        self.loop.create_task(self._daemon_monitor_loop())

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            print("Received keyboard interrupt, shutting down...")
        finally:
            self._cleanup()

    async def _daemon_monitor_loop(self):
        """Main monitoring loop for daemon mode"""
        print("Daemon monitoring loop started")

        while self.running:
            try:
                # Check device status every 30 seconds
                if self.device.is_connected:
                    # You could add periodic health checks here
                    pass
                else:
                    # Try to reconnect if auto_connect is enabled
                    if self.settings.auto_connect:
                        print("Device disconnected, attempting to reconnect...")
                        await self.connect_and_run()

                await asyncio.sleep(30)

            except Exception as e:
                print(f"Error in daemon monitor loop: {e}")
                await asyncio.sleep(5)

        print("Daemon monitoring loop stopped")

    def _cleanup(self):
        """Cleanup resources"""
        print("Cleaning up resources...")
        if self.device:
            try:
                future = asyncio.run_coroutine_threadsafe(self.device.disconnect(), self.loop)
                future.result(timeout=5)
            except Exception as e:
                print(f"Error during cleanup: {e}")

        if self.loop and not self.loop.is_closed():
            self.loop.close()

        print("Cleanup complete")

    # Daemon client methods for GUI mode
    def connect_menu_via_daemon(self):
        """Connect via daemon"""
        if self.daemon_client and self.daemon_client.is_connected():
            self.daemon_client.connect_device()

    def disconnect_menu_via_daemon(self):
        """Disconnect via daemon"""
        if self.daemon_client and self.daemon_client.is_connected():
            self.daemon_client.disconnect_device()

    def handle_pump_settings_via_daemon(self, voltage: PumpVoltage):
        """Handle pump settings via daemon"""
        if self.daemon_client and self.daemon_client.is_connected():
            self.daemon_client.set_pump_voltage(voltage)

    def handle_fan_settings_via_daemon(self, speed: int):
        """Handle fan settings via daemon"""
        if self.daemon_client and self.daemon_client.is_connected():
            self.daemon_client.set_fan_speed(speed)

    def handle_rgb_settings_via_daemon(self, state: RGBState, color: tuple = None):
        """Handle RGB settings via daemon"""
        if self.daemon_client and self.daemon_client.is_connected():
            self.daemon_client.set_rgb_state(state)
            if color:
                self.daemon_client.set_rgb_color(*color)

    def exit_app(self):
        future = asyncio.run_coroutine_threadsafe(self.device.disconnect(), self.loop)
        try:
            future.result(2)
        except Exception:
            pass
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.settings.save()
        self.tray.stop()

    def connect_menu(self):
        asyncio.run_coroutine_threadsafe(self.connect_and_run(), self.loop)

    def disconnect_menu(self):
        asyncio.run_coroutine_threadsafe(self.device.disconnect(), self.loop)
        self.tray.update_connection_status(False)

    async def connect_and_run(self):
        self.tray.show_notification("Scanning for CoolingSystem device...")
        devices = await self.device.get_device_list()
        
        if not devices:
            self.tray.show_notification("CoolingSystem device not found")
            return

        target_device = devices[0]
        self.tray.show_notification(f"Found device at {target_device.uuid}")
        
        try:
            await self.device.connect(target_device.uuid)
            self.tray.show_notification(f"Successfully connected to {target_device.name}")
            self.tray.update_connection_status(True)
            
            # Apply current settings
            await self.apply_current_settings()
            
        except Exception as e:
            self.tray.show_notification(f"Error occurred: {str(e)}")
            if await self.device.is_connected():
                await self.device.disconnect()
            self.tray.update_connection_status(False)

    async def apply_current_settings(self):
        await self.device.write_pump_mode(pump_voltage=self.settings.current_voltage)
        await self.device.write_fan_mode(self.settings.current_fan_speed)
        if not self.settings.rgb_is_off:
            await self.device.write_rgb(*self.settings.rgb_color, self.settings.rgb_state)

    def handle_pump_settings(self):
        menu = pystray.Menu(
            pystray.MenuItem('Turn Off', self._toggle_pump,
                           checked=lambda _: self.settings.pump_is_off),
            pystray.MenuItem('Voltage', pystray.Menu(
                pystray.MenuItem('7V', lambda: self._set_pump_voltage(PumpVoltage.V7),
                               checked=lambda _: not self.settings.pump_is_off and self.settings.current_voltage == PumpVoltage.V7),
                pystray.MenuItem('8V', lambda: self._set_pump_voltage(PumpVoltage.V8),
                               checked=lambda _: not self.settings.pump_is_off and self.settings.current_voltage == PumpVoltage.V8),
                pystray.MenuItem('11V', lambda: self._set_pump_voltage(PumpVoltage.V11),
                               checked=lambda _: not self.settings.pump_is_off and self.settings.current_voltage == PumpVoltage.V11)                
            ))
        )
        return menu

    def handle_fan_settings(self):
        menu = pystray.Menu(
            pystray.MenuItem('Turn Off', self._toggle_fan,
                           checked=lambda _: self.settings.fan_is_off),
            pystray.MenuItem('Speed', pystray.Menu(
                pystray.MenuItem('25%', lambda: self._set_fan_speed(25),
                               checked=lambda _: not self.settings.fan_is_off and self.settings.current_fan_speed == 25),
                pystray.MenuItem('50%', lambda: self._set_fan_speed(50),
                               checked=lambda _: not self.settings.fan_is_off and self.settings.current_fan_speed == 50),
                pystray.MenuItem('75%', lambda: self._set_fan_speed(75),
                               checked=lambda _: not self.settings.fan_is_off and self.settings.current_fan_speed == 75),
                pystray.MenuItem('90%', lambda: self._set_fan_speed(90),
                               checked=lambda _: not self.settings.fan_is_off and self.settings.current_fan_speed == 90)
            ))
        )
        return menu

    def handle_rgb_settings(self):
        menu = pystray.Menu(
            pystray.MenuItem('Turn Off', self._toggle_rgb,
                           checked=lambda _: self.settings.rgb_is_off),
            pystray.MenuItem('Mode', pystray.Menu(
                pystray.MenuItem('Static', lambda: self._set_rgb_mode(RGBState.STATIC),
                               checked=lambda _: not self.settings.rgb_is_off and self.settings.rgb_state == RGBState.STATIC),
                pystray.MenuItem('Breathe', lambda: self._set_rgb_mode(RGBState.BREATHE),
                               checked=lambda _: not self.settings.rgb_is_off and self.settings.rgb_state == RGBState.BREATHE),
                pystray.MenuItem('Rainbow', lambda: self._set_rgb_mode(RGBState.COLORFUL),
                               checked=lambda _: not self.settings.rgb_is_off and self.settings.rgb_state == RGBState.COLORFUL),
                pystray.MenuItem('Breathe Rainbow', lambda: self._set_rgb_mode(RGBState.BREATHE_COLOR),
                               checked=lambda _: not self.settings.rgb_is_off and self.settings.rgb_state == RGBState.BREATHE_COLOR)
            )),
            pystray.MenuItem('Color', pystray.Menu(
                pystray.MenuItem('Red', lambda: self._set_rgb_color(255, 0, 0),
                               checked=lambda _: not self.settings.rgb_is_off and self.settings.rgb_color == (255, 0, 0)),
                pystray.MenuItem('Green', lambda: self._set_rgb_color(0, 255, 0),
                               checked=lambda _: not self.settings.rgb_is_off and self.settings.rgb_color == (0, 255, 0)),
                pystray.MenuItem('Blue', lambda: self._set_rgb_color(0, 0, 255),
                               checked=lambda _: not self.settings.rgb_is_off and self.settings.rgb_color == (0, 0, 255)),
                pystray.MenuItem('White', lambda: self._set_rgb_color(255, 255, 255),
                               checked=lambda _: not self.settings.rgb_is_off and self.settings.rgb_color == (255, 255, 255))
            ))
        )
        return menu

    def handle_autostart_settings(self):
        self.settings.set_autostart(not self.settings.auto_start)

    def handle_autoconnect_settings(self):
        self.settings.auto_connect = not self.settings.auto_connect
        self.settings.save()

    def _toggle_pump(self):
        self.settings.pump_is_off = not self.settings.pump_is_off
        if self.settings.pump_is_off:
            asyncio.run_coroutine_threadsafe(self.device.write_pump_off(), self.loop)
        else:
            asyncio.run_coroutine_threadsafe(
                self.device.write_pump_mode(pump_voltage=self.settings.current_voltage), 
                self.loop
            )
        self.settings.save()

    def _set_pump_voltage(self, voltage: PumpVoltage):
        self.settings.current_voltage = voltage
        self.settings.pump_is_off = False
        asyncio.run_coroutine_threadsafe(
            self.device.write_pump_mode(pump_voltage=voltage),
            self.loop
        )
        self.settings.save()

    def _toggle_fan(self):
        self.settings.fan_is_off = not self.settings.fan_is_off
        if self.settings.fan_is_off:
            asyncio.run_coroutine_threadsafe(self.device.write_fan_off(), self.loop)
        else:
            asyncio.run_coroutine_threadsafe(
                self.device.write_fan_mode(self.settings.current_fan_speed),
                self.loop
            )
        self.settings.save()

    def _set_fan_speed(self, speed: int):
        self.settings.current_fan_speed = speed
        self.settings.fan_is_off = False
        asyncio.run_coroutine_threadsafe(
            self.device.write_fan_mode(speed),
            self.loop
        )
        self.settings.save()

    def _toggle_rgb(self):
        self.settings.rgb_is_off = not self.settings.rgb_is_off
        if self.settings.rgb_is_off:
            asyncio.run_coroutine_threadsafe(self.device.write_rgb_off(), self.loop)
        else:
            asyncio.run_coroutine_threadsafe(
                self.device.write_rgb(*self.settings.rgb_color, self.settings.rgb_state),
                self.loop
            )
        self.settings.save()

    def _set_rgb_mode(self, state: RGBState):
        self.settings.rgb_state = state
        self.settings.rgb_is_off = False
        asyncio.run_coroutine_threadsafe(
            self.device.write_rgb(*self.settings.rgb_color, state),
            self.loop
        )
        self.settings.save()

    def _set_rgb_color(self, red: int, green: int, blue: int):
        self.settings.rgb_color = (red, green, blue)
        self.settings.rgb_is_off = False
        asyncio.run_coroutine_threadsafe(
            self.device.write_rgb(red, green, blue, self.settings.rgb_state),
            self.loop
        )
        self.settings.save()