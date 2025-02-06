#!/usr/bin/env python3

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "gitpython",
#   "tqdm",
#   "transformers",
# ]
# ///

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

# File extensions mapped to their technologies
FILE_EXTENSIONS = {
    # Python and related
    '.py': 'Python',
    '.pyi': 'Python Interface',
    '.pyx': 'Cython',
    '.pxd': 'Cython Header',
    '.ipynb': 'Jupyter Notebook',
    '.requirements.txt': 'Python Requirements',
    '.pipfile': 'Python Pipenv',
    '.pyproject.toml': 'Python Project',
    '.txt': 'Plain Text',
    '.md': 'Markdown',

    # Web Technologies
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.scss': 'SASS',
    '.sass': 'SASS',
    '.less': 'LESS',
    '.js': 'JavaScript',
    '.jsx': 'React JSX',
    '.ts': 'TypeScript',
    '.tsx': 'React TSX',
    '.vue': 'Vue.js',
    '.svelte': 'Svelte',
    '.php': 'PHP',
    '.blade.php': 'Laravel Blade',
    '.hbs': 'Handlebars',
    '.ejs': 'EJS Template',
    '.astro': 'Astro',

    # System Programming
    '.c': 'C',
    '.h': 'C Header',
    '.cpp': 'C++',
    '.hpp': 'C++ Header',
    '.cc': 'C++',
    '.hh': 'C++ Header',
    '.cxx': 'C++',
    '.rs': 'Rust',
    '.go': 'Go',
    '.swift': 'Swift',
    '.m': 'Objective-C',
    '.mm': 'Objective-C++',

    # JVM Languages
    '.java': 'Java',
    '.class': 'Java Bytecode',
    '.jar': 'Java Archive',
    '.kt': 'Kotlin',
    '.kts': 'Kotlin Script',
    '.groovy': 'Groovy',
    '.scala': 'Scala',
    '.clj': 'Clojure',

    # .NET Languages
    '.cs': 'C#',
    '.vb': 'Visual Basic',
    '.fs': 'F#',
    '.fsx': 'F# Script',
    '.xaml': 'XAML',

    # Shell and Scripts
    '.sh': 'Shell Script',
    '.bash': 'Bash Script',
    '.zsh': 'Zsh Script',
    '.fish': 'Fish Script',
    '.ps1': 'PowerShell',
    '.bat': 'Batch File',
    '.cmd': 'Windows Command',
    '.nu': 'Nushell Script',

    # Ruby and Related
    '.rb': 'Ruby',
    '.erb': 'Ruby ERB Template',
    '.rake': 'Ruby Rake',
    '.gemspec': 'Ruby Gem Spec',

    # Other Programming Languages
    '.pl': 'Perl',
    '.pm': 'Perl Module',
    '.ex': 'Elixir',
    '.exs': 'Elixir Script',
    '.erl': 'Erlang',
    '.hrl': 'Erlang Header',
    '.hs': 'Haskell',
    '.lhs': 'Literate Haskell',
    '.lua': 'Lua',
    '.r': 'R',
    '.rmd': 'R Markdown',
    '.jl': 'Julia',
    '.dart': 'Dart',
    '.nim': 'Nim',
    '.ml': 'OCaml',
    '.mli': 'OCaml Interface',

    # Configuration and Data
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.toml': 'TOML',
    '.ini': 'INI',
    '.conf': 'Configuration',
    '.config': 'Configuration',
    '.env': 'Environment Variables',
    '.properties': 'Properties',
    '.xml': 'XML',
    '.xsd': 'XML Schema',
    '.dtd': 'Document Type Definition',
    '.csv': 'CSV',
    '.tsv': 'TSV',

    # Documentation and Text
    '.md': 'Markdown',
    '.mdx': 'MDX',
    '.rst': 'reStructuredText',
    '.txt': 'Plain Text',
    '.tex': 'LaTeX',
    '.adoc': 'AsciiDoc',
    '.wiki': 'Wiki Markup',
    '.org': 'Org Mode',

    # Database
    '.sql': 'SQL',
    '.psql': 'PostgreSQL',
    '.plsql': 'PL/SQL',
    '.tsql': 'T-SQL',
    '.prisma': 'Prisma Schema',

    # Build and Package
    '.gradle': 'Gradle',
    '.maven': 'Maven POM',
    '.cmake': 'CMake',
    '.make': 'Makefile',
    '.dockerfile': 'Dockerfile',
    '.containerfile': 'Container File',
    '.nix': 'Nix Expression',

    # Web Assembly
    '.wat': 'WebAssembly Text',
    '.wasm': 'WebAssembly Binary',

    # GraphQL
    '.graphql': 'GraphQL',
    '.gql': 'GraphQL',

    # Protocol Buffers and gRPC
    '.proto': 'Protocol Buffers',

    # Mobile Development
    '.xcodeproj': 'Xcode Project',
    '.pbxproj': 'Xcode Project',
    '.gradle': 'Android Gradle',
    '.plist': 'Property List',

    # Game Development
    '.unity': 'Unity Scene',
    '.prefab': 'Unity Prefab',
    '.godot': 'Godot Resource',
    '.tscn': 'Godot Scene',

    # AI/ML
    '.onnx': 'ONNX Model',
    '.h5': 'HDF5 Model',
    '.pkl': 'Pickle Model',
    '.model': 'Model File',
}

# Set of all text extensions for quick lookup
TEXT_EXTENSIONS = set(FILE_EXTENSIONS.keys())

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

def process_repository(repo_path: str) -> Tuple[int, Dict[str, int], Dict[str, int]]:
    """Process all files in the repository and count tokens."""
    total_tokens = 0
    extension_stats = {}  # {ext: (tokens, file_count)}
    file_counts = {}  # {ext: count}

    # Define directories to exclude
    exclude_dirs = {'.git', 'venv', '.venv', '__pycache__', '.pytest_cache', '.mypy_cache'}

    # Get list of all files for progress bar
    all_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            file_path = os.path.join(root, file)
            extension = os.path.splitext(file)[1].lower()
            if extension in FILE_EXTENSIONS and not is_binary(file_path):
                all_files.append((file_path, extension))
                file_counts[extension] = file_counts.get(extension, 0) + 1

    # Process files with progress bar
    for file_path, extension in tqdm(all_files, desc="Processing files"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tokens = count_tokens(content)
                total_tokens += tokens
                if extension not in extension_stats:
                    extension_stats[extension] = tokens
                else:
                    extension_stats[extension] += tokens
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    return total_tokens, extension_stats, file_counts

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
        print("Usage: python token_counter.py <repository_url_or_path>")
        sys.exit(1)

    target = sys.argv[1]

    # Check if the target is a local directory
    if os.path.isdir(target):
        print(f"Analyzing local directory: {target}")
        analyze_path = target
    else:
        # Create a temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        try:
            print(f"Cloning repository: {target}")
            repo = Repo.clone_from(target, temp_dir)
            analyze_path = temp_dir
        except Exception as e:
            print(f"Error cloning repository: {str(e)}")
            shutil.rmtree(temp_dir)
            sys.exit(1)

    print("\nAnalyzing repository...")
    try:
        total_tokens, extension_stats, file_counts = process_repository(analyze_path)
    except Exception as e:
        print(f"Error analyzing repository: {str(e)}")
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        sys.exit(1)

    # Print results
    print("\nResults:")
    print(f"Total tokens: {format_number(total_tokens)} ({total_tokens:,})")
    print("\nTokens by file extension:")
    for ext, count in sorted(extension_stats.items(), key=lambda x: x[1], reverse=True):
        files = file_counts[ext]
        print(f"{ext:8} {format_number(count):>8} ({count:,}) [{files} file{'s' if files != 1 else ''}]")

    # Group results by technology category
    tech_stats = {}
    tech_file_counts = {}
    for ext, count in extension_stats.items():
        tech = FILE_EXTENSIONS[ext]
        tech_stats[tech] = tech_stats.get(tech, 0) + count
        tech_file_counts[tech] = tech_file_counts.get(tech, 0) + file_counts[ext]

    # Print results by technology
    print("\nTokens by Technology:")
    for tech, count in sorted(tech_stats.items(), key=lambda x: x[1], reverse=True):
        files = tech_file_counts[tech]
        print(f"{tech:20} {format_number(count):>8} ({count:,}) [{files} file{'s' if files != 1 else ''}]")

    # Print context window comparisons
    print("\nContext Window Comparisons:")
    windows = {
        # OpenAI Models
        "GPT-3.5 (4K)": 4096,
        "GPT-4 (8K)": 8192,
        "GPT-4 (32K)": 32768,
        "GPT-4 Turbo (128K)": 128000,

        # Anthropic Models
        "Claude 2 (100K)": 100000,
        "Claude 3 Opus (200K)": 200000,
        "Claude 3 Sonnet (200K)": 200000,
        "Claude 3 Haiku (200K)": 200000,

        # Google Models
        "Gemini Pro (32K)": 32768,
        "PaLM 2 (8K)": 8192,

        # Meta Models
        "Llama 2 (4K)": 4096,
        "Code Llama (100K)": 100000,

        # Other Models
        "Mistral Large (32K)": 32768,
        "Mixtral 8x7B (32K)": 32768,
        "Yi-34B (200K)": 200000,
        "Cohere Command (128K)": 128000,
    }

    for model, window in windows.items():
        percentage = (total_tokens / window) * 100
        print(f"{model:20} {percentage:.1f}% of context window")

    # Clean up temp directory if we created one
    if 'temp_dir' in locals():
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
