""" Documentation of Pie Extended: `make docs` (output in docs/_build/html) """
import os
import sys
import warnings

sys.path.insert(0, os.path.abspath(".."))

project = "Pie Extended"
author = "Thibault Clérice"
copyright = "Thibault Clérice, MIT license"
html_title = "Pie Extended"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_click",
    "sphinx_copybutton",
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Examples of the documentation, and sites that refuse bots
linkcheck_ignore = [r"http://localhost", r"https://stackoverflow.com/"]
linkcheck_timeout = 30

# Markdown
myst_enable_extensions = ["colon_fence", "deflist", "attrs_inline"]
myst_heading_anchors = 3

# Python API
autodoc_member_order = "bysource"
# undoc-members: a class without a docstring (but with documented methods) is still listed, and linkable
autodoc_default_options = {"members": True, "undoc-members": True, "show-inheritance": True}
autodoc_typehints = "description"
autodoc_inherit_docstrings = False  # Not the (badly formatted) ones of the libraries we extend
napoleon_use_param = True

# Theme
html_theme = "furo"
html_theme_options = {
    "source_repository": "https://github.com/hipster-philology/nlp-pie-taggers/",
    "source_branch": "master",
    "source_directory": "docs/",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/hipster-philology/nlp-pie-taggers",
            "html": "",
            "class": "",
        },
    ],
}
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True


def _models_table() -> str:
    """ Table of the models, built from their metadata: it cannot get out of date """
    warnings.simplefilter("ignore")
    from pie_extended.cli.utils import get_list

    rows = ["| Model | Language | Name | Authors | More |", "|---|---|---|---|---|"]
    for module, desc in get_list():
        rows.append("| `{}` | `{}` | {} | {} | {} |".format(
            module, desc.lang, desc.title, ", ".join(desc.authors) if desc.authors else "",
            "[link]({})".format(desc.link) if str(desc.link).startswith(("http://", "https://")) else ""
        ))
    return "\n".join(rows) + "\n"


def _write_generated(app=None):
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_generated")
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, "models_table.md"), "w", encoding="utf-8") as f:
        f.write(_models_table())


def setup(app):
    app.connect("builder-inited", _write_generated)
