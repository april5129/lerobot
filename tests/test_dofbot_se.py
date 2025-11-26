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
Unit tests for Dofbot SE robot integration.

Note: These tests require a physical Dofbot SE connected to run properly.
Mock tests are provided for CI/CD environments.
"""

import pytest

from lerobot.robots.dofbot_se import DofbotSE, DofbotSEConfig
from lerobot.robots.dofbot_se.dofbot_serial import DofbotSerialDevice


class TestDofbotSEConfig:
    """Test Dofbot SE configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DofbotSEConfig()
        
        assert config.port == "/dev/myserial"
        assert config.baudrate == 115200
        assert config.timeout == 0.2
        assert config.disable_torque_on_disconnect is True
        assert config.max_relative_target == 30.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = DofbotSEConfig(
            port="/dev/ttyUSB0",
            baudrate=57600,
            timeout=0.5,
            max_relative_target=45.0,
        )
        
        assert config.port == "/dev/ttyUSB0"
        assert config.baudrate == 57600
        assert config.timeout == 0.5
        assert config.max_relative_target == 45.0

    def test_joint_limits(self):
        """Test joint limits are correctly defined."""
        config = DofbotSEConfig()
        
        assert len(config.joint_limits) == 6
        assert config.joint_limits["joint_1"] == (0.0, 180.0)
        assert config.joint_limits["joint_5"] == (0.0, 270.0)


class TestDofbotSerialDevice:
    """Test serial communication device."""

    def test_angle_to_raw_conversion(self):
        """Test angle to raw position conversion."""
        device = DofbotSerialDevice()
        
        # Test regular servo (0-180 degrees)
        assert device.angle_to_raw(0.0, 1) == 900
        assert device.angle_to_raw(90.0, 1) == 2000
        assert device.angle_to_raw(180.0, 1) == 3100
        
        # Test extended range servo (0-270 degrees)
        assert device.angle_to_raw(0.0, 5) == 380
        assert device.angle_to_raw(135.0, 5) == 2040
        assert device.angle_to_raw(270.0, 5) == 3700

    def test_raw_to_angle_conversion(self):
        """Test raw position to angle conversion."""
        device = DofbotSerialDevice()
        
        # Test regular servo
        assert abs(device.raw_to_angle(900, 1) - 0.0) < 0.1
        assert abs(device.raw_to_angle(2000, 1) - 90.0) < 0.1
        assert abs(device.raw_to_angle(3100, 1) - 180.0) < 0.1
        
        # Test extended range servo
        assert abs(device.raw_to_angle(380, 5) - 0.0) < 0.1
        assert abs(device.raw_to_angle(2040, 5) - 135.0) < 0.1
        assert abs(device.raw_to_angle(3700, 5) - 270.0) < 0.1

    def test_checksum_calculation(self):
        """Test checksum calculation."""
        device = DofbotSerialDevice()
        
        cmd = [0xFF, 0xFC, 0x07, 0x11, 0x08, 0x00, 0x03, 0xE8]
        checksum = device._calculate_checksum(cmd)
        
        # Checksum should be valid
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 255


class TestDofbotSERobot:
    """Test Dofbot SE robot class."""

    def test_robot_initialization(self):
        """Test robot initialization without connection."""
        config = DofbotSEConfig(port="/dev/null")  # Use /dev/null for testing
        robot = DofbotSE(config)
        
        assert robot.name == "dofbot_se"
        assert robot.config == config
        assert len(robot.JOINT_NAMES) == 6
        assert not robot.is_connected

    def test_observation_features(self):
        """Test observation features definition."""
        config = DofbotSEConfig(port="/dev/null")
        robot = DofbotSE(config)
        
        obs_features = robot.observation_features
        
        # Should have all joint positions
        for joint in robot.JOINT_NAMES:
            assert f"{joint}.pos" in obs_features
            assert obs_features[f"{joint}.pos"] == float

    def test_action_features(self):
        """Test action features definition."""
        config = DofbotSEConfig(port="/dev/null")
        robot = DofbotSE(config)
        
        action_features = robot.action_features
        
        # Should have all joint positions
        for joint in robot.JOINT_NAMES:
            assert f"{joint}.pos" in action_features
            assert action_features[f"{joint}.pos"] == float

    def test_string_representation(self):
        """Test string representation of robot."""
        config = DofbotSEConfig(id="test_robot", port="/dev/ttyUSB0")
        robot = DofbotSE(config)
        
        str_repr = str(robot)
        assert "DofbotSE" in str_repr
        assert "test_robot" in str_repr
        assert "/dev/ttyUSB0" in str_repr


@pytest.mark.physical
class TestDofbotSEPhysical:
    """Tests requiring physical hardware (skip in CI)."""

    @pytest.fixture
    def robot(self):
        """Create a robot instance for testing."""
        config = DofbotSEConfig(
            port="/dev/ttyUSB0",  # Adjust for your setup
            id="test_dofbot",
        )
        robot = DofbotSE(config)
        yield robot
        # Cleanup
        if robot.is_connected:
            robot.disconnect()

    def test_connect_disconnect(self, robot):
        """Test connection and disconnection."""
        robot.connect()
        assert robot.is_connected
        
        robot.disconnect()
        assert not robot.is_connected

    def test_get_observation(self, robot):
        """Test getting observations."""
        robot.connect()
        
        obs = robot.get_observation()
        
        # Check all joints are present
        for joint in robot.JOINT_NAMES:
            assert f"{joint}.pos" in obs
            angle = obs[f"{joint}.pos"]
            assert isinstance(angle, float)
            # Check angle is in valid range
            if joint == "joint_5":
                assert 0.0 <= angle <= 270.0
            else:
                assert 0.0 <= angle <= 180.0

    def test_send_action(self, robot):
        """Test sending actions."""
        robot.connect()
        
        # Send home position action
        action = {
            "joint_1.pos": 90.0,
            "joint_2.pos": 90.0,
            "joint_3.pos": 90.0,
            "joint_4.pos": 90.0,
            "joint_5.pos": 135.0,
            "joint_6.pos": 90.0,
        }
        
        result = robot.send_action(action)
        
        # Check result has all joints
        for joint in robot.JOINT_NAMES:
            assert f"{joint}.pos" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

