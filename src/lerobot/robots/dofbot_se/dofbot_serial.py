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

"""Serial communication module for Dofbot SE robotic arm.

This module provides a standalone implementation for communicating with the Dofbot SE
robotic arm via serial interface, without depending on external Dofbot libraries.
"""

import logging
import struct
from time import sleep
from typing import Optional

import serial

logger = logging.getLogger(__name__)


class DofbotSerialDevice:
    """Serial communication interface for Dofbot SE robotic arm.
    
    The Dofbot SE uses a custom serial protocol with the following packet structure:
    [0xFF, 0xFC, length, command, data..., checksum]
    
    Attributes:
        port: Serial port path (e.g., "/dev/ttyUSB0")
        baudrate: Communication baud rate (default: 115200)
        timeout: Serial read timeout in seconds
    """
    
    # Protocol headers
    HEAD = 0xFF
    DEVICE_ID = 0xFC
    
    # Command codes
    CMD_RGB = 0x02
    CMD_BUZZER = 0x06
    CMD_SERVO_WRITE = 0x10  # Base for individual servo control (0x10 + servo_id)
    CMD_SERVO_WRITE_ALL = 0x1D  # Control all 6 servos
    CMD_SERVO_READ = 0x30  # Base for reading servo position (0x30 + servo_id)
    CMD_TORQUE = 0x1A
    
    # Servo ranges (in raw position units)
    SERVO_RAW_MIN = 900
    SERVO_RAW_MAX = 3100
    SERVO_5_RAW_MIN = 380  # Joint 5 has extended range
    SERVO_5_RAW_MAX = 3700
    
    def __init__(self, port: str = "/dev/myserial", baudrate: int = 115200, timeout: float = 0.2):
        """Initialize serial connection to Dofbot SE.
        
        Args:
            port: Serial port path
            baudrate: Communication baud rate
            timeout: Serial read timeout
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        
        # Response data buffers
        self.servo_position_h = 0
        self.servo_position_l = 0
        self.response_id = 0
        
    def connect(self) -> None:
        """Open serial connection."""
        if self.ser is not None and self.ser.is_open:
            logger.warning("Serial connection already open")
            return
            
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            sleep(0.2)  # Wait for connection to stabilize (match original timing)
            # Clear any stale data in buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            logger.info(f"Connected to Dofbot SE on {self.port}")
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to connect to {self.port}: {e}") from e
    
    def disconnect(self) -> None:
        """Close serial connection."""
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            logger.info("Disconnected from Dofbot SE")
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
            raise ConnectionError("Not connected to Dofbot SE")
        
        try:
            self.ser.write(bytearray(cmd))
            sleep(0.01)  # Match original dofbot timing (10ms vs 1ms)
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
        if servo_id == 5:
            # Joint 5 has 270-degree range
            angle = max(0.0, min(270.0, angle))
            return int((self.SERVO_5_RAW_MAX - self.SERVO_5_RAW_MIN) * angle / 270.0 + self.SERVO_5_RAW_MIN)
        else:
            # Joints 1, 2, 3, 4, 6 have 180-degree range
            angle = max(0.0, min(180.0, angle))
            return int((self.SERVO_RAW_MAX - self.SERVO_RAW_MIN) * angle / 180.0 + self.SERVO_RAW_MIN)
    
    def raw_to_angle(self, raw_pos: int, servo_id: int) -> float:
        """Convert raw servo position to angle in degrees.
        
        Args:
            raw_pos: Raw position value
            servo_id: Servo ID (1-6)
            
        Returns:
            Angle in degrees (0-180 or 0-270)
        """
        if servo_id == 5:
            return (270.0 - 0.0) * (raw_pos - self.SERVO_5_RAW_MIN) / (self.SERVO_5_RAW_MAX - self.SERVO_5_RAW_MIN)
        else:
            return (180.0 - 0.0) * (raw_pos - self.SERVO_RAW_MIN) / (self.SERVO_RAW_MAX - self.SERVO_RAW_MIN)
    
    def write_servo(self, servo_id: int, angle: float, time_ms: int = 1000) -> None:
        """Write position command to a single servo.
        
        Args:
            servo_id: Servo ID (1-6)
            angle: Target angle in degrees
            time_ms: Movement duration in milliseconds
        """
        if not 1 <= servo_id <= 6:
            raise ValueError(f"Servo ID must be 1-6, got {servo_id}")
        
        # Convert angle to raw position
        # Note: Servos 2, 3, 4 are mounted reversed, so we invert the angle
        if servo_id in [2, 3, 4]:
            angle = 180.0 - angle
        
        raw_pos = self.angle_to_raw(angle, servo_id)
        
        # Split position and time into high/low bytes
        pos_h = (raw_pos >> 8) & 0xFF
        pos_l = raw_pos & 0xFF
        time_h = (time_ms >> 8) & 0xFF
        time_l = time_ms & 0xFF
        
        # Build command packet
        cmd = [self.HEAD, self.DEVICE_ID, 0x07, self.CMD_SERVO_WRITE + servo_id, pos_h, pos_l, time_h, time_l]
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
        
        # Validate angle ranges
        for i in range(6):
            max_angle = 270.0 if i == 4 else 180.0  # Index 4 is servo 5
            if not 0.0 <= angles[i] <= max_angle:
                raise ValueError(f"Angle {i+1} out of range: {angles[i]} (max: {max_angle})")
        
        # Convert angles to raw positions, accounting for reversed servos
        raw_positions = []
        for i, angle in enumerate(angles):
            servo_id = i + 1
            # Servos 2, 3, 4 are reversed (indices 1, 2, 3)
            if servo_id in [2, 3, 4]:
                angle = 180.0 - angle
            raw_pos = self.angle_to_raw(angle, servo_id)
            raw_positions.append(raw_pos)
        
        # Build command packet
        time_h = (time_ms >> 8) & 0xFF
        time_l = time_ms & 0xFF
        
        cmd = [self.HEAD, self.DEVICE_ID, 0x11, self.CMD_SERVO_WRITE_ALL]
        
        # Add all servo positions
        for raw_pos in raw_positions:
            cmd.append((raw_pos >> 8) & 0xFF)  # High byte
            cmd.append(raw_pos & 0xFF)          # Low byte
        
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
        cmd = [self.HEAD, self.DEVICE_ID, 0x03, self.CMD_SERVO_READ + servo_id]
        checksum = self._calculate_checksum(cmd)
        cmd.append(checksum)
        
        try:
            # Send command and receive data
            self._send_command(cmd)
            self._receive_data()
            # Send command and receive data again to ensure correctness
            self._send_command(cmd)
            self._receive_data()

            # Check if response is for the correct servo
            if self.response_id == (self.CMD_SERVO_READ + servo_id):
                raw_pos = self.servo_position_h * 256 + self.servo_position_l
                
                if raw_pos == 0:
                    return None
                
                # Convert to angle
                angle = self.raw_to_angle(raw_pos, servo_id)
                
                # Validate range
                max_angle = 270.0 if servo_id == 5 else 180.0
                if not 0.0 <= angle <= max_angle:
                    return None
                
                # Account for reversed servos
                if servo_id in [2, 3, 4]:
                    angle = 180.0 - angle
                
                return angle
            
        except Exception as e:
            logger.error(f"Error reading servo {servo_id}: {e}")
        
        return None
    
    def _receive_data(self) -> None:
        """Receive and parse response data from device.
        
        This implementation matches the original dofbot library's approach
        to avoid timing issues that could cause device disconnection.
        """
        if not self.is_connected:
            return
        
        try:
            # Read header - use original approach for better compatibility
            head1_data = self.ser.read(1)
            if len(head1_data) == 0:
                return
            
            head1 = head1_data[0]
            if head1 == self.HEAD:
                head2_data = self.ser.read(1)
                if len(head2_data) == 0:
                    return
                
                head2 = head2_data[0]
                if head2 == self.DEVICE_ID - 1:
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
                self.servo_position_h = data[0]
                self.servo_position_l = data[1]
                self.response_id = data[2]
    
    def set_torque(self, enable: bool) -> None:
        """Enable or disable servo torque.
        
        Args:
            enable: True to enable torque, False to disable (allows manual movement)
        """
        value = 0x01 if enable else 0x00
        cmd = [self.HEAD, self.DEVICE_ID, 0x04, self.CMD_TORQUE, value]
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
        cmd = [self.HEAD, self.DEVICE_ID, 0x06, self.CMD_RGB, red & 0xFF, green & 0xFF, blue & 0xFF]
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
        
        cmd = [self.HEAD, self.DEVICE_ID, 0x04, self.CMD_BUZZER, duration & 0xFF]
        checksum = self._calculate_checksum(cmd)
        cmd.append(checksum)
        
        self._send_command(cmd)

