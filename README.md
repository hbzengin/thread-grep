# ThreadGrep: A multi‐threaded CLI tool that searches for a given word in all files under a directory

This is a multi-threaded command line utility to search all the files in a directory (and its subdirectories) for a given word. For the tool to propery parse text files, files must be in the UTF-8 encoding.

## Quickstart

Create a Python virtual environment. Download dependencies in `requirements.txt`. If using uv package manager, activate the virtual environment and simply call `uv sync`.

## Usage

`python -m threadgrep {path} {word_to_search} {max_threads}`

If `path` is a relative path, it is appended to the current working directory. Else, if `path` is absolute, then it is treated as it is.
