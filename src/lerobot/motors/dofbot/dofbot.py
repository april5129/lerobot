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

"""Serial communication implementation for Dofbot robotic arm.

This module provides a standalone implementation for communicating with Dofbot
robotic arms via serial interface. Unlike Dynamixel and Feetech servos, Dofbot
uses a custom serial protocol that does not follow the standard control table
architecture, so this implementation does not inherit from MotorsBus.

The Dofbot protocol uses packets with the following structure:
    [0xFF, 0xFC, length, command, data..., checksum]

Note on architecture:
    Dofbot servos use a proprietary communication protocol that is fundamentally
    different from Dynamixel/Feetech. They do not support:
    - Standard control tables (e.g., Goal_Position, Present_Position addresses)
    - Motor calibration (homing offset, drive mode)
    - Fine-grained torque control
    - Firmware version queries
    - Many other Dynamixel SDK features
    
    For this reason, this implementation provides a simplified interface tailored
    to Dofbot's actual capabilities, rather than attempting to force-fit it into
    the MotorsBus abstraction which would require implementing many unsupported
    features.
"""

import logging
from time import sleep
from typing import Optional

import serial

from .tables import (
    CMD_BUZZER,
    CMD_RGB,
    CMD_SERVO_READ,
    CMD_SERVO_WRITE,
    CMD_SERVO_WRITE_ALL,
    CMD_TORQUE,
    DEFAULT_BAUDRATE,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    MODEL_SPECS,
    PACKET_DEVICE_ID,
    PACKET_HEADER,
    PACKET_RESPONSE_ID,
    REVERSED_SERVOS,
    SERVO_MODELS,
)

logger = logging.getLogger(__name__)


class DofbotMotorsBus:
    """Serial communication interface for Dofbot robotic arm.
    
    Provides methods for controlling Dofbot servos, RGB LED, buzzer, and reading
    servo positions via the custom Dofbot serial protocol.
    
    Attributes:
        port: Serial port path (e.g., "/dev/ttyUSB0")
        baudrate: Communication baud rate (default: 115200)
        timeout: Serial read timeout in seconds
    
    Example:
        ```python
        from lerobot.motors.dofbot import DofbotMotorsBus
        
        bus = DofbotMotorsBus(port="/dev/ttyUSB0")
        bus.connect()
        
        # Write to single servo
        bus.write_servo(1, 90.0, time_ms=1000)
        
        # Write to all servos
        bus.write_all_servos([90, 90, 90, 90, 135, 90], time_ms=1000)
        
        # Read servo position
        angle = bus.read_servo(1)
        
        bus.disconnect()
        ```
    """
    
    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize Dofbot motor bus.
        
        Args:
            port: Serial port path
            baudrate: Communication baud rate
            timeout: Serial read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        
        # Response data buffers
        self._servo_position_h = 0
        self._servo_position_l = 0
        self._response_id = 0
        
    def connect(self) -> None:
        """Open serial connection."""
        if self.ser is not None and self.ser.is_open:
            logger.warning("Serial connection already open")
            return
            
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            sleep(0.2)  # Wait for connection to stabilize
            # Clear any stale data in buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            logger.info(f"Connected to Dofbot on {self.port}")
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to connect to {self.port}: {e}") from e
    
    def disconnect(self) -> None:
        """Close serial connection."""
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            logger.info("Disconnected from Dofbot")
        self.ser = None
    
    @property
    def is_connected(self) -> bool:
        """Check if serial connection is active."""
        return self.ser is not None and self.ser.is_open
    
    def _calculate_checksum(self, cmd: list[int]) -> int:
        """Calculate checksum for command packet.
        
        The checksum is calculated from the length field (index 2) onwards,
        which excludes the header bytes (0xFF, 0xFC).
        
        Args:
            cmd: Command packet (without checksum), must include header
            
        Returns:
            Checksum byte (sum & 0xFF)
        """
        # Sum from index 2 (length field) onwards, excluding header
        return sum(cmd[2:]) & 0xFF
    
    def _send_command(self, cmd: list[int]) -> None:
        """Send command packet to device.
        
        Args:
            cmd: Complete command packet including checksum
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Dofbot")
        
        try:
            self.ser.write(bytearray(cmd))
            sleep(0.01)  # Command delay for device processing
        except serial.SerialException as e:
            logger.error(f"Error sending command: {e}")
            raise
    
    def angle_to_raw(self, angle: float, servo_id: int) -> int:
        """Convert angle in degrees to raw servo position.
        
        Args:
            angle: Angle in degrees (0-180 for most servos, 0-270 for servo 5)
            servo_id: Servo ID (1-6)
            
        Returns:
            Raw position value (900-3100 or 380-3700 for servo 5)
        """
        model = SERVO_MODELS[servo_id]
        specs = MODEL_SPECS[model]
        
        # Clamp angle to valid range
        angle = max(specs["angle_min"], min(specs["angle_max"], angle))
        
        # Linear mapping from angle to raw position
        angle_range = specs["angle_max"] - specs["angle_min"]
        raw_range = specs["raw_max"] - specs["raw_min"]
        raw_pos = int(raw_range * angle / angle_range + specs["raw_min"])
        
        return raw_pos
    
    def raw_to_angle(self, raw_pos: int, servo_id: int) -> float:
        """Convert raw servo position to angle in degrees.
        
        Args:
            raw_pos: Raw position value
            servo_id: Servo ID (1-6)
            
        Returns:
            Angle in degrees (0-180 or 0-270)
        """
        model = SERVO_MODELS[servo_id]
        specs = MODEL_SPECS[model]
        
        # Linear mapping from raw position to angle
        angle_range = specs["angle_max"] - specs["angle_min"]
        raw_range = specs["raw_max"] - specs["raw_min"]
        angle = angle_range * (raw_pos - specs["raw_min"]) / raw_range
        
        return angle
    
    def write_servo(self, servo_id: int, angle: float, time_ms: int = 1000) -> None:
        """Write position command to a single servo.
        
        Args:
            servo_id: Servo ID (1-6)
            angle: Target angle in degrees
            time_ms: Movement duration in milliseconds
        """
        if not 1 <= servo_id <= 6:
            raise ValueError(f"Servo ID must be 1-6, got {servo_id}")
        
        # Account for reversed servo mounting
        if servo_id in REVERSED_SERVOS:
            angle = 180.0 - angle
        
        raw_pos = self.angle_to_raw(angle, servo_id)
        
        # Split position and time into high/low bytes
        pos_h = (raw_pos >> 8) & 0xFF
        pos_l = raw_pos & 0xFF
        time_h = (time_ms >> 8) & 0xFF
        time_l = time_ms & 0xFF
        
        # Build command packet
        cmd = [
            PACKET_HEADER,
            PACKET_DEVICE_ID,
            0x07,
            CMD_SERVO_WRITE + servo_id,
            pos_h,
            pos_l,
            time_h,
            time_l,
        ]
        checksum = self._calculate_checksum(cmd)
        cmd.append(checksum)
        
        self._send_command(cmd)
    
    def write_all_servos(self, angles: list[float], time_ms: int = 1000) -> None:
        """Write position commands to all 6 servos simultaneously.
        
        Args:
            angles: List of 6 angles in degrees [s1, s2, s3, s4, s5, s6]
            time_ms: Movement duration in milliseconds
        """
        if len(angles) != 6:
            raise ValueError(f"Expected 6 angles, got {len(angles)}")
        
        # Convert angles to raw positions, accounting for reversed servos
        raw_positions = []
        for i, angle in enumerate(angles):
            servo_id = i + 1
            
            # Validate angle range
            model = SERVO_MODELS[servo_id]
            specs = MODEL_SPECS[model]
            if not specs["angle_min"] <= angle <= specs["angle_max"]:
                raise ValueError(
                    f"Angle {servo_id} out of range: {angle} "
                    f"(expected {specs['angle_min']}-{specs['angle_max']})"
                )
            
            # Reverse angle if needed
            if servo_id in REVERSED_SERVOS:
                angle = 180.0 - angle
            
            raw_pos = self.angle_to_raw(angle, servo_id)
            raw_positions.append(raw_pos)
        
        # Build command packet
        time_h = (time_ms >> 8) & 0xFF
        time_l = time_ms & 0xFF
        
        cmd = [PACKET_HEADER, PACKET_DEVICE_ID, 0x11, CMD_SERVO_WRITE_ALL]
        
        # Add all servo positions (high byte, low byte for each)
        for raw_pos in raw_positions:
            cmd.append((raw_pos >> 8) & 0xFF)  # High byte
            cmd.append(raw_pos & 0xFF)  # Low byte
        
        # Add time
        cmd.append(time_h)
        cmd.append(time_l)
        
        checksum = self._calculate_checksum(cmd)
        cmd.append(checksum)
        
        self._send_command(cmd)
    
    def read_servo(self, servo_id: int) -> Optional[float]:
        """Read current position of a servo.
        
        Args:
            servo_id: Servo ID (1-6)
            
        Returns:
            Current angle in degrees, or None if read fails
        """
        if not 1 <= servo_id <= 6:
            raise ValueError(f"Servo ID must be 1-6, got {servo_id}")
        
        # Send read command
        cmd = [PACKET_HEADER, PACKET_DEVICE_ID, 0x03, CMD_SERVO_READ + servo_id]
        checksum = self._calculate_checksum(cmd)
        cmd.append(checksum)
        
        try:
            # Send command twice for reliability
            self._send_command(cmd)
            sleep(0.001)
            self._receive_data()
            
            self._send_command(cmd)
            sleep(0.001)
            self._receive_data()
            
            # Check if response is for the correct servo
            if self._response_id == (CMD_SERVO_READ + servo_id):
                raw_pos = self._servo_position_h * 256 + self._servo_position_l
                
                if raw_pos == 0:
                    return None
                
                # Convert to angle
                angle = self.raw_to_angle(raw_pos, servo_id)
                
                # Validate range
                model = SERVO_MODELS[servo_id]
                specs = MODEL_SPECS[model]
                if not specs["angle_min"] <= angle <= specs["angle_max"]:
                    return None
                
                # Account for reversed servos
                if servo_id in REVERSED_SERVOS:
                    angle = 180.0 - angle
                
                return angle
            
        except Exception as e:
            logger.error(f"Error reading servo {servo_id}: {e}")
        
        return None
    
    def _receive_data(self) -> None:
        """Receive and parse response data from device."""
        if not self.is_connected:
            return
        
        try:
            # Read header
            head1_data = self.ser.read(1)
            if len(head1_data) == 0:
                return
            
            head1 = head1_data[0]
            if head1 == PACKET_HEADER:
                head2_data = self.ser.read(1)
                if len(head2_data) == 0:
                    return
                
                head2 = head2_data[0]
                if head2 == PACKET_RESPONSE_ID:  # Device responses use 0xFB
                    # Read length and type
                    ext_len_data = self.ser.read(1)
                    if len(ext_len_data) == 0:
                        return
                    ext_len = ext_len_data[0]
                    
                    ext_type_data = self.ser.read(1)
                    if len(ext_type_data) == 0:
                        return
                    ext_type = ext_type_data[0]
                    
                    # Read data
                    data_len = ext_len - 2
                    ext_data = []
                    check_sum = ext_len + ext_type
                    
                    # Read all data bytes
                    while len(ext_data) < data_len:
                        byte_data = self.ser.read(1)
                        if len(byte_data) == 0:
                            return
                        value = byte_data[0]
                        ext_data.append(value)
                        if len(ext_data) == data_len:
                            rx_check_num = value
                        else:
                            check_sum = check_sum + value
                    
                    # Verify checksum and parse data
                    if check_sum % 256 == rx_check_num:
                        self._parse_response(ext_type, ext_data)
                    else:
                        logger.warning(f"Checksum error: {ext_len}, {ext_type}, {ext_data}")
        
        except Exception as e:
            logger.error(f"Error receiving data: {e}")
    
    def _parse_response(self, response_type: int, data: list[int]) -> None:
        """Parse response data based on type.
        
        Args:
            response_type: Response type code
            data: Response data bytes
        """
        # Response type 0x0A is servo position data
        if response_type == 0x0A:
            if len(data) >= 3:
                self._servo_position_h = data[0]
                self._servo_position_l = data[1]
                self._response_id = data[2]
    
    def set_torque(self, enable: bool) -> None:
        """Enable or disable servo torque.
        
        Args:
            enable: True to enable torque, False to disable (allows manual movement)
        """
        value = 0x01 if enable else 0x00
        cmd = [PACKET_HEADER, PACKET_DEVICE_ID, 0x04, CMD_TORQUE, value]
        checksum = self._calculate_checksum(cmd)
        cmd.append(checksum)
        
        self._send_command(cmd)
        logger.debug(f"Torque {'enabled' if enable else 'disabled'}")
    
    def set_rgb(self, red: int, green: int, blue: int) -> None:
        """Set RGB LED color.
        
        Args:
            red: Red value (0-255)
            green: Green value (0-255)
            blue: Blue value (0-255)
        """
        cmd = [
            PACKET_HEADER,
            PACKET_DEVICE_ID,
            0x06,
            CMD_RGB,
            red & 0xFF,
            green & 0xFF,
            blue & 0xFF,
        ]
        checksum = self._calculate_checksum(cmd)
        cmd.append(checksum)
        
        self._send_command(cmd)
    
    def set_buzzer(self, enable: bool, duration: int = 0xFF) -> None:
        """Control buzzer.
        
        Args:
            enable: True to turn on, False to turn off
            duration: Duration code (0xFF for continuous, 0x00 to turn off)
        """
        if not enable:
            duration = 0x00
        
        cmd = [PACKET_HEADER, PACKET_DEVICE_ID, 0x04, CMD_BUZZER, duration & 0xFF]
        checksum = self._calculate_checksum(cmd)
        cmd.append(checksum)
        
        self._send_command(cmd)

