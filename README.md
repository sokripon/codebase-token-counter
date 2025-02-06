# Code Token Counter

This tool analyzes Git repositories to count the number of tokens they contain, which is useful for understanding if a codebase can fit within various LLM context windows.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python token_counter.py <repository_url>
```

The tool will:
1. Clone the specified repository
2. Analyze all text-based files
3. Count tokens using OpenAI's tiktoken library
4. Display a summary of token counts
