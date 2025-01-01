import difflib
from collections import Counter
import re

def detect_repetition(text, sequence_length=3, min_repeats=3):
    """
    Detect repeating patterns in text that may indicate LLM is stuck in a loop
    
    Args:
        text (str): Text to analyze
        sequence_length (int): Number of words in a sequence to check for repetition
        min_repeats (int): Minimum number of times a sequence must repeat to be flagged
        
    Returns:
        bool: True if significant repetition detected, False otherwise
    """
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Create sequences of words
    sequences = [' '.join(words[i:i+sequence_length]) 
                for i in range(len(words) - sequence_length + 1)]
    
    # Count sequence occurrences
    sequence_counts = Counter(sequences)
    
    # Check for repeating sequences
    for seq, count in sequence_counts.most_common():
        if count >= min_repeats:
            # Check if this is a meaningful repetition (not just short variations)
            if len(seq.split()) >= sequence_length:
                return True
                
    return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python detect_repetition.py <text_file>")
        sys.exit(1)
        
    with open(sys.argv[1], 'r') as f:
        text = f.read()
        
    if detect_repetition(text):
        print("Repetition detected!")
    else:
        print("No significant repetition found")
