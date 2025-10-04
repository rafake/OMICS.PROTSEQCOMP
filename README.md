# 🧬 OMICS.PROTSEQCOMP

> **OMICS Protein Sequence Comparison Project**  
> Developed during the first semester at ICM UW (Interdisciplinary Centre for Mathematical and Computational Modelling, University of Warsaw)

## 📋 Overview

This project focuses on protein sequence comparison and analysis using modern bioinformatics tools and high-performance computing resources.

## 🔬 Project Workflow

This project consists of 7 main tasks that demonstrate protein sequence analysis using comparative genomics approaches:

### Task 1: Setting up Apptainer with ADAM ⚙️

**Objective**: Configure the distributed genomics analysis environment on HPC

ADAM (A Distributed Alignment Manager) is a genomics analysis platform built on Apache Spark. Follow these steps to set up the environment on HPC:

#### 1. Launch Apptainer Container

Navigate to your HPC directory and execute:

```bash
./apptainer_local/bin/apptainer shell --overlay overlay docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0
```

#### 2. Verify ADAM Installation

Once inside the Apptainer shell (`Apptainer>`), test if ADAM is working:

```bash
adam-submit --help
```

#### 3. Environment Configuration (if needed)

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

### Task 4: [Coming Next] 🚧

_Description will be added as the project progresses..._

### Task 5: [Coming Next] 🚧

_Description will be added as the project progresses..._

### Task 6: [Coming Next] 🚧

_Description will be added as the project progresses..._

### Task 7: [Coming Next] 🚧

_Description will be added as the project progresses..._

## 📚 Dependencies

- **Apptainer**: Container platform for HPC environments
- **ADAM**: Genomics analysis framework (v1.0.1)
- **Apache Spark**: Distributed computing framework
- **Python**: 3.12+ with PySpark

## 🎯 Project Goals

- Protein sequence comparison and alignment
- High-performance bioinformatics analysis
- Distributed computing implementation using Spark

## 📖 Documentation

For more detailed information about ADAM, visit the [official documentation](https://adam.readthedocs.io/).

---

_This project is part of the OMICS curriculum at ICM UW._