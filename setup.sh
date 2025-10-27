#!/bin/bash -l
#SBATCH -J OMICS-setup    # job name
#SBATCH -N 1                        # number of nodes (1 node is sufficient)
#SBATCH -n 1                        # number of tasks (1 task)
#SBATCH -c 1                       
#SBATCH --time=00:05:00             
#SBATCH -p topola                   
#SBATCH -A g100-2238
#SBATCH --output=slurm/setup-%j.out
#SBATCH --error=slurm/setup-%j.err

echo "🧬 OMICS.PROTSEQCOMP Setup Script"
echo "================================="

# Create slurm output directory first
mkdir -p slurm

# Create tools directory
echo "📁 Creating tools directory..."
mkdir -p tools

# Install Apptainer using unprivileged installation
echo "⬇️  Installing Apptainer (unprivileged)..."
curl -s https://raw.githubusercontent.com/apptainer/apptainer/main/tools/install-unprivileged.sh | \
    bash -s - tools

# Create necessary directories
echo "📂 Creating project directories..."
mkdir -p input output slurm plots

# Batch scripts are already configured with correct paths
echo "✅ Batch scripts are pre-configured to use local Apptainer installation"

# Verify installation
echo "✅ Verifying installation..."
if ./tools/bin/apptainer --version > /dev/null 2>&1; then
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Apptainer version: $(./tools/bin/apptainer --version)"
    echo ""
    echo "You can now run the project tasks. Start with:"
    echo "  sbatch multi_dataset_sampling_batch.sh"
else
    echo "❌ Setup failed. Please check the installation manually."
    exit 1
fi

echo ""
echo "📖 See README.md for detailed task instructions."