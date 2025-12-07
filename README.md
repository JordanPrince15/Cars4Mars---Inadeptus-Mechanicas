
# 🚀 Cars4Mars 2026 – Team *Inadeptus-Mechanicas*  
### Mars Rover Design & Engineering Challenge  

Welcome to the official repository for our Cars4Mars 2026 rover project!  
This repo contains the hardware designs, software, documentation, CAD files, and research for our competition rover.

---

## 📌 Project Overview  
Cars4Mars 2026 is a pan-African Mars rover engineering challenge focused on designing a rover capable of:

- Traversing rocky and uneven terrain  
- Carrying a 1 kg science payload  
- Autonomous or semi-autonomous navigation  
- Real-time telemetry and video transmission  
- Completing mission tasks under time and energy constraints  

Our team is developing a modular rover platform using affordable components, robust mechanical systems, and reliable embedded software.

---

## 🧩 Subsystems  

### 🔹 **1. Mobility System**
- 8- wheel design  
- MG996R continuous rotation servos **or** GM3865 geared motors with encoders  
- Independent wheel control + optional suspension  
- Off-road wheels with shock absorption  
- Geared drivetrain for torque-heavy terrain  

### 🔹 **2. Chassis & Frame**
- PVC/aluminium hybrid structure  
- Shock-absorbing mounts  
- Weatherproof electronics housing  
- Custom 3D printed brackets and mounts  

### 🔹 **3. Computing & Control**
- Raspberry Pi (main computer)  
- Raspberry Pi Pico / Arduino (motor + sensor control)  
- Motor drivers (L298N / BTS7960 / Cytron)  
- Power management system  

### 🔹 **4. Sensors**
- IMU (MPU6050 / MPU9250 / BNO055)  
- Lidar / TOF sensor for mapping  
- Ultrasonic & IR sensors for obstacle detection  
- GPS module (navigation)  
- Soil moisture / pH sensor (science payload)

### 🔹 **5. Communications**
- HC-12 long-range 433MHz telemetry  
- FPV camera + 5.8GHz VTX for live video  
- Ground control station interface  

### 🔹 **6. Power System**
- 3S/4S LiPo battery  
- Power distribution board  
- XT60 connectors  
- Voltage regulation (5V / 3.3V)

---

## 🛠️ Repository Structure

