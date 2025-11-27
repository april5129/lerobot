# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Control tables and specifications for Dofbot serial bus servos.

Note: Dofbot uses a custom serial protocol, not a standard control table like Dynamixel/Feetech.
These definitions are for reference and compatibility with LeRobot's architecture.
"""

# Servo model identifiers
MODEL_DOFBOT_STANDARD = "dofbot_standard"  # Standard servos (joints 1-4, 6)
MODEL_DOFBOT_EXTENDED = "dofbot_extended"  # Extended range servo (joint 5)

# Protocol commands
CMD_RGB = 0x02
CMD_BUZZER = 0x06
CMD_SERVO_WRITE = 0x10  # Base for individual servo control (0x10 + servo_id)
CMD_SERVO_WRITE_ALL = 0x1D  # Control all 6 servos
CMD_SERVO_READ = 0x30  # Base for reading servo position (0x30 + servo_id)
CMD_TORQUE = 0x1A

# Servo position ranges (in raw units)
SERVO_RAW_MIN = 900
SERVO_RAW_MAX = 3100
SERVO_5_RAW_MIN = 380  # Joint 5 has extended range
SERVO_5_RAW_MAX = 3700

# Angle ranges (in degrees)
STANDARD_ANGLE_MIN = 0.0
STANDARD_ANGLE_MAX = 180.0
EXTENDED_ANGLE_MIN = 0.0
EXTENDED_ANGLE_MAX = 270.0

# Resolution (raw units per degree)
STANDARD_RESOLUTION = int((SERVO_RAW_MAX - SERVO_RAW_MIN) / (STANDARD_ANGLE_MAX - STANDARD_ANGLE_MIN))
EXTENDED_RESOLUTION = int((SERVO_5_RAW_MAX - SERVO_5_RAW_MIN) / (EXTENDED_ANGLE_MAX - EXTENDED_ANGLE_MIN))

# Model specifications
MODEL_SPECS = {
    MODEL_DOFBOT_STANDARD: {
        "angle_min": STANDARD_ANGLE_MIN,
        "angle_max": STANDARD_ANGLE_MAX,
        "raw_min": SERVO_RAW_MIN,
        "raw_max": SERVO_RAW_MAX,
        "resolution": STANDARD_RESOLUTION,
    },
    MODEL_DOFBOT_EXTENDED: {
        "angle_min": EXTENDED_ANGLE_MIN,
        "angle_max": EXTENDED_ANGLE_MAX,
        "raw_min": SERVO_5_RAW_MIN,
        "raw_max": SERVO_5_RAW_MAX,
        "resolution": EXTENDED_RESOLUTION,
    },
}

# Default communication settings
DEFAULT_PORT = "/dev/myserial"
DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT = 0.2

# Servo mounting orientations
# Servos 2, 3, 4 are mounted in reverse, requiring angle inversion
REVERSED_SERVOS = [2, 3, 4]

# Servo ID to model mapping (1-indexed as per Dofbot convention)
SERVO_MODELS = {
    1: MODEL_DOFBOT_STANDARD,  # Base rotation
    2: MODEL_DOFBOT_STANDARD,  # Shoulder
    3: MODEL_DOFBOT_STANDARD,  # Elbow
    4: MODEL_DOFBOT_STANDARD,  # Wrist pitch
    5: MODEL_DOFBOT_EXTENDED,  # Wrist roll (extended range)
    6: MODEL_DOFBOT_STANDARD,  # Gripper
}

# Protocol packet structure
PACKET_HEADER = 0xFF
PACKET_DEVICE_ID = 0xFC
PACKET_RESPONSE_ID = 0xFB  # Device responses use 0xFB

# Timing constants (in seconds)
COMMAND_DELAY = 0.01  # Delay after sending command
READ_RETRY_DELAY = 0.001  # Delay between read retries
CONNECTION_SETTLE_TIME = 0.2  # Wait time after opening port

