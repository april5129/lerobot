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

from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig

from ..config import RobotConfig


@RobotConfig.register_subclass("dofbot_se")
@dataclass
class DofbotSEConfig(RobotConfig):
    """Configuration for Dofbot SE robotic arm.
    
    The Dofbot SE is a 6-DOF robotic arm with:
    - 6 serial bus servos (joints 1-4, 6: 0-180 degrees, joint 5: 0-270 degrees)
    - RGB LED
    - Buzzer
    - Serial communication at 115200 baud
    """
    # Serial port to connect to the arm
    # Use `lerobot-find-port` to find the correct port
    # Example: "/dev/ttyUSB0" on Linux, "COM3" on Windows, "/dev/tty.usbmodem*" on macOS
    port: str
    
    # Baud rate for serial communication
    baudrate: int = 115200
    
    # Serial communication timeout in seconds
    # Increased timeout for gamepad mode where serial conflicts may occur
    timeout: float = 0.5
    
    # Disable torque on disconnect for safety
    disable_torque_on_disconnect: bool = True
    
    # Maximum relative target for safety (limits how far motors can move in one step)
    max_relative_target: float | dict[str, float] | None = 30.0  # degrees
    
    # Camera configurations
    cameras: dict[str, CameraConfig] = field(default_factory=dict)
    
    # Joint angle limits (in degrees)
    # Joints 1-4 and 6: 0-180 degrees, Joint 5: 0-270 degrees
    joint_limits: dict[str, tuple[float, float]] = field(default_factory=lambda: {
        "joint_1": (0.0, 180.0),
        "joint_2": (0.0, 180.0),
        "joint_3": (0.0, 180.0),
        "joint_4": (0.0, 180.0),
        "joint_5": (0.0, 270.0),
        "joint_6": (0.0, 180.0),
    })

