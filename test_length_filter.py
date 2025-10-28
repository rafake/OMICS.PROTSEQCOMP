#!/usr/bin/env python3
"""
Test script to demonstrate length filtering functionality
"""

def test_length_filter_logic():
    """Test the length filtering logic with sample data"""
    
    # Sample protein sequences with different lengths
    sequences = [
        ("prot1", "MKALLILCLAALTLTSLGAHA", 20),  # Length 20
        ("prot2", "MKALLILCLAALTLTSLGAHATAVTQE", 26),  # Length 26 (+30% of prot1)
        ("prot3", "MKALLILCLAALTLT", 15),  # Length 15 (-25% of prot1) 
        ("prot4", "MKALLILCLAALTLTSLG", 18),  # Length 18 (-10% of prot1)
        ("prot5", "MKALLILCLAALTLTSLGAHAV", 22),  # Length 22 (+10% of prot1)
    ]
    
    print("Testing length filtering logic (≤10% difference):")
    print("=" * 60)
    
    reference = sequences[0]  # prot1 with length 20
    ref_name, ref_seq, ref_len = reference
    
    print(f"Reference: {ref_name} (length: {ref_len})")
    print(f"Sequence: {ref_seq}")
    print()
    
    for name, seq, length in sequences[1:]:
        # Calculate percentage difference
        length_diff = abs(ref_len - length)
        percent_diff = length_diff / max(ref_len, length)
        
        # Apply 10% filter
        passes_filter = percent_diff <= 0.1
        
        print(f"Compare with: {name} (length: {length})")
        print(f"  Sequence: {seq}")
        print(f"  Length difference: {length_diff} ({percent_diff:.1%})")
        print(f"  Passes ≤10% filter: {'✓ YES' if passes_filter else '✗ NO'}")
        print()

if __name__ == "__main__":
    test_length_filter_logic()