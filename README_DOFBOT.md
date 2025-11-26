# Dofbot SE 使用指南 🤖

## 🎉 已完成改进

根据 LeRobot 最佳实践，我们改进了端口配置：

✅ **移除硬编码默认端口** - 现在必须显式指定  
✅ **支持命令行参数** - 更灵活的配置方式  
✅ **新增端口查找工具** - 特别为虚拟机优化  
✅ **完善虚拟机文档** - 详细的连接步骤  

## 🚀 快速开始

### 1. 激活环境
```bash
conda activate lerobot
cd /root/lerobot
```

### 2. 连接 USB 设备

**如果你在虚拟机中** (VMware/VirtualBox):
1. 连接 USB 到物理机
2. 在虚拟机菜单: `VM` → `Removable Devices` → `QinHeng USB Serial` → `Connect`

### 3. 查找端口
```bash
# 使用自动工具（推荐）
python examples/find_dofbot_port.py
```

示例输出：
```
✓ 找到 1 个串口设备:
  1. /dev/ttyUSB0                ✓ 可访问
```

### 4. 运行示例

**方法 A: 交互式** (推荐新手)
```bash
python examples/dofbot_se_example.py
# 会提示输入端口
```

**方法 B: 命令行参数** (推荐脚本)
```bash
python examples/dofbot_se_example.py /dev/ttyUSB0
```

## 💻 Python 代码示例

```python
from lerobot.robots.dofbot_se import DofbotSE, DofbotSEConfig

# 创建配置（必须指定端口）
config = DofbotSEConfig(
    port="/dev/ttyUSB0",  # 使用 find_dofbot_port.py 找到的端口
    baudrate=115200,
    max_relative_target=30.0,
)

# 连接机器人
robot = DofbotSE(config)
robot.connect()

# 控制机械臂
action = {
    "joint_1.pos": 90.0,
    "joint_2.pos": 90.0,
    "joint_3.pos": 90.0,
    "joint_4.pos": 90.0,
    "joint_5.pos": 135.0,
    "joint_6.pos": 90.0,
}
robot.send_action(action)

# 读取状态
obs = robot.get_observation()
print(obs)

# 断开连接
robot.disconnect()
```

## 🔧 与 LeRobot 工作流集成

### 数据收集
```bash
python lerobot/scripts/lerobot_record.py \
    --robot-type dofbot_se \
    --robot-config.port /dev/ttyUSB0 \
    --repo-id username/dofbot_demo \
    --num-episodes 50
```

### 训练策略
```bash
python lerobot/scripts/lerobot_train.py \
    --dataset username/dofbot_demo \
    --policy act
```

### 评估策略
```bash
python lerobot/scripts/lerobot_eval.py \
    --robot-type dofbot_se \
    --robot-config.port /dev/ttyUSB0 \
    --policy-checkpoint path/to/checkpoint
```

## 🐛 常见问题

### ❓ ModuleNotFoundError: No module named 'lerobot'

**解决**:
```bash
conda activate lerobot
# 你应该看到: ✓ PYTHONPATH 已设置
```

### ❓ 找不到串口设备

**虚拟机用户**:
1. 确认 USB 已连接到虚拟机（不是物理机）
2. 检查: `VM` → `Removable Devices` → `QinHeng USB Serial` → `Connect`

**所有用户**:
```bash
# 查看设备
python examples/find_dofbot_port.py
# 或
ls -l /dev/ttyUSB* /dev/ttyACM*
```

### ❓ Permission denied

```bash
sudo chmod 666 /dev/ttyUSB0
```

## 📚 详细文档

- **虚拟机用户**: 阅读 `虚拟机使用指南.md`
- **端口配置改进**: 阅读 `端口配置改进说明.md`
- **完整文档**: 阅读 `DOFBOT_SE_INTEGRATION.md`
- **快速参考**: 阅读 `快速开始.md`

## 🛠️ 可用工具

| 工具 | 用途 |
|------|------|
| `examples/find_dofbot_port.py` | 查找和测试串口 |
| `verify_dofbot_se.py` | 验证安装（无需硬件） |
| `examples/dofbot_se_example.py` | 完整使用示例 |
| `lerobot-find-port` | LeRobot 通用端口查找 |

## 📋 文件结构

```
lerobot/
├── 快速开始.md                    # 新手指南
├── 虚拟机使用指南.md              # 虚拟机专用
├── 端口配置改进说明.md            # 改进说明
├── DOFBOT_SE_INTEGRATION.md     # 完整文档
├── README_DOFBOT.md             # 本文件
├── examples/
│   ├── find_dofbot_port.py      # 端口查找工具 ⭐
│   └── dofbot_se_example.py     # 使用示例
├── verify_dofbot_se.py          # 验证脚本
└── src/lerobot/robots/dofbot_se/
    ├── config_dofbot_se.py      # 配置（已改进）
    ├── dofbot_serial.py         # 串口通信
    ├── dofbot_se.py             # 机器人类
    └── README.md                # 技术文档
```

## ✨ 重要变更

### ⚠️ 端口配置变更

**旧代码**（不再工作）:
```python
config = DofbotSEConfig()  # ❌ 缺少 port 参数
```

**新代码**（必需）:
```python
config = DofbotSEConfig(port="/dev/ttyUSB0")  # ✅ 必须指定
```

这符合 LeRobot 的标准做法（参考 Koch、SO100 等机器人）。

## 🎯 下一步

1. ✅ 环境已配置
2. ⏭️ 连接 Dofbot SE（虚拟机用户注意 USB 连接）
3. ⏭️ 运行 `find_dofbot_port.py` 找到端口
4. ⏭️ 运行示例测试
5. ⏭️ 开始收集数据和训练模型

## 🆘 需要帮助？

1. **查看文档**: 先阅读相关 .md 文件
2. **运行诊断**: `python examples/find_dofbot_port.py`
3. **验证安装**: `python verify_dofbot_se.py`
4. **查看日志**: 检查错误消息和日志

---

**版本**: 1.1  
**更新**: 2024  
**改进**: 移除硬编码端口，符合 LeRobot 最佳实践

