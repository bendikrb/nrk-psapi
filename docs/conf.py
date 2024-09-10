from pathlib import Path
import sys

sys.path.insert(0, Path("../").resolve().as_posix())

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx_autodoc_typehints"]
templates_path = ['_templates']
source_suffix = '.rst'
project = 'NRK Podcast API'
# copyright = '2023, Bendik R. Brenne'
author = '@bendikrb'
version = '0.0.0'
release = '0.0.0'
