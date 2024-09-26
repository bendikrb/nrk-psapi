from importlib.metadata import Distribution
from pathlib import Path
import sys

import sphinx_book_theme

sys.path.insert(0, Path("../").resolve().as_posix())

project = 'NRK Podcast API'
author = '@bendikrb'
release = Distribution.from_name("nrk_psapi").version

html_theme = "sphinx_book_theme"
html_theme_path = [sphinx_book_theme.get_html_theme_path()]
html_theme_options = {
    "repository_url": "https://github.com/bendikrb/nrk-psapi",
    "use_repository_button": True,
}

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "enum_tools.autoenum",
]
templates_path = ['_templates']
html_static_path = ["_static"]
intersphinx_mapping = {"python": ("http://docs.python.org/3", None)}

autodoc_typehints = "description"
autodoc_typehints_description_target = "documented_params"

source_suffix = '.rst'
