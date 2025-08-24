# Daemon/UI Architecture Guide

This document explains how the Watercooler Manager handles UI interaction when running as a daemon service.

## 🏗️ Architecture Overview

The Watercooler Manager uses a **client-server architecture** with D-Bus communication:

```
┌─────────────────┐    D-Bus     ┌─────────────────┐
│   GUI Client    │◄────────────►│     Daemon      │
│  (User Space)   │              │ (System/User)   │
└─────────────────┘              └─────────────────┘
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │ Bluetooth Device│
                                 │  (Water Cooler) │
                                 └─────────────────┘
```

## 🔧 Operation Modes

### **1. Standalone GUI Mode** (Traditional)
```bash
watercooler-manager
```
- **When**: No daemon is running
- **Behavior**: GUI controls device directly
- **Use Case**: Single-user, desktop usage

### **2. Daemon + GUI Client Mode** (Recommended)
```bash
# Start daemon
sudo systemctl start watercooler-manager.service
# or
systemctl --user start watercooler-manager.service

# Start GUI client
watercooler-manager-gui
```
- **When**: Daemon is running
- **Behavior**: GUI connects to daemon via D-Bus
- **Use Case**: System service with GUI control

### **3. Daemon-Only Mode** (Headless)
```bash
# System daemon only
sudo systemctl start watercooler-manager.service
```
- **When**: Server/headless systems
- **Behavior**: Daemon runs without GUI
- **Use Case**: Servers, embedded systems

## 📡 D-Bus Communication

### **Service Details**
- **Service Name**: `org.watercooler.Manager`
- **Object Path**: `/org/watercooler/Manager`
- **Interface**: `org.watercooler.Manager`

### **Available Methods**
```python
# Device Control
connect_device()           # Connect to water cooler
disconnect_device()        # Disconnect from device

# Settings
set_pump_voltage(voltage)  # Set pump voltage (7-12V)
set_fan_speed(speed)       # Set fan speed (0-100%)
set_rgb_color(r, g, b)     # Set RGB color (0-255 each)
set_rgb_state(state)       # Set RGB state (static/breathing/etc)

# Status
get_status()               # Get device status as JSON
get_settings()             # Get current settings as JSON
ping()                     # Connection test
```

### **Signals**
```python
StatusChanged(status_json) # Emitted when device status changes
```

## 🖥️ GUI Client Features

### **Automatic Detection**
The main `watercooler-manager` command automatically detects if a daemon is running:

```python
# Automatic mode selection
if daemon_available:
    # Use D-Bus to communicate with daemon
    gui_mode = "client"
else:
    # Control device directly
    gui_mode = "standalone"
```

### **Dedicated GUI Client**
The `watercooler-manager-gui` command is a dedicated client that **requires** a running daemon:

```bash
watercooler-manager-gui
```
- ✅ Lightweight - no device drivers loaded
- ✅ Multiple instances can run simultaneously
- ✅ Real-time status updates via D-Bus signals
- ❌ Fails if no daemon is running

## 🔄 Status Synchronization

### **Real-time Updates**
- GUI clients receive status updates via D-Bus signals
- Changes made by one client are immediately visible to others
- Daemon maintains authoritative state

### **Update Flow**
```
User Action → GUI Client → D-Bus → Daemon → Device
                ↑                    ↓
Status Display ← D-Bus Signal ← Status Change
```

## 🛠️ Configuration Management

### **Daemon Configuration**
- **System Daemon**: `/etc/watercooler-manager/config.json`
- **User Daemon**: `~/.watercooler.json`
- **Environment Override**: `WATERCOOLER_CONFIG_PATH`

### **GUI Client Configuration**
- **Local Settings**: `~/.watercooler.json` (GUI preferences only)
- **Device Settings**: Retrieved from daemon via D-Bus

## 🚀 Usage Scenarios

### **Scenario 1: Desktop User**
```bash
# Option A: Traditional standalone
watercooler-manager

# Option B: Daemon + GUI (recommended)
systemctl --user start watercooler-manager.service
watercooler-manager  # Auto-detects daemon
```

### **Scenario 2: Server with Remote GUI**
```bash
# On server
sudo systemctl start watercooler-manager.service

# On desktop (via SSH X11 forwarding)
ssh -X server
watercooler-manager-gui
```

### **Scenario 3: Multi-user System**
```bash
# System daemon for all users
sudo systemctl start watercooler-manager.service

# Each user can run GUI client
watercooler-manager-gui
```

### **Scenario 4: Development/Testing**
```bash
# Terminal 1: Daemon with debug output
WATERCOOLER_DAEMON_MODE=1 watercooler-manager

# Terminal 2: GUI client
watercooler-manager-gui
```

## 🔧 Troubleshooting

### **GUI Can't Connect to Daemon**
```bash
# Check if daemon is running
systemctl --user status watercooler-manager.service
sudo systemctl status watercooler-manager.service

# Check D-Bus service
dbus-send --session --print-reply \
  --dest=org.watercooler.Manager \
  /org/watercooler/Manager \
  org.watercooler.Manager.ping
```

### **D-Bus Not Available**
- GUI falls back to direct device control
- Daemon runs without D-Bus interface
- Multiple GUI instances may conflict

### **Permission Issues**
```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## 🎯 Benefits of This Architecture

### **Reliability**
- ✅ Daemon survives GUI crashes
- ✅ Device connection maintained across GUI restarts
- ✅ System service starts automatically

### **Flexibility**
- ✅ Multiple GUI clients can connect simultaneously
- ✅ Remote GUI access via SSH/VNC
- ✅ Headless operation for servers

### **Performance**
- ✅ Single device connection shared by all clients
- ✅ Lightweight GUI clients
- ✅ Efficient D-Bus communication

### **Security**
- ✅ Daemon runs with restricted permissions
- ✅ GUI clients don't need device access
- ✅ System-wide or per-user isolation

This architecture provides the best of both worlds: the simplicity of a standalone GUI application with the robustness and flexibility of a system service.
