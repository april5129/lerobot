# Dofbot SE 数据采集完整指南

本指南详细说明如何使用 Dofbot SE 机械臂进行数据采集，用于训练模仿学习模型。

> **⚡ 快速开始**：如果你是新手，建议先阅读 [`DOFBOT_快速开始.md`](./DOFBOT_快速开始.md)

## 📋 目录

1. [前期准备](#前期准备)
2. [摄像头配置](#摄像头配置)
3. [数据采集方法](#数据采集方法)
4. [采集流程](#采集流程)
5. [常见问题](#常见问题)

---

## 前期准备

### 1. 硬件要求

- ✅ Dofbot SE 机械臂（已连接并测试）
- ✅ 两个 USB 摄像头：
  - **腕部摄像头**：安装在机械臂末端，用于捕捉第一人称视角
  - **顶部摄像头**：固定在工作区上方，提供全局视角
- ✅ 外部电源适配器（必须！USB 供电不足）

### 2. 软件环境

确保已激活 `lerobot` conda 环境：

```bash
conda activate lerobot
source /root/lerobot/setup_dofbot_env.sh
```

### 3. 检查设备连接

#### 检查机械臂串口

```bash
python examples/find_dofbot_port.py
# 或
bash fix_usb.sh
```

应该看到 `/dev/ttyUSB0` 或 `/dev/dofbot`。

#### 检查摄像头

```bash
ls /dev/video*
```

你应该看到多个摄像头设备，例如：
```
/dev/video0
/dev/video1
/dev/video2
/dev/video3
```

**注意**：通常每个物理摄像头会对应两个设备号（一个用于视频，一个用于元数据）。实际可用的视频设备通常是偶数编号（0, 2, 4...）。

---

## 摄像头配置

### 查找可用摄像头

LeRobot 提供了工具来检测摄像头：

```bash
lerobot-find-cameras
```

这个命令会列出所有可用的摄像头及其索引。

### 测试摄像头

在开始数据采集前，建议先测试摄像头是否正常工作：

```python
import cv2

# 测试摄像头 0
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f"摄像头 0: {frame.shape} - 工作正常 ✓")
    cv2.imwrite('test_camera_0.jpg', frame)
cap.release()

# 测试摄像头 1
cap = cv2.VideoCapture(1)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f"摄像头 1: {frame.shape} - 工作正常 ✓")
    cv2.imwrite('test_camera_1.jpg', frame)
cap.release()
```

### 推荐的摄像头设置

根据你的硬件，选择合适的分辨率和帧率：

| 场景 | 分辨率 | 帧率 | 说明 |
|------|--------|------|------|
| **快速测试** | 320x240 | 15 FPS | 数据量小，适合调试 |
| **标准质量** | 640x480 | 30 FPS | 平衡性能与质量 ⭐ 推荐 |
| **高质量** | 1280x720 | 30 FPS | 更好的细节，需要更好的硬件 |
| **高速** | 640x480 | 60 FPS | 快速动作，需要高性能摄像头 |

---

## 数据采集方法

Dofbot SE 的数据采集是**演示式的**（kinesthetic teaching），即：

1. **关闭舵机扭矩**（使机械臂可以自由移动）
2. **手动移动机械臂**完成任务
3. **LeRobot 记录**：
   - 每个关节的角度
   - 摄像头的图像
   - 时间戳

### 基本命令

LeRobot 使用原生的 `lerobot-record` 命令进行数据采集：

```bash
lerobot-record \
    --robot.type=dofbot_se \
    --robot.port=/dev/ttyUSB0 \
    --robot.cameras='{"wrist": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --teleop.type=dofbot_kinesthetic \
    --dataset.repo_id=april5129/dofbot_demo \
    --dataset.single_task="place the red block into the plate" \
    --dataset.num_episodes=3 \
    --dataset.fps=30 \
    --dataset.episode_time_s=30 \
    --dataset.reset_time_s=10 \
    --display_data=false \
    --dataset.push_to_hub=false
```

**注意**：
- 摄像头配置使用 JSON 格式，整个 JSON 字符串用单引号包裹
- `--teleop.type=dofbot_kinesthetic` 启用手动示教模式（必需）

### 参数详解

| 参数 | 说明 | 示例 |
|------|------|------|
| `--robot.type` | 机器人类型 | `dofbot_se` |
| `--robot.port` | 串口地址 | `/dev/ttyUSB0` 或 `/dev/dofbot` |
| `--robot.cameras.{name}.type` | 摄像头类型 | `opencv`（USB 摄像头）或 `realsense`（深度摄像头） |
| `--robot.cameras.{name}.index_or_path` | 摄像头设备号或路径 | `0`, `1`, `2`... 或 `/dev/video0` |
| `--robot.cameras.{name}.width` | 图像宽度（像素） | `640`, `1280` |
| `--robot.cameras.{name}.height` | 图像高度（像素） | `480`, `720` |
| `--robot.cameras.{name}.fps` | 摄像头帧率 | `30`, `60` |
| `--dataset.repo_id` | 数据集标识符 | `your_username/dataset_name` |
| `--dataset.single_task` | 任务描述（简短清晰） | "抓取红色方块" |
| `--dataset.num_episodes` | 要采集的 episode 数量 | `50`, `100` |
| `--dataset.fps` | 数据采集频率 | `30`（推荐与摄像头 fps 一致） |
| `--dataset.episode_time_s` | 每个 episode 的最长时间（秒） | `60` |
| `--dataset.reset_time_s` | episode 间重置环境的时间（秒） | `60` |
| `--display_data` | 是否显示实时数据（调试用） | `true` 或 `false` |
| `--dataset.push_to_hub` | 是否上传到 Hugging Face Hub | `true` 或 `false` |

---

## 采集流程

### 步骤 1: 准备工作区

1. 清理工作台面
2. 放置好所需的物体（例如：方块、容器）
3. 固定顶部摄像头位置
4. 确保腕部摄像头安装牢固
5. 打开机械臂外部电源

### 步骤 2: 连接并测试

```bash
# 1. 激活环境
conda activate lerobot
source setup_dofbot_env.sh

# 2. 测试机械臂连接
python examples/dofbot_se_example.py /dev/ttyUSB0

# 3. 查找摄像头
lerobot-find-cameras

# 4. 测试完整系统（干运行，0 个 episode）
lerobot-record \
    --robot.type=dofbot_se \
    --robot.port=/dev/ttyUSB0 \
    --robot.cameras.wrist.type=opencv \
    --robot.cameras.wrist.index_or_path=0 \
    --robot.cameras.wrist.width=640 \
    --robot.cameras.wrist.height=480 \
    --robot.cameras.wrist.fps=30 \
    --robot.cameras.top.type=opencv \
    --robot.cameras.top.index_or_path=1 \
    --robot.cameras.top.width=640 \
    --robot.cameras.top.height=480 \
    --robot.cameras.top.fps=30 \
    --dataset.repo_id=test/dry_run \
    --dataset.single_task="测试" \
    --dataset.num_episodes=0 \
    --display_data=true
```

### 步骤 3: 正式采集

```bash
lerobot-record \
    --robot.type=dofbot_se \
    --robot.port=/dev/ttyUSB0 \
    --robot.cameras.wrist.type=opencv \
    --robot.cameras.wrist.index_or_path=0 \
    --robot.cameras.wrist.width=640 \
    --robot.cameras.wrist.height=480 \
    --robot.cameras.wrist.fps=30 \
    --robot.cameras.top.type=opencv \
    --robot.cameras.top.index_or_path=1 \
    --robot.cameras.top.width=640 \
    --robot.cameras.top.height=480 \
    --robot.cameras.top.fps=30 \
    --dataset.repo_id=your_username/pick_and_place \
    --dataset.single_task="拿起红色方块并放入蓝色盒子" \
    --dataset.num_episodes=50 \
    --dataset.episode_time_s=30 \
    --dataset.reset_time_s=10 \
    --dataset.fps=30 \
    --display_data=true \
    --dataset.push_to_hub=false
```

### 步骤 4: 录制 Episode

对于每个 episode：

1. **准备阶段**：
   - 程序会提示 "Recording episode X"
   - 此时机械臂舵机扭矩应该是关闭的（可以手动移动）

2. **演示阶段**：
   - 手动移动机械臂完成任务
   - 动作要**平滑**、**稳定**
   - 尽量保持**一致的速度**
   - 完成任务后保持最终姿态1-2秒

3. **重置阶段**：
   - Episode 录制完成后，程序会提示 "Reset the environment"
   - 将机械臂和物体恢复到初始状态
   - 准备下一个 episode

4. **控制按键**：
   - **空格键**：暂停/继续录制
   - **R 键**：重新录制当前 episode（如果出错）
   - **Q 键**：提前结束录制

### 步骤 5: 检查数据

采集完成后，数据会保存在 `~/.cache/huggingface/lerobot/` 目录下：

```bash
# 查看数据集
cd ~/.cache/huggingface/lerobot/your_username___dofbot_demo/

# 目录结构
# your_username___dofbot_demo/
# ├── data/
# │   ├── chunk-000/
# │   │   ├── episode_000000.parquet
# │   │   ├── ...
# │   └── ...
# ├── videos/
# │   ├── chunk-000/
# │   │   ├── observation.images.wrist_episode_000000.mp4
# │   │   ├── observation.images.top_episode_000000.mp4
# │   │   └── ...
# │   └── ...
# └── meta/
#     ├── info.json
#     └── stats.safetensors
```

---

## 常见问题

### Q1: 摄像头找不到或无法打开

**症状**：
```
Error: Failed to open camera 0
```

**解决方案**：
1. 检查摄像头是否连接：`ls /dev/video*`
2. 尝试其他摄像头索引（0, 1, 2...）
3. 使用 `lerobot-find-cameras` 查找可用摄像头
4. 在虚拟机中，确保 USB 设备已连接到虚拟机

### Q2: 采集帧率不稳定

**症状**：
```
WARNING: FPS dropped to 15 (target: 30)
```

**解决方案**：
1. 降低摄像头分辨率（例如：640x480 → 320x240）
2. 降低帧率（30 → 15）
3. 减少同时使用的摄像头数量
4. 关闭 `--display_data`（显示数据会占用 CPU）
5. 调整 `num_image_writer_threads_per_camera` 参数

### Q3: 机械臂无法手动移动

**症状**：
机械臂在录制过程中很难手动移动。

**原因**：
舵机扭矩可能没有正确关闭。

**解决方案**：
1. 检查 `config_dofbot_se.py` 中的 `disable_torque_on_disconnect`
2. 在录制开始前手动关闭扭矩（如果需要的话）

### Q4: 数据集名称格式错误

**症状**：
```
ValueError: repo_id must follow the format 'username/dataset_name'
```

**解决方案**：
确保 `--dataset.repo_id` 格式正确：
- ✅ 正确：`my_username/my_dataset`
- ❌ 错误：`my_dataset`
- ❌ 错误：`my_username-my_dataset`

### Q5: 如何选择合适的 episode 数量？

**建议**：
- **简单任务**（如拿起物体）：20-50 episodes
- **中等任务**（如拿起并放置）：50-100 episodes
- **复杂任务**（如组装）：100-200+ episodes

质量比数量更重要！确保每个 episode：
- 动作流畅
- 成功完成任务
- 初始状态一致

### Q6: 虚拟机中 USB 设备不稳定

参考我们之前创建的 `fix_usb.sh` 脚本：

```bash
bash fix_usb.sh
```

---

## 最佳实践

### 1. 任务设计

- ✅ 任务应该**明确**、**可重复**
- ✅ 物体位置应该有一定的**变化**（增加泛化能力）
- ✅ 避免过于复杂的多步骤任务
- ✅ 确保任务在摄像头视野内完成

### 2. 数据质量

- ✅ 动作要**平滑**（避免突然的抖动）
- ✅ 保持**一致的速度**
- ✅ 每个 episode 的**初始状态应相似**
- ✅ 失败的 episode 应该重新录制（按 R 键）

### 3. 采集效率

- ✅ 先用少量 episodes（5-10个）测试完整流程
- ✅ 确认数据质量后再大批量采集
- ✅ 定期检查数据集（每 10 个 episodes）
- ✅ 保存配置命令到脚本文件

### 4. 摄像头摆放

**腕部摄像头**：
- 安装在机械臂末端
- 视角应该朝向任务区域
- 捕捉"第一人称"视角

**顶部摄像头**：
- 固定在工作区正上方
- 高度适中（能看到整个工作区）
- 提供全局视角
- 避免阴影遮挡

---

## 下一步

采集完数据后，你可以：

1. **可视化数据集**：
   ```bash
   lerobot-visualize-dataset \
       --repo-id=your_username/your_dataset \
       --episode-index=0
   ```

2. **训练模型**：
   ```bash
   lerobot-train \
       --dataset.repo_id=your_username/your_dataset \
       --policy.type=act \
       --training.num_epochs=3000
   ```

3. **上传到 Hugging Face Hub**（可选）：
   ```bash
   # 在录制时添加 --dataset.push_to_hub=true
   # 或者事后上传：
   lerobot-push-dataset \
       --repo-id=your_username/your_dataset
   ```

---

## 联系与支持

如果遇到问题：
1. 查看 LeRobot 官方文档：https://huggingface.co/docs/lerobot
2. 查看本集成的 README：`/root/lerobot/README_DOFBOT.md`
3. 检查日志文件

祝你数据采集顺利！🚀

