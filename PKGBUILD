# Maintainer: Allan Ditzel <allan@allanditzel.com>
pkgname=watercooler-manager
pkgver=1.2.0
pkgrel=1
pkgdesc="System tray application for managing LCT water coolers with systemd daemon support"
arch=('x86_64')
url="https://github.com/tomups/watercooler-manager"
license=('MIT')
depends=(
    'python>=3.9'
    'python-bleak>=0.22.0'
    'python-pillow>=11.0.0'
    'python-pystray>=0.19.0'
    'python-six>=1.17.0'
    'python-typing_extensions>=4.12.0'
    'python-gobject>=3.42.0'
    'python-cairo>=1.20.0'
    'python-dbus'
    'gtk3>=3.12'
    'libappindicator-gtk3'
    'gir1.2-notify-0.7'
)
makedepends=(
    'python-build'
    'python-installer'
    'python-wheel'
    'python-setuptools'
)
optdepends=(
    'systemd: for daemon functionality'
    'polkit: for device access permissions'
)
backup=(
    'etc/watercooler-manager/config.json'
)
source=()
sha256sums=()

prepare() {
    # Copy current directory contents to srcdir for building
    cp -r "${startdir}"/* "${srcdir}/" || true

    # Modern Python packaging uses pyproject.toml (already included)
    # No need to generate setup.py
}

build() {
    cd "${srcdir}"
    python -m build --wheel --no-isolation
}

package() {
    cd "${srcdir}"
    
    # Install Python package
    python -m installer --destdir="$pkgdir" dist/*.whl
    
    # Install systemd service files
    install -Dm644 "arch/watercooler-manager.service" \
        "${pkgdir}/usr/lib/systemd/system/watercooler-manager.service"
    install -Dm644 "arch/watercooler-manager-user.service" \
        "${pkgdir}/usr/lib/systemd/user/watercooler-manager.service"
    
    # Install desktop entry
    install -Dm644 "arch/watercooler-manager.desktop" \
        "${pkgdir}/usr/share/applications/watercooler-manager.desktop"
    
    # Install icons
    install -Dm644 "src/icons/connected.png" \
        "${pkgdir}/usr/share/pixmaps/watercooler-manager.png"
    
    # Install configuration directory and default config
    install -Dm644 "arch/config.json" \
        "${pkgdir}/etc/watercooler-manager/config.json"
    
    # Install udev rules for device access
    install -Dm644 "arch/99-watercooler-manager.rules" \
        "${pkgdir}/usr/lib/udev/rules.d/99-watercooler-manager.rules"
    
    # Install polkit policy
    install -Dm644 "arch/org.watercooler.manager.policy" \
        "${pkgdir}/usr/share/polkit-1/actions/org.watercooler.manager.policy"
    
    # Install wrapper script for daemon mode
    install -Dm755 "arch/watercooler-manager-daemon" \
        "${pkgdir}/usr/bin/watercooler-manager-daemon"
    
    # Install documentation
    install -Dm644 "README.md" "${pkgdir}/usr/share/doc/${pkgname}/README.md"
    
    # Create log directory
    install -dm755 "${pkgdir}/var/log/watercooler-manager"
}

post_install() {
    # Create watercooler system user and group
    getent group watercooler >/dev/null || groupadd -r watercooler
    getent passwd watercooler >/dev/null || useradd -r -g watercooler -d /var/lib/watercooler -s /bin/false -c "Watercooler Manager daemon" watercooler

    # Create directories with proper permissions
    mkdir -p /var/lib/watercooler
    mkdir -p /var/log/watercooler-manager
    mkdir -p /run/watercooler-manager
    chown watercooler:watercooler /var/lib/watercooler
    chown watercooler:watercooler /var/log/watercooler-manager
    chown watercooler:watercooler /run/watercooler-manager

    # Reload udev rules
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger 2>/dev/null || true

    echo "==> Watercooler Manager installed successfully!"
    echo ""
    echo "==> To enable the system daemon:"
    echo "    sudo systemctl enable --now watercooler-manager.service"
    echo ""
    echo "==> To enable per-user daemon:"
    echo "    systemctl --user enable --now watercooler-manager.service"
    echo ""
    echo "==> To run as GUI application:"
    echo "    watercooler-manager"
    echo ""
    echo "==> Configuration file: /etc/watercooler-manager/config.json"
    echo "==> User config file: ~/.watercooler.json"
    echo ""
    echo "==> Add your user to the bluetooth group for device access:"
    echo "    sudo usermod -a -G bluetooth \$USER"
    echo "    (logout/login required after group change)"
}

post_upgrade() {
    post_install
}

pre_remove() {
    systemctl --quiet is-active watercooler-manager.service && \
        systemctl stop watercooler-manager.service
    systemctl --quiet is-enabled watercooler-manager.service && \
        systemctl disable watercooler-manager.service
}
