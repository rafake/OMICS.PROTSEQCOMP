# Test Script
# Simple test to verify Python execution

import os

print("Hello World!")

# Print current working directory
cwd = os.getcwd()
print("Current working directory:", cwd)

# List files in the current directory
files = os.listdir(cwd)
print("Files in directory:")
for f in files:
    print("  -", f)