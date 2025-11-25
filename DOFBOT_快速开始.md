# Dofbot SE 快速开始指南

## 🎯 目标

使用 Dofbot SE 机械臂采集数据，用于训练模仿学习模型。

---

## 📋 前期准备

### 1. 硬件检查

```bash
# 1. 确保机械臂已连接并打开电源
bash fix_usb.sh

# 2. 检查摄像头（你有 /dev/video0-3）
ls /dev/video*

# 3. 测试机械臂（可选）
python examples/dofbot_se_example.py /dev/ttyUSB0
```

### 2. 确定摄像头编号

虚拟机中通常有多个 video 设备，需要测试哪些是真正的摄像头：

```bash
# 测试方法 1：使用 v4l2-ctl（如果已安装）
v4l2-ctl --list-devices

# 测试方法 2：使用 Python 快速测试
python3 << 'EOF'
import cv2
for i in [0, 1, 2, 3]:
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"✓ /dev/video{i}: {frame.shape} - 可用")
        else:
            print(f"✗ /dev/video{i}: 打开但无法读取")
    else:
        print(f"✗ /dev/video{i}: 无法打开")
    cap.release()
EOF
```

假设测试结果：
- `/dev/video0` ✓ 可用 → **腕部摄像头**
- `/dev/video1` ✗ 元数据设备
- `/dev/video2` ✓ 可用 → **顶部摄像头**
- `/dev/video3` ✗ 元数据设备

---

## 🚀 开始采集数据

### 最简命令（推荐新手）

```bash
lerobot-record \
    --robot.type=dofbot_se \
    --robot.port=/dev/ttyUSB0 \
    --robot.cameras='{"wrist": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --teleop.type=dofbot_kinesthetic \
    --dataset.repo_id=test/pick_cube \
    --dataset.single_task="拿起红色方块" \
    --dataset.num_episodes=5 \
    --dataset.fps=30 \
    --display_data=true \
    --dataset.push_to_hub=false
```

**重要**：`--teleop.type=dofbot_kinesthetic` 启用手动示教模式（kinesthetic teaching）。

### 完整命令（更多控制）

```bash
lerobot-record \
    --robot.type=dofbot_se \
    --robot.port=/dev/ttyUSB0 \
    --robot.cameras='{"wrist": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --teleop.type=dofbot_kinesthetic \
    --dataset.repo_id=your_username/your_dataset \
    --dataset.single_task="描述你的任务" \
    --dataset.num_episodes=50 \
    --dataset.episode_time_s=30 \
    --dataset.reset_time_s=10 \
    --dataset.fps=30 \
    --dataset.video=true \
    --dataset.num_image_writer_threads_per_camera=4 \
    --display_data=true \
    --dataset.push_to_hub=false
```

---

## 📝 关键参数说明

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `--robot.type` | 机器人类型（固定） | `dofbot_se` |
| `--robot.port` | 串口地址 | `/dev/ttyUSB0` 或 `/dev/dofbot` |
| `--robot.cameras` | 摄像头配置（JSON 格式） | 见下方详细说明 |
| `--teleop.type` | 控制方式（手动示教） | `dofbot_kinesthetic` |
| `--dataset.repo_id` | 数据集 ID | `username/dataset_name` |
| `--dataset.single_task` | 任务描述 | "拿起方块并放入盒子" |
| `--dataset.num_episodes` | 采集的 episode 数量 | `50` |
| `--dataset.fps` | 数据采集频率 | `30` |
| `--dataset.episode_time_s` | 每个 episode 最长时间 | `30`（秒） |
| `--dataset.reset_time_s` | 重置环境的时间 | `10`（秒） |
| `--display_data` | 显示实时数据 | `true` / `false` |
| `--dataset.push_to_hub` | 上传到 HuggingFace Hub | `true` / `false` |

---

## 📷 摄像头配置详解

摄像头配置是一个 JSON 字典，格式：

```json
{
  "camera_name": {
    "type": "opencv",
    "index_or_path": 0,
    "width": 640,
    "height": 480,
    "fps": 30
  }
}
```

### 单个摄像头示例

```bash
--robot.cameras='{"wrist": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}}'
```

### 两个摄像头示例（推荐）

```bash
--robot.cameras='{
  "wrist": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30},
  "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}
}'
```

**注意**：命令行中整个 JSON 要用单引号包裹，内部使用双引号。

---

## 🎮 采集过程

### 1. 启动命令后

```
Recording episode 0
```

程序开始录制，此时机械臂的舵机扭矩会自动关闭，你可以手动移动机械臂。

### 2. 演示任务

- **手动移动**机械臂完成任务
- 动作要**平滑、稳定**
- 保持**一致的速度**
- 完成后保持姿态 1-2 秒

### 3. 重置环境

```
Reset the environment
```

Episode 录制完成后，程序给你时间重置环境（将物体和机械臂恢复到初始位置）。

### 4. 重复步骤 2-3

直到完成所有 episodes。

### 5. 控制按键

录制过程中：
- **空格键**：暂停/继续
- **R 键**：重新录制当前 episode
- **Q 键**：提前退出

---

## 🔍 查看采集的数据

### 数据存储位置

```bash
cd ~/.cache/huggingface/lerobot/
ls
```

你会看到你的数据集目录（格式：`username___dataset_name`）。

### 可视化数据

```bash
# 查看第一个 episode
lerobot-visualize-dataset \
    --repo-id=test/pick_cube \
    --episode-index=0
```

---

## 🎓 训练模型

数据采集完成后，可以训练模型：

```bash
lerobot-train \
    --dataset.repo_id=test/pick_cube \
    --policy.type=act \
    --training.num_epochs=3000 \
    --training.batch_size=8
```

---

## ❓ 常见问题

### Q1: 摄像头打不开

```bash
# 解决方法 1：尝试其他索引
--robot.cameras.wrist.index_or_path=2  # 尝试 0, 2, 4

# 解决方法 2：使用绝对路径
--robot.cameras.wrist.index_or_path=/dev/video0

# 解决方法 3：在虚拟机中检查 USB 设备是否连接到虚拟机
```

### Q2: 帧率不稳定

```bash
# 降低分辨率
--robot.cameras.wrist.width=320 \
--robot.cameras.wrist.height=240

# 降低帧率
--dataset.fps=15

# 关闭实时显示
--display_data=false
```

### Q3: 机械臂无法手动移动

机械臂在录制时应该自动关闭扭矩。如果仍然无法移动，检查：

```bash
# 检查配置中的 disable_torque_on_disconnect
--robot.disable_torque_on_disconnect=true
```

### Q4: JSON 格式错误

确保：
- 整个 JSON 用**单引号**包裹
- JSON 内部使用**双引号**
- 没有多余的空格或换行（除非使用多行格式）

**正确**：
```bash
--robot.cameras='{"wrist": {"type": "opencv", "index_or_path": 0}}'
```

**错误**：
```bash
--robot.cameras={"wrist": {"type": "opencv", "index_or_path": 0}}  # 缺少外层引号
--robot.cameras="{'wrist': {'type': 'opencv'}}"  # 使用了单引号在 JSON 内部
```

### Q5: 虚拟机 USB 问题

如果 USB 设备频繁断开：

```bash
# 运行修复脚本
bash fix_usb.sh

# 在采集前确认设备稳定
ls -l /dev/ttyUSB0 /dev/dofbot
```

---

## 📚 更多资源

- **LeRobot 官方文档**：https://huggingface.co/docs/lerobot
- **Dofbot SE 集成文档**：`/root/lerobot/DOFBOT_SE_INTEGRATION.md`
- **详细采集指南**：`/root/lerobot/DOFBOT_数据采集指南.md`

---

## 🎉 开始你的第一次采集！

```bash
# 1. 确保环境正确
conda activate lerobot
source setup_dofbot_env.sh

# 2. 测试硬件
bash fix_usb.sh
python examples/dofbot_se_example.py /dev/ttyUSB0

# 3. 开始采集（5 个测试 episodes）
lerobot-record \
    --robot.type=dofbot_se \
    --robot.port=/dev/ttyUSB0 \
    --robot.cameras='{"wrist": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --teleop.type=dofbot_kinesthetic \
    --dataset.repo_id=test/my_first_dataset \
    --dataset.single_task="拿起红色方块" \
    --dataset.num_episodes=5 \
    --dataset.fps=30 \
    --display_data=true \
    --dataset.push_to_hub=false
```

祝你数据采集顺利！🚀

