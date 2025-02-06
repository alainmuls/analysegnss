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
    html_dir = output_dir / "analysegnss" / "rinex"  # . "html"

    # Create output directory
    html_dir.mkdir(parents=True, exist_ok=True)

    # Configure pdoc
    pdoc.render.configure(template_directory=None)

    # Get all Python files
    python_files = list(src_dir.glob("*.py"))

    # Generate documentation for each module
    module_names = []
    for py_file in python_files:
        module_name = f"analysegnss.rinex.{py_file.stem}"
        module_names.append(module_name)
        pdoc.pdoc(module_name, output_directory=html_dir)
        print(f"Generated documentation for {py_file.name}")

    # Create index.html in the html directory
    index_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RINEX Documentation Index</title>
    </head>
    <body>
        <h1>RINEX Module Documentation</h1>
        <ul>
    """

    for module in module_names:
        module_short = module.split(".")[-1]
        index_content += (
            f'    <li><a href="{module_short}.html">{module_short}</a></li>\n'
        )

    index_content += """
        </ul>
    </body>
    </html>
    """

    with open(html_dir / "index.html", "w") as f:
        f.write(index_content)

    print("Created index.html in the html directory")


if __name__ == "__main__":
    generate_docs()
