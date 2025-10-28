# 🧬 OMICS.PROTSEQCOMP

> **OMICS Protein Sequence Comparison Project**  
> Developed during master studies at ICM UW (Interdisciplinary Centre for Mathematical and Computational Modelling, University of Warsaw)

## 📋 Overview

This project focuses on protein sequence comparison and analysis using modern bioinformatics tools and high-performance computing resources.

## 🚀 Quick Start

Clone this repository and follow these essential setup steps:

```bash
# 1. Clone the repository
git clone https://github.com/rafake/OMICS.PROTSEQCOMP.git

# 2. Navigate to the project directory
cd OMICS.PROTSEQCOMP

# 3. Run the automated setup script (downloads Apptainer to tools/ directory)
./setup.sh

# 4. Verify setup
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

#### 1. Launch Apptainer Container

```bash
# Launch ADAM container
./tools/apptainer/bin/apptainer shell docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0
```

#### 2. Verify Configuration

All batch scripts are pre-configured to use the local installation:

```bash
# Verify the configuration (optional)
# Using the local Apptainer installation
./tools/apptainer/bin/apptainer shell --overlay overlay docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0

# Or using the configured environment variable (after running batch scripts)
$APPTAINER shell --overlay overlay docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0
```

#### 3. Verify ADAM Installation

Once inside the Apptainer shell (`Apptainer>`), test if ADAM is working:

```bash
adam-submit --help
```

#### 4. Environment Configuration (if needed)

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

### Task 4: PySpark Environment Setup ⚙️

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

This script scans the input directory for parquet datasets, creates 100 random samples from each using PySpark's distributed sampling, and saves timestamped results to `output/sample_parquet/sample_YYYYMMDD_HHMMSS/`.

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

The batch scripts automatically detect the latest sample data, use timestamped results for consistency, and support a `--no-save` mode for console-only output during testing.

#### No-Save Mode

Both scripts support `--no-save` mode for testing - results display in console only without creating files:

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

The analysis extracts 3-mers from protein sequences, computes Jaccard similarity coefficients using PySpark's distributed processing, and identifies the top 10 most similar protein pairs.

#### Interpretation

The Jaccard similarity score ranges from 0 to 1:

- **1.0**: Identical k-mer composition (potentially homologous)
- **0.5-0.9**: High similarity (likely related proteins)
- **0.1-0.5**: Moderate similarity (possible functional relationship)
- **0.0**: No shared k-mers (likely unrelated)


### Task 6: Performance Benchmarking ⚡

**Objective**: Measure and analyze computational performance across different CPU configurations using automated SLURM jobs

This task evaluates the scalability and performance characteristics of the protein comparison algorithms using systematic benchmarking across multiple CPU core configurations with a single command execution.

#### Benchmark Features

📄 **`benchmark.sh`** and **`benchmark-performance.sh`** - Automated multi-core performance measurement scripts

These scripts test multiple CPU configurations (1, 2, 4, 8, 16, 24 cores) with comprehensive resource usage measurement. Both Jaccard and MinHash algorithms can be benchmarked.

#### Usage

To run comprehensive performance benchmarks across all CPU configurations, specify the comparison method as a required parameter:

```bash
# Benchmark Jaccard similarity analysis
sbatch benchmark.sh jaccard

# Benchmark MinHash similarity analysis
sbatch benchmark.sh minhash

# High-performance (24-core, 110GB RAM) benchmarking with length filter
sbatch benchmark-performance.sh minhash --length-filter
sbatch benchmark-performance.sh jaccard --length-filter
```

**Optional parameters:**
- `--length-filter` — Only compare protein pairs with sequence lengths within 10% of each other (biologically relevant filtering)
- `-c <cores>` — Set maximum number of cores (default: 24 for performance script)
- `-m <memory>` — Set memory in MB (default: 110000 for performance script)
- `-t <time>` — Set time limit (default: 00:30:00 for performance script)

**Examples:**
```bash
# MinHash with length filtering and custom resources
sbatch benchmark-performance.sh minhash --length-filter -c 24 -m 110000 -t 01:00:00

# Jaccard without length filtering
sbatch benchmark-performance.sh jaccard
```

#### Output

Benchmark results are automatically organized by sample timestamp and CPU core count:

```
output/
└── benchmark_results/
    └── YYYYMMDD_HHMMSS/                    # Sample timestamp
        ├── jaccard_benchmark_1cores.out    # 1-core Jaccard benchmark
        ├── ...
        ├── minhash_benchmark_24cores.out   # 24-core MinHash benchmark
```

Each benchmark run uses the same sample data timestamp with clear separation between Jaccard and MinHash results. Filenames include CPU core count for easy identification, and analysis scripts run in no-save mode for accurate performance measurement with detailed execution time, memory usage, and CPU utilization metrics.

#### Length Filter Usage

The `--length-filter` flag can be added to any Jaccard or MinHash run (batch or interactive) to restrict comparisons to protein pairs whose sequence lengths differ by no more than 10%. This improves biological relevance and performance:

```bash
# Example: Jaccard with length filter
python jaccard.py --length-filter

# Example: MinHash with length filter
python minhash.py --length-filter
```

#### Performance Analysis & Visualization

📄 **`analyze_benchmark_batch.sh`** - Automated performance analysis and plotting script

The project includes an integrated analysis system that automatically processes benchmark results and generates visualization plots:

```bash
# Analyze and visualize all benchmark results for the latest sample timestamp
sbatch analyze_benchmark_batch.sh
```

This system uses the Anaconda module (`apps/anaconda/2024-10`) for scientific computing with Matplotlib to generate comprehensive performance visualization plots. It automatically detects benchmark directories, processes all available results, and saves plots directly in benchmark results directories alongside raw data.

#### Job Monitoring
Monitor job progress with standard SLURM commands:

```bash
# Check job status
squeue -u $USER

# Check SLURM job logs
ls slurm/
```

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
