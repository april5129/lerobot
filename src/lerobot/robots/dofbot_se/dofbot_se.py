#!/usr/bin/env python

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
Dofbot SE robotic arm implementation for LeRobot.

The Dofbot SE is a 6-DOF educational robotic arm with serial bus servos.
This implementation provides a LeRobot-compatible interface for the Dofbot SE.
"""

import logging
import time
from functools import cached_property
from typing import Any

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from ..robot import Robot
from ..utils import ensure_safe_goal_position
from .config_dofbot_se import DofbotSEConfig
from .dofbot_serial import DofbotSerialDevice

logger = logging.getLogger(__name__)


class DofbotSE(Robot):
    """LeRobot interface for Dofbot SE robotic arm.
    
    The Dofbot SE is a 6-DOF robotic arm designed for education and research:
    - 6 serial bus servos with different angle ranges
    - RGB LED and buzzer for feedback
    - Serial communication at 115200 baud
    - Joints 1-4, 6: 0-180 degrees
    - Joint 5: 0-270 degrees (gripper rotation)
    
    Example usage:
        ```python
        from lerobot.robots.dofbot_se import DofbotSE, DofbotSEConfig
        
        config = DofbotSEConfig(port="/dev/ttyUSB0")
        robot = DofbotSE(config)
        robot.connect()
        
        # Get observation
        obs = robot.get_observation()
        
        # Send action
        action = {
            "joint_1.pos": 90.0,
            "joint_2.pos": 90.0,
            "joint_3.pos": 90.0,
            "joint_4.pos": 90.0,
            "joint_5.pos": 135.0,
            "joint_6.pos": 90.0,
        }
        robot.send_action(action)
        
        robot.disconnect()
        ```
    """

    config_class = DofbotSEConfig
    name = "dofbot_se"

    # Joint names in order (servo IDs 1-6)
    JOINT_NAMES = [
        "joint_1",  # Base rotation
        "joint_2",  # Shoulder
        "joint_3",  # Elbow
        "joint_4",  # Wrist pitch
        "joint_5",  # Wrist roll / gripper rotation
        "joint_6",  # Gripper
    ]

    def __init__(self, config: DofbotSEConfig):
        """Initialize Dofbot SE robot.
        
        Args:
            config: Configuration object for the robot
        """
        super().__init__(config)
        self.config = config
        
        # Initialize serial device
        self.device = DofbotSerialDevice(
            port=config.port,
            baudrate=config.baudrate,
            timeout=config.timeout,
        )
        
        # Initialize cameras
        self.cameras = make_cameras_from_configs(config.cameras)
        
        # Track connection state
        self._is_connected = False
        self._is_calibrated_flag = True  # Dofbot SE doesn't require calibration
        
        # Cache for last known joint positions (for gamepad mode with serial conflicts)
        self._last_known_positions = {}
        self._read_fail_counts = {}  # Track failures to reduce log spam
        
        # Read-only mode flag (for external gamepad control)
        self._read_only_mode = False
        
        logger.info(f"Initialized {self.name} with port {config.port}")

    @property
    def _motors_ft(self) -> dict[str, type]:
        """Define motor observation/action features."""
        return {f"{joint}.pos": float for joint in self.JOINT_NAMES}

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        """Define camera observation features."""
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) 
            for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        """Define all observation features (motors + cameras)."""
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        """Define all action features (motors only)."""
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        """Check if robot is connected."""
        cameras_connected = all(cam.is_connected for cam in self.cameras.values())
        return self.device.is_connected and cameras_connected

    def connect(self, calibrate: bool = True) -> None:
        """Connect to the Dofbot SE robot.
        
        Args:
            calibrate: Not used for Dofbot SE (no calibration required)
        """
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        # Connect to serial device
        self.device.connect()
        
        # Connect cameras
        for cam in self.cameras.values():
            cam.connect()
        
        # Configure robot
        self.configure()
        
        self._is_connected = True
        logger.info(f"{self} connected successfully")

    @property
    def is_calibrated(self) -> bool:
        """Check if robot is calibrated.
        
        Dofbot SE doesn't require calibration, so always returns True.
        """
        return self._is_calibrated_flag

    def calibrate(self) -> None:
        """Calibrate the robot.
        
        Dofbot SE uses absolute position servos and doesn't require calibration.
        This is a no-op for compatibility with the Robot interface.
        """
        logger.info(f"{self} does not require calibration")
        self._is_calibrated_flag = True

    def configure(self) -> None:
        """Configure robot settings.
        
        Sets up initial robot state:
        - Enables torque (unless in read-only mode)
        - Sets RGB LED to green (ready state)
        - Moves to home position (unless in read-only mode)
        """
        if not self.device.is_connected:
            raise DeviceNotConnectedError(f"{self} device not connected")
        
        # Enable torque (skip if in read-only mode for external control)
        if not self._read_only_mode:
            self.device.set_torque(True)
        
        # Set LED to green (ready)
        self.device.set_rgb(0, 255, 0)
        
        # Move to home position (skip if in read-only mode)
        if not self._read_only_mode:
            # home_angles = [90.0, 135.0, 0.0, 1.0, 89.0, 3.0]
            home_angles = [90.0, 90.0, 90.0, 90.0, 90.0, 180.0]
            try:
                self.device.write_all_servos(home_angles, time_ms=2000)
                time.sleep(2.0)  # Wait for movement to complete
                logger.info("Moved to home position")
            except Exception as e:
                logger.warning(f"Failed to move to home position: {e}")
        else:
            logger.info("Skipping home position (read-only mode)")
    
    def set_read_only_mode(self, enabled: bool) -> None:
        """Enable or disable read-only mode.
        
        In read-only mode, the robot will not send any action commands.
        This is useful when using an external controller (e.g., gamepad).
        
        Args:
            enabled: If True, send_action() becomes a no-op
        """
        self._read_only_mode = enabled
        if enabled:
            logger.info(f"{self} set to read-only mode (external control)")
        else:
            logger.info(f"{self} read-only mode disabled")

    def get_observation(self) -> dict[str, Any]:
        """Get current robot state observation.
        
        Returns:
            Dictionary containing:
            - Joint positions: {joint_name.pos: angle_in_degrees}
            - Camera images: {camera_name: image_array}
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")

        obs_dict = {}
        
        # For gamepad mode: brief pause before reading to let gamepad commands finish
        # This "polite waiting" reduces serial bus contention
        if self._read_only_mode:
            time.sleep(0.05)  # 50ms quiet time for gamepad to complete current command
        
        # Read joint positions
        start = time.perf_counter()
        for i, joint_name in enumerate(self.JOINT_NAMES):
            servo_id = i + 1
            try:
                angle = self.device.read_servo(servo_id)
                if angle is not None:
                    obs_dict[f"{joint_name}.pos"] = angle
                    # Update cache with successful read
                    self._last_known_positions[joint_name] = angle
                    self._read_fail_counts[joint_name] = 0
                else:
                    # Use last known position or default
                    if joint_name in self._last_known_positions:
                        obs_dict[f"{joint_name}.pos"] = self._last_known_positions[joint_name]
                    else:
                        default_angle = 135.0 if servo_id == 5 else 90.0
                        obs_dict[f"{joint_name}.pos"] = default_angle
                    
                    # Only log warning occasionally to reduce spam
                    self._read_fail_counts[joint_name] = self._read_fail_counts.get(joint_name, 0) + 1
                    if self._read_fail_counts[joint_name] == 1 or self._read_fail_counts[joint_name] % 30 == 0:
                        logger.warning(f"Failed to read {joint_name} ({self._read_fail_counts[joint_name]} times), using cached/default")
            except Exception as e:
                # Use last known position or default
                if joint_name in self._last_known_positions:
                    obs_dict[f"{joint_name}.pos"] = self._last_known_positions[joint_name]
                else:
                    default_angle = 135.0 if servo_id == 5 else 90.0
                    obs_dict[f"{joint_name}.pos"] = default_angle
                
                self._read_fail_counts[joint_name] = self._read_fail_counts.get(joint_name, 0) + 1
                if self._read_fail_counts[joint_name] == 1 or self._read_fail_counts[joint_name] % 30 == 0:
                    logger.error(f"Error reading {joint_name} ({self._read_fail_counts[joint_name]} times): {e}")
        
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read joint positions: {dt_ms:.1f}ms")

        # Capture images from cameras
        # Increased timeout for gamepad mode where serial communication may cause delays
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read(timeout_ms=1000)  # 1 second timeout
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, float]) -> dict[str, float]:
        """Send action command to the robot.
        
        Args:
            action: Dictionary of joint goal positions {joint_name.pos: angle_in_degrees}
        
        Returns:
            Dictionary of actual commands sent (potentially clipped for safety)
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")
        
        # In read-only mode, don't send any commands (for external gamepad control)
        if self._read_only_mode:
            logger.debug(f"{self} in read-only mode, skipping send_action")
            return action

        # Extract goal positions
        goal_pos = {
            key.removesuffix(".pos"): val 
            for key, val in action.items() 
            if key.endswith(".pos")
        }

        # Safety: Cap goal position when too far from present position
        if self.config.max_relative_target is not None:
            try:
                # Read current positions (use cached values if read fails to avoid conflicts)
                present_pos = {}
                for i, joint_name in enumerate(self.JOINT_NAMES):
                    if joint_name in goal_pos:
                        servo_id = i + 1
                        angle = self.device.read_servo(servo_id)
                        if angle is not None:
                            present_pos[joint_name] = angle
                            self._last_known_positions[joint_name] = angle
                        elif joint_name in self._last_known_positions:
                            # Use cached value if read fails (e.g., during gamepad control)
                            present_pos[joint_name] = self._last_known_positions[joint_name]
                        else:
                            # If no cache available, skip safety check for this joint
                            continue
                
                # Apply safety limits
                goal_present_pos = {
                    key: (g_pos, present_pos[key]) 
                    for key, g_pos in goal_pos.items() 
                    if key in present_pos
                }
                
                if goal_present_pos:
                    goal_pos_safe = ensure_safe_goal_position(
                        goal_present_pos, 
                        self.config.max_relative_target
                    )
                    # Update only the joints that were safety-checked
                    goal_pos.update(goal_pos_safe)
            
            except Exception as e:
                logger.warning(f"Error during safety check: {e}, proceeding without limits")

        # Clip angles to joint limits
        for joint_name, angle in goal_pos.items():
            if joint_name in self.config.joint_limits:
                min_angle, max_angle = self.config.joint_limits[joint_name]
                goal_pos[joint_name] = max(min_angle, min(max_angle, angle))

        # Send commands to servos
        start = time.perf_counter()
        try:
            # Prepare angles array in servo order
            angles = []
            for joint_name in self.JOINT_NAMES:
                if joint_name in goal_pos:
                    angles.append(goal_pos[joint_name])
                else:
                    # If joint not in action, use current position or default
                    servo_id = self.JOINT_NAMES.index(joint_name) + 1
                    current = self.device.read_servo(servo_id)
                    if current is not None:
                        angles.append(current)
                    else:
                        # Use mid-range as fallback
                        default = 135.0 if servo_id == 5 else 90.0
                        angles.append(default)
            
            # Send all servo commands at once (faster than individual writes)
            self.device.write_all_servos(angles, time_ms=100)  # 100ms movement time for responsive control
            
        except Exception as e:
            logger.error(f"Error sending action: {e}")
            raise
        
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} sent action: {dt_ms:.1f}ms")

        # Return the action actually sent
        return {f"{joint}.pos": angles[i] for i, joint in enumerate(self.JOINT_NAMES)}

    def disconnect(self) -> None:
        """Disconnect from the robot."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")

        # Disable torque if configured
        if self.config.disable_torque_on_disconnect:
            try:
                self.device.set_torque(False)
                logger.info("Torque disabled")
            except Exception as e:
                logger.warning(f"Failed to disable torque: {e}")

        # Set LED to red (disconnected)
        try:
            self.device.set_rgb(255, 0, 0)
        except Exception as e:
            logger.warning(f"Failed to set LED: {e}")

        # Disconnect cameras
        for cam in self.cameras.values():
            try:
                cam.disconnect()
            except Exception as e:
                logger.warning(f"Failed to disconnect camera: {e}")

        # Disconnect serial device
        self.device.disconnect()
        
        self._is_connected = False
        logger.info(f"{self} disconnected")

    def __str__(self) -> str:
        """String representation of the robot."""
        return f"DofbotSE(id={self.id}, port={self.config.port})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"DofbotSE(id={self.id}, port={self.config.port}, "
            f"connected={self.is_connected}, joints={len(self.JOINT_NAMES)})"
        )

