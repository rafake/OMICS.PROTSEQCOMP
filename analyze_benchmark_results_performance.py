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

def main():
    if len(sys.argv) < 3:
        print("Usage: python analyze_benchmark_results_performance.py <log_file_path> <benchmark_results_dir>")
        sys.exit(1)
    log_file = sys.argv[1]
    benchmark_dir = sys.argv[2]
    print(f"Analyzing benchmark results in: {benchmark_dir}")
    print(f"Using log file: {log_file}")
    partitions = extract_partitions_from_log(log_file)
    df = analyze_benchmark_directory(benchmark_dir)
    if df is not None and partitions:
        create_performance_partitions_plot(df, partitions, os.path.join(benchmark_dir, 'plots'))
    else:
        print("No valid data for plotting.")

if __name__ == "__main__":
    main()
