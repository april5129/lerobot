#!/bin/bash
# 将 PYTHONPATH 添加到 conda 环境中

CONDA_ENV_PATH="$HOME/miniforge3/envs/lerobot"

# 创建激活脚本目录
mkdir -p "$CONDA_ENV_PATH/etc/conda/activate.d"
mkdir -p "$CONDA_ENV_PATH/etc/conda/deactivate.d"

# 创建激活脚本
cat > "$CONDA_ENV_PATH/etc/conda/activate.d/env_vars.sh" << 'EOF'
#!/bin/sh
export PYTHONPATH="/root/lerobot/src:$PYTHONPATH"
echo "✓ PYTHONPATH 已设置: /root/lerobot/src"
EOF

# 创建停用脚本
cat > "$CONDA_ENV_PATH/etc/conda/deactivate.d/env_vars.sh" << 'EOF'
#!/bin/sh
unset PYTHONPATH
EOF

chmod +x "$CONDA_ENV_PATH/etc/conda/activate.d/env_vars.sh"
chmod +x "$CONDA_ENV_PATH/etc/conda/deactivate.d/env_vars.sh"

echo "✓ PYTHONPATH 已永久添加到 lerobot conda 环境"
echo "  重新激活环境生效: conda deactivate && conda activate lerobot"

