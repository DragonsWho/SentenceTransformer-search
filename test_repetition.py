from detect_repetition import detect_repetition
import sys
import os

def test_file(file_path):
    """Test a specific file for repetition patterns"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if detect_repetition(content, sequence_length=3, min_repeats=10):
            print("Repetition detected in:", file_path)
            return True
        else:
            print("No significant repetition found in:", file_path)
            return False
            
    except Exception as e:
        print(f"Error testing file {file_path}: {str(e)}")
        return False

def test_directory(directory):
    """Test all .md files in a directory"""
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return
        
    repetition_count = 0
    total_files = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                total_files += 1
                file_path = os.path.join(root, file)
                if test_file(file_path):
                    repetition_count += 1
                    
    print(f"\nTest complete. Scanned {total_files} files.")
    print(f"Found repetition in {repetition_count} files.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_repetition.py <directory_or_file>")
        sys.exit(1)
        
    path = sys.argv[1]
    if os.path.isdir(path):
        test_directory(path)
    else:
        test_file(path)
