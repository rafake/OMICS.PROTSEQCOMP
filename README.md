# 🧬 OMICS.PROTSEQCOMP

> **OMICS Protein Sequence Comparison Project**  
> Developed during the first semester at ICM UW (Interdisciplinary Centre for Mathematical and Computational Modelling, University of Warsaw)

## 📋 Overview

This project focuses on protein sequence comparison and analysis using modern bioinformatics tools and high-performance computing resources.

## 🚀 Quick Start

After cloning this repository, follow these essential setup steps:

```bash
# 1. Clone the repository
git clone https://github.com/rafake/OMICS.PROTSEQCOMP.git
cd OMICS.PROTSEQCOMP

# 2. Run the automated setup script (downloads Apptainer to tools/ directory)
./setup.sh

# 3. Verify setup
./tools/apptainer/bin/apptainer --version
```

**That's it!** Your environment is now ready for all 6 project tasks.

## 🔬 Project Workflow

This project consists of 6 main tasks that demonstrate protein sequence analysis using comparative genomics approaches:

1. **Environment Setup** - Configure Apptainer and ADAM
2. **Data Acquisition** - Download protein sequences from NCBI
3. **File Format Conversion** - Convert FASTA to Parquet format
4. **PySpark Environment & Sampling** - Create samples for analysis
5. **Similarity Analysis** - Compare sequences using Jaccard and MinHash
6. **Performance Benchmarking** - Measure scalability across CPU configurations

## ⚙️ Pre-configured Setup

All batch scripts are pre-configured and ready to use after running `./setup.sh`:

- `multi_dataset_sampling_batch.sh` ✅
- `jaccard_batch.sh` ✅
- `minhash_batch.sh` ✅
- `benchmark.sh` ✅
- `test_sbatch.sh` ✅

## 📚 Dependencies

- **Apptainer**: Container platform for HPC environments (downloaded locally)
- **ADAM**: Genomics analysis framework (v1.0.1)
- **Apache Spark**: Distributed computing framework
- **Python**: 3.12+ with PySpark
- **Anaconda**: Scientific Python environment (`apps/anaconda/2024-10`) for analysis and plotting
- **SLURM**: HPC job scheduler with organized output management

## 📁 Project Structure

```
OMICS.PROTSEQCOMP/
├── tools/                         # Local Apptainer installation (ignored by git)
│   └── apptainer/
│       └── bin/apptainer
├── input/                         # Input datasets (organized by species)
├── output/                        # Analysis results and samples
│   ├── samples_parquet/          # Sampled datasets with timestamps
│   ├── protein_comparison/       # Jaccard and MinHash analysis results
│   └── benchmark_results/        # Performance analysis with plots
├── slurm/                        # SLURM job output logs (.out/.err files)
├── plots/                        # Generated visualization plots
├── setup.sh                     # Automated setup script
├── *.sh                         # SLURM batch job scripts
├── *.py                         # Python analysis scripts
├── .gitignore                    # Git ignore rules
└── README.md                     # Project documentation
```

### Task 1: Setting up Apptainer with ADAM ⚙️

**Objective**: Configure the distributed genomics analysis environment on HPC

ADAM (A Distributed Alignment Manager) is a genomics analysis platform built on Apache Spark. Follow these steps to set up the environment on HPC:

**Prerequisites**: Complete the Quick Start setup above.

#### Launch Apptainer Container

Launch the ADAM container using the local installation:

```bash
# Clone the repository
git clone https://github.com/rafake/OMICS.PROTSEQCOMP.git
cd OMICS.PROTSEQCOMP

# Create tools directory for local installations
mkdir -p tools

# Download Apptainer to the tools directory
cd tools
curl -s https://api.github.com/repos/apptainer/apptainer/releases/latest \
| grep browser_download_url \
| grep linux_amd64.tar.gz \
| cut -d '"' -f 4 \
| wget -qi -

# Extract Apptainer
tar -xzf apptainer_*.tar.gz
mv apptainer-* apptainer
rm apptainer_*.tar.gz

# Return to project root
cd ..

# Verify installation
./tools/apptainer/bin/apptainer --version
```

#### 2. Verify Configuration

All batch scripts are pre-configured to use the local installation:

````bash
# Verify the configuration (optional)


```bash
# Using the local Apptainer installation
./tools/apptainer/bin/apptainer shell --overlay overlay docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0

# Or using the configured environment variable (after running batch scripts)
$APPTAINER shell --overlay overlay docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0
````

#### 4. Verify ADAM Installation

Once inside the Apptainer shell (`Apptainer>`), test if ADAM is working:

```bash
adam-submit --help
```

#### 5. Environment Configuration (if needed)

If ADAM doesn't work initially, configure the Spark environment:

```bash
export SPARK_HOME=/usr/local/lib/python3.12/site-packages/pyspark
export PATH=$SPARK_HOME/bin:$PATH
```

### Task 2: Data Acquisition 📥

**Objective**: Download protein sequence datasets for comparative analysis

We obtained protein sequences for two model organisms from NCBI:

- **Mus musculus** (House Mouse) - Reference genome GCF_000001635.27
- **Danio rerio** (Zebrafish) - Reference genome GCF_049306965.1

#### Download & Extraction Commands

Execute these commands directly on HPC in your chosen directory:

```bash
# Download mouse protein sequences
curl -L "https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/GCF_000001635.27/download?include_annotation_type=PROT_FASTA" -o mouse_protein.zip

# Download zebrafish protein sequences
curl -L "https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/GCF_049306965.1/download?include_annotation_type=PROT_FASTA" -o zebrafish_protein.zip

# Extract downloaded archives
unzip mouse_protein.zip -d mouse_protein
unzip zebrafish_protein.zip -d zebrafish_protein
```

#### Data Sources

- 🐭 **Mouse**: [GCF_000001635.27](https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/GCF_000001635.27/download?include_annotation_type=PROT_FASTA) - Complete proteome
- 🐟 **Zebrafish**: [GCF_049306965.1](https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/GCF_049306965.1/download?include_annotation_type=PROT_FASTA) - Complete proteome

### Task 3: File Format Conversion 🔄

**Objective**: Convert protein sequence files from FASTA format to Parquet for optimized processing

After extracting the downloaded archives, the protein sequence data is located deep within the directory structure in `.faa` format (FASTA Amino Acid files). This task involves a two-step conversion process to prepare the data for efficient analysis with ADAM.

#### File Location & Structure

The protein sequences are found in `protein.faa` files nested within the extracted directories:

- `mouse_protein/` → navigate to find `protein.faa`
- `zebrafish_protein/` → navigate to find `protein.faa`

#### Conversion Process

The conversion involves two sequential steps:

**Step 1: File Renaming**
Rename `.faa` files to `.fa` format (standard FASTA extension):

```bash
# Navigate to the protein.faa file location within mouse_protein directory
mv protein.faa mouse_protein.fa

# Navigate to the protein.faa file location within zebrafish_protein directory
mv protein.faa zebrafish_protein.fa
```

**Step 2: Format Conversion**
Convert `.fa` files to `.parquet` format for optimized distributed processing using ADAM:

```bash
# Convert mouse protein sequences to Parquet format
adam-submit transformSequences mouse_protein.fa mouse_protein_parquet

# Convert zebrafish protein sequences to Parquet format
adam-submit transformSequences zebrafish_protein.fa zebrafish_protein_parquet
```

#### Why Parquet Format?

- **🚀 Performance**: Faster read/write operations for large datasets
- **💾 Compression**: Reduced storage requirements
- **⚡ Spark Integration**: Native support in Apache Spark/ADAM
- **🔍 Columnar Storage**: Efficient querying and analysis

This format conversion enables efficient distributed processing of protein sequences using ADAM's Spark-based architecture.

### Task 4: PySpark Environment Setup �

**Objective**: Initialize PySpark session and verify data availability for analysis

After converting the protein sequences to Parquet format, we need to set up PySpark to work with the data files and verify they are accessible in our current working environment.

#### Environment Setup

The APPTAINER variable is automatically configured in all batch scripts:

```bash
# All batch scripts use the local installation
APPTAINER=$PWD/tools/apptainer/bin/apptainer
```

#### Starting PySpark Session

Launch PySpark within the Apptainer environment:

```bash
pyspark
```

#### Multi-Dataset Batch Sampling

For processing multiple datasets automatically, use the batch job system to create samples for downstream analysis:

📄 **`multi_dataset_sampling_batch.sh`** - Automated batch processing script

This SLURM batch job will:

- 🔍 **Scan input directory** for datasets with parquet files or "parquet" in the name
- 🎲 **Create 100 random samples** from each dataset using PySpark's `orderBy(rand()).limit(100)`
- 💾 **Save timestamped results** to `output/sample_parquet/sample_YYYYMMDD_HHMMSS/`
- ⚡ **Process multiple datasets** in a single job submission
- 🗂️ **Organize output** with timestamp-based directory structure for easy tracking

**Setup and Usage:**

1. **Organize input data:**

   ```
   input/
   ├── mus_musculus_parquet/
   ├── zebrafish_parquet/
   └── other_dataset_parquet/
   ```

2. **Submit batch job:**

   ```bash
   sbatch multi_dataset_sampling_batch.sh
   ```

3. **Check results:**
   ```
   output/
   └── samples_parquet/
       └── sample_YYYYMMDD_HHMMSS/
           ├── YYYYMMDD_HHMMSS_100_mouse_protein_output.adam
           ├── YYYYMMDD_HHMMSS_100_zebrafish_protein_output.adam
           └── other_dataset_output.adam
   ```

**Key Features:**

- **Reproducible sampling**: Uses PySpark's distributed sampling for consistent results
- **Timestamp organization**: Each batch run creates a unique timestamped directory
- **Efficient processing**: Leverages Spark's distributed computing capabilities
- **Flexible input**: Automatically detects and processes all parquet datasets

### Task 5: Jaccard Similarity Analysis 🧮

**Objective**: Compare protein sequences between species using k-mer analysis and Jaccard similarity

This task implements pairwise protein sequence comparison between mouse and zebrafish using k-mer decomposition and Jaccard similarity metrics to identify potentially homologous proteins.

#### Analysis Overview

The Jaccard similarity analysis performs the following operations:

1. **K-mer Extraction**: Decomposes protein sequences into overlapping 3-mers (tripeptides)
2. **Pairwise Comparison**: Creates all possible combinations between mouse and zebrafish samples (100 × 100 = 10,000 pairs)
3. **Similarity Calculation**: Computes Jaccard similarity coefficient for each pair
4. **Results Ranking**: Identifies and ranks the most similar protein pairs

#### Running the Analysis

**Interactive Execution:**

```python
# Run the Jaccard analysis script directly
python jaccard.py

# Run without saving files (console output only)
python jaccard.py --no-save
```

**Batch Job Execution:**

For automated processing on HPC systems, use the SLURM batch script:

📄 **`jaccard_batch.sh`** - Automated Jaccard similarity analysis

```bash
# Submit the batch job (with file saving)
sbatch jaccard_batch.sh

# Submit in no-save mode (console output only)
sbatch jaccard_batch.sh --no-save
```

**MinHash Analysis:**

```bash
# Submit MinHash batch job
sbatch minhash_batch.sh

# Submit MinHash in no-save mode
sbatch minhash_batch.sh --no-save
```

#### Batch Job Features

The batch scripts (`jaccard_batch.sh`, `minhash_batch.sh`) provide:

- 🎯 **Environment Integration**: Automatically detects and uses the latest sample data from `output/samples_parquet/`
- 🕐 **Timestamped Results**: Uses sample timestamp for consistent directory naming
- 💾 **Complete Data Package**: Saves both analysis results and original input data for reproducibility
- ⚡ **HPC Optimization**: Configured for SLURM job scheduler with appropriate resource allocation
- 🔍 **No-Save Mode**: Optional `--no-save` parameter for console-only output without file creation
- 📁 **Organized Logging**: All SLURM job outputs are automatically saved to the `slurm/` directory for clean project organization

#### No-Save Mode

Both analysis scripts support a special no-save mode for testing and development:

**Features:**

- 📺 **Console Output Only**: Results displayed in job output, no files created
- 🚀 **Faster Execution**: Skips all file I/O operations for pure computation timing
- 💾 **No Disk Usage**: Zero storage consumption during analysis
- 🧪 **Perfect for Testing**: Ideal for script validation and debugging

**Usage:**

```bash
# Interactive mode
python jaccard.py --no-save
python minhash.py --no-save

# Batch mode
sbatch jaccard_batch.sh --no-save
sbatch minhash_batch.sh --no-save

# Alternative parameter
sbatch jaccard_batch.sh --dry-run
```

#### Output Structure

Both Jaccard and MinHash analyses are now organized in a unified comparison structure:

```
output/
└── protein_comparison/
    └── YYYYMMDD_HHMMSS/                    # Sample timestamp
        ├── jaccard/
        │   ├── mouse_zebrafish_100x100_jaccard.parquet
        │   └── top10_mouse_fish_jaccard.csv
        ├── minhash/
        │   ├── mouse_fish_minhash_results.parquet
        │   └── top10_mouse_fish_minhash.csv
        └── input_data/                     # Shared input data
            ├── mouse_sample/               # Original mouse sample
            └── fish_sample/                # Original zebrafish sample
```

#### Key Analysis Features

- **🔬 K-mer Analysis**: Extracts unique 3-mers from protein sequences for comparison
- **📊 Jaccard Coefficient**: Measures similarity as intersection over union of k-mer sets
- **⚡ Distributed Computing**: Leverages PySpark for efficient parallel processing
- **🎯 Top Matches**: Identifies and displays the 10 most similar protein pairs
- **📈 Scalable Design**: Handles large-scale protein comparisons efficiently

#### Interpretation

The Jaccard similarity score ranges from 0 to 1:

- **1.0**: Identical k-mer composition (potentially homologous)
- **0.5-0.9**: High similarity (likely related proteins)
- **0.1-0.5**: Moderate similarity (possible functional relationship)
- **0.0**: No shared k-mers (likely unrelated)

### Task 6: Performance Benchmarking ⚡

**Objective**: Measure and analyze computational performance across different CPU configurations using automated SLURM array jobs

This task evaluates the scalability and performance characteristics of the protein comparison algorithms using systematic benchmarking across multiple CPU core configurations with a single command execution.

#### Benchmark Features

📄 **`benchmark.sh`** - Automated multi-core performance measurement script

The benchmark system provides:

- 🎯 **Automated Execution**: Uses the latest sample data for consistent benchmarking
- ⏱️ **Detailed Timing**: Comprehensive resource usage measurement with `/usr/bin/time -v`
- � **SLURM Array Jobs**: Automatically tests 5 different CPU configurations (1, 2, 4, 8, 16 cores)
- 📊 **Organized Results**: Timestamped output files for performance analysis
- 🔀 **Multiple Methods**: Supports benchmarking both Jaccard and MinHash algorithms
- 🚀 **Pure Performance**: Always runs analysis scripts in no-save mode for accurate timing
- ⚡ **Single Command**: One submission automatically benchmarks all core configurations

#### Usage

To run comprehensive performance benchmarks across all CPU configurations, specify the comparison method as a required parameter:

```bash
# Benchmark Jaccard similarity analysis across 1, 2, 4, 8, 16 cores
sbatch benchmark.sh jaccard

# Benchmark MinHash similarity analysis across 1, 2, 4, 8, 16 cores
sbatch benchmark.sh minhash
```

**SLURM Array Job System:**
The benchmark script uses `#SBATCH --array=0-4` to automatically submit 5 separate tasks, each with a different CPU core configuration:

- **Array Task 0**: 1 CPU core
- **Array Task 1**: 2 CPU cores
- **Array Task 2**: 4 CPU cores
- **Array Task 3**: 8 CPU cores
- **Array Task 4**: 16 CPU cores

**Available Methods:**

- `jaccard` - Benchmark Jaccard similarity analysis with k-mer comparison
- `minhash` - Benchmark MinHash similarity analysis with LSH approximation

**Error Handling:**
The script validates input parameters and provides clear error messages:

```bash
# Missing parameter
sbatch benchmark.sh
# Error: Missing required parameter!
# Usage: sbatch benchmark.sh <comparison_method>

# Invalid method
sbatch benchmark.sh invalid
# Error: Invalid comparison method 'invalid'
# Available methods: jaccard, minhash
```

#### Output

Benchmark results are automatically organized by sample timestamp and CPU core count:

```
output/
└── benchmark_results/
    └── YYYYMMDD_HHMMSS/                    # Sample timestamp
        ├── jaccard_benchmark_1cores.out    # 1-core Jaccard benchmark
        ├── jaccard_benchmark_2cores.out    # 2-core Jaccard benchmark
        ├── jaccard_benchmark_4cores.out    # 4-core Jaccard benchmark
        ├── jaccard_benchmark_8cores.out    # 8-core Jaccard benchmark
        ├── jaccard_benchmark_16cores.out   # 16-core Jaccard benchmark
        ├── minhash_benchmark_1cores.out    # 1-core MinHash benchmark
        ├── minhash_benchmark_2cores.out    # 2-core MinHash benchmark
        ├── minhash_benchmark_4cores.out    # 4-core MinHash benchmark
        ├── minhash_benchmark_8cores.out    # 8-core MinHash benchmark
        └── minhash_benchmark_16cores.out   # 16-core MinHash benchmark
```

**Key Features:**

- **📁 Organized by Sample**: Each benchmark run uses the same sample data timestamp
- **🔬 Method-Specific**: Clear separation between Jaccard and MinHash results
- **⚙️ Core Configuration**: Filename includes CPU core count for easy identification
- **🚀 Pure Computation**: Analysis scripts run in no-save mode for accurate performance measurement
- **📊 Comprehensive Metrics**: Each file contains detailed execution time, memory usage, and CPU utilization
- **🔢 Complete Coverage**: Single command generates comprehensive scalability analysis

**Performance Analysis:**
This automated system enables comprehensive analysis of:

- CPU core scalability (1 → 16 cores performance scaling)
- Algorithm comparison (Jaccard vs MinHash efficiency)
- Resource utilization patterns across different configurations
- Optimal core count determination for specific workloads

**Performance Analysis & Visualization:**

📄 **`analyze_benchmark_batch.sh`** - Automated performance analysis and plotting script

The project includes an integrated analysis system that automatically processes benchmark results and generates visualization plots:

```bash
# Analyze and visualize all benchmark results for the latest sample timestamp
sbatch analyze_benchmark_batch.sh
```

**Analysis Features:**

- 🐍 **Python Environment**: Uses Anaconda module (`apps/anaconda/2024-10`) for scientific computing
- 📊 **Matplotlib Plotting**: Generates comprehensive performance visualization plots
- 📈 **Automatic Analysis**: Detects benchmark directories and processes all available results
- 💾 **Organized Results**: Saves plots directly in benchmark results directories alongside raw data
- 🔍 **Comprehensive Coverage**: Analyzes both Jaccard and MinHash benchmark results
- 📁 **SLURM Integration**: Job outputs organized in the `slurm/` directory

**Generated Plots:**
The analysis system automatically creates performance visualization plots saved in each benchmark results directory, enabling easy comparison of:

- CPU core scalability patterns
- Algorithm performance comparison (Jaccard vs MinHash)
- Memory usage trends across configurations
- Execution time scaling analysis

**Job Monitoring:**
Monitor array job progress with standard SLURM commands:

```bash
# Check job status
squeue -u $USER

# View specific array task output
squeue -j <job_id>_<array_index>

# Check all array tasks
scontrol show job <job_id>

# Check SLURM job logs
ls slurm/
```

## � Project Structure

```
OMICS.PROTSEQCOMP/
├── tools/                         # Local tools and dependencies (ignored by git)
│   └── apptainer/                # Local Apptainer installation
│       └── bin/
│           └── apptainer         # Apptainer executable
├── input/                          # Input datasets (organized by species)
├── output/                         # Analysis results and samples
│   ├── samples_parquet/           # Sampled datasets with timestamps
│   ├── protein_comparison/        # Jaccard and MinHash analysis results
│   └── benchmark_results/         # Performance analysis with plots
├── slurm/                         # SLURM job output logs (.out/.err files)
├── plots/                         # Generated visualization plots
├── setup.sh                      # Automated setup script
├── *.sh                          # SLURM batch job scripts
├── *.py                          # Python analysis scripts
├── .gitignore                    # Git ignore rules
└── README.md                     # Project documentation
```

## �📚 Dependencies

- **Apptainer**: Container platform for HPC environments
- **ADAM**: Genomics analysis framework (v1.0.1)
- **Apache Spark**: Distributed computing framework
- **Python**: 3.12+ with PySpark
- **Anaconda**: Scientific Python environment (`apps/anaconda/2024-10`) for analysis and plotting
- **SLURM**: HPC job scheduler with organized output management

## 🎯 Project Goals

- **Comparative Genomics**: Cross-species protein sequence comparison between mouse and zebrafish
- **Scalable Analysis**: High-performance bioinformatics analysis using distributed computing
- **Algorithm Comparison**: Implementation and benchmarking of Jaccard and MinHash similarity methods
- **Performance Optimization**: Multi-core scalability analysis and resource utilization measurement
- **Reproducible Workflows**: Organized batch processing with automated data management and visualization

## 📖 Documentation

For more detailed information about ADAM, visit the [official documentation](https://adam.readthedocs.io/).

---

_This project is part of the OMICS curriculum at ICM UW._
