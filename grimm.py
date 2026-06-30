#!/usr/bin/env python3
import serial
import time

PORT = "/dev/GRIMM"
BAUD = 9600

print(f"Connecting to {PORT} at {BAUD} baud...")
with serial.Serial(PORT, BAUD, timeout=2) as ser:
    # Check version
    print("Checking firmware version...")
    ser.write(b"v\r")
    time.sleep(1)
    version_response = ser.read(300).decode(errors="ignore").strip()
    print(f"Response: {version_response}\n")
    
    if "7.80" not in version_response:
        print("ERROR: Not version 7.80. Exiting.")
        exit(1)
    
    print("✓ Version 7.80 detected. Reading particle sizes...\n")
    print("ID\t\tPM1.0\t\tPM2.5\t\tPM10")
    print("-" * 50)
    
    while True:
        try:
            line = ser.readline().decode("ascii").strip()
            
            if not line or len(line) < 4:
                continue
            
            values = [v for v in line.split() if v]
            
            # Skip status messages and incomplete lines
            if values[0].upper() == 'P' or len(values) < 4:
                continue
            
            # Parse N-lines using grimm.py ordering
            line_id = values[0]
            pm10 = values[1]   # PM10
            pm25 = values[2]   # PM2.5
            pm10_dup = values[3]  # PM1.0
            
            print(f"{line_id}\t\t{pm10}\t\t{pm25}\t\t{pm10_dup}")
            
        except (UnicodeDecodeError, ValueError, IndexError) as e:
            continue
        except KeyboardInterrupt:
            print("\n\nStopped.")
            break