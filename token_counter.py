#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from git import Repo
from tqdm import tqdm
from transformers import AutoTokenizer

# Initialize the tokenizer (using GPT-2 tokenizer as it's commonly used)
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# File extensions to analyze
TEXT_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.md', '.txt',
    '.yml', '.yaml', '.json', '.xml', '.csv', '.sql', '.sh', '.bash',
    '.java', '.cpp', '.c', '.h', '.hpp', '.rs', '.go', '.rb', '.php'
}

def is_binary(file_path: str) -> bool:
    """Check if a file is binary."""
    try:
        with open(file_path, 'tr') as check_file:
            check_file.read(1024)
            return False
    except UnicodeDecodeError:
        return True

def count_tokens(content: str) -> int:
    """Count tokens in the given content using GPT-2 tokenizer."""
    return len(tokenizer.encode(content))

def process_repository(repo_path: str) -> Tuple[int, Dict[str, int]]:
    """Process all files in the repository and count tokens."""
    total_tokens = 0
    extension_stats = {}
    
    # Get list of all files for progress bar
    all_files = []
    for root, _, files in os.walk(repo_path):
        if '.git' in root:
            continue
        for file in files:
            file_path = os.path.join(root, file)
            extension = os.path.splitext(file)[1].lower()
            if extension in TEXT_EXTENSIONS and not is_binary(file_path):
                all_files.append((file_path, extension))
    
    # Process files with progress bar
    for file_path, extension in tqdm(all_files, desc="Processing files"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tokens = count_tokens(content)
                total_tokens += tokens
                extension_stats[extension] = extension_stats.get(extension, 0) + tokens
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
                
    return total_tokens, extension_stats

def format_number(num: int) -> str:
    """Format a number with thousands separator and appropriate suffix."""
    if num < 1000:
        return str(num)
    elif num < 1_000_000:
        return f"{num/1000:.1f}K"
    else:
        return f"{num/1_000_000:.1f}M"

def main():
    if len(sys.argv) != 2:
        print("Usage: python token_counter.py <repository_url>")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    
    # Create a temporary directory for cloning
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Cloning repository: {repo_url}")
        try:
            repo = Repo.clone_from(repo_url, temp_dir)
        except Exception as e:
            print(f"Error cloning repository: {str(e)}")
            sys.exit(1)
            
        print("\nAnalyzing repository...")
        total_tokens, extension_stats = process_repository(temp_dir)
        
        # Print results
        print("\nResults:")
        print(f"Total tokens: {format_number(total_tokens)} ({total_tokens:,})")
        print("\nTokens by file extension:")
        for ext, count in sorted(extension_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"{ext:8} {format_number(count):>8} ({count:,})")
            
        # Print context window comparisons
        print("\nContext Window Comparisons:")
        windows = {
            "GPT-3.5 (4K)": 4096,
            "GPT-4 (8K)": 8192,
            "GPT-4 (32K)": 32768,
            "Claude 2 (100K)": 100000,
            "Claude 3 (200K)": 200000
        }
        
        for model, window in windows.items():
            percentage = (total_tokens / window) * 100
            print(f"{model:15} {percentage:.1f}% of context window")

if __name__ == "__main__":
    main()
