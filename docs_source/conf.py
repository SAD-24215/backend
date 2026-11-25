# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from dotenv import load_dotenv


project = 'Carting Docs'
copyright = '2026, SAD-24215'
author = 'SAD-24215'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

source_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(source_dir, '..'))
dotenv_path = os.path.join(root_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

sys.path.insert(0, root_dir)

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.githubpages',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

# Новый autodoc в Sphinx 9 повреждает аннотации Pydantic (sphinx-doc/sphinx#14337).
autodoc_use_legacy_class_based = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ['_templates']
exclude_patterns = ['build']

language = 'ru'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static'] if os.path.isdir(os.path.join(source_dir, '_static')) else []
html_copy_source = False
