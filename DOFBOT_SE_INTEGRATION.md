# Dofbot SE 机械臂 LeRobot 集成说明

## 概述

本文档说明了如何在 LeRobot 代码库中使用新集成的 Dofbot SE 机械臂。此集成完全独立于 `/root/dofbot` 目录，不依赖任何外部 dofbot 包或库。

## ✅ 集成完成状态

所有核心功能已成功实现并通过测试：

- ✅ 配置类 (`DofbotSEConfig`)
- ✅ 串口通信模块 (`DofbotSerialDevice`)
- ✅ 机器人类 (`DofbotSE`)
- ✅ 工厂函数集成
- ✅ 特征定义（观察和动作）
- ✅ 6/6 基础测试通过

## 📁 文件结构

```
lerobot/
├── src/lerobot/robots/
│   ├── dofbot_se/
│   │   ├── __init__.py              # 模块导出
│   │   ├── config_dofbot_se.py      # 配置类
│   │   ├── dofbot_serial.py         # 串口通信层
│   │   ├── dofbot_se.py             # 主机器人类
│   │   └── README.md                # 详细文档
│   ├── __init__.py                  # 已更新，导出 DofbotSE
│   └── utils.py                     # 已更新，支持 dofbot_se
├── examples/
│   └── dofbot_se_example.py         # 使用示例
├── tests/
│   └── test_dofbot_se.py            # 单元测试
└── verify_dofbot_se.py              # 验证脚本
```

## 🚀 快速开始

### 1. 激活环境

```bash
conda activate lerobot
cd /root/lerobot
export PYTHONPATH=/root/lerobot/src:$PYTHONPATH
```

### 2. 基本使用示例

```python
from lerobot.robots.dofbot_se import DofbotSE, DofbotSEConfig

# 创建配置
config = DofbotSEConfig(
    port="/dev/ttyUSB0",  # 根据实际情况修改
    baudrate=115200,
    max_relative_target=30.0,  # 安全限制
)

# 创建并连接机器人
robot = DofbotSE(config)
robot.connect()

# 读取当前状态
observation = robot.get_observation()
print("当前关节位置:", observation)

# 发送控制命令
action = {
    "joint_1.pos": 90.0,   # 基座旋转
    "joint_2.pos": 90.0,   # 肩部
    "joint_3.pos": 90.0,   # 肘部
    "joint_4.pos": 90.0,   # 腕部俯仰
    "joint_5.pos": 135.0,  # 腕部旋转
    "joint_6.pos": 90.0,   # 夹爪
}
robot.send_action(action)

# 断开连接
robot.disconnect()
```

### 3. 运行示例脚本

```bash
# 确保设置了 PYTHONPATH
export PYTHONPATH=/root/lerobot/src:$PYTHONPATH

# 运行示例（需要连接实际硬件）
python examples/dofbot_se_example.py
```

### 4. 运行验证脚本

```bash
# 验证集成（不需要硬件）
export PYTHONPATH=/root/lerobot/src:$PYTHONPATH
python verify_dofbot_se.py
```

## 📋 硬件要求

1. **Dofbot SE 机械臂**
   - 6 个串行总线舵机
   - 控制板（Yahboom）
   - USB 转串口线

2. **连接方式**
   - 通过 USB 连接到计算机
   - 默认串口：`/dev/ttyUSB0` 或 `/dev/myserial`
   - 波特率：115200

3. **串口权限**
   ```bash
   # 临时授权
   sudo chmod 666 /dev/ttyUSB0
   
   # 或永久添加用户到 dialout 组
   sudo usermod -a -G dialout $USER
   # 需要重新登录生效
   ```

## 🎯 关节说明

| 关节名称 | 舵机ID | 角度范围 | 描述 |
|---------|--------|----------|------|
| joint_1 | 1 | 0-180° | 基座旋转 |
| joint_2 | 2 | 0-180° | 肩部升降 |
| joint_3 | 3 | 0-180° | 肘部弯曲 |
| joint_4 | 4 | 0-180° | 腕部俯仰 |
| joint_5 | 5 | 0-270° | 腕部/夹爪旋转 |
| joint_6 | 6 | 0-180° | 夹爪开合 |

**注意**：关节 2、3、4 的舵机是反向安装的，代码会自动处理角度转换。

## ⚙️ 配置选项

```python
DofbotSEConfig(
    id="dofbot_01",                    # 机器人标识符
    port="/dev/ttyUSB0",               # 串口设备路径
    baudrate=115200,                   # 通信波特率
    timeout=0.2,                       # 串口超时（秒）
    disable_torque_on_disconnect=True, # 断开时禁用扭矩
    max_relative_target=30.0,          # 最大单步移动（度）
    calibration_dir=None,              # 校准文件目录
    cameras={},                        # 相机配置字典
    joint_limits={...},                # 关节角度限制
)
```

## 📷 添加相机

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
        ),
        "wrist": CameraConfig(
            type="opencv",
            index=1,
            width=640,
            height=480,
            fps=30,
        ),
    }
)
```

## 🔧 与 LeRobot 工作流集成

### 数据收集

```bash
export PYTHONPATH=/root/lerobot/src:$PYTHONPATH

python lerobot/scripts/lerobot_record.py \
    --robot-type dofbot_se \
    --robot-config.port /dev/ttyUSB0 \
    --robot-config.cameras.top.type opencv \
    --robot-config.cameras.top.index 0 \
    --robot-config.cameras.top.width 640 \
    --robot-config.cameras.top.height 480 \
    --robot-config.cameras.top.fps 30 \
    --repo-id username/dofbot_demo \
    --num-episodes 50
```

### 策略训练

```bash
python lerobot/scripts/lerobot_train.py \
    --dataset username/dofbot_demo \
    --policy act \
    --config lerobot/configs/policies/act.py
```

### 策略评估

```bash
export PYTHONPATH=/root/lerobot/src:$PYTHONPATH

python lerobot/scripts/lerobot_eval.py \
    --robot-type dofbot_se \
    --robot-config.port /dev/ttyUSB0 \
    --policy-checkpoint path/to/checkpoint \
    --num-episodes 10
```

## 🛡️ 安全特性

1. **扭矩控制**
   - 连接后自动启用扭矩
   - 断开时可选择性禁用扭矩（默认）
   - 手动控制：`robot.device.set_torque(False)`

2. **运动限制**
   - `max_relative_target`：限制单步最大移动角度
   - `joint_limits`：限制每个关节的绝对角度范围
   - 自动裁剪超出范围的命令

3. **错误处理**
   - 串口通信重试机制
   - 读取失败时的默认值处理
   - 完整的异常捕获和日志记录

## 🐛 故障排除

### 问题：无法导入 lerobot 模块

**解决方案**：
```bash
export PYTHONPATH=/root/lerobot/src:$PYTHONPATH
```

### 问题：无法连接串口

**检查**：
```bash
# 查看串口设备
ls -l /dev/ttyUSB*

# 检查权限
ls -l /dev/ttyUSB0

# 添加权限
sudo chmod 666 /dev/ttyUSB0
```

### 问题：读取舵机位置失败

**可能原因**：
- 舵机供电不足
- 舵机 ID 配置错误
- 串口通信干扰

**解决方案**：
- 检查电源连接
- 降低通信频率
- 使用更短的 USB 线

### 问题：机械臂运动不流畅

**调整参数**：
```python
# 在 send_action 中增加运动时间
device.write_all_servos(angles, time_ms=500)  # 默认 100ms

# 或降低控制频率
time.sleep(0.1)  # 在控制循环中添加延迟
```

## 📖 API 参考

### 主要类

#### `DofbotSE`
```python
# 主要方法
robot.connect(calibrate=True)           # 连接机器人
robot.disconnect()                      # 断开连接
robot.get_observation() -> dict         # 获取观察
robot.send_action(action: dict) -> dict # 发送动作
robot.configure()                       # 配置机器人

# 属性
robot.is_connected -> bool              # 连接状态
robot.is_calibrated -> bool             # 校准状态
robot.observation_features -> dict      # 观察特征
robot.action_features -> dict           # 动作特征
robot.JOINT_NAMES -> list               # 关节名称列表
```

#### `DofbotSerialDevice`
```python
# 串口通信方法
device.connect()                        # 打开串口
device.disconnect()                     # 关闭串口
device.write_servo(id, angle, time_ms)  # 写入单个舵机
device.write_all_servos(angles, time)   # 写入所有舵机
device.read_servo(id) -> float          # 读取舵机位置
device.set_torque(enable: bool)         # 扭矩控制
device.set_rgb(r, g, b)                 # RGB LED 控制
device.set_buzzer(enable, duration)     # 蜂鸣器控制

# 工具方法
device.angle_to_raw(angle, id) -> int   # 角度转换
device.raw_to_angle(raw, id) -> float   # 反向转换
```

## 🎓 技术细节

### 串口通信协议

数据包格式：
```
[0xFF, 0xFC, length, command, data..., checksum]
```

- 头部：`0xFF 0xFC`
- 长度：数据长度 + 2
- 命令：操作代码
- 数据：参数字节
- 校验和：从索引 5 开始的字节和 & 0xFF

### 舵机坐标系

- **原始位置范围**：
  - 关节 1-4, 6：900-3100 (对应 0-180°)
  - 关节 5：380-3700 (对应 0-270°)

- **反向舵机**：关节 2, 3, 4
  - 软件自动处理角度反转
  - 用户使用正常角度即可

## 🔗 相关资源

- **LeRobot 文档**：https://huggingface.co/docs/lerobot
- **硬件集成教程**：https://huggingface.co/docs/lerobot/integrate_hardware
- **Dofbot SE 产品页**：https://www.yahboom.com/tbdetails/id/562
- **详细 README**：`src/lerobot/robots/dofbot_se/README.md`

## 📝 开发说明

### 代码独立性

本实现完全独立于 `/root/dofbot` 目录：
- ✅ 无文件依赖
- ✅ 无包依赖
- ✅ 自包含串口协议实现
- ✅ 所有舵机控制逻辑自实现

### 扩展和修改

1. **添加新功能**：修改 `dofbot_se.py`
2. **调整通信协议**：修改 `dofbot_serial.py`
3. **更新配置**：修改 `config_dofbot_se.py`

### 测试

```bash
# 运行单元测试（不需要硬件）
export PYTHONPATH=/root/lerobot/src:$PYTHONPATH
python verify_dofbot_se.py

# 运行物理测试（需要硬件）
pytest tests/test_dofbot_se.py -m physical
```

## ✨ 下一步

1. **连接硬件**：将 Dofbot SE 连接到串口
2. **运行示例**：`python examples/dofbot_se_example.py`
3. **收集数据**：使用 LeRobot 记录脚本
4. **训练模型**：使用收集的数据训练策略
5. **部署评估**：在真实硬件上测试训练的策略

## 📧 支持

如有问题或需要帮助，请参考：
- LeRobot GitHub Issues
- LeRobot 文档
- 本文档和 README

---

**版本**：1.0  
**更新日期**：2024  
**许可证**：Apache License 2.0

