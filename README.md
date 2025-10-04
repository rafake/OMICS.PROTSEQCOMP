# 🧬 OMICS.PROTSEQCOMP

> **OMICS Protein Sequence Comparison Project**  
> Developed during the first semester at ICM UW (Interdisciplinary Centre for Mathematical and Computational Modelling, University of Warsaw)

## 📋 Overview

This project focuses on protein sequence comparison and analysis using modern bioinformatics tools and high-performance computing resources.

## 🚀 Getting Started

### Setting up Apptainer with ADAM

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

## � Project Workflow

This project consists of 6 main tasks that demonstrate protein sequence analysis using comparative genomics approaches:

### Task 1: Data Acquisition 📥

**Objective**: Download protein sequence datasets for comparative analysis

We obtained protein sequences for two model organisms from NCBI:

- **Mus musculus** (House Mouse) - Reference genome GCF_000001635.27
- **Danio rerio** (Zebrafish) - Reference genome GCF_049306965.1

#### Download Commands

Execute these commands directly on HPC in your chosen directory:

```bash
# Download mouse protein sequences
curl -L "https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/GCF_000001635.27/download?include_annotation_type=PROT_FASTA" -o mouse_protein.zip

# Download zebrafish protein sequences
curl -L "https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/GCF_049306965.1/download?include_annotation_type=PROT_FASTA" -o zebrafish_protein.zip
```

#### Data Sources

- 🐭 **Mouse**: [GCF_000001635.27](https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/GCF_000001635.27/download?include_annotation_type=PROT_FASTA) - Complete proteome
- 🐟 **Zebrafish**: [GCF_049306965.1](https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/GCF_049306965.1/download?include_annotation_type=PROT_FASTA) - Complete proteome

### Task 2: [Coming Next] 🚧

_Description will be added as the project progresses..._

### Task 3: [Coming Next] 🚧

_Description will be added as the project progresses..._

### Task 4: [Coming Next] 🚧

_Description will be added as the project progresses..._

### Task 5: [Coming Next] 🚧

_Description will be added as the project progresses..._

### Task 6: [Coming Next] 🚧

_Description will be added as the project progresses..._

## �📚 Dependencies

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
