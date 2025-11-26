#!/bin/bash
# Dofbot SE 环境设置脚本

echo "======================================================"
echo "Dofbot SE for LeRobot - 环境设置"
echo "======================================================"
echo ""

# 激活 conda 环境
echo "激活 lerobot conda 环境..."
source ~/miniforge3/etc/profile.d/conda.sh
conda activate lerobot

# 设置 PYTHONPATH
echo "设置 PYTHONPATH..."
export PYTHONPATH=/root/lerobot/src:$PYTHONPATH

# 检查串口设备
echo ""
echo "检查串口设备..."
if ls /dev/ttyUSB* 1> /dev/null 2>&1; then
    echo "✓ 找到串口设备:"
    ls -l /dev/ttyUSB*
else
    echo "⚠ 未找到 /dev/ttyUSB* 设备"
    echo "  请检查 Dofbot SE 是否已连接"
fi

# 检查串口权限
if [ -e "/dev/ttyUSB0" ]; then
    if [ -r "/dev/ttyUSB0" ] && [ -w "/dev/ttyUSB0" ]; then
        echo "✓ 串口权限正常"
    else
        echo "⚠ 串口权限不足，运行以下命令授权:"
        echo "  sudo chmod 666 /dev/ttyUSB0"
    fi
fi

echo ""
echo "======================================================"
echo "环境设置完成！"
echo "======================================================"
echo ""
echo "快速命令:"
echo "  1. 运行验证: python verify_dofbot_se.py"
echo "  2. 运行示例: python examples/dofbot_se_example.py"
echo "  3. 查看文档: cat DOFBOT_SE_INTEGRATION.md"
echo ""
echo "使用方法:"
echo "  source setup_dofbot_env.sh"
echo ""

