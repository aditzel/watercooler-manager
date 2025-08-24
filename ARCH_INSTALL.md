# Arch Linux Installation Guide

This guide covers installing Watercooler Manager as a native Arch Linux package with systemd daemon support.

## Requirements

- **Python**: 3.9+ (3.8 is EOL as of 2024)
- **GTK**: 3.12+ for proper system tray support
- **PyGObject**: 3.42+ for Python-GTK bindings
- **systemd**: For daemon functionality

## Installation Methods

### Method 1: Using makepkg (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tomups/watercooler-manager.git
   cd watercooler-manager
   ```

2. **Build and install the package:**
   ```bash
   makepkg -si
   ```

3. **The package will automatically:**
   - Install all dependencies
   - Create system user and group
   - Install systemd service files
   - Set up udev rules for device access
   - Install desktop entry and icons

### Method 2: Manual Installation

If you prefer to install manually:

```bash
# Install dependencies
sudo pacman -S python python-bleak python-pillow python-pystray python-six \
               python-typing_extensions python-gobject python-cairo gtk3 \
               libappindicator-gtk3

# Install the Python package
pip install -e .

# Copy systemd files manually
sudo cp arch/watercooler-manager.service /usr/lib/systemd/system/
sudo cp arch/watercooler-manager-user.service /usr/lib/systemd/user/watercooler-manager.service
sudo cp arch/watercooler-manager-daemon /usr/bin/
sudo chmod +x /usr/bin/watercooler-manager-daemon

# Copy configuration and rules
sudo mkdir -p /etc/watercooler-manager
sudo cp arch/config.json /etc/watercooler-manager/
sudo cp arch/99-watercooler-manager.rules /usr/lib/udev/rules.d/
sudo cp arch/org.watercooler.manager.policy /usr/share/polkit-1/actions/

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Usage Options

### 1. GUI Application (Traditional)

Run the application with system tray interface:

```bash
watercooler-manager
```

### 2. User Daemon (Per-User Service)

Enable and start the user service:

```bash
# Enable for current user
systemctl --user enable watercooler-manager.service
systemctl --user start watercooler-manager.service

# Check status
systemctl --user status watercooler-manager.service

# View logs
journalctl --user -u watercooler-manager.service -f
```

### 3. System Daemon (System-Wide Service)

Enable and start the system service:

```bash
# Enable system-wide
sudo systemctl enable watercooler-manager.service
sudo systemctl start watercooler-manager.service

# Check status
sudo systemctl status watercooler-manager.service

# View logs
sudo journalctl -u watercooler-manager.service -f
```

## Configuration

### User Configuration
- **Location:** `~/.watercooler.json`
- **Used by:** GUI application and user daemon

### System Configuration
- **Location:** `/etc/watercooler-manager/config.json`
- **Used by:** System daemon
- **Permissions:** Readable by watercooler group

### Configuration Options

```json
{
    "current_voltage": 7,
    "current_fan_speed": 50,
    "pump_is_off": false,
    "fan_is_off": false,
    "rgb_state": 1,
    "rgb_is_off": false,
    "rgb_color": [255, 0, 0],
    "auto_start": true,
    "auto_connect": true
}
```

## Permissions and Security

The package automatically sets up:

- **watercooler system user/group** for daemon operation
- **udev rules** for Bluetooth device access
- **polkit policies** for privilege escalation
- **systemd security hardening** in service files

## Troubleshooting

### Check Service Status
```bash
# User service
systemctl --user status watercooler-manager.service

# System service
sudo systemctl status watercooler-manager.service
```

### View Logs
```bash
# User service logs
journalctl --user -u watercooler-manager.service -f

# System service logs
sudo journalctl -u watercooler-manager.service -f

# Daemon logs (system service only)
sudo tail -f /var/log/watercooler-manager/watercooler-manager.log
```

### Device Access Issues
```bash
# Check if user is in bluetooth group
groups $USER

# Add user to bluetooth group if needed
sudo usermod -a -G bluetooth $USER

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Bluetooth Issues
```bash
# Check Bluetooth service
sudo systemctl status bluetooth.service

# Restart Bluetooth if needed
sudo systemctl restart bluetooth.service
```

## Uninstallation

```bash
# Stop and disable services
systemctl --user stop watercooler-manager.service
systemctl --user disable watercooler-manager.service
sudo systemctl stop watercooler-manager.service
sudo systemctl disable watercooler-manager.service

# Remove package
sudo pacman -R watercooler-manager
```

## Desktop Integration

The package includes a desktop entry with actions:

- **Start Daemon:** Launch user daemon
- **Stop Daemon:** Stop user daemon  
- **Check Status:** View daemon status

Access via application menu or:
```bash
gtk-launch watercooler-manager
```

## Advanced Usage

### Custom Configuration Path
```bash
# Set custom config for daemon
sudo systemctl edit watercooler-manager.service
```

Add:
```ini
[Service]
Environment=WATERCOOLER_CONFIG_PATH=/path/to/custom/config.json
```

### Running Multiple Instances
The system daemon and user daemon can run simultaneously with different configurations, allowing both system-wide management and per-user customization.
