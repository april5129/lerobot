#!/bin/bash
# 修复虚拟机 USB 串口断开问题

echo "======================================================"
echo "修复 Dofbot SE USB 连接问题"
echo "======================================================"
echo ""

# 禁用 USB 自动挂起
echo "禁用 USB 自动挂起..."
echo -1 | sudo tee /sys/module/usbcore/parameters/autosuspend > /dev/null
echo "   ✓ 完成"
echo ""

# 重新加载 udev
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "   ✓ 完成"
echo ""

# 等待设备出现
echo ""
echo "等待设备出现..."
for i in {1..10}; do
    if [ -e "/dev/ttyUSB0" ] || [ -e "/dev/dofbot" ]; then
        echo "   ✓ 设备已连接！"
        if [ -e "/dev/ttyUSB0" ]; then
            echo "   设备: /dev/ttyUSB0"
            ls -l /dev/ttyUSB0
        fi
        if [ -e "/dev/dofbot" ]; then
            echo "   设备: /dev/dofbot (符号链接)"
            ls -l /dev/dofbot
        fi
        break
    fi
    echo "   等待... ($i/10)"
    sleep 1
done

if [ ! -e "/dev/ttyUSB0" ] && [ ! -e "/dev/dofbot" ]; then
    echo "   ⚠ 设备未出现，请检查:"
    echo "   1. USB 是否在虚拟机菜单中连接"
    echo "   2. Dofbot SE 电源是否打开"
    echo "   3. USB 线缆是否正常"
    exit 1
fi

echo ""
echo "======================================================"
echo "修复完成！"
echo "======================================================"
echo ""
echo "现在可以使用以下命令:"
echo ""
if [ -e "/dev/dofbot" ]; then
    echo "  python examples/find_dofbot_port.py"
    echo "  python examples/dofbot_se_example.py /dev/dofbot"
elif [ -e "/dev/ttyUSB0" ]; then
    echo "  python examples/find_dofbot_port.py"
    echo "  python examples/dofbot_se_example.py /dev/ttyUSB0"
fi
echo ""

