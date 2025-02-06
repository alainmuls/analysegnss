#!/usr/bin:env python3
import sys
from pathlib import Path

import pdoc


def generate_docs():
    # Add the src directory to Python path so modules can be imported
    sys.path.append(str(Path("src").absolute()))

    # Source code directory
    src_dir = Path("src/analysegnss/rinex")
    output_dir = Path("docs/rinex")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all Python files
    python_files = list(src_dir.glob("*.py"))

    for py_file in python_files:
        # Convert file path to module path
        module_name = f"analysegnss.rinex.{py_file.stem}"

        # Generate and save markdown documentation
        pdoc.pdoc(module_name, output_directory=output_dir, format="markdown")

        print(f"Generated documentation for {py_file.name}")


if __name__ == "__main__":
    generate_docs()
