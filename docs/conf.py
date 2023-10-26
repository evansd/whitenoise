from __future__ import annotations

import datetime
import sys
import tomllib
from pathlib import Path

# -- Path setup --------------------------------------------------------------

here = Path(__file__).parent.resolve()
sys.path.insert(0, str(here / ".." / "src"))

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The encoding of source files.
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "WhiteNoise"
copyright = f"2013-{datetime.datetime.today().year}, David Evans"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.


def _get_version() -> str:
    with (here / ".." / "pyproject.toml").open("rb") as fp:
        data = tomllib.load(fp)
    version: str = data["project"]["version"]
    return version


version = _get_version()
# The full version, including alpha/beta/rc tags.
release = version

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = [
    "_build",
    "venv",
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "furo"
html_theme_options = {
    "dark_css_variables": {
        "admonition-font-size": "100%",
        "admonition-title-font-size": "100%",
    },
    "light_css_variables": {
        "admonition-font-size": "100%",
        "admonition-title-font-size": "100%",
    },
}

# Output file base name for HTML help builder.
htmlhelp_basename = "WhiteNoisedoc"

# -- Options for LaTeX output --------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    ("index", "WhiteNoise.tex", "WhiteNoise Documentation", "David Evans", "manual")
]

# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "whitenoise", "WhiteNoise Documentation", ["David Evans"], 1)]

# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "WhiteNoise",
        "WhiteNoise Documentation",
        "David Evans",
        "WhiteNoise",
        "One line description of project.",
        "Miscellaneous",
    )
]

git_tag = f"{version}" if version != "development" else "main"
github_base_url = f"https://github.com/evansd/whitenoise/blob/{git_tag}/src/"
extlinks = {"ghfile": (github_base_url + "%s", "")}
