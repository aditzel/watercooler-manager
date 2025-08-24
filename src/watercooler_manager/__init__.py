"""
Water Cooler Manager - A system tray application to control LCT water cooling devices

Note: On Linux, you may see a deprecation warning about libayatana-appindicator.
This is a harmless warning from the pystray library's use of the older API.
The application functions normally despite this warning.
"""

from .app import WaterCoolerManager

__version__ = "1.2.0"
__all__ = ['WaterCoolerManager']

def main():
    """Main entry point for the application"""
    app = WaterCoolerManager(version=__version__)
    app.run()

if __name__ == "__main__":
    main()