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

"""Kinesthetic teaching teleoperator for Dofbot SE.

This teleoperator enables kinesthetic teaching (manual demonstration) for the Dofbot SE.
It doesn't control the robot - instead, it reads the robot's current joint positions
and returns them as actions, effectively recording the user's manual movements.
"""

import logging

from lerobot.robots.dofbot_se import DofbotSE
from lerobot.teleoperators.teleoperator import Teleoperator

from .configuration_dofbot_kinesthetic import DofbotKinestheticConfig

logger = logging.getLogger(__name__)


class DofbotKinesthetic(Teleoperator):
    """Kinesthetic teaching teleoperator for Dofbot SE.
    
    This is a "dummy" teleoperator that enables manual demonstration recording.
    It reads the robot's current joint positions and returns them as actions,
    effectively recording movements as demonstrations.
    
    Two modes:
    1. Manual kinesthetic teaching (disable_torque=True, default):
       - Robot torque is disabled, allowing manual arm movement by hand
       - User physically moves the arm to demonstrate the task
       
    2. Gamepad recording mode (disable_torque=False):
       - Robot torque remains enabled
       - User controls the robot with the physical gamepad controller
       - LeRobot records the resulting movements
    
    Usage:
        Kinesthetic mode: Manually move the robot arm to demonstrate the task.
        Gamepad mode: Use the physical gamepad to control the robot while recording.
    """
    
    name = "dofbot_kinesthetic"
    
    def __init__(self, config: DofbotKinestheticConfig):
        """Initialize the kinesthetic teaching teleoperator.
        
        Args:
            config: Configuration for the teleoperator.
        """
        super().__init__(config)
        self.config = config
        self.robot = None  # Will be set by set_robot() after robot is created
        self._is_connected = False
        
        logger.info("Dofbot SE kinesthetic recording teleoperator initialized")
        if config.disable_torque:
            logger.info("Mode: Manual kinesthetic teaching (torque will be disabled)")
        else:
            logger.info("Mode: Gamepad recording (torque will remain enabled)")
    
    def set_robot(self, robot: DofbotSE) -> None:
        """Set the robot instance for this teleoperator.
        
        This must be called after robot creation and before connect().
        
        Args:
            robot: The Dofbot SE robot instance to read joint positions from.
        """
        self.robot = robot
        
        # If using gamepad mode (torque enabled), set robot to read-only mode
        # This must be done BEFORE robot.connect() to prevent homing movement
        if not self.config.disable_torque:
            self.robot.set_read_only_mode(True)
            logger.info("Robot set to read-only mode for gamepad control")
        
        logger.info("Robot instance linked to kinesthetic teleoperator")
    
    @property
    def action_features(self) -> dict:
        """Return action features matching Dofbot SE's joint structure."""
        return {
            "joint_1": float,
            "joint_2": float,
            "joint_3": float,
            "joint_4": float,
            "joint_5": float,
            "joint_6": float,
        }
    
    @property
    def feedback_features(self) -> dict:
        """No feedback for kinesthetic teaching."""
        return {}
    
    @property
    def is_calibrated(self) -> bool:
        """Kinesthetic teaching doesn't require calibration."""
        return True
    
    def calibrate(self) -> None:
        """No calibration needed for kinesthetic teaching."""
        pass
    
    def configure(self) -> None:
        """No configuration needed for kinesthetic teaching."""
        pass
    
    def send_feedback(self, feedback: dict) -> None:
        """No feedback for kinesthetic teaching."""
        pass
    
    def connect(self, calibrate: bool = True) -> None:
        """Connect the teleoperator.
        
        For kinesthetic teaching, this just marks the teleoperator as connected.
        The robot's torque will be disabled to allow manual movement (if disable_torque=True).
        
        Args:
            calibrate: Ignored for kinesthetic teaching.
        """
        if self.robot is None:
            raise RuntimeError("Robot must be set via set_robot() before connect()")
        
        if not self.robot.is_connected:
            raise RuntimeError("Robot must be connected before teleoperator")
        
        # For kinesthetic teaching, disable torque and set to read-only
        if self.config.disable_torque:
            # Per user request, read-only mode is disabled to allow robot movement.
            self.robot.set_read_only_mode(False)
            logger.info("Kinesthetic teleop: read-only mode DEACTIVATED, torque ENABLED.")
        else:
            logger.info("Kinesthetic recording mode active (read-only)")
            logger.info("Use the physical gamepad controller to control the robot")
        
        self._is_connected = True
    
    def disconnect(self) -> None:
        """Disconnect the teleoperator.
        
        Re-enables robot torque on disconnect (if it was disabled).
        """
        if self._is_connected:
            # Disable read-only mode
            if not self.config.disable_torque and self.robot.is_connected:
                self.robot.set_read_only_mode(False)
            
            # Only re-enable torque if robot is still connected and we disabled it
            if self.config.disable_torque and self.robot.is_connected:
                logger.info("Re-enabling robot torque...")
                self.robot.device.set_torque(True)
            self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if teleoperator is connected."""
        return self._is_connected
    
    def get_action(self) -> dict:
        """Get the current action by reading robot joint positions.
        
        For kinesthetic teaching, the "action" is simply the current joint positions
        of the robot, which reflects where the user has manually moved the arm.
        
        Returns:
            Dictionary containing current joint positions in degrees.
        """
        if not self._is_connected:
            raise RuntimeError("Teleoperator not connected")
        
        # Read current joint positions from the robot
        observation = self.robot.get_observation()
        
        # Extract joint positions and return them as the action
        # This creates a "recording" of the manual movements
        action = {}
        for key, value in observation.items():
            if key.startswith("joint_"):
                action[key] = value
        
        return action

