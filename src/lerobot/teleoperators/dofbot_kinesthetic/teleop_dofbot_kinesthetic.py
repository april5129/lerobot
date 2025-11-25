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
    
    This is a "dummy" teleoperator that enables manual demonstration (kinesthetic teaching).
    The robot's torque is disabled, allowing the user to physically move the arm.
    This teleoperator reads the robot's current joint positions and returns them as actions,
    effectively recording the manual movements as demonstrations.
    
    Usage:
        The user manually moves the robot arm to demonstrate the task. The teleoperator
        reads the current joint positions and treats them as the "commanded" actions,
        which are then recorded in the dataset along with camera observations.
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
        
        logger.info("Dofbot SE kinesthetic teaching teleoperator initialized")
        logger.info("The robot will be manually moved to demonstrate the task")
    
    def set_robot(self, robot: DofbotSE) -> None:
        """Set the robot instance for this teleoperator.
        
        This must be called after robot creation and before connect().
        
        Args:
            robot: The Dofbot SE robot instance to read joint positions from.
        """
        self.robot = robot
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
        The robot's torque will be disabled to allow manual movement.
        
        Args:
            calibrate: Ignored for kinesthetic teaching.
        """
        if self.robot is None:
            raise RuntimeError("Robot must be set via set_robot() before connect()")
        
        if not self.robot.is_connected:
            raise RuntimeError("Robot must be connected before teleoperator")
        
        # Disable torque to allow manual movement
        logger.info("Disabling robot torque for kinesthetic teaching...")
        self.robot.device.set_torque(False)
        
        self._is_connected = True
        logger.info("Kinesthetic teaching mode enabled - you can now manually move the robot")
    
    def disconnect(self) -> None:
        """Disconnect the teleoperator.
        
        Re-enables robot torque on disconnect.
        """
        if self._is_connected:
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

