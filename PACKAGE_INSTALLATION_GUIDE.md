# Package Installation Guide

## 🎯 Current Status: Ready for Installation

The Watercooler Manager Arch Linux package has been successfully built and tested. Here's how to install and use it.

## 📦 Package Information

- **Package**: `watercooler-manager-1.2.0-1-x86_64.pkg.tar.zst`
- **Size**: ~100KB
- **Architecture**: Complete UI/Daemon system with D-Bus integration

## 🔧 Installation Methods

### Method 1: Direct Installation (Recommended for Testing)

Since some Python dependencies aren't available in official Arch repos, install them first:

```bash
# Install Python dependencies
pip install --user bleak==0.22.3 pillow==11.0.0 pystray==0.19.5 six==1.17.0 typing_extensions==4.12.2

# Install the package (will install system dependencies)
sudo pacman -U watercooler-manager-1.2.0-1-x86_64.pkg.tar.zst
```

### Method 2: System-wide Python Dependencies

```bash
# Install system dependencies first
sudo pacman -S python python-gobject python-cairo python-dbus gtk3 libappindicator-gtk3 libnotify

# Install Python packages system-wide
sudo pip install --break-system-packages bleak pillow pystray six typing_extensions

# Install the package
sudo pacman -U watercooler-manager-1.2.0-1-x86_64.pkg.tar.zst
```

## 🚀 Usage After Installation

### 1. GUI Application (Auto-Detection Mode)
```bash
watercooler-manager
```
- Automatically detects if daemon is running
- Uses daemon if available, direct control if not
- Creates system tray interface

### 2. Start User Daemon + GUI Client
```bash
# Start user daemon
systemctl --user start watercooler-manager.service

# Start GUI client (connects to daemon)
watercooler-manager-gui
```

### 3. System-wide Daemon + GUI Client
```bash
# Start system daemon
sudo systemctl start watercooler-manager.service

# Any user can connect with GUI client
watercooler-manager-gui
```

### 4. Enable Auto-start
```bash
# User daemon auto-start
systemctl --user enable watercooler-manager.service

# System daemon auto-start
sudo systemctl enable watercooler-manager.service
```

## 🔍 Verification Commands

### Check Service Status
```bash
# User service
systemctl --user status watercooler-manager.service

# System service
sudo systemctl status watercooler-manager.service
```

### Test D-Bus Communication
```bash
# Test daemon D-Bus interface (when daemon running)
dbus-send --session --print-reply \
  --dest=org.watercooler.Manager \
  /org/watercooler/Manager \
  org.watercooler.Manager.ping
```

### Check Logs
```bash
# User daemon logs
journalctl --user -u watercooler-manager.service -f

# System daemon logs
sudo journalctl -u watercooler-manager.service -f
```

## 🛠️ Configuration

### User Configuration
- **Location**: `~/.watercooler.json`
- **Used by**: GUI application and user daemon

### System Configuration
- **Location**: `/etc/watercooler-manager/config.json`
- **Used by**: System daemon

### Example Configuration
```json
{
    "current_voltage": 7,
    "current_fan_speed": 50,
    "pump_is_off": false,
    "fan_is_off": false,
    "rgb_state": 1,
    "rgb_is_off": false,
    "rgb_color": [255, 0, 0],
    "auto_start": false,
    "auto_connect": true
}
```

## 🔧 Troubleshooting

### Python Dependencies Missing
```bash
# Install missing dependencies
pip install --user bleak pillow pystray six typing_extensions
```

### Bluetooth Access Issues
```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER
# Logout/login required after group change
```

### D-Bus Service Not Found
```bash
# Check if daemon is running
systemctl --user status watercooler-manager.service

# Start daemon if not running
systemctl --user start watercooler-manager.service
```

### GUI Client Can't Connect
```bash
# Ensure daemon is running first
systemctl --user start watercooler-manager.service

# Then start GUI client
watercooler-manager-gui
```

## 🎯 Desktop Integration

The package includes desktop integration:

- **Application Menu**: Find "Watercooler Manager" in applications
- **Desktop Actions**: Right-click for daemon controls
- **System Tray**: GUI mode creates system tray icon

## 📋 What's Included

### Binaries
- `watercooler-manager` - Main application (auto-detect mode)
- `watercooler-manager-gui` - GUI client (requires daemon)
- `watercooler-manager-daemon` - Daemon wrapper script

### Services
- System daemon: `/usr/lib/systemd/system/watercooler-manager.service`
- User daemon: `/usr/lib/systemd/user/watercooler-manager.service`

### Integration
- Desktop entry: `/usr/share/applications/watercooler-manager.desktop`
- udev rules: `/usr/lib/udev/rules.d/99-watercooler-manager.rules`
- polkit policies: `/usr/share/polkit-1/actions/org.watercooler.manager.policy`

## 🎉 Success Indicators

After successful installation, you should see:

1. **✅ Commands available**: `watercooler-manager`, `watercooler-manager-gui`
2. **✅ Services available**: `systemctl --user status watercooler-manager.service`
3. **✅ Desktop entry**: Application appears in menu
4. **✅ Configuration**: `/etc/watercooler-manager/config.json` exists

## 🚀 Next Steps

1. **Test GUI**: Run `watercooler-manager` to test basic functionality
2. **Test Daemon**: Start daemon and connect with GUI client
3. **Configure Auto-start**: Enable systemd service for automatic startup
4. **Customize Settings**: Edit configuration files as needed

The package is production-ready and provides a complete professional water cooler management system! 🏆
