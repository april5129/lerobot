#!/usr/bin/env python
"""简单的串口连接测试工具"""

import serial
import time

def test_serial(port="/dev/dofbot", baudrate=115200):
    print(f"测试串口连接: {port} @ {baudrate}")
    print("=" * 50)
    
    try:
        # 打开串口
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"✓ 串口打开成功: {port}")
        print(f"  波特率: {baudrate}")
        print(f"  超时: {ser.timeout}s")
        print()
        
        # 尝试写入测试命令
        print("尝试发送测试命令...")
        test_cmd = [0xFF, 0xFC, 0x03, 0x01, 0x00]  # 简单的查询命令
        
        try:
            ser.write(bytearray(test_cmd))
            print("✓ 命令发送成功")
            
            # 尝试读取响应
            time.sleep(0.1)
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                print(f"✓ 收到响应: {len(data)} 字节")
                print(f"  数据: {' '.join(f'{b:02X}' for b in data)}")
            else:
                print("⚠ 未收到响应（这是正常的，如果机械臂电源未打开）")
                print()
                print("请检查:")
                print("  1. Dofbot SE 电源是否打开")
                print("  2. 电源指示灯是否亮起")
                print("  3. 控制板是否正常供电")
                
        except Exception as e:
            print(f"✗ 发送命令失败: {e}")
            print()
            print("可能的原因:")
            print("  1. Dofbot SE 电源未打开")
            print("  2. 虚拟机 USB 传输问题")
            print("  3. 硬件故障")
            return False
            
        ser.close()
        print()
        print("✓ 串口测试完成")
        return True
        
    except serial.SerialException as e:
        print(f"✗ 无法打开串口: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print()
    print("=" * 50)
    print("Dofbot SE 串口连接测试")
    print("=" * 50)
    print()
    
    # 测试 /dev/dofbot
    success = test_serial("/dev/dofbot")
    
    print()
    print("=" * 50)
    if success:
        print("串口通信正常！")
        print()
        print("如果仍然遇到问题，请确保:")
        print("  ✓ Dofbot SE 电源已打开")
        print("  ✓ 控制板指示灯正常")
        print("  ✓ 所有舵机已连接")
    else:
        print("串口通信失败！")
        print()
        print("请检查:")
        print("  1. Dofbot SE 电源开关")
        print("  2. USB 连接")
        print("  3. 在物理机上测试")
    print("=" * 50)

