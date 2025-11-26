#!/bin/bash
# Dofbot SE 数据采集 - 交替读取优化方案
# 
# 核心优化：
# 1. 50ms 静默期：每次读取前暂停，让手柄完成命令
# 2. 低频采集：5Hz 降低串口压力
# 3. 快速超时：读取失败快速返回，不阻塞
# 4. 缓存机制：失败时使用上次成功的值

cd /root/lerobot

conda activate lerobot && lerobot-record \
  --robot.type=dofbot_se \
  --robot.port=/dev/ttyUSB0 \
  --robot.cameras="{wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, top: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
  --teleop.type=dofbot_kinesthetic \
  --teleop.disable_torque=false \
  --dataset.repo_id=april5129/dofbot_alternation \
  --dataset.single_task="place the red block into the plate" \
  --dataset.num_episodes=3 \
  --dataset.fps=5 \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=10 \
  --display_data=false \
  --play_sounds=false \
  --dataset.push_to_hub=false

echo ""
echo "=========================================="
echo "采集完成！现在分析数据质量..."
echo "=========================================="

# 自动分析数据质量
python3 << 'EOF'
from lerobot.datasets.lerobot_dataset import LeRobotDataset
import numpy as np

dataset = LeRobotDataset('/root/.cache/huggingface/lerobot/april5129/dofbot_alternation')

print("\n" + "=" * 60)
print("📊 交替方案数据质量分析")
print("=" * 60)

for ep_idx in range(min(3, dataset.num_episodes)):
    episode_data = dataset.hf_dataset.filter(lambda x: x['episode_index'] == ep_idx)
    
    print(f"\nEpisode {ep_idx}:")
    print(f"  总帧数: {len(episode_data)}")
    
    # 计算唯一率
    unique_rates = []
    for joint_idx in range(6):
        positions = np.array([frame['observation.state'][joint_idx] for frame in episode_data])
        unique_rate = (len(np.unique(positions)) / len(positions)) * 100
        unique_rates.append(unique_rate)
    
    avg_rate = np.mean(unique_rates)
    
    if avg_rate >= 70:
        status = "✅ 优秀"
    elif avg_rate >= 50:
        status = "✅ 良好"
    elif avg_rate >= 30:
        status = "⚠️ 一般"
    else:
        status = "❌ 差"
    
    print(f"  平均数据唯一率: {avg_rate:.1f}% {status}")

print("\n" + "=" * 60)
EOF

