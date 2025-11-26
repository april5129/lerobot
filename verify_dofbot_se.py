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
验证 Dofbot SE 集成的基本功能。
此脚本不需要物理硬件连接，仅测试代码结构和导入。
"""

import sys


def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)
    
    try:
        from lerobot.robots.dofbot_se import DofbotSE, DofbotSEConfig, DofbotSerialDevice
        print("✓ 成功导入 DofbotSE, DofbotSEConfig, DofbotSerialDevice")
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    try:
        from lerobot.robots import make_robot_from_config
        print("✓ 成功导入 make_robot_from_config")
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    print()
    return True


def test_config():
    """测试配置类"""
    print("=" * 60)
    print("测试 2: 配置类")
    print("=" * 60)
    
    try:
        from lerobot.robots.dofbot_se import DofbotSEConfig
        
        # 测试默认配置
        config = DofbotSEConfig(port="/dev/ttyUSB0")
        print(f"✓ 创建默认配置: port={config.port}, baudrate={config.baudrate}")
        
        # 测试自定义配置
        config = DofbotSEConfig(
            id="test_robot",
            port="/dev/ttyUSB0",
            baudrate=115200,
            max_relative_target=45.0,
        )
        print(f"✓ 创建自定义配置: id={config.id}, port={config.port}")
        
        # 检查关节限制
        assert len(config.joint_limits) == 6
        assert config.joint_limits["joint_1"] == (0.0, 180.0)
        assert config.joint_limits["joint_5"] == (0.0, 270.0)
        print(f"✓ 关节限制配置正确: {len(config.joint_limits)} 个关节")
        
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True


def test_serial_device():
    """测试串口设备类"""
    print("=" * 60)
    print("测试 3: 串口设备类")
    print("=" * 60)
    
    try:
        from lerobot.robots.dofbot_se import DofbotSerialDevice
        
        device = DofbotSerialDevice(port="/dev/null")
        print("✓ 创建串口设备实例")
        
        # 测试角度转换
        raw_pos = device.angle_to_raw(90.0, 1)
        print(f"✓ 角度转换 (90° → {raw_pos} raw)")
        
        angle = device.raw_to_angle(2000, 1)
        print(f"✓ 反向转换 (2000 raw → {angle:.1f}°)")
        
        # 测试校验和计算
        cmd = [0xFF, 0xFC, 0x07, 0x11, 0x08, 0x00, 0x03, 0xE8]
        checksum = device._calculate_checksum(cmd)
        print(f"✓ 校验和计算: {checksum}")
        
    except Exception as e:
        print(f"✗ 串口设备测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True


def test_robot_class():
    """测试机器人类"""
    print("=" * 60)
    print("测试 4: 机器人类")
    print("=" * 60)
    
    try:
        from lerobot.robots.dofbot_se import DofbotSE, DofbotSEConfig
        
        config = DofbotSEConfig(port="/dev/null")
        robot = DofbotSE(config)
        print(f"✓ 创建机器人实例: {robot}")
        
        # 检查基本属性
        assert robot.name == "dofbot_se"
        print(f"✓ 机器人名称: {robot.name}")
        
        assert len(robot.JOINT_NAMES) == 6
        print(f"✓ 关节数量: {len(robot.JOINT_NAMES)}")
        
        # 检查特征定义
        obs_features = robot.observation_features
        action_features = robot.action_features
        print(f"✓ 观察特征: {len(obs_features)} 个")
        print(f"✓ 动作特征: {len(action_features)} 个")
        
        # 检查关节名称
        expected_joints = ["joint_1", "joint_2", "joint_3", "joint_4", "joint_5", "joint_6"]
        assert robot.JOINT_NAMES == expected_joints
        print(f"✓ 关节名称正确: {', '.join(robot.JOINT_NAMES)}")
        
    except Exception as e:
        print(f"✗ 机器人类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True


def test_robot_factory():
    """测试机器人工厂函数"""
    print("=" * 60)
    print("测试 5: 机器人工厂")
    print("=" * 60)
    
    try:
        from lerobot.robots import make_robot_from_config
        from lerobot.robots.dofbot_se import DofbotSEConfig
        
        config = DofbotSEConfig(port="/dev/null", id="factory_test")
        robot = make_robot_from_config(config)
        
        print(f"✓ 通过工厂函数创建机器人: {robot}")
        assert robot.name == "dofbot_se"
        assert robot.id == "factory_test"
        print(f"✓ 机器人类型和 ID 正确")
        
    except Exception as e:
        print(f"✗ 工厂函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True


def test_features_structure():
    """测试特征结构"""
    print("=" * 60)
    print("测试 6: 特征结构")
    print("=" * 60)
    
    try:
        from lerobot.robots.dofbot_se import DofbotSE, DofbotSEConfig
        
        config = DofbotSEConfig(port="/dev/null")
        robot = DofbotSE(config)
        
        # 检查观察特征
        obs_features = robot.observation_features
        for joint in robot.JOINT_NAMES:
            key = f"{joint}.pos"
            assert key in obs_features
            assert obs_features[key] == float
        print(f"✓ 所有关节都在观察特征中")
        
        # 检查动作特征
        action_features = robot.action_features
        for joint in robot.JOINT_NAMES:
            key = f"{joint}.pos"
            assert key in action_features
            assert action_features[key] == float
        print(f"✓ 所有关节都在动作特征中")
        
    except Exception as e:
        print(f"✗ 特征结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Dofbot SE 集成验证")
    print("=" * 60)
    print()
    
    tests = [
        ("模块导入", test_imports),
        ("配置类", test_config),
        ("串口设备类", test_serial_device),
        ("机器人类", test_robot_class),
        ("机器人工厂", test_robot_factory),
        ("特征结构", test_features_structure),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 汇总结果
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {name}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! Dofbot SE 集成已成功配置。")
        print("\n下一步:")
        print("1. 连接 Dofbot SE 硬件到串口")
        print("2. 运行示例脚本: python examples/dofbot_se_example.py")
        print("3. 查看文档: src/lerobot/robots/dofbot_se/README.md")
        return 0
    else:
        print("\n⚠ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

