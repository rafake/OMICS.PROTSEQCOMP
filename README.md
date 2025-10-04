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

*This project is part of the OMICS curriculum at ICM UW.*
