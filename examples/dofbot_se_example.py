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
Example script for using the Dofbot SE robotic arm with LeRobot.

This script demonstrates basic usage including:
- Connecting to the robot
- Reading observations (joint positions)
- Sending actions (target positions)
- Disconnecting safely

Usage:
    python examples/dofbot_se_example.py
"""

import time

from lerobot.robots.dofbot_se import DofbotSE, DofbotSEConfig


def main():
    # Create robot configuration
    # IMPORTANT: Find your port first using: lerobot-find-port
    # Common ports:
    #   - Linux: /dev/ttyUSB0, /dev/ttyACM0
    #   - macOS: /dev/tty.usbmodem*, /dev/tty.usbserial*
    #   - Windows: COM3, COM4, etc.
    
    import sys
    
    # Check if port is provided as command line argument
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        # Prompt user for port
        print("Please specify the serial port.")
        print("Run 'lerobot-find-port' to find your device port.")
        print()
        port = input("Enter port (e.g., /dev/ttyUSB0): ").strip()
        if not port:
            print("Error: Port is required!")
            sys.exit(1)
    
    config = DofbotSEConfig(
        id="dofbot_01",
        port=port,
        baudrate=115200,
        max_relative_target=30.0,  # Maximum 30 degrees change per step
    )

    print("=" * 60)
    print("Dofbot SE Example Script")
    print("=" * 60)
    print(f"Configuration: {config}")
    print()

    # Create and connect to robot
    print("Connecting to Dofbot SE...")
    robot = DofbotSE(config)
    
    try:
        robot.connect()
        print("✓ Robot connected successfully!")
        print()

        # Wait for robot to reach home position
        time.sleep(2.0)

        # Read initial observation
        print("Reading initial observation...")
        obs = robot.get_observation()
        print("Joint positions:")
        for joint_name in robot.JOINT_NAMES:
            pos = obs.get(f"{joint_name}.pos")
            print(f"  {joint_name}: {pos:.1f}°")
        print()

        # Define a simple movement sequence
        print("Executing movement sequence...")
        
        # Position 1: Wave gesture
        print("Position 1: Wave gesture")
        action1 = {
            "joint_1.pos": 90.0,   # Base centered
            "joint_2.pos": 45.0,   # Shoulder up
            "joint_3.pos": 135.0,  # Elbow bent
            "joint_4.pos": 90.0,   # Wrist neutral
            "joint_5.pos": 135.0,  # Gripper rotation neutral
            "joint_6.pos": 60.0,   # Gripper open
        }
        robot.send_action(action1)
        time.sleep(2.0)
        
        # Position 2: Reach forward
        print("Position 2: Reach forward")
        action2 = {
            "joint_1.pos": 90.0,   # Base centered
            "joint_2.pos": 90.0,   # Shoulder level
            "joint_3.pos": 90.0,   # Elbow straight
            "joint_4.pos": 90.0,   # Wrist neutral
            "joint_5.pos": 135.0,  # Gripper rotation neutral
            "joint_6.pos": 90.0,   # Gripper centered
        }
        robot.send_action(action2)
        time.sleep(2.0)
        
        # Position 3: Pick position
        print("Position 3: Pick position")
        action3 = {
            "joint_1.pos": 90.0,   # Base centered
            "joint_2.pos": 120.0,  # Shoulder down
            "joint_3.pos": 60.0,   # Elbow down
            "joint_4.pos": 120.0,  # Wrist down
            "joint_5.pos": 135.0,  # Gripper rotation neutral
            "joint_6.pos": 120.0,  # Gripper closing
        }
        robot.send_action(action3)
        time.sleep(2.0)
        
        # Return to home
        print("Returning to home position")
        home_action = {
            "joint_1.pos": 90.0,
            "joint_2.pos": 90.0,
            "joint_3.pos": 90.0,
            "joint_4.pos": 90.0,
            "joint_5.pos": 135.0,
            "joint_6.pos": 90.0,
        }
        robot.send_action(home_action)
        time.sleep(2.0)

        # Read final observation
        print("\nReading final observation...")
        final_obs = robot.get_observation()
        print("Final joint positions:")
        for joint_name in robot.JOINT_NAMES:
            pos = final_obs.get(f"{joint_name}.pos")
            print(f"  {joint_name}: {pos:.1f}°")
        print()

        print("✓ Movement sequence completed successfully!")

    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always disconnect safely
        print("\nDisconnecting from robot...")
        try:
            robot.disconnect()
            print("✓ Robot disconnected safely")
        except Exception as e:
            print(f"⚠ Warning during disconnect: {e}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

