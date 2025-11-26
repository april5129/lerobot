#!/usr/bin/env python3
"""
简单的 PARQUET 文件查看工具
用于分析 lerobot 数据集文件



数据列说明：
action - 机器人动作数据（6维浮点数组）
observation.state - 机器人观测状态（6维浮点数组）
timestamp - 时间戳（浮点数）
frame_index - 帧索引（0-71）
episode_index - 回合索引（包含 3 个回合：0, 1, 2）
index - 全局索引（0-215）
task_index - 任务索引（全部为 0）
"""

import pandas as pd
import pyarrow.parquet as pq

# 硬编码文件路径
PARQUET_FILE = "/root/.cache/huggingface/lerobot/april5129/dofbot_demo/data/chunk-000/file-000.parquet"


def analyze_parquet_file(file_path):
    """分析 PARQUET 文件的基本信息"""
    
    print("=" * 80)
    print(f"分析 PARQUET 文件: {file_path}")
    print("=" * 80)
    
    # 使用 PyArrow 读取元数据
    print("\n【文件元数据信息】")
    parquet_file = pq.read_table(file_path)
    print(f"总行数: {parquet_file.num_rows}")
    print(f"总列数: {parquet_file.num_columns}")
    print(f"文件大小: {parquet_file.nbytes / 1024:.2f} KB")
    
    # 显示列信息
    print("\n【列信息】")
    print(f"列名列表: {parquet_file.column_names}")
    print("\n列的数据类型:")
    for i, field in enumerate(parquet_file.schema):
        print(f"  {i+1}. {field.name}: {field.type}")
    
    # 使用 Pandas 读取数据进行详细分析
    print("\n【使用 Pandas 读取数据】")
    df = pd.read_parquet(file_path)
    
    # 显示数据框基本信息
    print(f"\nDataFrame shape: {df.shape}")
    print(f"\nDataFrame 列:")
    print(df.columns.tolist())
    
    # 显示数据类型
    print("\n数据类型详情:")
    print(df.dtypes)
    
    # 显示统计信息
    print("\n【数值列统计信息】")
    print(df.describe())
    
    # 显示前几行数据
    print("\n【前 5 行数据】")
    print(df.head())
    
    # 显示后几行数据
    print("\n【后 5 行数据】")
    print(df.tail())
    
    # 检查是否有缺失值
    print("\n【缺失值检查】")
    missing_values = df.isnull().sum()
    if missing_values.sum() == 0:
        print("没有缺失值")
    else:
        print(missing_values[missing_values > 0])
    
    # 显示每列的唯一值数量（对于小数据集，跳过数组列）
    print("\n【每列唯一值数量】")
    for col in df.columns:
        try:
            unique_count = df[col].nunique()
            print(f"  {col}: {unique_count}")
        except TypeError:
            # 跳过包含数组的列
            print(f"  {col}: (数组列，跳过)")
    
    # 如果有特定的列，显示其范围
    print("\n【数值列的取值范围】")
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        print(f"  {col}: [{df[col].min():.4f}, {df[col].max():.4f}]")
    
    print("\n" + "=" * 80)
    print("分析完成！")
    print("=" * 80)
    
    return df


def main():
    """主函数"""
    try:
        df = analyze_parquet_file(PARQUET_FILE)
        
        # 可以在这里添加更多自定义分析
        print("\n\n【额外分析】")
        
        # 如果有时间戳列，显示时间范围
        if 'timestamp' in df.columns:
            print(f"\n时间戳范围:")
            print(f"  开始: {df['timestamp'].min()}")
            print(f"  结束: {df['timestamp'].max()}")
            print(f"  时长: {df['timestamp'].max() - df['timestamp'].min():.4f} 秒")
        
        # 如果有索引列，显示索引范围
        if 'index' in df.columns:
            print(f"\n索引范围: {df['index'].min()} 到 {df['index'].max()}")
        
        print("\n如需查看完整数据，可以使用:")
        print(f"  df = pd.read_parquet('{PARQUET_FILE}')")
        
    except FileNotFoundError:
        print(f"错误: 文件不存在 - {PARQUET_FILE}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

