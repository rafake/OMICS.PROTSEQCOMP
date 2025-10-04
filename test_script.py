import os

# Prepare an output file in the current directory
out_file = os.path.join(os.getcwd(), "test_output.txt")
with open(out_file, "w") as f:
    # Print and save at the same time, flushing stdout immediately
    print("Hello World!", flush=True)
    print("Hello World!", file=f, flush=True)
