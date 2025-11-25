#!/usr/bin/env python

"""
如果驱动一直找不到的话，就重新加载驱动：
sudo modprobe -r ch341 && sleep 1 && sudo modprobe ch341 && echo "✓ 驱动已重新加载" && sleep 2 && (ls -l /dev/ttyUSB* /dev/dofbot 2>/dev/null || echo "设备仍未出现")

Usage:
    python examples/find_dofbot_port.py
"""

import platform
import time
from pathlib import Path


def find_available_ports():
    """Find all available serial ports on the system."""
    try:
        from serial.tools import list_ports
        
        if platform.system() == "Windows":
            ports = [port.device for port in list_ports.comports()]
        else:  # Linux/macOS
            # Look for common USB serial devices
            dev_path = Path("/dev")
            patterns = ["ttyUSB*", "ttyACM*", "tty.usbserial*", "tty.usbmodem*"]
            ports = []
            for pattern in patterns:
                ports.extend([str(p) for p in dev_path.glob(pattern)])
            ports.sort()
        
        return ports
    except ImportError:
        print("⚠ pyserial not installed. Install it with: pip install pyserial")
        return []


def test_port(port: str) -> bool:
    """Test if a port can be opened."""
    try:
        import serial
        ser = serial.Serial(port, 115200, timeout=0.2)
        ser.close()
        return True
    except Exception as e:
        return False


def main():
    print("=" * 60)
    print("Dofbot SE 端口查找工具")
    print("=" * 60)
    print()
    
    # Check if running in VM
    print("💡 提示:")
    print("  如果在虚拟机中运行，请确保:")
    print("  1. USB 设备已连接到物理机")
    print("  2. 在虚拟机菜单中: VM -> Removable Devices -> QinHeng USB Serial")
    print("     选择 'Connect (Disconnect from Host)'")
    print()
    
    # Find ports
    print("查找可用串口...")
    ports = find_available_ports()
    
    if not ports:
        print("❌ 未找到任何串口设备")
        print()
        print("可能的原因:")
        print("  1. Dofbot SE 未连接")
        print("  2. USB 驱动未安装")
        print("  3. (虚拟机) USB 设备未连接到虚拟机")
        print()
        print("解决方法:")
        print("  - 检查 USB 连接")
        print("  - 虚拟机: VM -> Removable Devices -> 连接 USB 设备")
        print("  - Linux: 检查设备权限")
        return
    
    print(f"✓ 找到 {len(ports)} 个串口设备:")
    print()
    
    # Test each port
    for i, port in enumerate(ports, 1):
        can_open = test_port(port)
        status = "✓ 可访问" if can_open else "✗ 无权限/被占用"
        print(f"  {i}. {port:<30} {status}")
        
        # Show permission info for Linux
        if not can_open and platform.system() == "Linux":
            port_path = Path(port)
            if port_path.exists():
                import stat
                st = port_path.stat()
                mode = stat.filemode(st.st_mode)
                print(f"     权限: {mode}")
                print(f"     提示: sudo chmod 666 {port}")
    
    print()
    print("=" * 60)
    print("使用方法:")
    print("=" * 60)
    print()
    print("1. 选择上面列出的端口")
    print()
    print("2. 运行示例:")
    if ports:
        example_port = ports[0]
        print(f"   python examples/dofbot_se_example.py {example_port}")
    else:
        print("   python examples/dofbot_se_example.py /dev/ttyUSB0")
    print()
    print("3. 或在代码中使用:")
    print("   config = DofbotSEConfig(port='/dev/ttyUSB0')")
    print()
    
    # Interactive mode
    if ports:
        print("=" * 60)
        try:
            choice = input("输入端口编号进行测试 (直接回车跳过): ").strip()
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(ports):
                    selected_port = ports[idx]
                    print()
                    print(f"测试连接到 {selected_port}...")
                    
                    try:
                        import serial
                        ser = serial.Serial(selected_port, 115200, timeout=0.2)
                        print(f"✓ 成功打开端口 {selected_port}")
                        ser.close()
                        print()
                        print(f"使用此端口运行:")
                        print(f"  python examples/dofbot_se_example.py {selected_port}")
                    except Exception as e:
                        print(f"✗ 无法打开端口: {e}")
                        if "Permission denied" in str(e):
                            print(f"  运行: sudo chmod 666 {selected_port}")
        except KeyboardInterrupt:
            print("\n已取消")


if __name__ == "__main__":
    main()

