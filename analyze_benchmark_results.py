#!/usr/bin/env python3
"""
Benchmark Results Analysis Script

This script analyzes benchmark output files from the OMICS protein comparison project,
extracts timing information, and creates line plots comparing performance across
different CPU core configurations.

Usage: python analyze_benchmark_results.py [directory_path]
"""

import os
import re
import sys
import glob
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def extract_benchmark_data(file_path):
    """
    Extract benchmark data from a single output file.
    
    Args:
        file_path (str): Path to the benchmark output file
        
    Returns:
        dict: Dictionary containing extracted data or None if parsing fails
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract method and core count from filename
        filename = os.path.basename(file_path)
        # Pattern: method_benchmark_Xcores.out
        match = re.match(r'(\w+)_benchmark_(\d+)cores\.out', filename)
        if not match:
            print(f"Warning: Could not parse filename format: {filename}")
            return None
            
        method = match.group(1)
        cores = int(match.group(2))
        
        # Extract timing information (real, user, sys)
        real_match = re.search(r'real\s+(\d+)m([\d.]+)s', content)
        user_match = re.search(r'user\s+(\d+)m([\d.]+)s', content)
        sys_match = re.search(r'sys\s+(\d+)m([\d.]+)s', content)
        
        if not all([real_match, user_match, sys_match]):
            print(f"Warning: Could not extract timing data from {filename}")
            return None
        
        # Convert time to seconds
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
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def analyze_benchmark_directory(directory_path):
    """
    Analyze all benchmark files in a directory.
    
    Args:
        directory_path (str): Path to directory containing benchmark files
        
    Returns:
        pd.DataFrame: DataFrame with benchmark results
    """
    if not os.path.exists(directory_path):
        print(f"Error: Directory {directory_path} does not exist")
        return None
    
    # Find all benchmark output files
    pattern = os.path.join(directory_path, "*_benchmark_*cores.out")
    files = glob.glob(pattern)
    
    if not files:
        print(f"No benchmark files found in {directory_path}")
        print(f"Looking for pattern: *_benchmark_*cores.out")
        return None
    
    print(f"Found {len(files)} benchmark files:")
    for f in sorted(files):
        print(f"  - {os.path.basename(f)}")
    
    # Extract data from all files
    results = []
    for file_path in files:
        data = extract_benchmark_data(file_path)
        if data:
            results.append(data)
    
    if not results:
        print("No valid benchmark data could be extracted")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values(['method', 'cores'])
    
    print(f"\nExtracted data from {len(results)} files:")
    print(df[['method', 'cores', 'real_time', 'user_time', 'sys_time']])
    
    return df

def create_performance_plots(df, output_dir=None):
    """
    Create line plots showing performance comparison.
    
    Args:
        df (pd.DataFrame): DataFrame with benchmark results
        output_dir (str): Directory to save plots (optional)
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Set up the plot style
    plt.style.use('default')
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('OMICS Protein Comparison - Performance Analysis', fontsize=16, fontweight='bold')
    
    time_types = [
        ('real_time', 'Real Time (Wall Clock)', 'Real time represents the actual elapsed time'),
        ('user_time', 'User Time (CPU)', 'User time represents CPU time spent in user mode'),
        ('sys_time', 'System Time (Kernel)', 'System time represents CPU time spent in kernel mode')
    ]
    
    colors = {'jaccard': '#2E86C1', 'minhash': '#E74C3C'}
    markers = {'jaccard': 'o', 'minhash': 's'}
    
    for idx, (time_col, title, description) in enumerate(time_types):
        ax = axes[idx]
        
        # Plot data for each method
        for method in df['method'].unique():
            method_data = df[df['method'] == method].sort_values('cores')
            
            ax.plot(method_data['cores'], method_data[time_col], 
                   color=colors.get(method, '#333333'),
                   marker=markers.get(method, 'o'),
                   linewidth=2.5,
                   markersize=8,
                   label=method.capitalize(),
                   markerfacecolor='white',
                   markeredgewidth=2)
            
            # Add value annotations
            for _, row in method_data.iterrows():
                ax.annotate(f'{row[time_col]:.1f}s', 
                           (row['cores'], row[time_col]),
                           textcoords="offset points", 
                           xytext=(0,10), 
                           ha='center',
                           fontsize=9,
                           alpha=0.8)
        
        # Customize the subplot
        ax.set_xlabel('CPU Cores', fontweight='bold')
        ax.set_ylabel('Time (seconds)', fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend(frameon=True, shadow=True)
        
        # Set x-axis to show only integer core counts
        core_values = sorted(df['cores'].unique())
        ax.set_xticks(core_values)
        ax.set_xticklabels(core_values)
        
        # Add description as subtitle
        ax.text(0.5, -0.15, description, transform=ax.transAxes, 
                ha='center', fontsize=10, style='italic', alpha=0.7)
    
    plt.tight_layout()
    
    # Save plot if output directory specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        plot_path = os.path.join(output_dir, 'benchmark_performance_analysis.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"\nPlot saved to: {plot_path}")
    
    plt.show()

def create_summary_table(df):
    """
    Create a summary table of the benchmark results.
    
    Args:
        df (pd.DataFrame): DataFrame with benchmark results
    """
    if df is None or df.empty:
        return
    
    print("\n" + "="*80)
    print("BENCHMARK RESULTS SUMMARY")
    print("="*80)
    
    # Summary statistics
    for method in df['method'].unique():
        method_data = df[df['method'] == method]
        print(f"\n{method.upper()} METHOD:")
        print("-" * 40)
        
        for _, row in method_data.sort_values('cores').iterrows():
            efficiency = (row['user_time'] + row['sys_time']) / row['real_time'] * 100
            print(f"  {row['cores']:2d} cores: Real={row['real_time']:6.1f}s  "
                  f"User={row['user_time']:6.1f}s  Sys={row['sys_time']:5.1f}s  "
                  f"CPU Efficiency={efficiency:5.1f}%")
    
    # Performance comparison
    print(f"\nPERFORMACE COMPARISON (Real Time):")
    print("-" * 40)
    
    pivot_df = df.pivot(index='cores', columns='method', values='real_time')
    print(pivot_df.to_string(float_format='%.1f'))
    
    # Calculate speedup
    if len(df['method'].unique()) == 2:
        methods = list(df['method'].unique())
        print(f"\nSPEEDUP ANALYSIS:")
        print("-" * 40)
        
        for cores in sorted(df['cores'].unique()):
            core_data = df[df['cores'] == cores]
            if len(core_data) == 2:
                times = {row['method']: row['real_time'] for _, row in core_data.iterrows()}
                if methods[0] in times and methods[1] in times:
                    ratio = times[methods[0]] / times[methods[1]]
                    faster_method = methods[0] if ratio < 1 else methods[1]
                    speedup = max(ratio, 1/ratio)
                    print(f"  {cores:2d} cores: {faster_method.capitalize()} is {speedup:.2f}x faster")

def main():
    """Main function to run the benchmark analysis."""
    # Get directory path from command line argument or use current directory
    if len(sys.argv) > 1:
        directory_path = sys.argv[1]
    else:
        # Try to find benchmark results directory automatically
        possible_dirs = [
            'output/benchmark_results',
            '.',
            'benchmark_results'
        ]
        
        directory_path = None
        for dir_path in possible_dirs:
            if os.path.exists(dir_path):
                # Check if it contains benchmark files
                pattern = os.path.join(dir_path, "*_benchmark_*cores.out")
                if glob.glob(pattern):
                    directory_path = dir_path
                    break
                # Check subdirectories for timestamp-based directories
                subdirs = [d for d in os.listdir(dir_path) 
                          if os.path.isdir(os.path.join(dir_path, d)) and 
                          re.match(r'\d{8}_\d{6}', d)]
                if subdirs:
                    # Use the latest timestamp directory
                    latest_dir = os.path.join(dir_path, sorted(subdirs)[-1])
                    pattern = os.path.join(latest_dir, "*_benchmark_*cores.out")
                    if glob.glob(pattern):
                        directory_path = latest_dir
                        break
        
        if directory_path is None:
            print("Error: No benchmark files found.")
            print("Usage: python analyze_benchmark_results.py [directory_path]")
            print("\nLooking for files matching pattern: *_benchmark_*cores.out")
            sys.exit(1)
    
    print(f"Analyzing benchmark results in: {directory_path}")
    print("="*60)
    
    # Analyze the benchmark files
    df = analyze_benchmark_directory(directory_path)
    
    if df is not None:
        # Create summary table
        create_summary_table(df)
        
        # Create performance plots
        output_dir = os.path.join(os.path.dirname(directory_path) or '.', 'plots')
        create_performance_plots(df, output_dir)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()