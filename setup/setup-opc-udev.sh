#!/usr/bin/env bash
# Install OPC sensor udev rules. Run as root: sudo ./setup-opc-udev.sh
set -e

cat > /etc/udev/rules.d/99-opc-sensors.rules <<'EOF'
# OPC Sensors - CP210x devices on the Genesys hub, named by physical port
SUBSYSTEM=="tty", DRIVERS=="cp210x", KERNELS=="1-1.3.1:*", SYMLINK+="sensor_0"
SUBSYSTEM=="tty", DRIVERS=="cp210x", KERNELS=="1-1.3.2:*", SYMLINK+="sensor_1"
SUBSYSTEM=="tty", DRIVERS=="cp210x", KERNELS=="1-1.3.3:*", SYMLINK+="sensor_2"
SUBSYSTEM=="tty", DRIVERS=="cp210x", KERNELS=="1-1.3.4:*", SYMLINK+="sensor_3"

# GRIMM - FTDI device, matched by VID/PID + serial on the USB device node
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="FTCB5KIB", SYMLINK+="GRIMM"
EOF

udevadm control --reload
udevadm trigger --subsystem-match=tty
udevadm settle

ls -l /dev/sensor_* /dev/GRIMM