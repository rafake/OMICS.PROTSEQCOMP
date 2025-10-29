#!/usr/bin/env python3
"""
Benchmark Partitions Results Analysis Script

This script analyzes benchmark output files and a batch log file to extract timing and Spark partition information,
and creates line plots comparing performance and partitioning across different CPU core configurations.

Usage: python analyze_benchmark_results_performance.py <log_file_path> <benchmark_results_dir>
"""
import os
import re
import sys
import glob
import matplotlib.pyplot as plt
import pandas as pd

def extract_partitions_from_log(log_path):
    """Extracts core count and partitions from the batch log file."""
    partitions = {}
    current_cores = None
    with open(log_path, 'r') as f:
        for line in f:
            m = re.match(r"Spark configuration for (\d+) cores:", line)
            if m:
                current_cores = int(m.group(1))
            pm = re.match(r"\s*Partitions: (\d+)", line)
            if pm and current_cores is not None:
                partitions[current_cores] = int(pm.group(1))
    return partitions

def extract_benchmark_data(file_path):
    """Extract benchmark data from a single output file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        filename = os.path.basename(file_path)
        match = re.match(r'(\w+)_benchmark_(\d+)cores\.out', filename)
        if not match:
            return None
        method = match.group(1)
        cores = int(match.group(2))
        real_match = re.search(r'real\s+(\d+)m([\d.]+)s', content)
        user_match = re.search(r'user\s+(\d+)m([\d.]+)s', content)
        sys_match = re.search(r'sys\s+(\d+)m([\d.]+)s', content)
        if not all([real_match, user_match, sys_match]):
            return None
        real_time = int(real_match.group(1)) * 60 + float(real_match.group(2))
        user_time = int(user_match.group(1)) * 60 + float(user_match.group(2))
        sys_time = int(sys_match.group(1)) * 60 + float(sys_match.group(2))
        return {
            'method': method,
            'cores': cores,
            'real_time': real_time,
            'user_time': user_time,
            'sys_time': sys_time,
            'filename': filename
        }
    except Exception:
        return None

def analyze_benchmark_directory(directory_path):
    """Analyze all benchmark files in a directory."""
    pattern = os.path.join(directory_path, "*_benchmark_*cores.out")
    files = glob.glob(pattern)
    results = []
    for file_path in files:
        data = extract_benchmark_data(file_path)
        if data:
            results.append(data)
    if not results:
        return None
    df = pd.DataFrame(results)
    df = df.sort_values(['method', 'cores'])
    return df

def extract_spark_config_from_log(log_path):
    """Extracts core count and Spark config (partitions, driver/executor memory, max result size) from the batch log file."""
    config = {}
    current_cores = None
    with open(log_path, 'r') as f:
        for line in f:
            m = re.match(r"Spark configuration for (\d+) cores:", line)
            if m:
                current_cores = int(m.group(1))
                config[current_cores] = {}
            if current_cores is not None:
                pm = re.match(r"\s*Partitions: (\d+)", line)
                if pm:
                    config[current_cores]['partitions'] = int(pm.group(1))
                dm = re.match(r"\s*Driver memory: (\d+)m", line)
                if dm:
                    config[current_cores]['driver_memory'] = int(dm.group(1))
                em = re.match(r"\s*Executor memory: (\d+)m", line)
                if em:
                    config[current_cores]['executor_memory'] = int(em.group(1))
                mm = re.match(r"\s*Max result size: (\d+)m", line)
                if mm:
                    config[current_cores]['max_result_size'] = int(mm.group(1))
    return config

def create_performance_partitions_plot(df, partitions, output_dir=None):
    """Create line plots showing performance and partitions comparison."""
    if df is None or df.empty:
        print("No data to plot")
        return
    plt.style.use('default')
    fig, ax1 = plt.subplots(figsize=(10, 6))
    color_map = {'jaccard': '#2E86C1', 'minhash': '#E74C3C'}
    marker_map = {'jaccard': 'o', 'minhash': 's'}
    # Plot real_time for each method
    for method in df['method'].unique():
        method_data = df[df['method'] == method].sort_values('cores')
        ax1.plot(method_data['cores'], method_data['real_time'],
                 color=color_map.get(method, '#333333'),
                 marker=marker_map.get(method, 'o'),
                 linewidth=2.5, markersize=8, label=f"{method.capitalize()} (time)",
                 markerfacecolor='white', markeredgewidth=2)
        for _, row in method_data.iterrows():
            ax1.annotate(f'{row["real_time"]:.1f}s', (row['cores'], row['real_time']),
                         textcoords="offset points", xytext=(0,10), ha='center', fontsize=9, alpha=0.8)
    ax1.set_xlabel('CPU Cores', fontweight='bold')
    ax1.set_ylabel('Real Time (seconds)', fontweight='bold', color='black')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    # Plot partitions on secondary y-axis
    ax2 = ax1.twinx()
    core_vals = sorted(partitions.keys())
    part_vals = [partitions[c] for c in core_vals]
    ax2.plot(core_vals, part_vals, color='#27AE60', marker='^', linestyle='--', linewidth=2, markersize=8, label='Spark Partitions')
    for x, y in zip(core_vals, part_vals):
        ax2.annotate(f'{y}', (x, y), textcoords="offset points", xytext=(0,-15), ha='center', fontsize=9, color='#27AE60', alpha=0.8)
    ax2.set_ylabel('Spark Partitions', fontweight='bold', color='#27AE60')
    ax2.legend(loc='upper right')
    plt.title('OMICS Protein Comparison - Performance & Spark Partitions', fontsize=15, fontweight='bold')
    plt.tight_layout()
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        plot_path = os.path.join(output_dir, 'benchmark_partitions_analysis.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"\nPlot saved to: {plot_path}")
    plt.show()

def plot_spark_config(config, output_dir=None):
    """Plot Spark configuration parameters (partitions, driver memory, executor memory, max result size) against core counts."""
    if not config:
        print("No Spark config data to plot")
        return
    cores = sorted(config.keys())
    partitions = [config[c].get('partitions', None) for c in cores]
    driver_mem = [config[c].get('driver_memory', None) for c in cores]
    executor_mem = [config[c].get('executor_memory', None) for c in cores]
    max_result = [config[c].get('max_result_size', None) for c in cores]

    fig, axs = plt.subplots(4, 1, figsize=(8, 12), sharex=True)
    axs[0].plot(cores, partitions, marker='o')
    axs[0].set_ylabel('Partitions')
    axs[0].set_title('Spark Partitions vs Cores')
    axs[0].grid(True)

    axs[1].plot(cores, driver_mem, marker='o', color='g')
    axs[1].set_ylabel('Driver Memory (MB)')
    axs[1].set_title('Driver Memory vs Cores')
    axs[1].grid(True)

    axs[2].plot(cores, executor_mem, marker='o', color='r')
    axs[2].set_ylabel('Executor Memory (MB)')
    axs[2].set_title('Executor Memory vs Cores')
    axs[2].grid(True)

    axs[3].plot(cores, max_result, marker='o', color='m')
    axs[3].set_ylabel('Max Result Size (MB)')
    axs[3].set_xlabel('Cores')
    axs[3].set_title('Max Result Size vs Cores')
    axs[3].grid(True)

    plt.tight_layout()
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        plot_path = os.path.join(output_dir, 'benchmark_spark_config.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"\nSpark config plots saved to: {plot_path}")
    plt.close()

import traceback

def debug_list_dir(path, label=None):
    try:
        print(f"\nDirectory listing for {label or path}:")
        for f in os.listdir(path):
            print(f"  {f}")
    except Exception as e:
        print(f"Could not list directory {path}: {e}")

def main():
    try:
        if len(sys.argv) < 3:
            print("Usage: python analyze_benchmark_results_performance.py <log_file_path> <benchmark_results_dir>")
            sys.exit(1)
        log_file = sys.argv[1]
        benchmark_dir = sys.argv[2]
        print(f"Analyzing benchmark results in: {benchmark_dir}")
        print(f"Using log file: {log_file}")
        print(f"Python version: {sys.version}")
        print(f"Current working directory: {os.getcwd()}")
        debug_list_dir('.', label='current directory')
        debug_list_dir(benchmark_dir, label='benchmark_dir')
        config = extract_spark_config_from_log(log_file)
        df = analyze_benchmark_directory(benchmark_dir)
        plots_dir = os.path.join(benchmark_dir, 'plots')
        if df is not None:
            print(f"DataFrame shape: {df.shape}")
            print(df.head())
            create_performance_partitions_plot(df, config if config else {}, plots_dir)
        else:
            print("No benchmark data found for plotting.")
        if config:
            print(f"Spark config extracted for cores: {list(config.keys())}")
            plot_spark_config(config, plots_dir)
        else:
            print("No Spark config data found for plotting.")
        if (df is None) and (not config):
            print("No valid data for plotting.")
        debug_list_dir(plots_dir, label='plots_dir')
    except Exception as e:
        print("\n--- Exception occurred in analysis script ---")
        print(f"Error: {e}")
        traceback.print_exc()
        print("--- End exception ---\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
