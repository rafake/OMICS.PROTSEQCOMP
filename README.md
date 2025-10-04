# OMICS.PROTSEQCOMP

OMICS project after first semester on ICM UW

## How to download apptainer with ADAM

Enter the directory on HPC and run a command:
./apptainer_local/bin/apptainer shell --overlay overlay docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0

When the apptainer shell opens: Apptainer> then check whether ADAM works:
adam-submit --help

If not run those two lines:
export SPARK_HOME=/usr/local/lib/python3.12/site-packages/pyspark
export PATH=$SPARK_HOME/bin:$PATH
