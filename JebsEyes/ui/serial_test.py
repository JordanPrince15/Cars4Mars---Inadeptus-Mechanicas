import serial
import time

try:
    # Try connecting to the real hardware
    pico = serial.Serial("COM7", 115200, timeout=1)
    is_mock = False
    print("✅ Connected to Pico on COM7")
except (serial.SerialException, FileNotFoundError):
    # Fallback simulation mode if hardware is missing
    pico = None
    is_mock = True
    print("⚠️ Pico not found on COM7. Running in SIMULATION MODE.")

# Give the hardware a moment to boot/initialize if connected
time.sleep(2)

while True:
    try:
        if not is_mock:
            pico.write(b"LEFT\n")
            # Clear buffers to ensure prompt physical transmission
            pico.flush() 
            print("Sent LEFT (Hardware)")
        else:
            print("Sent LEFT (Simulation Mock)")
            
        time.sleep(1)

        if not is_mock:
            pico.write(b"RIGHT\n")
            pico.flush()
            print("Sent RIGHT (Hardware)")
        else:
            print("Sent RIGHT (Simulation Mock)")
            
        time.sleep(1)
        
    except Exception as e:
        print(f"❌ Connection lost during transmission: {e}")
        is_mock = True
        time.sleep(2)