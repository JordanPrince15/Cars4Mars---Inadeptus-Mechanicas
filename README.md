
# 🚀 Cars4Mars 2026 – Team *Inadeptus-Mechanicas*  
### Mars Rover Design & Engineering Challenge  

Welcome to the official repository for our Cars4Mars 2026 rover project!  
This repo contains the hardware designs, software, documentation, CAD files, and research for our competition rover.
Recently, we uploaded a video on YouTube showcasing what the rover can do: 
https://www.youtube.com/watch?v=LHno_W5JRfo


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
- PVC structure  
- Shock-absorbing mounts  
- Weatherproof electronics housing  
- Custom 3D-printed brackets and mounts  

### 🔹 **3. Computing & Control**
- Raspberry Pi (main computer)  
- Raspberry Pi Pico / Arduino (motor + sensor control)  
- Motor drivers (L298N / BTS7960 / Cytron)  
- Power management system  

### 🔹 **4. Sensors**
- IMU (MPU6050 / MPU9250 / BNO055)  
- Lidar / TOF sensor for mapping  

### 🔹 **5. Communications**
- HC-12 long-range 433MHz telemetry  
- FPV camera + 5.8GHz VTX for live video  
- Ground control station interface  

### 🔹 **6. Power System**
- 3S/4S LiPo battery  
- Power distribution board  
- XT60 connectors  
- Voltage regulation (5V / 3.3V)


# Jeb Computer Vision

Computer vision and autonomous mission-control software

The system handles camera input, balloon detection, mission logic, and communication with the Raspberry Pi Pico responsible for rover movement.

---

## Project Status

### Currently implemented

* Camera input
* Roboflow balloon detection
* Balloon colour classification
* Target-balloon selection
* Balloon mission ordering
* Seeking for the current target
* Basic target tracking
* Left/right steering decisions
* Forward driving command
* Serial communication with the Raspberry Pi Pico
* Mock Pico mode when the Pico is unavailable
* UI display of balloon detections

### Not implemented yet

* Panoramic-image seeking
* Ultrasonic distance integration
* Reliable 1.5 m arrival detection
* 5-second arrival timer
* Automatic transition to the next balloon
* Robust target-loss recovery
* Advanced/proportional steering
* Full autonomous mission state machine
* Final mission completion logic

---

# Mission

Jeb must locate and visit the balloons in the following order:

```text
BLACK
  ↓
WHITE
  ↓
PINK
  ↓
YELLOW
  ↓
BLUE
```

For each balloon, the intended behaviour is:

```text
SEEK
  ↓
Find target
  ↓
TRACK
  ↓
Approach target
  ↓
Stop within 1.5 m
  ↓
Remain stopped for 5 seconds
  ↓
Next balloon
```

The current software implements the **SEEK → TRACK** portion.

---

# System Architecture

```text
                         JEB COMPUTER
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Camera                                                 │
│    │                                                    │
│    ▼                                                    │
│  main.py                                                │
│    │                                                    │
│    ▼                                                    │
│  MissionController                                      │
│    │                                                    │
│    ├── ObjectMission                                    │
│    │                                                    │
│    └── BalloonMission                                   │
│             │                                           │
│             ├── SEEKING                                 │
│             │                                           │
│             └── TRACKING                                │
│                    │                                    │
│                    ▼                                    │
│              RobotController                            │
│                    │                                    │
└────────────────────┼────────────────────────────────────┘
                     │
                  Serial
                   COM7
                     │
                     ▼
              Raspberry Pi Pico
                     │
                     ▼
                  Motors
```

---

# Directory Structure

```text
JebsEyes/
│
├── main.py
│
├── mission_controller.py
├── object_mission.py
├── balloon_mission.py
├── balloon_decector.py
│
├── robot_controller.py
├── robot_state.py
│
├── hsv_ball.py
├── yolo_ball.py
├── fusion.py
│
└── ui/
    └── main_ui.py
```

---

# Main Components

## `main.py`

The main application entry point.

Responsibilities include:

* Starting the camera
* Reading camera frames
* Running the mission controller
* Updating `RobotState`
* Providing frames to the UI
* Maintaining the main vision loop

General flow:

```text
Camera
  ↓
Frame
  ↓
MissionController
  ↓
Mission
  ↓
RobotState
  ↓
UI
```

---

# `mission_controller.py`

Controls which mission is currently active.

The system supports:

```text
MANUAL
AUTONOMOUS
```

and currently has:

```text
OBJECTS
BALLOONS
```

When the balloon mission is selected:

```text
MissionController
       ↓
BalloonMission
```

The controller passes the camera frame to the balloon mission and returns the resulting detections and movement action.

---

# `balloon_mission.py`

This contains the main balloon-mission logic.

## Mission order

The target sequence is defined by:

```python
MISSION = [
    "black_balloon",
    "white_balloon",
    "pink_balloon",
    "yellow_balloon",
    "blue_balloon"
]
```

The mission starts with:

```text
black_balloon
```

and advances using `next_target()`.

---

## Mission States

The current mission uses:

```text
SEEKING
TRACKING
COMPLETE
```

### SEEKING

The rover is looking for the current target.

Example:

```text
Current target:
black_balloon
```

If Roboflow detects:

```text
pink_balloon
yellow_balloon
black_balloon
```

only:

```text
black_balloon
```

is used.

Once the target is found:

```text
SEEKING
   ↓
TRACKING
```

---

## TRACKING

Tracking uses the horizontal position of the detected balloon.

The camera image is divided conceptually into three regions:

```text
┌─────────────────────────────────────────┐
│                                         │
│       LEFT       CENTRE       RIGHT     │
│                                         │
└─────────────────────────────────────────┘
```

The centre of the image is calculated using:

```python
frame_center = frame_width / 2
```

The balloon's horizontal error is:

```python
error = balloon_x - frame_center
```

Therefore:

```text
error < 0
    ↓
balloon is LEFT

error > 0
    ↓
balloon is RIGHT

error ≈ 0
    ↓
balloon is CENTRED
```

A deadzone is currently used:

```python
deadzone = 50
```

Movement decisions are:

```text
Balloon left
    ↓
T L
```

```text
Balloon right
    ↓
T R
```

```text
Balloon centred
    ↓
D 50
```

---

# Movement Commands

Movement commands are sent as ASCII strings over serial.

### Turn left

```text
T L
```

### Turn right

```text
T R
```

### Drive forward

```text
D 50
```

The general drive format is:

```text
D [speed]
```

where the speed range is:

```text
-100 → +100
```

Negative values represent reverse motion and positive values represent forward motion.

The current tracking implementation only uses:

```text
D 50
```

for forward motion.

---

# `robot_controller.py`

Handles communication with the Raspberry Pi Pico.

The mission code determines **what** movement is required.

`RobotController` determines **how** the command is transmitted.

The main method is:

```python
makeMovementCommand(command)
```

Example:

```python
self.robot.makeMovementCommand("T L")
```

This sends:

```text
T L\n
```

over the serial connection.

---

# Serial Connection

The current default configuration is:

```text
Port: COM7
Baud rate: 115200
```

The controller attempts to connect using:

```python
serial.Serial(
    self.port,
    self.baudrate
)
```

If the Pico cannot be found, the controller enters mock mode.

Example:

```text
[MOCK PICO] Movement command: T L
```

This allows the computer-vision and mission logic to be tested without the physical rover.

---

# `balloon_decector.py`

Handles Roboflow inference.

> Note: the filename is currently spelled `balloon_decector.py`. Do not rename it unless all imports are updated.

The detector:

1. Receives a camera frame.
2. Temporarily saves it as a JPEG.
3. Sends the image to the Roboflow workflow.
4. Receives the detections.
5. Converts the result into a standard detection format.
6. Deletes the temporary image.

Each detection has the form:

```python
{
    "class": "black_balloon",
    "confidence": 0.72,
    "x": 420,
    "y": 350,
    "width": 183,
    "height": 241
}
```

---

# Roboflow Configuration

The current workflow is:

```text
Workspace:
jagman05

Workflow:
balloon-color-detection-v8vdm
```

The detector uses approximately:

```text
Confidence: 0.4
IoU threshold: 0.3
Maximum detections: 1000
```

The API key should **never be committed to Git**.

Use an environment variable or another secure configuration method instead.

If an API key has previously been exposed, revoke/regenerate it before using the repository publicly.

---

# Detection Pipeline

The current pipeline is:

```text
Camera Frame
     ↓
BalloonDetector
     ↓
Roboflow
     ↓
Raw predictions
     ↓
_parse_result()
     ↓
Clean detections
     ↓
BalloonMission
```

The mission then filters the detections based on the current target.

For example:

```text
Current target:
black_balloon
```

Roboflow returns:

```text
black_balloon   0.72
pink_balloon    0.81
yellow_balloon  0.65
```

The mission uses:

```text
black_balloon   0.72
```

and ignores the others.

---

# Target Selection

If multiple balloons of the current colour are detected, the highest-confidence detection is selected.

Example:

```text
black_balloon  0.58
black_balloon  0.81
black_balloon  0.63
```

The selected target is:

```text
black_balloon  0.81
```

This is handled by:

```python
max(
    matching,
    key=lambda detection: detection["confidence"]
)
```

---

# Command Timing

Movement commands are limited to one command every:

```text
0.2 seconds
```

This corresponds to:

```text
5 commands per second
```

The timing is implemented using:

```python
time.monotonic()
```

and:

```python
self.command_interval = 0.2
```

This prevents the computer from continuously flooding the Pico with commands.

The Raspberry Pi/Pico-side safety timeout is handled separately by the onboard system.

---

# Robot State

`robot_state.py` stores information shared between the mission system and UI.

Relevant balloon information includes:

```python
balloon_detected
balloon_class
balloon_x
balloon_y
balloon_width
balloon_height
balloon_confidence
balloon_detections
balloon_target
balloon_status
```

The state also contains:

```python
distance_cm
```

for future ultrasonic integration.

---

# Current Tracking Algorithm

The current algorithm is intentionally simple.

```text
                Balloon
                   │
                   ▼
             Get balloon X
                   │
                   ▼
          Calculate image centre
                   │
                   ▼
              Calculate error
                   │
          ┌────────┼────────┐
          │        │        │
       LEFT     CENTRE     RIGHT
          │        │        │
          ▼        ▼        ▼
         T L      D 50      T R
```

This is a first-stage controller and is expected to be tuned after testing on the actual rover.

---

# Running the System

From the project environment, run the main application using the project's normal entry point.

For example:

```bash
python main.py
```

Make sure the required Python dependencies are installed.

The system should initialize:

```text
Camera
Roboflow detector
Mission controller
Balloon mission
Robot controller
UI
```

---

# Testing Without the Robot

Before testing physical movement, use the mock Pico mode.

If `COM7` is unavailable, you should see something similar to:

```text
❌ Failed to connect to Pico on COM7
```

and movement commands should appear as:

```text
[MOCK PICO] Movement command: T L
```

or:

```text
[MOCK PICO] Movement command: T R
```

or:

```text
[MOCK PICO] Movement command: D 50
```

This allows tracking decisions to be tested independently of the rover.

---

# Expected Tracking Behaviour

With the target on the left:

```text
[BALLOON TRACKING]
X=400 | CENTER=640 | ERROR=-240 | COMMAND=T L
```

With the target on the right:

```text
[BALLOON TRACKING]
X=900 | CENTER=640 | ERROR=260 | COMMAND=T R
```

With the target approximately centred:

```text
[BALLOON TRACKING]
X=650 | CENTER=640 | ERROR=10 | COMMAND=D 50
```

---

# Current Limitations

## 1. No distance control

The system does not currently know how far Jeb is from the balloon.

The ultrasonic sensor will eventually be used for this.

---

## 2. No arrival detection

The mission does not yet automatically determine:

```text
≤ 1.5 m
```

from the target.

---

## 3. No five-second timer

Once Jeb reaches the target, the required five-second waiting period has not yet been implemented.

---

## 4. No automatic target transition

`next_target()` exists, but the current tracking system does not automatically call it.

---

## 5. Target loss immediately returns to seeking

If the target disappears from the detections:

```text
TRACKING
    ↓
target lost
    ↓
SEEKING
```

A more robust target-loss strategy will be added later.

---

## 6. Basic steering

The current controller only has:

```text
T L
T R
D 50
```

It does not yet dynamically vary turning or driving speed based on how far the balloon is from the centre.

---

## 7. Roboflow inference latency

Inference currently occurs through the remote Roboflow workflow.

This introduces network and inference latency.

For final rover operation, inference frequency and/or local inference may need to be optimized.

---

# Planned Development

The intended development path is:

```text
CURRENT
   │
   ├── Balloon detection             ✓
   ├── Target selection              ✓
   ├── Seeking                       ✓ Basic
   ├── Tracking                      ✓ Basic
   │
   ▼
NEXT
   │
   ├── Tune steering
   ├── Improve target-loss handling
   ├── Reduce inference latency
   │
   ▼
DISTANCE
   │
   ├── Integrate ultrasonic sensor
   ├── Detect ≤1.5 m
   └── Stop rover
   │
   ▼
ARRIVAL
   │
   ├── Five-second timer
   └── Advance target
   │
   ▼
FULL MISSION
   │
   ├── Black
   ├── White
   ├── Pink
   ├── Yellow
   └── Blue
   │
   ▼
MISSION COMPLETE
```

---

# Development Philosophy

The Jeb software is being developed incrementally.

The goal is to verify each layer independently before adding the next layer:

```text
Detection
    ↓
Target selection
    ↓
Seeking
    ↓
Tracking
    ↓
Movement
    ↓
Distance
    ↓
Arrival
    ↓
Mission progression
```

This makes it easier to identify whether a problem originates from:

* the camera,
* Roboflow,
* detection parsing,
* mission logic,
* tracking,
* serial communication,
* or the rover hardware.

---

# Safety During Testing

Initial tracking tests should be performed with the rover unable to move freely, using mock Pico mode where possible.

First verify that the computer produces the correct commands:

```text
T L
T R
D 50
```

based on the balloon's position.

Only after the decisions are behaving correctly should the movement interface be tested on the physical rover in a controlled environment.

---

# Team

**Team:** Inadeptus Mechanicus
**Project:** Jeb — Cars4Mars Rover

---

# Current Core Files

| File                    | Purpose                          |
| ----------------------- | -------------------------------- |
| `main.py`               | Main application and camera loop |
| `mission_controller.py` | Selects and runs missions        |
| `balloon_mission.py`    | Balloon seeking and tracking     |
| `balloon_decector.py`   | Roboflow balloon detection       |
| `robot_controller.py`   | Pico serial communication        |
| `robot_state.py`        | Shared rover/mission state       |
| `main_ui.py`            | User interface                   |
| `object_mission.py`     | Object-detection mission         |
| `hsv_ball.py`           | HSV-based ball detection         |
| `yolo_ball.py`          | YOLO-based ball detection        |
| `fusion.py`             | Vision fusion logic              |

---

## Version Status

**Balloon Mission:** Early autonomous tracking implementation

**Current milestone:**

> Detect the correct balloon, transition from SEEKING to TRACKING, and generate movement commands based on the balloon's horizontal position.

