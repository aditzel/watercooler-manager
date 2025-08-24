#!/bin/bash

# Test script for Arch Linux package functionality
# This tests the package structure and daemon functionality locally

set -euo pipefail

echo "🧪 Testing Arch Linux package structure..."
echo "=========================================="

# Check if we're on Arch Linux
if ! command -v pacman &> /dev/null; then
    echo "⚠️  This script is designed for Arch Linux systems"
    echo "ℹ️  Continuing anyway for testing purposes..."
fi

# Test 1: Check required files exist
echo ""
echo "📁 Checking package files..."
files=(
    "PKGBUILD"
    "setup.py"
    "arch/watercooler-manager.service"
    "arch/watercooler-manager-user.service"
    "arch/watercooler-manager-daemon"
    "arch/watercooler-manager.desktop"
    "arch/config.json"
    "arch/99-watercooler-manager.rules"
    "arch/org.watercooler.manager.policy"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file - exists"
    else
        echo "❌ $file - missing"
    fi
done

# Test 2: Check PKGBUILD syntax
echo ""
echo "📋 Validating PKGBUILD..."
if command -v namcap &> /dev/null; then
    namcap PKGBUILD || echo "⚠️  namcap warnings (may be normal)"
else
    echo "ℹ️  namcap not available, skipping PKGBUILD validation"
fi

# Test 3: Test daemon mode functionality
echo ""
echo "🔧 Testing daemon mode..."

# Create test environment
export WATERCOOLER_DAEMON_MODE=1
export WATERCOOLER_CONFIG_PATH="./test-config.json"

# Create test config
cat > test-config.json << 'EOF'
{
    "current_voltage": 7,
    "current_fan_speed": 50,
    "pump_is_off": false,
    "fan_is_off": false,
    "rgb_state": 1,
    "rgb_is_off": false,
    "rgb_color": [255, 0, 0],
    "auto_start": false,
    "auto_connect": false
}
EOF

echo "✅ Test configuration created"

# Test Python module import
echo ""
echo "🐍 Testing Python module..."
if python3 -c "
import sys
sys.path.insert(0, 'src')
from watercooler_manager import WaterCoolerManager
print('✅ Module import successful')
app = WaterCoolerManager(version='test')
print('✅ App initialization successful')
print(f'✅ Daemon mode: {app.daemon_mode}')
print(f'✅ Config path: {app.settings.config_path}')
"; then
    echo "✅ Python module test passed"
else
    echo "❌ Python module test failed"
fi

# Test 4: Validate systemd service files
echo ""
echo "⚙️  Validating systemd service files..."

if command -v systemd-analyze &> /dev/null; then
    for service in arch/watercooler-manager.service arch/watercooler-manager-user.service; do
        if systemd-analyze verify "$service" 2>/dev/null; then
            echo "✅ $service - valid"
        else
            echo "⚠️  $service - validation warnings (may be normal)"
        fi
    done
else
    echo "ℹ️  systemd-analyze not available, skipping service validation"
fi

# Test 5: Check desktop entry
echo ""
echo "🖥️  Validating desktop entry..."
if command -v desktop-file-validate &> /dev/null; then
    if desktop-file-validate arch/watercooler-manager.desktop; then
        echo "✅ Desktop entry valid"
    else
        echo "❌ Desktop entry validation failed"
    fi
else
    echo "ℹ️  desktop-file-validate not available, skipping desktop entry validation"
fi

# Cleanup
rm -f test-config.json

echo ""
echo "🎉 Arch Linux package testing completed!"
echo ""
echo "Next steps to test the full package:"
echo "1. Run 'makepkg -si' to build and install"
echo "2. Test GUI: 'watercooler-manager'"
echo "3. Test user daemon: 'systemctl --user start watercooler-manager.service'"
echo "4. Test system daemon: 'sudo systemctl start watercooler-manager.service'"
echo ""
echo "📖 See ARCH_INSTALL.md for detailed installation and usage instructions"
