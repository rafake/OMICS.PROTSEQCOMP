import builtins

# --- Logging setup ---
class TeeLogger:
    def __init__(self, log_path):
        self.log_path = log_path
        self.log_file = open(log_path, 'w', encoding='utf-8')
        self._orig_print = builtins.print

    def print(self, *args, **kwargs):
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        msg = sep.join(str(a) for a in args) + end
        self.log_file.write(msg)
        self.log_file.flush()
        self._orig_print(*args, **kwargs)

    def close(self):
        self.log_file.close()

# Will be set in main()
tee_logger = None

def tee_print(*args, **kwargs):
    if tee_logger is not None:
        tee_logger.print(*args, **kwargs)
    else:
        print(*args, **kwargs)
#!/usr/bin/env python3
"""
Benchmark Results Analysis Script

This script analyzes benchmark output files from the OMICS protein comparison project,
extracts timing information, and creates line plots comparing performance across
different CPU core configurations.

Usage: python analyze_benchmark_results.py [input_dir] [output_dir]

Arguments:
    input_dir   (optional) Directory containing benchmark files. If omitted, auto-detect.
    output_dir  (optional) Directory to save plots and summary. If omitted, defaults to <input_dir>/plots or auto-detected/plots.
"""

import os
import re
import sys
import glob
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import re
import openpyxl
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
            tee_print(f"Warning: Could not parse filename format: {filename}")
            return None

        method = match.group(1)
        cores = int(match.group(2))

        # Extract timing information (real, user, sys)
        real_match = re.search(r'real\s+(\d+)m([\d.]+)s', content)
        user_match = re.search(r'user\s+(\d+)m([\d.]+)s', content)
        sys_match = re.search(r'sys\s+(\d+)m([\d.]+)s', content)

        if not all([real_match, user_match, sys_match]):
            tee_print(f"Warning: Could not extract timing data from {filename}")
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
        tee_print(f"Error processing {file_path}: {e}")
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
        tee_print(f"Error: Directory {directory_path} does not exist")
        return None

    # Find all benchmark output files
    pattern = os.path.join(directory_path, "*_benchmark_*cores.out")
    files = glob.glob(pattern)

    if not files:
        tee_print(f"No benchmark files found in {directory_path}")
        tee_print(f"Looking for pattern: *_benchmark_*cores.out")
        return None

    tee_print(f"Found {len(files)} benchmark files:")
    for f in sorted(files):
        tee_print(f"  - {os.path.basename(f)}")

    # Extract data from all files
    results = []
    for file_path in files:
        data = extract_benchmark_data(file_path)
        if data:
            results.append(data)

    if not results:
        tee_print("No valid benchmark data could be extracted")
        return None

    # Create DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values(['method', 'cores'])

    tee_print(f"\nExtracted data from {len(results)} files:")
    tee_print(df[['method', 'cores', 'real_time', 'user_time', 'sys_time']])

    return df

def create_performance_plots(df, output_dir=None):
    """
    Create line plots showing performance comparison.
    
    Args:
        df (pd.DataFrame): DataFrame with benchmark results
        output_dir (str): Directory to save plots (optional)
    """
    if df is None or df.empty:
        tee_print("No data to plot")
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
    tee_print(f"\nPlot saved to: {plot_path}")
    
    plt.show()

def create_summary_table(df, output_dir=None):
    """
    Create a summary table of the benchmark results.
    
    Args:
        df (pd.DataFrame): DataFrame with benchmark results
    """
    if df is None or df.empty:
        return

    tee_print("\n" + "="*80)
    tee_print("BENCHMARK RESULTS SUMMARY")
    tee_print("="*80)

    # Prepare summary statistics for Excel
    summary_rows = []
    for method in df['method'].unique():
        method_data = df[df['method'] == method]
        for _, row in method_data.sort_values('cores').iterrows():
            efficiency = (row['user_time'] + row['sys_time']) / row['real_time'] * 100
            summary_rows.append({
                'Metoda': method.upper(),
                'Rdzenie CPU': row['cores'],
                'Czas rzeczywisty (s)': row['real_time'],
                'Czas użytkownika (s)': row['user_time'],
                'Czas systemowy (s)': row['sys_time'],
                'Wydajność CPU (%)': efficiency
            })
            tee_print(f"  {row['cores']:2d} cores: Real={row['real_time']:6.1f}s  "
                      f"User={row['user_time']:6.1f}s  Sys={row['sys_time']:5.1f}s  "
                      f"CPU Efficiency={efficiency:5.1f}%")

    # Performance comparison
    tee_print(f"\nPORÓWNANIE WYDAJNOŚCI (Czas rzeczywisty):")
    tee_print("-" * 40)

    pivot_df = df.pivot(index='cores', columns='method', values='real_time')
    # Polish headers for pivot table
    pivot_df.index.name = 'Rdzenie CPU'
    pivot_df.columns = [m.capitalize() for m in pivot_df.columns]
    tee_print(pivot_df.to_string(float_format='%.1f'))

    # Calculate speedup
    speedup_rows = []
    if len(df['method'].unique()) == 2:
        methods = list(df['method'].unique())
        tee_print(f"\nANALIZA PRZYSPIESZENIA:")
        tee_print("-" * 40)

        for cores in sorted(df['cores'].unique()):
            core_data = df[df['cores'] == cores]
            if len(core_data) == 2:
                times = {row['method']: row['real_time'] for _, row in core_data.iterrows()}
                if methods[0] in times and methods[1] in times:
                    ratio = times[methods[0]] / times[methods[1]]
                    faster_method = methods[0] if ratio < 1 else methods[1]
                    speedup = max(ratio, 1/ratio)
                    tee_print(f"  {cores:2d} cores: {faster_method.capitalize()} is {speedup:.2f}x faster")
                    speedup_rows.append({
                        'Rdzenie CPU': cores,
                        'Szybsza metoda': faster_method.capitalize(),
                        'Przyspieszenie': f"{speedup:.2f}x"
                    })

    # Write to Excel in output_dir
    try:
        excel_path = os.path.join(output_dir if output_dir else '.', 'benchmark_results_summary.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name='Podsumowanie', index=False)
            pivot_df.to_excel(writer, sheet_name='Porównanie', index=True)
            if speedup_rows:
                pd.DataFrame(speedup_rows).to_excel(writer, sheet_name='Przyspieszenie', index=False)
        tee_print(f"\nZapisano podsumowanie do pliku: {excel_path}")
    except Exception as e:
        tee_print(f"Błąd podczas zapisu do Excela: {e}")

def main():
    def parse_multi_benchmark_files(input_dir):
        """
        Parse OMICS-multi-benchmark-p-* files for Spark config and run info (format: Benchmarking: ... + Spark configuration for X cores: ...)
        Returns: DataFrame with columns: method, cores, partitions, driver_memory, executor_memory, max_result_size
        """
        pattern = os.path.join(input_dir, 'OMICS-multi-benchmark-p-*')
        files = glob.glob(pattern)
        rows = []
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Split by Spark config blocks
            spark_blocks = re.split(r'={10,}', content)
            # Track the most recent method seen before each block
            method = None
            for block in spark_blocks:
                # Update method if a new 'Benchmarking:' line is found
                method_match = re.search(r'Benchmarking:\s*(\w+)', block, re.IGNORECASE)
                if method_match:
                    method = method_match.group(1).lower()
                # Look for 'Spark configuration for X cores:'
                config_match = re.search(r'Spark configuration for (\d+) cores:', block)
                if config_match and method:
                    cores = int(config_match.group(1))
                    part_match = re.search(r'Partitions:\s*(\d+)', block)
                    partitions = int(part_match.group(1)) if part_match else None
                    driver_match = re.search(r'Driver memory:\s*([\w\.]+)', block)
                    driver_memory = driver_match.group(1) if driver_match else None
                    exec_match = re.search(r'Executor memory:\s*([\w\.]+)', block)
                    executor_memory = exec_match.group(1) if exec_match else None
                    maxres_match = re.search(r'Max result size:\s*([\w\.]+)', block)
                    max_result_size = maxres_match.group(1) if maxres_match else None
                    rows.append({
                        'Metoda': method,
                        'Rdzenie CPU': cores,
                        'Partycje': partitions,
                        'Pamięć drivera': driver_memory,
                        'Pamięć executora': executor_memory,
                        'Max rozmiar wyniku': max_result_size
                    })
        if rows:
            df = pd.DataFrame(rows)
            df = df.sort_values(['Metoda', 'Rdzenie CPU'])
            return df
        return None

    def plot_spark_config_summary(df, output_dir):
        """
        Plot Spark config values vs. core count for jaccard and minhash.
        """
        if df is None or df.empty:
            tee_print("Brak danych Spark config do wykresu.")
            return
        import matplotlib.pyplot as plt
        # Only plot numeric config (partitions), memory as text annotations
        fig, ax = plt.subplots(figsize=(10,6))
        for method in df['Metoda'].unique():
            mdf = df[df['Metoda'] == method]
            ax.plot(mdf['Rdzenie CPU'], mdf['Partycje'], marker='o', label=f"{method.capitalize()} - Partycje")
            # Annotate memory configs
            for _, row in mdf.iterrows():
                label = f"D:{row['Pamięć drivera']}\nE:{row['Pamięć executora']}\nMax:{row['Max rozmiar wyniku']}"
                ax.annotate(label, (row['Rdzenie CPU'], row['Partycje']), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, alpha=0.7)
        ax.set_xlabel('Rdzenie CPU', fontweight='bold')
        ax.set_ylabel('Liczba partycji', fontweight='bold')
        ax.set_title('Spark config: Partycje vs. Rdzenie CPU', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            plot_path = os.path.join(output_dir, 'benchmark_spark_config_summary.png')
            plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
            tee_print(f"Zapisano wykres Spark config: {plot_path}")
        plt.close()
    """Main function to run the benchmark analysis."""
    # Parse up to two optional arguments: input_dir and output_dir (order-insensitive)
    input_dir = None
    output_dir = None
    args = sys.argv[1:]
    for arg in args:
        if os.path.isdir(arg):
            if input_dir is None:
                input_dir = arg
            elif output_dir is None:
                output_dir = arg
        else:
            # If not a directory, treat as output_dir if not set
            if output_dir is None:
                output_dir = arg

    # Auto-detect input_dir if not provided
    if input_dir is None:
        possible_dirs = [
            'output/benchmark_results',
            '.',
            'benchmark_results'
        ]
        for dir_path in possible_dirs:
            if os.path.exists(dir_path):
                pattern = os.path.join(dir_path, "*_benchmark_*cores.out")
                if glob.glob(pattern):
                    input_dir = dir_path
                    break
                subdirs = [d for d in os.listdir(dir_path)
                          if os.path.isdir(os.path.join(dir_path, d)) and
                          re.match(r'\d{8}_\d{6}', d)]
                if subdirs:
                    latest_dir = os.path.join(dir_path, sorted(subdirs)[-1])
                    pattern = os.path.join(latest_dir, "*_benchmark_*cores.out")
                    if glob.glob(pattern):
                        input_dir = latest_dir
                        break
        if input_dir is None:
            print("Error: No benchmark files found.")
            print("Usage: python analyze_benchmark_results.py [input_dir] [output_dir]")
            print("\nLooking for files matching pattern: *_benchmark_*cores.out")
            sys.exit(1)

    # Set up logging to both console and file
    global tee_logger
    log_path = os.path.join(input_dir if input_dir else '.', 'benchmark_results_logs.out')
    tee_logger = TeeLogger(log_path)
    try:
        tee_print(f"Analyzing benchmark results in: {input_dir}")
        tee_print("="*60)

        # Analyze the benchmark files
        df = analyze_benchmark_directory(input_dir)



        if df is not None:
            # Create summary table and Excel output (pass output_dir)
            create_summary_table(df, output_dir)

            # Create performance plots in the specified output directory (or default)
            if output_dir is None:
                output_dir = os.path.join(input_dir, 'plots')
            create_performance_plots(df, output_dir)

            # Parse and plot Spark config summary from OMICS-multi-benchmark-p-* files
            spark_df = parse_multi_benchmark_files(input_dir)
            if spark_df is not None and not spark_df.empty:
                tee_print("\nPODSUMOWANIE KONFIGURACJI SPARK:")
                tee_print(spark_df.to_string(index=False))
            plot_spark_config_summary(spark_df, output_dir)

        tee_print("\nAnalysis complete!")
    finally:
        tee_logger.close()
    sys.exit(0)

if __name__ == "__main__":
    main()