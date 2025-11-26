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

from dataclasses import dataclass

from ..teleoperator import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("dofbot_kinesthetic")
@dataclass
class DofbotKinestheticConfig(TeleoperatorConfig):
    """Configuration for Dofbot SE kinesthetic teaching (manual demonstration).
    
    This teleoperator is used for kinesthetic teaching, where the robot is manually
    moved to demonstrate the task. The teleoperator simply returns the current
    robot joint positions as the action, effectively recording the manual movements.
    
    No physical teleoperator device is required - the user manually moves the robot
    arm to demonstrate the task while the torque is disabled.
    
    Attributes:
        disable_torque: If True, disable servo torque to allow manual movement.
                       If False, keep torque enabled (for use with physical gamepad controller).
                       Default: True (traditional kinesthetic teaching)
    """
    disable_torque: bool = True

