#!/bin/bash

echo "🧬 OMICS.PROTSEQCOMP Setup Script"
echo "================================="

# Create tools directory
echo "📁 Creating tools directory..."
mkdir -p tools
cd tools

# Download Apptainer
echo "⬇️  Downloading Apptainer..."
curl -s https://api.github.com/repos/apptainer/apptainer/releases/latest \
| grep browser_download_url \
| grep linux_amd64.tar.gz \
| cut -d '"' -f 4 \
| wget -qi -

# Extract Apptainer
echo "📦 Extracting Apptainer..."
tar -xzf apptainer_*.tar.gz
mv apptainer-* apptainer
rm apptainer_*.tar.gz

# Return to project root
cd ..

# Create necessary directories
echo "📂 Creating project directories..."
mkdir -p input output slurm plots

# Batch scripts are already configured with correct paths
echo "✅ Batch scripts are pre-configured to use local Apptainer installation"

# Verify installation
echo "✅ Verifying installation..."
if ./tools/apptainer/bin/apptainer --version > /dev/null 2>&1; then
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Apptainer version: $(./tools/apptainer/bin/apptainer --version)"
    echo ""
    echo "You can now run the project tasks. Start with:"
    echo "  sbatch multi_dataset_sampling_batch.sh"
else
    echo "❌ Setup failed. Please check the installation manually."
    exit 1
fi

echo ""
echo "📖 See README.md for detailed task instructions."