import pdoc
import os
from pathlib import Path
import sys
import shutil
import argparse


def create_main_index(base_dir: Path):
    """Creates main index.html linking to all subdirectory documentation"""
    # Create base directory if it doesn't exist
    base_dir.mkdir(parents=True, exist_ok=True)

    subdirs = [d for d in base_dir.iterdir() if d.is_dir()]

    main_index = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AnalyseGNSS Documentation</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            ul {{ list-style-type: none; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>AnalyseGNSS Documentation</h1>
        <ul>
    """

    for subdir in sorted(subdirs):  # Sort subdirs for consistent ordering
        main_index += f'    <li><a href="{subdir.name}/index.html">{subdir.name.upper()}</a></li>\n'

    main_index += """
        </ul>
    </body>
    </html>
    """

    with open(base_dir / "index.html", "w") as f:
        f.write(main_index)


def generate_docs(subdir: str):
    # Add the src directory to Python path so modules can be imported
    sys.path.append(str(Path("src").absolute()))

    # Define directories
    src_dir = Path(f"src/analysegnss/{subdir}")
    doc_dir = Path(f"docs/analysegnss/{subdir}")

    # Clean and create directories
    if doc_dir.exists():
        shutil.rmtree(doc_dir)
    doc_dir.mkdir(parents=True, exist_ok=True)

    # Generate documentation
    module_names = []
    for py_file in src_dir.glob("*.py"):
        # Skip __init__.py
        if py_file.name == "__init__.py":
            continue

        module_name = f"analysegnss.{subdir}.{py_file.stem}"
        module_names.append(module_name)

        # Generate docs and move files to correct location
        pdoc.pdoc(module_name, output_directory=doc_dir)

        # Move files from nested structure to flat structure
        nested_dir = doc_dir / "analysegnss" / subdir
        if nested_dir.exists():
            for file in nested_dir.glob("*.html"):
                file.rename(doc_dir / file.name)
            shutil.rmtree(doc_dir / "analysegnss")

        print(f"Generated documentation for {py_file.name}")

    # Create index.html with proper string formatting
    index_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{subdir.upper()} Documentation Index</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            ul {{ list-style-type: none; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>{subdir.upper()} Module Documentation</h1>
        <ul>
    """

    for module in sorted(module_names):  # Sort modules for consistent ordering
        module_short = module.split(".")[-1]
        index_content += (
            f'    <li><a href="{module_short}.html">{module_short}</a></li>\n'
        )

    index_content += """
        </ul>
    </body>
    </html>
    """

    with open(doc_dir / "index.html", "w") as f:
        f.write(index_content)

    print(f"Documentation generated successfully for {subdir}")

    # Create/update main index
    create_main_index(Path("docs/analysegnss"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate documentation for a specific subdirectory"
    )
    parser.add_argument("subdir", help="Subdirectory name (e.g., rinex, sbf, rtkpos)")
    args = parser.parse_args()

    generate_docs(args.subdir)
