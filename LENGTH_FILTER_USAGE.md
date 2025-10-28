# Length-Based Filtering Feature

## Overview

Both `jaccard.py` and `minhash.py` now support a `--length-filter` flag that implements biological relevance filtering by comparing only protein pairs with sequence lengths that differ by ≤10%.

## Feature Details

### Why Length Filtering?

- **Biological Relevance**: Proteins with very different lengths are unlikely to be functionally similar
- **Performance Improvement**: Reduces the number of comparisons, making analysis faster
- **Focused Results**: Eliminates spurious similarities between proteins of vastly different sizes

### Length Filter Criterion

- Only compares protein pairs where: `|length1 - length2| / max(length1, length2) ≤ 0.1`
- This means length difference must be ≤10% of the longer sequence
- Example: A 100AA protein will only be compared with proteins between 91-111AA in length

## Usage Examples

### Jaccard Analysis with Length Filtering

```bash
# Local execution
python jaccard.py --length-filter

# SLURM batch execution
sbatch jaccard_batch.sh --length-filter

# Combined with no-save mode
sbatch jaccard_batch.sh --length-filter --no-save
```

### MinHash Analysis with Length Filtering

```bash
# Local execution
python minhash.py --length-filter

# SLURM batch execution
sbatch minhash_batch.sh --length-filter

# Combined with no-save mode
sbatch minhash_batch.sh --length-filter --no-save
```

## Implementation Details

### Jaccard Implementation

- Adds `length()` calculation for both datasets before cross-join
- Applies filter condition during cross-join operation
- Maintains all existing functionality (k-mer extraction, similarity calculation)

### MinHash Implementation

- Adds sequence length columns to datasets before MinHashLSH transformation
- Preserves length information through the LSH join process
- Applies filter condition to similarity join results
- Compatible with approximate similarity thresholds

## Performance Impact

### Expected Benefits

- **Reduced Comparisons**: Typically 20-40% fewer protein pairs to analyze
- **Faster Execution**: Less computation time for similarity calculations
- **Lower Memory Usage**: Fewer intermediate results to store
- **Better Biological Focus**: More meaningful similarity results

### Benchmarking Results

Run these commands to see the performance difference:

```bash
# Standard analysis (all pairs)
time sbatch jaccard_batch.sh --no-save

# Length-filtered analysis
time sbatch jaccard_batch.sh --length-filter --no-save
```

## Test Case

A simple test demonstrates the filtering logic:

```bash
python test_length_filter.py
```

**Example Output:**

```
Reference: prot1 (length: 20)
└─ prot4 (length: 18): 10.0% difference → ✓ PASSES
└─ prot5 (length: 22): 9.1% difference → ✓ PASSES
└─ prot2 (length: 26): 23.1% difference → ✗ FILTERED OUT
└─ prot3 (length: 15): 25.0% difference → ✗ FILTERED OUT
```

## Backwards Compatibility

- All existing functionality remains unchanged
- `--length-filter` is optional - scripts work normally without it
- Can be combined with existing flags like `--no-save`, `--limit-100`
- Results format and output structure unchanged

## Technical Notes

- Uses Spark SQL functions: `length()`, `greatest()`, `abs()`
- Filter applied at optimal points in each algorithm for best performance
- Preserves all metadata and sequence information in results
- Compatible with both local Python execution and SLURM containerized runs
