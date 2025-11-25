# Dofbot SE Integration for LeRobot

Dofbot SE 是一款 6 自由度教育型机械臂，本集成为其提供了 LeRobot 兼容接口。

## 硬件规格

- **自由度**: 6 DOF
- **舵机**: 串行总线舵机
- **通信**: 串口通信 (115200 波特率)
- **关节范围**:
  - 关节 1-4, 6: 0-180 度
  - 关节 5: 0-270 度 (夹爪旋转)
- **附加功能**: RGB LED, 蜂鸣器

## 安装要求

```bash
pip install pyserial
```

## 硬件连接

1. 通过 USB 转串口线连接 Dofbot SE 到计算机
2. 确认串口设备路径 (通常是 `/dev/ttyUSB0` 或 `/dev/myserial`)
3. 确保有权限访问串口设备:
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   # 或者将用户添加到 dialout 组
   sudo usermod -a -G dialout $USER
   ```

## 快速开始

### 基本使用

```python
from lerobot.robots.dofbot_se import DofbotSE, DofbotSEConfig

# 创建配置
config = DofbotSEConfig(
    port="/dev/ttyUSB0",
    baudrate=115200,
)

# 连接机器人
robot = DofbotSE(config)
robot.connect()

# 读取观察值
obs = robot.get_observation()
print(obs)

# 发送动作
action = {
    "joint_1.pos": 90.0,
    "joint_2.pos": 90.0,
    "joint_3.pos": 90.0,
    "joint_4.pos": 90.0,
    "joint_5.pos": 135.0,
    "joint_6.pos": 90.0,
}
robot.send_action(action)

# 断开连接
robot.disconnect()
```

### 配置选项

```python
config = DofbotSEConfig(
    id="dofbot_01",                    # 机器人 ID
    port="/dev/ttyUSB0",               # 串口路径
    baudrate=115200,                   # 波特率
    timeout=0.2,                       # 串口超时时间
    disable_torque_on_disconnect=True, # 断开时禁用扭矩
    max_relative_target=30.0,          # 最大单步移动角度（安全限制）
    cameras={},                        # 相机配置
)
```

### 使用相机

```python
from lerobot.cameras import CameraConfig

config = DofbotSEConfig(
    port="/dev/ttyUSB0",
    cameras={
        "top": CameraConfig(
            type="opencv",
            index=0,
            width=640,
            height=480,
            fps=30,
        )
    }
)

robot = DofbotSE(config)
robot.connect()

obs = robot.get_observation()
# obs 将包含相机图像: obs["top"]
```

## 示例脚本

运行示例脚本:

```bash
python examples/dofbot_se_example.py
```

## 与 LeRobot 工作流集成

### 数据收集

使用 LeRobot 的记录脚本收集演示数据:

```bash
python lerobot/scripts/lerobot_record.py \
    --robot-type dofbot_se \
    --robot-config.port /dev/ttyUSB0 \
    --robot-config.cameras.top.type opencv \
    --robot-config.cameras.top.index 0 \
    --robot-config.cameras.top.width 640 \
    --robot-config.cameras.top.height 480 \
    --robot-config.cameras.top.fps 30 \
    --repo-id your-username/dofbot_demo \
    --num-episodes 50
```

### 训练策略

```bash
python lerobot/scripts/lerobot_train.py \
    --dataset your-username/dofbot_demo \
    --policy act \
    --config lerobot/configs/policies/act.py
```

### 评估策略

```bash
python lerobot/scripts/lerobot_eval.py \
    --robot-type dofbot_se \
    --robot-config.port /dev/ttyUSB0 \
    --policy-checkpoint path/to/checkpoint \
    --num-episodes 10
```

## 关节映射

| 关节名称 | 舵机 ID | 范围 | 描述 |
|---------|---------|------|------|
| joint_1 | 1 | 0-180° | 基座旋转 |
| joint_2 | 2 | 0-180° | 肩部 |
| joint_3 | 3 | 0-180° | 肘部 |
| joint_4 | 4 | 0-180° | 腕部俯仰 |
| joint_5 | 5 | 0-270° | 腕部旋转/夹爪旋转 |
| joint_6 | 6 | 0-180° | 夹爪 |

## 注意事项

1. **舵机反向**: 关节 2, 3, 4 的舵机是反向安装的，代码会自动处理角度转换
2. **安全限制**: 配置 `max_relative_target` 可以限制单步移动范围，防止意外剧烈运动
3. **断开安全**: 断开连接时默认会禁用扭矩，防止舵机锁定
4. **串口权限**: 确保有权限访问串口设备

## 故障排除

### 无法连接到串口

```bash
# 检查设备是否存在
ls -l /dev/ttyUSB*

# 检查权限
ls -l /dev/ttyUSB0

# 添加权限
sudo chmod 666 /dev/ttyUSB0
```

### 读取舵机位置失败

- 检查舵机供电是否正常
- 确认舵机 ID 配置正确
- 尝试降低通信频率

### 运动不流畅

- 调整 `time_ms` 参数（在 `write_all_servos` 中）
- 检查舵机负载是否过大
- 确保供电充足

## 架构说明

实现包含以下主要组件:

- `DofbotSEConfig`: 配置类，定义机器人参数
- `DofbotSerialDevice`: 串口通信层，处理底层协议
- `DofbotSE`: 主机器人类，实现 LeRobot Robot 接口

### 与 dofbot 目录的独立性

本实现**完全独立**于 dofbot 目录，不依赖其中的任何代码或库:

- 串口通信协议从头实现
- 所有舵机控制逻辑自包含
- 不需要安装 Arm_Lib 或其他 dofbot 依赖

## 贡献

欢迎贡献改进! 请确保:

1. 代码通过 linter 检查
2. 添加适当的文档和注释
3. 包含示例用法
4. 测试与真实硬件的兼容性

## 许可证

Apache License 2.0 - 参见 LICENSE 文件

## 参考资源

- [LeRobot 文档](https://huggingface.co/docs/lerobot)
- [Dofbot SE 产品页面](https://www.yahboom.com/tbdetails/id/562)
- [硬件集成教程](https://huggingface.co/docs/lerobot/integrate_hardware)

